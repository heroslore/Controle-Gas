# -*- coding: utf-8 -*-
"""
Modelo de Regressão Ridge Polinomial para estimativa de NPP
Localidade: BA, Mata Atlântica, Cerrado e Caatinga | Período: 2001-2020 (n=240 observações mensais)

Autor: 
PPGCTA — Programa de Pós-Graduação em Ciências e Tecnologia Ambiental
"""

# =============================================================================
# IMPORTAÇÕES
# =============================================================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats

from itertools import combinations
from datetime import datetime

from scipy.stats.mstats import winsorize                          # tratamento de outliers

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.model_selection import RepeatedKFold, GridSearchCV

from statsmodels.stats.outliers_influence import variance_inflation_factor

# =============================================================================
# DIRETÓRIO BASE — todos os arquivos de entrada e saída ficam na pasta do script
# =============================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def caminho(nome):
    return os.path.join(BASE_DIR, nome)

# =============================================================================
# LISTAS PARA ARMAZENAR ESTATÍSTICAS DE TODOS OS FOLDS
# =============================================================================

lista_r2_treino    = []
lista_r2_teste     = []
lista_r2aj_treino  = []
lista_rmse_teste   = []
lista_mae_teste    = []
lista_f            = []
lista_p_valor      = []
alphas_escolhidos  = []

# =============================================================================
# INICIALIZAÇÃO DOS ARQUIVOS DE SAÍDA
# Zera os arquivos a cada execução para evitar acúmulo de rodadas anteriores
# =============================================================================

for f in ["melhores_combinacoes_20.txt", "melhores_combinacoes_60.txt", "melhores_combinacoes.txt",
          "linhas_analisadas_ordem.txt"]:
    open(caminho(f), "w").close()

# Arquivo de controle: registra os conjuntos de linhas de teste já processados.
# Permite retomar a execução do ponto onde parou em caso de interrupção.
with open(caminho("linhas_analisadas_ordem.txt"), "a+") as armazena_linhas_analisadas:
    armazena_linhas_analisadas.seek(0)
    conteudo_arquivo_linhas = armazena_linhas_analisadas.read()

# =============================================================================
# CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS
# =============================================================================

dados_total = pd.read_excel(caminho('Dados_Benfica_.xlsx'))

# Remove espaços invisíveis nos nomes das colunas (problema comum em planilhas Excel)
dados_total.columns = dados_total.columns.str.strip()

# Sazonalidade harmônica: decompõe o ciclo anual em duas componentes ortogonais.
# saz_sin e saz_cos descrevem completamente qualquer ciclo periódico de 12 meses
# sem impor linearidade no tempo (diferente de usar o número do mês diretamente).
dados_total['saz_sin'] = np.sin(2 * np.pi * dados_total['MÊS'] / 12)
dados_total['saz_cos'] = np.cos(2 * np.pi * dados_total['MÊS'] / 12)

# Transformação log(1+x) em área queimada: normaliza a distribuição fortemente
# assimétrica de BURN_MA, que concentra zeros e possui raros picos muito elevados.
dados_total['BURN_MA_log'] = np.log1p(dados_total['BURN_MA'])
dados_total['BURN_CE_log'] = np.log1p(dados_total['BURN_CE'])
dados_total['BURN_CA_log'] = np.log1p(dados_total['BURN_CA'])

# =============================================================================
# DEFINIÇÃO DO BIOMA ATIVO E VARIÁVEIS DO MODELO
# =============================================================================

BIOMA_ATIVO = 'CE'  # ← altere aqui: 'MA', 'CE' ou 'CA'

config_biomas = {
    'MA': {
        'nome':     'Mata Atlântica',
        'y':        'NP_MA',
        'x':        ['EV_MA', 'PRE_MA', 'TST_MA', 'saz_sin', 'saz_cos'],
        'winsor_y': 'NP_MA',
    },
    'CE': {
        'nome':     'Cerrado',
        'y':        'NP_CE',
        'x':        ['EV_CE', 'PRE_CE', 'WAI_CE', 'saz_sin', 'saz_cos'],
        'winsor_y': 'NP_CE',
    },
    'CA': {
        'nome':     'Caatinga',
        'y':        'NP_CA',
        'x':        ['EV_CA', 'PRE_CA', 'TST_CA', 'saz_sin', 'saz_cos'],
        'winsor_y': 'NP_CA',
    },
}

cfg       = config_biomas[BIOMA_ATIVO]
colunas_y = [cfg['y']]
colunas_x = cfg['x']

