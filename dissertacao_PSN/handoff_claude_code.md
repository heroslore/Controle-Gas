# Handoff — Modelagem MRMP-N (Dissertação PPGCTA)

## Contexto do projeto

Dissertação de mestrado (PPGCTA — UFSB/IFBA, Porto Seguro):
**"Desenvolvimento de um Modelo de Regressão Múltipla Polinomial de ordem N para
análise de variáveis ambientais na Bahia"** — Ygor Augusto dos Santos Oliveira.
Orientador: Prof. Dr. Fabrício Berton Zanchi. Coorientadora: Profa. Dra. Nayanne
Silva Benfica.

Modelo (MRMP-N): regressão Ridge com expansão polinomial (grau 2), estimando a
Fotossíntese Líquida (PSN) a partir de variáveis climáticas/hídricas, para os
biomas **Mata Atlântica (MA)**, **Cerrado (CE)** e **Caatinga (CA)** na Bahia.
Base original da qualificação: 2001–2020 (n=240). Está sendo atualizada para
2001–2025.

## Arquivos do projeto (estado atual)

- **`Modelo_PSN.py`** — script principal, correto e completo (Y-randomization
  fora da amostra, GroupKFold por ano, TimeSeriesSplit expansível, Ljung-Box/ACF,
  winsorização sem vazamento). É este que deve ser usado para gerar os
  resultados finais — não o `Modelo_Ridge.py` nem o
  `modelo_com__escolha_de_melhor_grau.py` (ambos são versões antigas, sem
  Y-randomization fora da amostra / GroupKFold / TimeSeriesSplit / Ljung-Box).
  Melhorias já aplicadas nele:
  - Detecta sozinho o CSV bruto (`base_final_2001_2025_plan1_excel_ptbr.csv`),
    converte para `Dados_base_nova_2001_2025.xlsx`, remove linhas com
    precipitação ausente (meses recentes ainda não publicados pela NASA).
  - `BIOMA_ATIVO` aceita `'MA'`, `'CE'`, `'CA'` ou `'TODOS'` (via variável de
    ambiente ou editando a linha).
  - `RODAR_EM_PARALELO = True` roda os 3 biomas ao mesmo tempo (um processo
    por núcleo) quando `BIOMA_ATIVO = 'TODOS'`.
  - Pasta própria por bioma (`saidas_figuras/MA/`, `/CE/`, `/CA/`).
  - **Nomes de arquivo fixos** (cada rodada sobrescreve a anterior — sem
    numeração `_1`, `_2`...).
  - Toggles: `GRAU_MODELO=2`, `TESTAR_GRAUS=True`, `GRAU_MAXIMO_TESTE=5`,
    `RODAR_YRANDOMIZATION=False` (⚠️ **ainda não rodei com True** — precisa
    rodar para ter os números finais da Figura 7/Y-randomization).

- **`Analise_Biomas_PSN.py`** — Kruskal-Wallis por fase ENSO, correlação de
  Pearson ONI×variáveis, regressão OLS ONI→variáveis, boxplots (Figuras 8, 9,
  10), dispersão PSN×variáveis. Também atualizado com:
  - Mesma detecção automática de CSV, salvando no **mesmo**
    `Dados_base_nova_2001_2025.xlsx` que o `Modelo_PSN.py` usa (arquivo
    compartilhado entre os dois scripts).
  - Fase ENSO (`Enso`: La Niña/Neutro/El Niño) calculada a partir do ONI por
    limiar simples (`ONI ≥ 0,5` → El Niño; `≤ -0,5` → La Niña; senão Neutro),
    porque o CSV bruto não vem com essa classificação pronta.
  - ⚠️ **Pendência a verificar**: essa classificação por limiar simples é uma
    aproximação. A definição operacional da NOAA exige o ONI sustentado por 5
    trimestres móveis consecutivos. Se a planilha antiga (`Dados_Benfica_.xlsx`)
    usava a classificação oficial NOAA/INPE, os resultados podem diferir perto
    das transições de fase — vale confirmar com o Ygor se ele tem a fonte
    oficial das fases por mês.
  - Nomes de arquivo fixos (sobrescreve, sem numeração) e títulos/rótulos
    dinâmicos (período e n reais da base, não mais fixos em "2001-2020"/"n=240").

- **`plot_obs_vs_pred_painel.py`** — **aposentado**. Ficou redundante: o
  `Modelo_PSN.py` já gera a Figura 3 (Observado vs. Predito, out-of-fold) com
  mais rigor (winsorização sem vazamento). Não precisa mais rodar esse script.

