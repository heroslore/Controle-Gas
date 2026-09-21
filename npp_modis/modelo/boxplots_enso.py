#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valores exatos dos boxplots por fase ENSO (Figuras 8-10 da dissertação) e testes de
dispersão/extremos: Fligner-Killeen (variância), P10/P90 por fase, fração de meses extremos.
Uso: python boxplots_enso.py --dados Dados_base_nova_2001_2025.xlsx --saida enso_sazonalidade"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

VARS = {"MA": ["NP_MA", "EV_MA", "PRE_MA", "TST_MA", "WAI_MA", "BURN_MA"], "CE": ["NP_CE", "EV_CE", "PRE_CE", "TST_CE", "WAI_CE", "BURN_CE"], "CA": ["NP_CA", "EV_CA", "PRE_CA", "TST_CA", "WAI_CA", "BURN_CA"]}
NOME = {"MA": "Mata Atlântica", "CE": "Cerrado", "CA": "Caatinga"}; FASES = ["El Niño", "Neutro", "La Niña"]
COR = {"El Niño": "#c0392b", "Neutro": "#7f8c8d", "La Niña": "#2471a3"}


def stats_box(v):
    v = np.asarray(v, float); q1, med, q3 = np.percentile(v, [25, 50, 75]); iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return dict(n=len(v), minimo=v.min(), P10=np.percentile(v, 10), Q1=q1, mediana=med, media=v.mean(), Q3=q3, P90=np.percentile(v, 90), maximo=v.max(),
                bigode_inf=v[v >= lo].min(), bigode_sup=v[v <= hi].max(), n_outliers=int(((v < lo) | (v > hi)).sum()), amplitude=v.max() - v.min(), IQR=iqr, desvio_padrao=v.std(ddof=1))


def main():
    p = argparse.ArgumentParser(); p.add_argument("--dados", required=True); p.add_argument("--saida", default="enso_sazonalidade")
    p.add_argument("--criterio", choices=["mensal", "noaa"], default="mensal"); a = p.parse_args()
    out = Path(a.saida); out.mkdir(exist_ok=True)
    d = pd.read_excel(a.dados); d.columns = d.columns.str.strip()
    from analise_enso_sazonalidade import classificar_fase
    d["fase"] = classificar_fase(d.ONI.values, a.criterio)
    linhas, testes = [], []
    for tipo in ("bruto", "anomalia"):
        for b, cols in VARS.items():
            for c in cols:
                serie = d[c] if tipo == "bruto" else d[c] - d.groupby("MÊS")[c].transform("mean")
                g = {f: serie[d.fase == f].values for f in FASES}
                for f in FASES:
                    linhas.append(dict(tipo=tipo, bioma=NOME[b], variavel=c.split("_")[0], fase=f, **stats_box(g[f])))
                # testes: mediana (Kruskal), dispersão (Fligner-Killeen), extremos (fração < P10 e > P90 globais, qui-quadrado)
                p10, p90 = np.percentile(serie, [10, 90])
                tab = np.array([[np.sum(g[f] < p10), np.sum(g[f] > p90), np.sum((g[f] >= p10) & (g[f] <= p90))] for f in FASES])
                try: chi = stats.chi2_contingency(tab)[1]
                except ValueError: chi = np.nan   # BURN: muitos zeros
                testes.append(dict(tipo=tipo, bioma=NOME[b], variavel=c.split("_")[0], p_kruskal_mediana=stats.kruskal(*g.values()).pvalue,
                                   p_fligner_dispersao=stats.fligner(*g.values()).pvalue, p_qui2_extremos=chi,
                                   **{f"pct_meses_abaixo_P10_{f}": 100 * np.mean(g[f] < p10) for f in FASES},
                                   **{f"pct_meses_acima_P90_{f}": 100 * np.mean(g[f] > p90) for f in FASES},
                                   **{f"amplitude_{f}": g[f].max() - g[f].min() for f in FASES}))
    L = pd.DataFrame(linhas); T = pd.DataFrame(testes)
    L.round(3).to_csv(out / "D_boxplots_valores_exatos.csv", index=False, encoding="utf-8-sig")
    T.round(4).to_csv(out / "D_boxplots_testes_dispersao_extremos.csv", index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(out / "D_boxplots_ENSO.xlsx", engine="openpyxl") as xw:
        for tipo in ("bruto", "anomalia"):
            L[L.tipo == tipo].drop(columns="tipo").round(3).to_excel(xw, sheet_name=f"valores_{tipo}", index=False)
            T[T.tipo == tipo].drop(columns="tipo").round(4).to_excel(xw, sheet_name=f"testes_{tipo}", index=False)
    # figura: boxplots das anomalias de PSN, EV, TST/WAI por fase (3 biomas)
    fig, axes = plt.subplots(3, 4, figsize=(16, 10))
    for i, (b, cols) in enumerate(VARS.items()):
        for j, c in enumerate(cols[:4]):
            ax = axes[i, j]; serie = d[c] - d.groupby("MÊS")[c].transform("mean")
            bp = ax.boxplot([serie[d.fase == f] for f in FASES], tick_labels=FASES, patch_artist=True, widths=0.6, showmeans=True, meanprops=dict(marker="D", markerfacecolor="k", markersize=4))
            for patch, f in zip(bp["boxes"], FASES): patch.set_facecolor(COR[f]); patch.set_alpha(0.5)
            ax.axhline(0, color="#999", lw=0.8); ax.set_title(f"{NOME[b]} — {c.split('_')[0]} (anomalia)", fontsize=10); ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout(); plt.savefig(out / "D_boxplots_anomalias_por_fase.png", dpi=140); plt.close()
    pd.set_option("display.width", 250)
    print(T[T.tipo == "anomalia"][["bioma", "variavel", "p_kruskal_mediana", "p_fligner_dispersao", "p_qui2_extremos"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