print(f"\n===== RODANDO MODELO RIDGE — {cfg['nome'].upper()} =====")
print(f"Variável resposta : {cfg['y']}")
print(f"Preditores        : {colunas_x}\n")

# Winsorização da variável resposta: substitui os 3% menores valores
# pelo percentil 3%, reduzindo a influência de outliers extremos nos resíduos
# sem remover observações do conjunto de dados.
dados_total[cfg['winsor_y']] = winsorize(dados_total[cfg['winsor_y']], limits=[0.03, 0.0])

dados_x = dados_total[colunas_x]
dados_y = dados_total[colunas_y]

# =============================================================================
# CONFIGURAÇÃO DA BUSCA POR COMBINAÇÕES
# MA: 5 variáveis candidatas → C(5,5) = 1 combinação.
# MA/CE/CA: 7 variáveis candidatas → C(7,5) = 21 combinações.
# =============================================================================

numero_colunas_agrupamento = 5
lista_comb_colunas = list(combinations(colunas_x, numero_colunas_agrupamento))

# =============================================================================
# CONFIGURAÇÃO DO GRAU POLINOMIAL
# ─────────────────────────────────────────────────────────────────────────────
# GRAU_MODELO  → grau usado no modelo principal (validação cruzada completa).
#                Altere este valor para rodar o modelo com o grau desejado.
#
# TESTAR_GRAUS → ativa a comparação automática de graus ao final do script.
#                True  = compara todos os graus de 1 até GRAU_MAXIMO_TESTE.
#                False = pula a comparação (execução mais rápida).
#
# GRAU_MAXIMO_TESTE → até qual grau comparar quando TESTAR_GRAUS = True.
#                     Recomendado: máximo 5 (acima disso há overfitting severo
#                     com n=240 e 5 variáveis preditoras).
# =============================================================================

GRAU_MODELO       = 2     # ← altere aqui o grau do modelo principal
TESTAR_GRAUS      = False  # ← True para comparar graus | False para pular
GRAU_MAXIMO_TESTE = 5     # ← até qual grau comparar (válido se TESTAR_GRAUS=True)

# =============================================================================
# CONFIGURAÇÃO DA VALIDAÇÃO CRUZADA
# RepeatedKFold com 5 splits e 30 repetições = 150 folds independentes.
# Garante estimativa robusta e intervalo de confiança confiável do R².
# =============================================================================

rkf = RepeatedKFold(
    n_splits=5,
    n_repeats=30,
    random_state=42        # semente fixa para reprodutibilidade
)

# Contadores e controle de progresso
qtd_rodadas_linhas = 150                               # total de folds (5 splits × 30 repeats)
tot_rodadas        = qtd_rodadas_linhas * len(lista_comb_colunas)
rodada             = 0
data_e_hora_atual  = datetime.now()

# Variáveis para rastrear o melhor resultado por fold
r2_treino_melhor                = 0
r2_teste_melhor                 = 0
melhor_parametos_equacao_treino = ''

# =============================================================================
# LOOP PRINCIPAL DE VALIDAÇÃO CRUZADA
# =============================================================================