- **`Modelo_Ridge.py`** e **`modelo_com__escolha_de_melhor_grau.py`** —
  versões antigas/incompletas, mantidas só para referência histórica. Não usar
  para gerar números finais da dissertação.

## Pipeline de dados

```
base_final_2001_2025_plan1_excel_ptbr.csv   (bruto, colunas em português)
        │  (conversão automática, dentro dos dois scripts acima)
        ▼
Dados_base_nova_2001_2025.xlsx              (colunas renomeadas: MÊS, NP_*,
                                              WAI_*, EV_*, PRE_*, TST_*, BURN_*,
                                              Enso; linhas sem precipitação
                                              removidas)
```

Colunas do modelo por bioma (fixas, definidas em `config_biomas` dentro de
`Modelo_PSN.py`):
- MA: `EV_MA, PRE_MA, TST_MA, saz_sin, saz_cos`
- CE: `EV_CE, PRE_CE, WAI_CE, saz_sin, saz_cos`
- CA: `EV_CA, PRE_CA, TST_CA, saz_sin, saz_cos`

`PET` (evapotranspiração potencial) foi **excluída de propósito** do conjunto
de preditores — testamos e confirmamos que ela é redundante com a temperatura
(correlação 0,73–0,80 com TST em MA/CA) e pioraria a multicolinearidade.

## Resultados já confirmados com a base nova (2001–2025, n≈297)

| Bioma | R² teste (qualificação, 2001-2020) | R² teste (novo) | Gap overfitting (antes→agora) |
|---|---|---|---|
| MA | 62,3% | 70,96% | 10,20 pp → 5,14 pp |
| CE | 95,7% | 96,66% | 1,05 pp → 0,59 pp |
| CA | 94,0% | 94,16% | 1,36 pp → 1,03 pp |

CE e CA ficaram estáveis; MA melhorou bastante (mais dados ajudaram o bioma
mais heterogêneo).

**Achado novo e importante**: com a base estendida, o teste de Ljung-Box
detectou autocorrelação residual significativa **nos três biomas**
(MA: p=0,0000, ACF=0,299; CE: p=0,0052, ACF=0,201; CA: p=0,0000, ACF=0,420).
Na qualificação original (2001-2020), só a Caatinga apresentava esse problema.
Isso não invalida o modelo (TimeSeriesSplit continua com quedas < 10 pp nos
três), mas é um resultado novo a reportar na seção de diagnóstico.

**Multicolinearidade do Cerrado** (já conhecida, mas confirmada de novo):
`EV_CE` e `WAI_CE` têm VIF de 36,99 e 31,61 (correlação 0,973 entre elas) —
colinearidade grave, mitigada pela regularização Ridge, mas que exige cautela
na interpretação isolada dos coeficientes dessas duas variáveis.

## O que ainda falta rodar / obter

1. **`Modelo_PSN.py` com `RODAR_YRANDOMIZATION = True`** para os 3 biomas —
   ainda não tenho o Δ, p-valor e status (APROVADO/VERIFICAR) da Y-randomization
   com a base nova. É o mais demorado (100 permutações × validação cruzada).
2. **Tabela VIF completa por bioma** (as 5 variáveis, não só o VIF máximo).
3. **Os 3 arquivos `coeficientes_ridge_MA/CE/CA.csv`** — preciso deles para
   atualizar a Figura 5 (importância relativa das variáveis).
4. **Rodar `Analise_Biomas_PSN.py` com a base nova** — nenhum resultado de
   ENSO (Kruskal-Wallis, correlação, regressão OLS, Figuras 8-10) foi gerado
   ainda com 2001-2025.
5. **Confirmar a metodologia de classificação de fase ENSO** (ver pendência
   acima) antes de reportar os resultados de ENSO na dissertação.

## Textos já redigidos (prontos para colar, ajustar números quando os itens acima saírem)

- Parágrafo de metodologia justificando a exclusão do PET (colinearidade com
  temperatura).
- Parágrafo de discussão sobre a colinearidade EV_CE×WAI_CE no Cerrado.
- Esboço de frase sobre a não-normalidade dos resíduos / Ljung-Box.

## Coisas a não esquecer

- O modelo **não prevê o futuro sozinho** — ele precisa que EV/PRE/TST/WAI já
  estejam disponíveis (observados ou vindos de outra fonte/previsão) para
  estimar a PSN daquele mês. É um modelo explicativo-preditivo contemporâneo,
  não um forecast autônomo tipo ARIMA. Vale declarar isso como limitação
  explícita nas Considerações Finais.
- Todos os scripts agora sobrescrevem os arquivos de saída a cada rodada
  (sem acumular `_1`, `_2`...) — a pedido do Ygor.
