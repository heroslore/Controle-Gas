#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Replica as análises reportadas na dissertação (além do Modelo_Ridge.py) para
um conjunto de dados, por bioma, com a mesma especificação do MRMP-N:
StandardScaler -> PolynomialFeatures(grau 2) -> Ridge (alpha por GridSearchCV),
winsorização de 3 % da resposta só no treino.

  - RepeatedKFold 5x30, GroupKFold por ano, TimeSeriesSplit (janela expansiva)   [Tabela 2/3]
  - seleção do grau polinomial 1-5                                              [Figura 4]
  - Shapiro-Wilk, Ljung-Box, % resíduos < -2 dp                                 [6.4]
  - Y-randomization fora da amostra (100 permutações, R² por CV 5-fold)         [Figura 7]
  - Kruskal-Wallis das variáveis por fase ENSO e R² da regressão ONI -> variável [6.5]

Uso: python analise_dissertacao.py --dados rotulo=arquivo.xlsx [--dados ...] --saida comparacao
"""
import argparse, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats.mstats import winsorize
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.model_selection import RepeatedKFold, GroupKFold, TimeSeriesSplit, GridSearchCV, KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from statsmodels.stats.diagnostic import acorr_ljungbox
warnings.filterwarnings("ignore")

CFG = {"MA": ("NP_MA", ["EV_MA", "PRE_MA", "TST_MA", "saz_sin", "saz_cos"]),
       "CE": ("NP_CE", ["EV_CE", "PRE_CE", "WAI_CE", "saz_sin", "saz_cos"]),
       "CA": ("NP_CA", ["EV_CA", "PRE_CA", "TST_CA", "saz_sin", "saz_cos"])}
ALPHAS = [0.1, 1.0, 10.0, 50.0, 100.0]


def pipeline(grau):
    return GridSearchCV(make_pipeline(StandardScaler(), PolynomialFeatures(grau, include_bias=False), Ridge()),
                        {"ridge__alpha": ALPHAS}, cv=5, scoring="r2")


def cv(X, y, splits, grau=2):
    r2tr, r2te, rmse, mae = [], [], [], []
    for tr, te in splits:
        ytr = np.asarray(winsorize(y[tr], limits=[0.03, 0.0]))       # winsoriza só o treino
        m = pipeline(grau).fit(X[tr], ytr)
        r2tr.append(r2_score(ytr, m.predict(X[tr]))); p = m.predict(X[te])
        r2te.append(r2_score(y[te], p)); rmse.append(np.sqrt(mean_squared_error(y[te], p))); mae.append(mean_absolute_error(y[te], p))
    r2te = np.array(r2te) * 100
    return dict(r2_treino=np.mean(r2tr) * 100, r2_teste=r2te.mean(), ic_inf=np.percentile(r2te, 2.5), ic_sup=np.percentile(r2te, 97.5),
                rmse=np.mean(rmse), mae=np.mean(mae), gap=np.mean(r2tr) * 100 - r2te.mean())


def analisar(d, rotulo):
    d = d.copy(); d.columns = d.columns.str.strip()
    d["saz_sin"] = np.sin(2 * np.pi * d["MÊS"] / 12); d["saz_cos"] = np.cos(2 * np.pi * d["MÊS"] / 12)
    linhas, graus, enso = [], [], []
    for b, (ycol, xcols) in CFG.items():
        X, y = d[xcols].values, d[ycol].values.astype(float)
        rk = list(RepeatedKFold(n_splits=5, n_repeats=30, random_state=42).split(X))
        gk = list(GroupKFold(n_splits=5).split(X, y, groups=d["ANO"].values))
        ts = list(TimeSeriesSplit(n_splits=5).split(X))
        r = {k: cv(X, y, s) for k, s in (("RepeatedKFold", rk), ("GroupKFold", gk), ("TimeSeriesSplit", ts))}
        # diagnóstico no ajuste completo
        m = pipeline(2).fit(X, np.asarray(winsorize(y, limits=[0.03, 0.0])))
        res = y - m.predict(X)
        W, p_sw = stats.shapiro(res); lb = acorr_ljungbox(res, lags=[12], return_df=True)
        cauda = 100 * np.mean(res < -2 * res.std())
        # Y-randomization fora da amostra
        rng = np.random.default_rng(42); r2p = []
        for _ in range(100):
            yp = rng.permutation(y)
            pred = cross_val_predict(pipeline(2), X, yp, cv=KFold(5, shuffle=True, random_state=42))
            r2p.append(r2_score(yp, pred) * 100)
        linhas.append(dict(dados=rotulo, bioma=b, n=len(y),
                           r2_rkf=r["RepeatedKFold"]["r2_teste"], ic_inf=r["RepeatedKFold"]["ic_inf"], ic_sup=r["RepeatedKFold"]["ic_sup"],
                           rmse=r["RepeatedKFold"]["rmse"], mae=r["RepeatedKFold"]["mae"], gap_pp=r["RepeatedKFold"]["gap"],
                           r2_groupkfold=r["GroupKFold"]["r2_teste"], r2_timeseries=r["TimeSeriesSplit"]["r2_teste"],
                           queda_max_pp=r["RepeatedKFold"]["r2_teste"] - min(r["GroupKFold"]["r2_teste"], r["TimeSeriesSplit"]["r2_teste"]),
                           shapiro_W=W, shapiro_p=p_sw, ljungbox_p=float(lb["lb_pvalue"].iloc[0]), acf1=float(pd.Series(res).autocorr(1)),
                           cauda_esq_pct=cauda, yrand_r2_perm_medio=np.mean(r2p),
                           yrand_delta_pp=r["RepeatedKFold"]["r2_teste"] - np.mean(r2p), yrand_p=(np.sum(np.array(r2p) >= r["RepeatedKFold"]["r2_teste"]) + 1) / 101))
        for g in range(1, 6):
            c = cv(X, y, rk, g); graus.append(dict(dados=rotulo, bioma=b, grau=g, r2_teste=c["r2_teste"], gap_pp=c["gap"], rmse=c["rmse"]))
        # ENSO
        fases = d["Enso"].astype(str).str.strip()
        for var in [ycol] + [c for c in xcols if not c.startswith("saz")]:
            grupos = [d.loc[fases == f, var].dropna().values for f in ["El Niño", "La Niña", "Neutro"]]
            kw = stats.kruskal(*[g for g in grupos if len(g) > 0])
            ok = d[[var, "ONI"]].dropna(); lr = stats.linregress(ok["ONI"], ok[var])
            enso.append(dict(dados=rotulo, bioma=b, variavel=var, kruskal_p=kw.pvalue, r2_oni_pct=100 * lr.rvalue ** 2))
    return pd.DataFrame(linhas), pd.DataFrame(graus), pd.DataFrame(enso)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dados", action="append", required=True); p.add_argument("--saida", default="comparacao")
    a = p.parse_args(); out = Path(a.saida); out.mkdir(exist_ok=True)
    L, G, E = [], [], []
    for item in a.dados:
        rot, arq = item.split("=", 1); print("analisando", rot, flush=True)
        l, g, e = analisar(pd.read_excel(arq), rot); L.append(l); G.append(g); E.append(e)
    pd.concat(L).round(3).to_csv(out / "desempenho_validacao.csv", index=False, encoding="utf-8-sig")
    pd.concat(G).round(3).to_csv(out / "selecao_grau.csv", index=False, encoding="utf-8-sig")
    pd.concat(E).round(4).to_csv(out / "enso.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250); print(pd.concat(L).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