for train_index, test_index in rkf.split(dados_x):

    # Separação treino/teste para X e Y
    x_train  = dados_x.iloc[train_index]
    x_test   = dados_x.iloc[test_index]
    y_treino = dados_y.iloc[train_index]
    y_teste  = dados_y.iloc[test_index]

    # Converte índices para lista ordenada de inteiros (para controle de duplicatas)
    linhas_treino = str(sorted([int(v) for v in x_train.index]))
    linhas_teste  = str(sorted([int(v) for v in x_test.index]))

    # Verifica se este conjunto de linhas de teste já foi processado em execução anterior
    if linhas_teste not in conteudo_arquivo_linhas:

        # Registra o conjunto de teste para evitar reprocessamento
        with open(caminho('linhas_analisadas_ordem.txt'), 'a+') as armazena_linhas:
            armazena_linhas.writelines(linhas_teste + '\n')

        melhor_resultado_treino = '\n\nNenhum resultado com R² treino e teste > 60%'

        # -----------------------------------------------------------------
        # LOOP INTERNO: itera sobre as combinações de variáveis preditoras
        # (no modelo final há apenas 1 combinação; loop preservado por compatibilidade)
        # -----------------------------------------------------------------
        for i in lista_comb_colunas:

            x_treino = x_train[list(i)]
            x_teste  = x_test[list(i)]

            # Garante alinhamento correto de índices entre X e Y
            y_treino = dados_y.loc[x_treino.index]
            y_teste  = dados_y.loc[x_teste.index]

            rodada += 1

            # ---------------------------------------------------------------
            # ETAPA 1: Padronização (StandardScaler)
            # Transforma cada variável para média 0 e desvio-padrão 1.
            # Necessário para que a regularização Ridge trate os coeficientes
            # de forma equitativa, independente da escala original das variáveis.
            # ---------------------------------------------------------------
            scaler          = StandardScaler()
            x_treino_scaled = scaler.fit_transform(x_treino)  # ajusta e transforma treino
            x_teste_scaled  = scaler.transform(x_teste)       # apenas transforma (sem reajuste)

            # ---------------------------------------------------------------
            # ETAPA 2: Expansão Polinomial
            # O grau é definido pela variável GRAU_MODELO no topo do script.
            # Gera termos polinomiais e de interação entre variáveis.
            # ---------------------------------------------------------------
            poly          = PolynomialFeatures(degree=GRAU_MODELO, include_bias=False)
            X_treino_poly = poly.fit_transform(x_treino_scaled)
            X_teste_poly  = poly.transform(x_teste_scaled)

            # ---------------------------------------------------------------
            # ETAPA 3: Regressão Ridge com seleção automática de alpha
            # GridSearchCV testa 5 valores de alpha via validação cruzada interna (cv=5).
            # O alpha controla a força da regularização L2 que penaliza coeficientes
            # grandes, evitando overfitting causado pela expansão polinomial.
            # ---------------------------------------------------------------
            alphas   = [0.1, 1.0, 10.0, 50.0, 100.0]
            ridge_cv = GridSearchCV(Ridge(),
                                    param_grid={'alpha': alphas},
                                    cv=5,
                                    scoring='r2')
            ridge_cv.fit(X_treino_poly, y_treino.values.ravel())

            # Reutiliza o melhor estimador e o re-treina no conjunto completo de treino
            maquina_preditiva = ridge_cv.best_estimator_
            maquina_preditiva.fit(X_treino_poly, y_treino.values.ravel())
            alphas_escolhidos.append(ridge_cv.best_params_['alpha'])

            # ---------------------------------------------------------------
            # PREDIÇÃO E CÁLCULO DO R²
            # ---------------------------------------------------------------
            y_pred   = maquina_preditiva.predict(X_treino_poly)
            r2       = r2_score(y_treino, y_pred) * 100           # R² treino (%)

            y_pred_teste = maquina_preditiva.predict(X_teste_poly)
            r2_teste     = r2_score(y_teste, y_pred_teste) * 100  # R² teste (%)

            # ---------------------------------------------------------------
            # MÉTRICAS COMPLEMENTARES
            # ---------------------------------------------------------------

            # Erros de predição no conjunto de teste
            rmse_teste = np.sqrt(mean_squared_error(y_teste, y_pred_teste))
            mae_teste  = mean_absolute_error(y_teste, y_pred_teste)

            # Tamanhos dos conjuntos e número de preditores após expansão polinomial
            n_tr = len(y_treino)
            n_te = len(y_teste)
            k    = X_treino_poly.shape[1]   # 20 termos para 5 variáveis (grau 2)

            R2_tr = r2 / 100
            R2_te = r2_teste / 100

            # R² ajustado: penaliza pelo número de preditores, evitando inflação do R²
            r2aj_tr = 1 - (1 - R2_tr) * (n_tr - 1) / (n_tr - k - 1)

            # Métrica complementar — calculada no treino para verificação de significância global
            # Estatística F: testa se o modelo é globalmente significativo
            # H0: todos os coeficientes são zero (modelo nulo)
            F       = (R2_tr / k) / ((1 - R2_tr) / (n_tr - k - 1))
            p_valor = 1 - stats.f.cdf(F, k, n_tr - k - 1)

            # Armazena resultados de todos os folds para as estatísticas finais
            lista_r2_treino.append(r2)
            lista_r2_teste.append(r2_teste)
            lista_r2aj_treino.append(r2aj_tr * 100)
            lista_rmse_teste.append(rmse_teste)
            lista_mae_teste.append(mae_teste)
            lista_f.append(F)
            lista_p_valor.append(p_valor)

            # ---------------------------------------------------------------
            # FORMATAÇÃO DO RESULTADO E CONTROLE DE TEMPO
            # ---------------------------------------------------------------
            resultado = (
                f'\n#################  Rodada {rodada} / {tot_rodadas}  '
                f'{round((rodada / tot_rodadas) * 100, 2)} %'
                f'\nParâmetros {i}'
                f'\nLinhas de Treino {linhas_treino}'
                f'\nLinhas de Teste {linhas_teste}'
                f'\nR2 de Treino = {round(r2, 2)}'
                f'\nR2 de Teste = {round(r2_teste, 2)}'
            )
            parametos_equacao = (
                f'Coeficientes (pesos): {maquina_preditiva.coef_}'
                f'\nInterceptor (constante): {maquina_preditiva.intercept_}'
            )

            data_e_hora_pos   = datetime.now()
            tempo_restante    = (data_e_hora_pos - data_e_hora_atual) * (tot_rodadas - rodada)
            data_e_hora_atual = datetime.now()

            # Imprime no terminal apenas folds com R² treino e teste > 50%
            if r2 > 50 and r2_teste > 50:
                print(resultado)
                print(f'\n{rodada} / {tot_rodadas}  {round((rodada / tot_rodadas) * 100, 2)} %'
                      f'\nTempo restante {tempo_restante}')

            # ---------------------------------------------------------------
            # SALVAMENTO DOS RESULTADOS EM ARQUIVO
            # melhores_combinacoes_20.txt → todos os folds (sem filtro)
            # melhores_combinacoes_60.txt → folds com R² treino>50% e teste>60%
            # melhores_combinacoes.txt    → melhor resultado por fold
            # ---------------------------------------------------------------
            with open(caminho('melhores_combinacoes_20.txt'), 'a') as armazena_resultado:
                armazena_resultado.write(resultado + '\n')

            if r2_teste > 60 and r2 > 50:
                with open(caminho('melhores_combinacoes_60.txt'), 'a') as armazena_resultado:
                    armazena_resultado.write(resultado + '\n')
                    armazena_resultado.write(parametos_equacao + '\n')

            # Atualiza o melhor resultado de treino do fold atual
            if r2 > r2_treino_melhor:
                r2_treino_melhor                = r2
                melhor_parametos_equacao_treino = parametos_equacao
                melhor_resultado_treino         = (
                    f'\nRodada {rodada} / {tot_rodadas}  '
                    f'{round((rodada / tot_rodadas) * 100, 2)} %'
                    f'\nParâmetros {i}'
                    f'\nR2 de Treino = {round(r2, 2)}'
                    f'\nR2 de Teste = {round(r2_teste, 2)}'
                )

            if r2_teste > r2_teste_melhor:
                r2_teste_melhor = r2_teste

        # Salva o melhor resultado (treino) encontrado no fold atual
        with open(caminho('melhores_combinacoes.txt'), 'a') as armazena_melhor_resultado:
            armazena_melhor_resultado.write(
                f'\n********* Melhor Resultado do Fold ************'
                f'\nLinhas de Treino {linhas_treino}'
                f'\nLinhas de Teste {linhas_teste}'
                f'\n{melhor_resultado_treino}\n'
                f'{melhor_parametos_equacao_treino}\n\n'
            )

        # Reinicia os melhores para o próximo fold
        r2_treino_melhor = 0
        r2_teste_melhor  = 0

    else:
        # Fold já processado: ajusta o contador de rodadas sem reprocessar
        rodada = rodada + (tot_rodadas / qtd_rodadas_linhas)

