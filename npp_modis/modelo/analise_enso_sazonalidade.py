#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Três análises pedidas pela orientação, na base nova (2001-2025):

A. Sazonalidade: por que a importância das variáveis muda quando os termos
   seno/cosseno entram no MRMP-N (mesma métrica da Figura 5: soma dos |coef|
   padronizados por variável) + quanto de cada variável é ciclo anual.
B. ENSO -> preditores -> PSN: efeito das fases (em anomalias mensais, sem o
   ciclo anual), tamanho de efeito, e quanto dessa mudança se propaga à PSN
   pelo próprio modelo ajustado (análise de mediação/sensibilidade).
C. Defasagem: a PSN sobe ou desce nos meses de ENSO e nos meses seguintes?
   Correlação cruzada ONI x anomalia de PSN (lags 0-12) e compósitos por fase.

Uso: python analise_enso_sazonalidade.py --dados Dados_base_nova_2001_2025.xlsx --saida enso_sazonalidade
"""
import argparse, warnings
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats.mstats import winsorize
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV, RepeatedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.inspection import permutation_importance
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")

CFG = {"MA": ("Mata Atlântica", "NP_MA", ["EV_MA", "PRE_MA", "TST_MA"]),
       "CE": ("Cerrado", "NP_CE", ["EV_CE", "PRE_CE", "WAI_CE"]),
       "CA": ("Caatinga", "NP_CA", ["EV_CA", "PRE_CA", "TST_CA"])}
SAZ = ["saz_sin", "saz_cos"]
ALPHAS = [0.1, 1.0, 10.0, 50.0, 100.0]
COR = {"El Niño": "#c0392b", "La Niña": "#2471a3", "Neutro": "#7f8c8d"}


def classificar_fase(oni, criterio="mensal"):
    s = np.where(oni >= 0.5, 1, np.where(oni <= -0.5, -1, 0))
    if criterio == "noaa":                      # >= 5 trimestres móveis consecutivos
        f = np.zeros(len(s), int); i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and s[j + 1] == s[i]: j += 1
            if s[i] != 0 and j - i + 1 >= 5: f[i:j + 1] = s[i]
            i = j + 1
        s = f
    return np.select([s == 1, s == -1], ["El Niño", "La Niña"], "Neutro")


def ajustar(X, y):
    m = GridSearchCV(make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), Ridge()),
                     {"ridge__alpha": ALPHAS}, cv=5, scoring="r2").fit(X, np.asarray(winsorize(y, limits=[0.03, 0])))
    return m.best_estimator_


def importancia_coef(modelo, nomes):
    """Método da dissertação: soma de |coef| de todos os termos que contêm a variável, normalizada a 100 %."""
    pf = modelo.named_steps["polynomialfeatures"]; coef = modelo.named_steps["ridge"].coef_
    termos = pf.get_feature_names_out(nomes); imp = {}
    for n in nomes:
        imp[n] = sum(abs(c) for t, c in zip(termos, coef) if n in t.split(" ") or any(p.split("^")[0] == n for p in t.split(" ")))
    tot = sum(imp.values()); return {k: 100 * v / tot for k, v in imp.items()}


def r2cv(X, y):
    return 100 * cross_val_score(make_pipeline(StandardScaler(), PolynomialFeatures(2, include_bias=False), Ridge(alpha=10.0)),
                                 X, y, cv=RepeatedKFold(n_splits=5, n_repeats=10, random_state=42), scoring="r2").mean()


def anomalias(d, cols):
    """Anomalia = valor - média do mês do calendário (remove o ciclo anual)."""
    a = d[cols].copy()
    for c in cols:
        clim = d.groupby("MÊS")[c].transform("mean"); a[c] = d[c] - clim; a[c + "_pct"] = 100 * (d[c] - clim) / clim
    return a


def main():
    p = argparse.ArgumentParser(); p.add_argument("--dados", required=True); p.add_argument("--saida", default="enso_sazonalidade")
    p.add_argument("--criterio", choices=["mensal", "noaa"], default="mensal", help="fase por mês (±0,5) ou critério oficial NOAA (5 trimestres consecutivos)")
    p.add_argument("--ma-vars", nargs="+", default=None, help="preditores da Mata Atlântica (ex.: EV_MA TST_MA WAI_MA)")
    a = p.parse_args(); out = Path(a.saida); out.mkdir(exist_ok=True)
    if a.ma_vars: CFG["MA"] = ("Mata Atlântica", "NP_MA", a.ma_vars)
    d = pd.read_excel(a.dados); d.columns = d.columns.str.strip()
    d["saz_sin"] = np.sin(2 * np.pi * d["MÊS"] / 12); d["saz_cos"] = np.cos(2 * np.pi * d["MÊS"] / 12)
    d["fase"] = classificar_fase(d.ONI.values, a.criterio)
    d["t"] = pd.to_datetime(dict(year=d.ANO, month=d["MÊS"], day=1))

    # ======================= A. SAZONALIDADE =======================
    linA, sazon = [], []
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))
    for k, (b, (nome, ycol, xs)) in enumerate(CFG.items()):
        y = d[ycol].values
        m_sem = ajustar(d[xs].values, y); m_com = ajustar(d[xs + SAZ].values, y)
        i_sem = importancia_coef(m_sem, xs); i_com = importancia_coef(m_com, xs + SAZ)
        pi_sem = permutation_importance(m_sem, d[xs].values, y, n_repeats=30, random_state=42, scoring="r2").importances_mean
        pi_com = permutation_importance(m_com, d[xs + SAZ].values, y, n_repeats=30, random_state=42, scoring="r2").importances_mean
        for v in xs + SAZ:
            linA.append(dict(bioma=nome, variavel=v.split("_")[0] if v not in SAZ else v,
                             imp_coef_sem_saz=i_sem.get(v, np.nan), imp_coef_com_saz=i_com[v],
                             queda_r2_permut_sem_saz=100 * pi_sem[xs.index(v)] if v in xs else np.nan,
                             queda_r2_permut_com_saz=100 * pi_com[(xs + SAZ).index(v)]))
        linA.append(dict(bioma=nome, variavel="R2_cv_modelo", imp_coef_sem_saz=r2cv(d[xs].values, y), imp_coef_com_saz=r2cv(d[xs + SAZ].values, y)))
        # quanto de cada variável é ciclo anual, e correlação com PSN bruta x anomalia
        an = anomalias(d, [ycol] + xs)
        for v in xs:
            r2_ciclo = 100 * stats.linregress(d.saz_sin, d[v]).rvalue ** 2 + 100 * stats.linregress(d.saz_cos, d[v]).rvalue ** 2
            sazon.append(dict(bioma=nome, variavel=v.split("_")[0], pct_variancia_ciclo_anual=r2_ciclo,
                              r_PSN_bruto=stats.pearsonr(d[v], d[ycol])[0], r_PSN_anomalias=stats.pearsonr(an[v], an[ycol])[0]))
        sazon.append(dict(bioma=nome, variavel="PSN", pct_variancia_ciclo_anual=100 * stats.linregress(d.saz_sin, d[ycol]).rvalue ** 2 + 100 * stats.linregress(d.saz_cos, d[ycol]).rvalue ** 2, r_PSN_bruto=1, r_PSN_anomalias=1))
        ax = axes[k]; labs = [v.split("_")[0] for v in xs] + ["saz_sin", "saz_cos"]; x = np.arange(len(labs))
        ax.bar(x - 0.2, [i_sem.get(v, 0) for v in xs] + [0, 0], 0.4, color="#b0b0b0", label="sem seno/cosseno")
        ax.bar(x + 0.2, [i_com[v] for v in xs + SAZ], 0.4, color="#2471a3", label="com seno/cosseno")
        ax.set_xticks(x); ax.set_xticklabels(labs); ax.set_title(nome); ax.set_ylabel("importância (%)" if k == 0 else ""); ax.spines[["top", "right"]].set_visible(False)
        if k == 0: ax.legend(frameon=False, fontsize=8)
    plt.suptitle("Importância relativa (soma dos |coeficientes| padronizados) com e sem os termos de sazonalidade"); plt.tight_layout()
    plt.savefig(out / "A_importancia_com_sem_sazonalidade.png", dpi=150); plt.close()
    pd.DataFrame(linA).round(2).to_csv(out / "A_importancia_variaveis.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(sazon).round(3).to_csv(out / "A_ciclo_anual_e_correlacoes.csv", index=False, encoding="utf-8-sig")

    # ======================= B. ENSO -> PREDITORES -> PSN =======================
    linB, linMed = [], []
    for b, (nome, ycol, xs) in CFG.items():
        an = anomalias(d, [ycol] + xs); an["fase"] = d.fase.values
        modelo = ajustar(d[xs + SAZ].values, d[ycol].values)
        clim = d.groupby("MÊS")[xs].mean()                         # climatologia mensal dos preditores
        base = np.column_stack([clim.loc[d["MÊS"]].values, d[SAZ].values])
        psn_clim = modelo.predict(base)                             # PSN prevista sob condições "normais"
        for var in [ycol] + xs:
            g = {f: an.loc[an.fase == f, var].values for f in ["El Niño", "La Niña", "Neutro"]}
            gp = {f: an.loc[an.fase == f, var + "_pct"].values for f in g}
            kw = stats.kruskal(*g.values()); H = kw.statistic; n = len(an); eps2 = (H - 2) / (n - 3)   # tamanho de efeito
            for f in ["El Niño", "La Niña"]:
                mw = stats.mannwhitneyu(g[f], g["Neutro"])
                linB.append(dict(bioma=nome, variavel=var.split("_")[0], fase=f, n_meses=len(g[f]),
                                 anomalia_media=g[f].mean(), anomalia_media_pct=gp[f].mean(), anomalia_neutro_pct=gp["Neutro"].mean(),
                                 dif_vs_neutro_pct=gp[f].mean() - gp["Neutro"].mean(), p_mannwhitney_vs_neutro=mw.pvalue,
                                 p_kruskal_3fases=kw.pvalue, epsilon2=max(eps2, 0)))
            # mediação: PSN prevista se SÓ este preditor assumir sua anomalia média da fase
            if var != ycol:
                j = xs.index(var)
                for f in ["El Niño", "La Niña"]:
                    dv = g[f].mean() - g["Neutro"].mean()
                    Xc = base.copy(); Xc[:, j] += dv
                    dpsn = (modelo.predict(Xc) - psn_clim).mean()
                    linMed.append(dict(bioma=nome, fase=f, preditor=var.split("_")[0], anomalia_do_preditor=dv,
                                       efeito_na_PSN_g_c_m2=dpsn, efeito_na_PSN_pct=100 * dpsn / psn_clim.mean()))
        # todos os preditores juntos
        for f in ["El Niño", "La Niña"]:
            Xc = base.copy()
            for j, var in enumerate(xs):
                Xc[:, j] += an.loc[an.fase == f, var].mean() - an.loc[an.fase == "Neutro", var].mean()
            dpsn = (modelo.predict(Xc) - psn_clim).mean()
            obs = an.loc[an.fase == f, ycol + "_pct"].mean() - an.loc[an.fase == "Neutro", ycol + "_pct"].mean()
            linMed.append(dict(bioma=nome, fase=f, preditor="TODOS (via modelo)", anomalia_do_preditor=np.nan,
                               efeito_na_PSN_g_c_m2=dpsn, efeito_na_PSN_pct=100 * dpsn / psn_clim.mean(), PSN_observada_dif_vs_neutro_pct=obs))
    pd.DataFrame(linB).round(4).to_csv(out / "B_enso_efeito_nas_variaveis.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(linMed).round(3).to_csv(out / "B_enso_propagacao_para_PSN.csv", index=False, encoding="utf-8-sig")

    # ======================= C. DEFASAGEM =======================
    lags = range(0, 13); linC, comp = [], []
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    fig2, axes2 = plt.subplots(1, 3, figsize=(15, 4), sharey=True)
    for k, (b, (nome, ycol, xs)) in enumerate(CFG.items()):
        an = anomalias(d, [ycol] + xs)
        for var in [ycol] + xs:
            for L in lags:                                          # variável no mês t+L vs ONI no mês t
                x = d.ONI.values[:len(d) - L] if L else d.ONI.values; yv = an[var + "_pct"].values[L:]
                r, pv = stats.spearmanr(x, yv)
                linC.append(dict(bioma=nome, variavel=var.split("_")[0], lag_meses=L, rho_spearman=r, p=pv, n=len(yv)))
        # compósitos: anomalia % da PSN em t+L quando a fase em t é El Niño / La Niña
        for f in ["El Niño", "La Niña"]:
            idx = np.where(d.fase.values == f)[0]
            for L in [0, 1, 2, 3, 4, 6, 9, 12]:
                ii = idx + L; ii = ii[ii < len(d)]; vals = an[ycol + "_pct"].values[ii]
                neutro = an.loc[d.fase == "Neutro", ycol + "_pct"].values
                w = stats.mannwhitneyu(vals, neutro); boot = [np.mean(np.random.default_rng(s).choice(vals, len(vals))) for s in range(500)]
                comp.append(dict(bioma=nome, fase=f, lag_meses=L, n=len(vals), anomalia_PSN_pct_media=vals.mean(), ic95_inf=np.percentile(boot, 2.5),
                                 ic95_sup=np.percentile(boot, 97.5), pct_meses_com_PSN_abaixo_normal=100 * np.mean(vals < 0), p_vs_neutro=w.pvalue))
        cc = pd.DataFrame(linC); q = cc[(cc.bioma == nome) & (cc.variavel == "NP")]
        ax = axes[k]; ax.axhline(0, color="#999", lw=0.8); ax.bar(q.lag_meses, q.rho_spearman, color=["#2471a3" if pv < 0.05 else "#b0b0b0" for pv in q.p])
        ax.set_title(nome); ax.set_xlabel("defasagem (meses após o ONI)"); ax.spines[["top", "right"]].set_visible(False)
        if k == 0: ax.set_ylabel("ρ Spearman (ONI × anomalia PSN)")
        cp = pd.DataFrame(comp); ax2 = axes2[k]; ax2.axhline(0, color="#999", lw=0.8)
        for f in ["El Niño", "La Niña"]:
            qq = cp[(cp.bioma == nome) & (cp.fase == f)]
            ax2.errorbar(qq.lag_meses, qq.anomalia_PSN_pct_media, yerr=[qq.anomalia_PSN_pct_media - qq.ic95_inf, qq.ic95_sup - qq.anomalia_PSN_pct_media], fmt="o-", color=COR[f], label=f, capsize=3)
        ax2.set_title(nome); ax2.set_xlabel("meses após o mês em fase ENSO"); ax2.spines[["top", "right"]].set_visible(False)
        if k == 0: ax2.set_ylabel("anomalia média da PSN (%)"); ax2.legend(frameon=False)
    fig.suptitle("Correlação cruzada: ONI no mês t × anomalia de PSN no mês t+lag (azul = p < 0,05)"); fig.tight_layout(); fig.savefig(out / "C_correlacao_cruzada_ONI_PSN.png", dpi=150)
    fig2.suptitle("Compósitos: anomalia da PSN durante e após meses de El Niño / La Niña (IC 95 % bootstrap)"); fig2.tight_layout(); fig2.savefig(out / "C_compositos_PSN_por_fase.png", dpi=150)
    pd.DataFrame(linC).round(4).to_csv(out / "C_correlacao_cruzada_lags.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(comp).round(3).to_csv(out / "C_compositos_PSN_lags.csv", index=False, encoding="utf-8-sig")

    # eventos ENSO (>= 5 meses consecutivos na fase) e PSN durante / 3 meses após
    ev = []; fase = d.fase.values; i = 0
    while i < len(d):
        if fase[i] != "Neutro":
            j = i
            while j + 1 < len(d) and fase[j + 1] == fase[i]: j += 1
            if j - i + 1 >= 5:
                row = dict(fase=fase[i], inicio=d.t.iloc[i].strftime("%Y-%m"), fim=d.t.iloc[j].strftime("%Y-%m"), meses=j - i + 1, ONI_pico=d.ONI.iloc[i:j + 1].abs().max() * (1 if fase[i] == "El Niño" else -1))
                for b, (nome, ycol, xs) in CFG.items():
                    an = anomalias(d, [ycol]); row[f"PSN_{b}_durante_pct"] = an[ycol + "_pct"].iloc[i:j + 1].mean(); row[f"PSN_{b}_3m_depois_pct"] = an[ycol + "_pct"].iloc[j + 1:j + 4].mean() if j + 1 < len(d) else np.nan
                ev.append(row)
            i = j + 1
        else: i += 1
    pd.DataFrame(ev).round(2).to_csv(out / "C_eventos_ENSO_e_PSN.csv", index=False, encoding="utf-8-sig")
    print("concluído em", out)


if __name__ == "__main__":
    main()
