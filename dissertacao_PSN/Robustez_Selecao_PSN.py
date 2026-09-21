# -*- coding: utf-8 -*-
"""
Robustez da seleção do MRMP-N e complementos de validação (respostas aos pontos 1, 4, 6 e 7 da
revisão do artigo JSAES). Mesmo pipeline do Modelo_PSN.py (winsorização 3% só no treino,
StandardScaler, PolynomialFeatures, Ridge com GridSearchCV do alfa; random_state = 42).

(a) Seleção do grau (1 a 5) sob GroupKFold por ano e TimeSeriesSplit (janela expansível).
(b) Seleção das 10 combinações de três variáveis ambientais sob os mesmos dois esquemas temporais.
(c) Estabilidade da seleção sob RepeatedKFold 5 x 30: frequência com que cada combinação é a melhor
    partição a partição, diferença pareada entre a 1ª e a 2ª combinações (IC bootstrap de 95% sobre
    as 150 partições) e teste de Wilcoxon pareado.
(d) Importância por permutação fora da amostra, por bloco temporal (GroupKFold por ano e
    TimeSeriesSplit): queda do R² de teste (pontos percentuais) ao embaralhar cada preditor no
    teste, média e desvio-padrão entre blocos (20 repetições por bloco).
(e) Nulos que preservam a estrutura temporal (complemento ao Y-randomization): deslocamento
    circular da PSN (todos os 296 deslocamentos possíveis; os múltiplos de 12 preservam o
    calendário) e permutação de anos inteiros (100 permutações dos 24 anos completos, com os 9
    meses de 2025 mantidos no lugar). R² pela mesma validação cruzada (RepeatedKFold 5 x 30,
    Ridge com alfa médio), como no Y-randomization do Modelo_PSN.py.

Saídas: resultados_2001_2025/robustez/*.csv e robustez.json
"""
import os, json, itertools, numpy as np, pandas as pd
from concurrent.futures import ProcessPoolExecutor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.model_selection import RepeatedKFold, GridSearchCV, GroupKFold, TimeSeriesSplit
from sklearn.metrics import r2_score
from scipy.stats import wilcoxon

BASE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(BASE, 'resultados_2001_2025')
OUT = os.path.join(RES, 'robustez'); os.makedirs(OUT, exist_ok=True)
df = pd.read_excel(os.path.join(BASE, 'Dados_base_nova_2001_2025.xlsx')); df.columns = df.columns.str.strip()
df['saz_sin'] = np.sin(2 * np.pi * df['MÊS'] / 12); df['saz_cos'] = np.cos(2 * np.pi * df['MÊS'] / 12)
for b in ['MA', 'CE', 'CA']: df[f'BURN_{b}_log'] = np.log1p(df[f'BURN_{b}'])
NUMX = json.load(open(os.path.join(RES, 'numeros_extra.json'), encoding='utf-8'))
X_SEL = {b: NUMX[b]['x'] for b in ['MA', 'CE', 'CA']}
ALPHA = {b: NUMX[b]['alpha_medio'] for b in ['MA', 'CE', 'CA']}
NOME = {'MA': 'Mata Atlântica', 'CE': 'Cerrado', 'CA': 'Caatinga'}
ALPHAS = [0.1, 1.0, 10.0, 50.0, 100.0]
ANOS = df['ANO'].values

def cols_de(b, combo): return [f'{v}_{b}' if v != 'BURNlog' else f'BURN_{b}_log' for v in combo] + ['saz_sin', 'saz_cos']
def nome_combo(combo): return ' + '.join(combo)

def fit_pipeline(x_tr, y_tr, grau=2, alpha=None):
    y_tr = y_tr.clip(lower=np.percentile(y_tr.values, 3))
    sc = StandardScaler(); pf = PolynomialFeatures(degree=grau, include_bias=False)
    Xtr = pf.fit_transform(sc.fit_transform(x_tr))
    if alpha is None:
        m = GridSearchCV(Ridge(), {'alpha': ALPHAS}, cv=5, scoring='r2').fit(Xtr, y_tr.values).best_estimator_
    else:
        m = Ridge(alpha=alpha).fit(Xtr, y_tr.values)
    return sc, pf, m, r2_score(y_tr, m.predict(Xtr)) * 100