# Marca o fim da execução no arquivo de controle
with open(caminho('linhas_analisadas_ordem.txt'), 'a+') as armazena_linhas:
    armazena_linhas.write('\n')

# =============================================================================
# ESTATÍSTICAS GERAIS (RESUMO DE TODOS OS FOLDS)
# =============================================================================

print("\nDiretório atual:", os.getcwd())

print("\n===== ESTATÍSTICAS GERAIS =====")
print("R2 Treino médio:",                  round(np.mean(lista_r2_treino),    2))
print("R2 Treino desvio padrão:",          round(np.std(lista_r2_treino),     2))
print("R2 Ajustado Treino médio:",         round(np.mean(lista_r2aj_treino),  2))
print("R2 Ajustado Treino desvio padrão:", round(np.std(lista_r2aj_treino),   2))
print("R2 Teste médio:",                   round(np.mean(lista_r2_teste),     2))
print("R2 Teste desvio padrão:",           round(np.std(lista_r2_teste),      2))
print("RMSE Teste médio:",                 round(np.mean(lista_rmse_teste),   2))
print("MAE Teste médio:",                  round(np.mean(lista_mae_teste),    2))
print("MAE Teste desvio padrão:",          round(np.std(lista_mae_teste),     2))
print("F médio:",                          round(np.mean(lista_f),            2))
print("p-valor médio:",                    np.mean(lista_p_valor))

# Intervalo de confiança empírico de 95% do R² de teste (percentis 2,5 e 97,5)
ic_lower = np.percentile(lista_r2_teste, 2.5)
ic_upper = np.percentile(lista_r2_teste, 97.5)
print(f"\nIC 95% R² Teste: [{ic_lower:.2f}% — {ic_upper:.2f}%]")

# =============================================================================
# DIAGNÓSTICO DE MULTICOLINEARIDADE — VIF (Variance Inflation Factor)
# Calculado sobre as variáveis originais (antes da expansão polinomial).
# Referência: VIF < 5 aceitável | 5-10 moderado | > 10 grave
# =============================================================================

from statsmodels.tools import add_constant
X_vif   = dados_total[colunas_x].dropna()
X_const = add_constant(X_vif)

vif_data = pd.DataFrame({
    "Variável": X_vif.columns,
    "VIF": [variance_inflation_factor(X_const.values, i+1)
            for i in range(X_vif.shape[1])]
})

print("\n===== VIF =====")
print(vif_data)

# =============================================================================
# ANÁLISE DE RESÍDUOS — MODELO AJUSTADO EM TODOS OS DADOS
# O modelo é ajustado no conjunto completo (n=240) apenas para diagnóstico visual.
# A avaliação preditiva real é feita pela validação cruzada acima.
# =============================================================================


X_full = dados_total[colunas_x].values
y_full = dados_total[colunas_y].values.ravel()

# Padronização e expansão polinomial no conjunto completo
scaler_full = StandardScaler()
X_sc        = scaler_full.fit_transform(X_full)

poly_full = PolynomialFeatures(degree=GRAU_MODELO, include_bias=False)
X_poly    = poly_full.fit_transform(X_sc)

# Ajuste do modelo com alpha médio dos folds para diagnóstico de resíduos
alpha_medio  = np.mean(alphas_escolhidos)
print(f"Alpha médio utilizado na análise de resíduos: {alpha_medio:.4f}")
modelo_final = Ridge(alpha=alpha_medio)
modelo_final.fit(X_poly, y_full)

# =============================================================================
# EXPORTAÇÃO DOS COEFICIENTES DO MODELO FINAL
# =============================================================================

nomes_features = poly_full.get_feature_names_out(colunas_x)
coef_final = pd.DataFrame({
    'feature': nomes_features,
    'coef':    modelo_final.coef_,
    'bioma':   BIOMA_ATIVO
})
coef_final.to_csv(caminho(f'coeficientes_ridge_{BIOMA_ATIVO}.csv'), index=False)
print(f"Arquivo coeficientes_ridge_{BIOMA_ATIVO}.csv salvo com sucesso!")
print(coef_final)

y_pred_full = modelo_final.predict(X_poly)
residuos    = y_full - y_pred_full

# Teste de Shapiro-Wilk: verifica normalidade dos resíduos
# H0: resíduos seguem distribuição normal (p > 0.05 → não rejeita H0)
stat_sw, p_sw = stats.shapiro(residuos)
print(f"\n===== NORMALIDADE DOS RESÍDUOS =====")
print(f"Shapiro-Wilk: stat={stat_sw:.4f}, p={p_sw:.4f}")
print("Resíduos normais" if p_sw > 0.05 else "Resíduos NÃO normais")

# =============================================================================
# GRÁFICOS DE DIAGNÓSTICO DOS RESÍDUOS
# Painel 1: Resíduos vs Valores Ajustados — detecta heterocedasticidade
# Painel 2: QQ-Plot — avalia aderência à distribuição normal
# Painel 3: Histograma dos resíduos — visualiza a forma da distribuição
# =============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Painel 1 — Resíduos vs Valores Ajustados
axes[0].scatter(y_pred_full, residuos, alpha=0.5, color='steelblue')
axes[0].axhline(0, color='red', linestyle='--')
axes[0].set_xlabel('Valores Ajustados')
axes[0].set_ylabel('Resíduos')
axes[0].set_title('Resíduos vs Ajustados')