def predict(sc, pf, m, x): return m.predict(pf.transform(sc.transform(x)))

def splits(esquema, x):
    if esquema == 'GroupKFold': return list(GroupKFold(n_splits=5).split(x, groups=ANOS))
    if esquema == 'TimeSeriesSplit': return list(TimeSeriesSplit(n_splits=5).split(x))
    return list(RepeatedKFold(n_splits=5, n_repeats=30, random_state=42).split(x))

# ---------------------------------------------------------------- (a) grau x esquema temporal
def tarefa_grau(args):
    b, grau, esq = args
    x, y = df[cols_de(b, X_SEL[b])], df[f'NP_{b}']; tr_l, te_l = [], []
    for tr, te in splits(esq, x):
        sc, pf, m, r2tr = fit_pipeline(x.iloc[tr], y.iloc[tr].copy(), grau)
        tr_l.append(r2tr); te_l.append(r2_score(y.iloc[te], predict(sc, pf, m, x.iloc[te])) * 100)
    return dict(bioma=NOME[b], grau=grau, esquema=esq, r2_treino=np.mean(tr_l), r2_teste=np.mean(te_l), gap_pp=np.mean(tr_l) - np.mean(te_l))

# ---------------------------------------------------------------- (b)/(c) combinações
def tarefa_combo(args):
    b, combo, esq = args
    x, y = df[cols_de(b, combo)], df[f'NP_{b}']; te_l = []
    for tr, te in splits(esq, x):
        sc, pf, m, _ = fit_pipeline(x.iloc[tr], y.iloc[tr].copy(), 2)
        te_l.append(r2_score(y.iloc[te], predict(sc, pf, m, x.iloc[te])) * 100)
    return dict(bioma=b, variaveis=nome_combo(combo), esquema=esq, r2_teste=np.mean(te_l), folds=te_l)

# ---------------------------------------------------------------- (d) permutation importance
def tarefa_perm(args):
    b, esq = args
    vars_ = X_SEL[b] + ['SAZsin', 'SAZcos']; x, y = df[cols_de(b, X_SEL[b])], df[f'NP_{b}']
    rng = np.random.default_rng(42); quedas = {v: [] for v in vars_}; razao = {v: [] for v in vars_}; parcela = {v: [] for v in vars_}; r2_base = []
    for tr, te in splits(esq, x):
        sc, pf, m, _ = fit_pipeline(x.iloc[tr], y.iloc[tr].copy(), 2)
        x_te = x.iloc[te].reset_index(drop=True); y_te = y.iloc[te].values
        pb = predict(sc, pf, m, x_te); r2b = r2_score(y_te, pb) * 100; r2_base.append(r2b); rmse_b = np.sqrt(np.mean((y_te - pb) ** 2))
        q_bloco = {}
        for j, v in enumerate(vars_):
            qs, rz = [], []
            for _ in range(20):
                xp = x_te.copy(); xp.iloc[:, j] = rng.permutation(xp.iloc[:, j].values); pp = predict(sc, pf, m, xp)
                qs.append(r2b - r2_score(y_te, pp) * 100); rz.append(np.sqrt(np.mean((y_te - pp) ** 2)) / rmse_b)
            q_bloco[v] = np.mean(qs); quedas[v].append(np.mean(qs)); razao[v].append(np.mean(rz))
        tot = sum(max(q, 0) for q in q_bloco.values())
        for v in vars_: parcela[v].append(max(q_bloco[v], 0) / tot * 100 if tot > 0 else np.nan)
    return [dict(bioma=NOME[b], esquema=esq, variavel=v, queda_media_pp=np.mean(quedas[v]), queda_dp_pp=np.std(quedas[v]),
                 razao_rmse_media=np.mean(razao[v]), razao_rmse_dp=np.std(razao[v]), parcela_media_pct=np.nanmean(parcela[v]),
                 parcela_dp_pct=np.nanstd(parcela[v]), r2_base=np.mean(r2_base)) for v in vars_]