# Painel 2 — QQ-Plot
stats.probplot(residuos, dist="norm", plot=axes[1])
axes[1].set_title('QQ-Plot dos Resíduos')

# Painel 3 — Histograma
axes[2].hist(residuos, bins=30, color='steelblue', edgecolor='white')
axes[2].set_xlabel('Resíduo')
axes[2].set_ylabel('Frequência')
axes[2].set_title('Distribuição dos Resíduos')

plt.tight_layout()
plt.savefig(caminho('analise_residuos.png'), dpi=150)
plt.show()
print("Gráfico salvo em analise_residuos.png")

# =============================================================================
# Y-RANDOMIZATION
# Verifica se o desempenho do modelo é genuíno e não produto de overfitting
# ou coincidência numérica. A variável resposta (NPP) é permutada 100 vezes
# e o modelo é reajustado em cada permutação, mantendo a mesma estrutura.
# Critério de aprovação: diferença > 60 pp entre R² original e R² permutado.
# Herdado de Guimarães et al. (2024).
# =============================================================================

print("\n===== Y-RANDOMIZATION (100 permutações) =====")

lista_r2_permutado = []

X_yr = dados_total[colunas_x].values
y_yr = dados_total[colunas_y].values.ravel().copy()

scaler_yr = StandardScaler()
X_yr_sc   = scaler_yr.fit_transform(X_yr)

poly_yr  = PolynomialFeatures(degree=GRAU_MODELO, include_bias=False)
X_yr_pol = poly_yr.fit_transform(X_yr_sc)

np.random.seed(42)

for perm in range(100):
    y_perm = y_yr.copy()
    np.random.shuffle(y_perm)

    modelo_yr = Ridge(alpha=alpha_medio)
    modelo_yr.fit(X_yr_pol, y_perm)

    r2_perm = r2_score(y_perm, modelo_yr.predict(X_yr_pol)) * 100
    lista_r2_permutado.append(r2_perm)

    if (perm + 1) % 10 == 0:
        print(f"  Permutação {perm+1}/100 — R² = {r2_perm:.2f}%")

r2_original_insample = r2_score(y_full, y_pred_full) * 100
r2_perm_medio        = np.mean(lista_r2_permutado)
diferenca            = r2_original_insample - r2_perm_medio

print(f"\nR² in-sample (modelo original)  : {r2_original_insample:.2f}%")
print(f"R² in-sample permutado (médio)  : {r2_perm_medio:.2f}%")
print(f"Diferença (Δ)                   : {diferenca:.2f} pp")

if diferenca >= 60:
    print(f"✅ Y-randomization APROVADO — diferença de {diferenca:.2f} pp > 60 pp")
else:
    print(f"⚠️  Y-randomization REPROVADO — diferença de {diferenca:.2f} pp < 60 pp")

fig_yr, ax_yr = plt.subplots(figsize=(8, 5))
ax_yr.hist(lista_r2_permutado, bins=25, color='lightgray',
           edgecolor='white', label='R² modelos permutados')
ax_yr.axvline(r2_perm_medio, color='green', linestyle='--',
              linewidth=2, label=f'Média permutados ({r2_perm_medio:.2f}%)')
ax_yr.axvline(r2_original_insample, color='red', linestyle='-',
              linewidth=2, label=f'R² modelo original ({r2_original_insample:.2f}%)')
ax_yr.set_xlabel('R² do teste (%)')
ax_yr.set_ylabel('Frequência')
status = 'APROVADO' if diferenca >= 60 else 'REPROVADO'
ax_yr.set_title(f'Y-Randomization — {cfg["nome"]}  |  Δ = {diferenca:.2f} pp  |  {status}')
ax_yr.legend()
plt.tight_layout()
plt.savefig(caminho(f'yrandomization_{BIOMA_ATIVO}.png'), dpi=150, bbox_inches='tight')
plt.show()
print(f"Gráfico salvo em yrandomization_{BIOMA_ATIVO}.png")

# =============================================================================
# SELEÇÃO DO GRAU POLINOMIAL ÓTIMO
# Executado apenas se TESTAR_GRAUS = True (configurado no topo do script).
#
# Testa graus de 1 até GRAU_MAXIMO_TESTE usando a mesma validação cruzada
# do modelo principal (RepeatedKFold 5×30 = 150 folds).
# Critério de seleção: maior R² teste com menor gap treino-teste (overfitting).
#
# Referência: Guimarães et al. (2024) testaram graus de 1 a 8 e selecionaram
# o grau 4 como ótimo para dados moleculares. Para dados ambientais com
# n=240 e 5 preditores, o grau ótimo pode diferir — daí a importância
# de rodar este teste com seus próprios dados.
# =============================================================================

if TESTAR_GRAUS:

    print(f"\n===== SELEÇÃO DO GRAU POLINOMIAL (graus 1 a {GRAU_MAXIMO_TESTE}) =====")
    print("Aguarde — rodando 150 folds para cada grau...\n")

    from sklearn.utils import shuffle as sk_shuffle

    resultados_graus = {}

    for degree in range(1, GRAU_MAXIMO_TESTE + 1):

        lst_r2_tr = []
        lst_r2_te = []
        lst_rmse  = []
        lst_mae   = []

        rkf_grau = RepeatedKFold(n_splits=5, n_repeats=30, random_state=42)

        for tr_idx, te_idx in rkf_grau.split(dados_x):
            x_tr = dados_x.iloc[tr_idx]
            x_te = dados_x.iloc[te_idx]
            y_tr = dados_y.iloc[tr_idx]
            y_te = dados_y.iloc[te_idx]

            sc   = StandardScaler()
            xtr_sc = sc.fit_transform(x_tr)
            xte_sc = sc.transform(x_te)

            pf     = PolynomialFeatures(degree=degree, include_bias=False)
            Xtr_p  = pf.fit_transform(xtr_sc)
            Xte_p  = pf.transform(xte_sc)

            rc = GridSearchCV(Ridge(),
                              param_grid={'alpha': [0.1, 1.0, 10.0, 50.0, 100.0]},
                              cv=5, scoring='r2')
            rc.fit(Xtr_p, y_tr.values.ravel())
            m = rc.best_estimator_
            m.fit(Xtr_p, y_tr.values.ravel())

            lst_r2_tr.append(r2_score(y_tr, m.predict(Xtr_p)) * 100)
            lst_r2_te.append(r2_score(y_te, m.predict(Xte_p)) * 100)
            lst_rmse.append(np.sqrt(mean_squared_error(y_te, m.predict(Xte_p))))
            lst_mae.append(mean_absolute_error(y_te, m.predict(Xte_p)))

        n_termos = PolynomialFeatures(degree=degree,
                                      include_bias=False).fit_transform(
                                      np.zeros((1, len(colunas_x)))).shape[1]

        resultados_graus[degree] = {
            'r2_treino' : np.mean(lst_r2_tr),
            'r2_teste'  : np.mean(lst_r2_te),
            'std_teste' : np.std(lst_r2_te),
            'overfitting': np.mean(lst_r2_tr) - np.mean(lst_r2_te),
            'rmse'      : np.mean(lst_rmse),
            'mae'       : np.mean(lst_mae),
            'ic_lower'  : np.percentile(lst_r2_te, 2.5),
            'ic_upper'  : np.percentile(lst_r2_te, 97.5),
            'n_termos'  : n_termos,
        }

        r = resultados_graus[degree]
        marca = ' ◄ MODELO ATUAL' if degree == GRAU_MODELO else ''
        print(f"  Grau {degree} | {n_termos:>3} termos | "
              f"R²treino={r['r2_treino']:.1f}% | "
              f"R²teste={r['r2_teste']:.1f}% | "
              f"Overfit={r['overfitting']:.1f}p.p | "
              f"RMSE={r['rmse']:.4f}{marca}")

    # ── Tabela resumo ────────────────────────────────────────────────────────
    print("\n" + "="*90)
    print(f"{'Grau':>5} | {'Termos':>6} | {'R²Treino':>9} | {'R²Teste':>8} | "
          f"{'Std':>6} | {'Overfit':>9} | {'RMSE':>8} | IC 95% Teste")
    print("="*90)
    melhor_grau = max(resultados_graus,
                      key=lambda d: resultados_graus[d]['r2_teste'] -
                                    0.5 * resultados_graus[d]['overfitting'])
    for d, r in resultados_graus.items():
        marca = ' ◄ ÓTIMO' if d == melhor_grau else ''
        marca += ' ◄ ATUAL' if d == GRAU_MODELO and d != melhor_grau else ''
        print(f"{d:>5} | {r['n_termos']:>6} | {r['r2_treino']:>8.1f}% | "
              f"{r['r2_teste']:>7.1f}% | {r['std_teste']:>5.1f}% | "
              f"{r['overfitting']:>8.1f}p.p | {r['rmse']:>8.4f} | "
              f"[{r['ic_lower']:.1f}% — {r['ic_upper']:.1f}%]{marca}")
    print("="*90)
    print(f"\nGrau sugerido pelo critério R²teste − 0.5×overfitting: {melhor_grau}")
    if melhor_grau == GRAU_MODELO:
        print(f"✅ O grau atual ({GRAU_MODELO}) já é o ótimo para estes dados.")
    else:
        print(f"⚠️  Considere alterar GRAU_MODELO de {GRAU_MODELO} para {melhor_grau} "
              f"e rodar novamente.")

    # ── Gráfico ──────────────────────────────────────────────────────────────
    graus      = list(resultados_graus.keys())
    r2_trs     = [resultados_graus[d]['r2_treino']   for d in graus]
    r2_tes     = [resultados_graus[d]['r2_teste']    for d in graus]
    stds       = [resultados_graus[d]['std_teste']   for d in graus]
    overfits   = [resultados_graus[d]['overfitting'] for d in graus]
    rmses      = [resultados_graus[d]['rmse']        for d in graus]
    n_termos_l = [resultados_graus[d]['n_termos']    for d in graus]

    fig2, axes2 = plt.subplots(1, 3, figsize=(17, 5))

    # Painel 1 — R² treino vs teste
    axes2[0].plot(graus, r2_trs, 'o-', color='steelblue',
                  linewidth=2, markersize=7, label='R² Treino')
    axes2[0].errorbar(graus, r2_tes, yerr=stds, fmt='s--', color='#d62728',
                      linewidth=2, markersize=7, capsize=5,
                      label='R² Teste (±1dp)')
    axes2[0].axvline(melhor_grau, color='green', linestyle=':',
                     alpha=0.7, label=f'Grau ótimo ({melhor_grau})')
    axes2[0].axvline(GRAU_MODELO, color='orange', linestyle='--',
                     alpha=0.7, label=f'Grau atual ({GRAU_MODELO})')
    axes2[0].set_xlabel('Grau Polinomial')
    axes2[0].set_ylabel('R² (%)')
    axes2[0].set_title('R² Treino vs Teste por Grau')
    axes2[0].legend(fontsize=8)
    axes2[0].grid(alpha=0.3)
    axes2[0].set_xticks(graus)

    # Painel 2 — Gap de overfitting
    cores_ov = ['#2ca02c' if o < 10 else '#ff7f0e' if o < 20 else '#d62728'
                for o in overfits]
    bars2 = axes2[1].bar(graus, overfits, color=cores_ov,
                         edgecolor='white', width=0.5)
    for bar, val in zip(bars2, overfits):
        axes2[1].text(bar.get_x() + bar.get_width()/2,
                      bar.get_height() + 0.3,
                      f'{val:.1f}', ha='center', va='bottom', fontsize=9)
    axes2[1].axhline(10, color='orange', linestyle='--',
                     alpha=0.7, label='Limite aceitável (10p.p.)')
    axes2[1].set_xlabel('Grau Polinomial')
    axes2[1].set_ylabel('Treino − Teste (p.p.)')
    axes2[1].set_title('Gap de Overfitting por Grau')
    axes2[1].legend(fontsize=8)
    axes2[1].grid(alpha=0.3)
    axes2[1].set_xticks(graus)

    # Painel 3 — RMSE e número de termos
    ax_twin = axes2[2].twinx()
    axes2[2].plot(graus, rmses, 'o-', color='purple',
                  linewidth=2, markersize=7, label='RMSE')
    ax_twin.bar(graus, n_termos_l, alpha=0.2, color='gray',
                width=0.4, label='Nº termos')
    axes2[2].set_xlabel('Grau Polinomial')
    axes2[2].set_ylabel('RMSE', color='purple')
    ax_twin.set_ylabel('Nº de termos', color='gray')
    axes2[2].set_title('RMSE e Complexidade por Grau')
    axes2[2].grid(alpha=0.3)
    axes2[2].set_xticks(graus)
    l1, lb1 = axes2[2].get_legend_handles_labels()
    l2, lb2 = ax_twin.get_legend_handles_labels()
    axes2[2].legend(l1 + l2, lb1 + lb2, fontsize=8)

    plt.suptitle(
        f'Seleção do Grau Polinomial Ótimo (testados: 1 a {GRAU_MAXIMO_TESTE})',
        fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(caminho('selecao_grau_polinomial.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print("Gráfico salvo em selecao_grau_polinomial.png")