# ---------------------------------------------------------------- (e) nulos temporais
def r2_cv_fixo(b, y_vetor):
    x = df[cols_de(b, X_SEL[b])]; y = pd.Series(y_vetor, index=x.index); r2s = []
    for tr, te in splits('RepeatedKFold', x):
        sc, pf, m, _ = fit_pipeline(x.iloc[tr], y.iloc[tr].copy(), 2, alpha=ALPHA[b])
        r2s.append(r2_score(y.iloc[te], predict(sc, pf, m, x.iloc[te])) * 100)
    return np.mean(r2s)

def tarefa_nulo(args):
    b, tipo, k = args
    y = df[f'NP_{b}'].values.copy()
    if tipo == 'shift':
        y_n = np.roll(y, k)
    else:                                   # permutação de anos inteiros (2001-2024), 2025 fixo
        rng = np.random.default_rng(1000 + k); anos_c = np.arange(2001, 2025); perm = rng.permutation(anos_c)
        y_n = y.copy()
        for a_dest, a_orig in zip(anos_c, perm):
            y_n[ANOS == a_dest] = y[ANOS == a_orig]
    return dict(bioma=b, tipo=tipo, k=int(k), r2=r2_cv_fixo(b, y_n))

if __name__ == '__main__':
    BIOMAS = ['MA', 'CE', 'CA']; ESQ_T = ['GroupKFold', 'TimeSeriesSplit']
    with ProcessPoolExecutor(max_workers=4) as ex:
        # (a)
        grau = pd.DataFrame(list(ex.map(tarefa_grau, [(b, g, e) for b in BIOMAS for g in range(1, 6) for e in ESQ_T])))
        grau.to_csv(os.path.join(OUT, 'grau_temporal.csv'), index=False); print(grau.round(2).to_string(index=False))
        # (b) + (c)
        combos = list(itertools.combinations(['EV', 'PRE', 'TST', 'WAI', 'BURNlog'], 3))
        res = list(ex.map(tarefa_combo, [(b, c, e) for b in BIOMAS for c in combos for e in ESQ_T + ['RepeatedKFold']]))
        # (d)
        perm = pd.DataFrame([r for lst in ex.map(tarefa_perm, [(b, e) for b in BIOMAS for e in ESQ_T]) for r in lst])
        perm.to_csv(os.path.join(OUT, 'permutation_importance.csv'), index=False); print(perm.round(2).to_string(index=False))
        # (e)
        tarefas = [(b, 'shift', k) for b in BIOMAS for k in range(1, 297)] + [(b, 'anos', k) for b in BIOMAS for k in range(100)]
        nulos = pd.DataFrame(list(ex.map(tarefa_nulo, tarefas, chunksize=8)))
    # ---- (b) tabela por esquema temporal com posição da combinação selecionada
    tab = pd.DataFrame([{k: v for k, v in r.items() if k != 'folds'} for r in res])
    tab['rank'] = tab.groupby(['bioma', 'esquema'])['r2_teste'].rank(ascending=False, method='min').astype(int)
    tab['bioma'] = tab['bioma'].map(NOME); tab.sort_values(['bioma', 'esquema', 'rank']).to_csv(os.path.join(OUT, 'combos_temporal.csv'), index=False)
    # ---- (c) estabilidade sob RepeatedKFold (partição a partição)
    est_rows, dif_rows = [], []
    for b in BIOMAS:
        rk = [r for r in res if r['bioma'] == b and r['esquema'] == 'RepeatedKFold']
        F = np.array([r['folds'] for r in rk]); nomes = [r['variaveis'] for r in rk]     # 10 x 150
        vence = np.bincount(F.argmax(axis=0), minlength=len(nomes)) / F.shape[1] * 100
        ordem = np.argsort(-F.mean(axis=1))
        for i in ordem: est_rows.append(dict(bioma=NOME[b], variaveis=nomes[i], r2_teste=F[i].mean(), freq_melhor_pct=vence[i]))
        i1, i2 = ordem[0], ordem[1]; d = F[i1] - F[i2]
        rng = np.random.default_rng(42); boots = [rng.choice(d, size=len(d), replace=True).mean() for _ in range(5000)]
        dif_rows.append(dict(bioma=NOME[b], primeira=nomes[i1], segunda=nomes[i2], dif_media_pp=d.mean(), ic95_inf=np.percentile(boots, 2.5),
                             ic95_sup=np.percentile(boots, 97.5), prop_particoes_primeira_maior=(d > 0).mean() * 100, p_wilcoxon=wilcoxon(d).pvalue))
    est = pd.DataFrame(est_rows); est.to_csv(os.path.join(OUT, 'estabilidade_selecao.csv'), index=False); print(est.round(2).to_string(index=False))
    dif = pd.DataFrame(dif_rows); dif.to_csv(os.path.join(OUT, 'diferenca_pareada.csv'), index=False); print(dif.round(4).to_string(index=False))
    # ---- (e) resumo dos nulos
    nulos.to_csv(os.path.join(OUT, 'nulos_temporais_bruto.csv'), index=False)
    orig = {b: r2_cv_fixo(b, df[f'NP_{b}'].values) for b in BIOMAS}; nul_rows = []
    for b in BIOMAS:
        for tipo, sub in [('Deslocamento circular (todos os 296)', nulos[(nulos.bioma == b) & (nulos.tipo == 'shift')]),
                          ('Deslocamento circular múltiplo de 12 meses (calendário preservado)', nulos[(nulos.bioma == b) & (nulos.tipo == 'shift') & (nulos.k % 12 == 0)]),
                          ('Permutação de anos inteiros (calendário preservado)', nulos[(nulos.bioma == b) & (nulos.tipo == 'anos')])]:
            r = sub['r2'].values
            nul_rows.append(dict(bioma=NOME[b], teste=tipo, n=len(r), r2_original=orig[b], r2_nulo_media=r.mean(), r2_nulo_dp=r.std(), r2_nulo_max=r.max(),
                                 p_empirico=((r >= orig[b]).sum() + 1) / (len(r) + 1)))
    nul = pd.DataFrame(nul_rows); nul.to_csv(os.path.join(OUT, 'nulos_temporais.csv'), index=False); print(nul.round(3).to_string(index=False))
    # ---- json de síntese
    js = {}
    for b in BIOMAS:
        nb = NOME[b]; sel = nome_combo(X_SEL[b])
        js[b] = dict(selecionado=sel,
                     grau={e: {int(g): float(grau[(grau.bioma == nb) & (grau.esquema == e) & (grau.grau == g)]['r2_teste'].iloc[0]) for g in range(1, 6)} for e in ESQ_T},
                     melhor_grau={e: int(grau[(grau.bioma == nb) & (grau.esquema == e)].sort_values('r2_teste', ascending=False)['grau'].iloc[0]) for e in ESQ_T},
                     rank_selecionado={e: int(tab[(tab.bioma == nb) & (tab.esquema == e) & (tab.variaveis == sel)]['rank'].iloc[0]) for e in ESQ_T},
                     top3={e: tab[(tab.bioma == nb) & (tab.esquema == e)].sort_values('rank').head(3)[['variaveis', 'r2_teste']].values.tolist() for e in ESQ_T},
                     freq_melhor=float(est[(est.bioma == nb) & (est.variaveis == sel)]['freq_melhor_pct'].iloc[0]),
                     dif=dif[dif.bioma == nb].iloc[0].to_dict(),
                     perm={e: perm[(perm.bioma == nb) & (perm.esquema == e)][['variavel', 'queda_media_pp', 'queda_dp_pp', 'razao_rmse_media', 'razao_rmse_dp', 'parcela_media_pct', 'parcela_dp_pct']].values.tolist() for e in ESQ_T},
                     nulos=nul[nul.bioma == nb].to_dict('records'))
    json.dump(js, open(os.path.join(OUT, 'robustez.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=float)
    print('\nconcluído:', OUT)
