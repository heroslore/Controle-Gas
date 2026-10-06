#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Análise de sensibilidade da TST (MOD11A2, LST_Day_1km) ao filtro de qualidade QC_Day.
Três versões, mesma máscara espacial, período e agregação da base:
  sem_filtro : só exclui preenchimento (DN fora de 7500-65535)   [= base atual]
  erro_3k    : + QC_Day bits 0-1 em {00,01} (produzido) e bits 6-7 != 11 (erro LST <= 3 K)
  boa        : QC_Day bits 0-1 == 00 (boa qualidade)
Etapa 1 (--extrair): Earth Engine, uma linha por composto de 8 dias x bioma.
Etapa 2 (--analisar): agregação mensal (janelas da base), tabelas, resumo, gráficos, ENSO.
"""
import argparse, sys, csv, datetime as dt
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import npp_modis_gee as m

VERS = ["sem_filtro", "erro_3k", "boa"]; ROT = {"sem_filtro": "sem filtro", "erro_3k": "erro ≤ 3 K", "boa": "boa qualidade"}
BIOMAS = ["Mata Atlântica", "Cerrado", "Caatinga"]; SIG = {"Mata Atlântica": "MA", "Cerrado": "CE", "Caatinga": "CA"}
COR = {"sem_filtro": "#444444", "erro_3k": "#2471a3", "boa": "#c0392b"}

# ------------------------------------------------------------------ 1. extração
def extrair(project, ibge, saida, a0=2000, a1=2025):
    import ee; ee.Initialize(project=project)
    geoms = m.biomas_locais(ee, f"{ibge}/lm_bioma_250.shp", f"{ibge}/BA_UF_2022.shp", "Bioma", BIOMAS, 0.0005)
    fc = ee.FeatureCollection([ee.Feature(g, {"bioma": b}) for b, g in geoms.items()])
    col = ee.ImageCollection("MODIS/061/MOD11A2"); proj = ee.Image(col.first()).select("LST_Day_1km").projection(); esc = proj.nominalScale().getInfo()
    red = ee.Reducer.mean().combine(ee.Reducer.count(), sharedInputs=True)
    out = open(saida, "w", newline=""); w = csv.writer(out)
    w.writerow(["data", "bioma"] + [f"{v}_mean" for v in VERS] + [f"{v}_count" for v in VERS]); out.flush()
    for ano in range(a0, a1 + 1):
        sub = col.filterDate(f"{ano}-01-01", f"{ano + 1}-01-01")
        def f(img):
            img = ee.Image(img); lst = img.select("LST_Day_1km"); qc = img.select("QC_Day")
            valido = lst.gte(7500).And(lst.lte(65535)); c = lst.multiply(0.02).add(-273.15)
            b01 = qc.bitwiseAnd(3); b67 = qc.rightShift(6).bitwiseAnd(3)
            img3 = ee.Image.cat(c.updateMask(valido).rename("sem_filtro"),
                                c.updateMask(valido.And(b01.lte(1)).And(b67.lte(2))).rename("erro_3k"),
                                c.updateMask(valido.And(b01.eq(0))).rename("boa"))
            return img3.reduceRegions(collection=fc, reducer=red, crs=proj, scale=esc, tileScale=4).map(lambda ft: ft.set({"t": img.get("system:time_start")}))
        feats = ee.FeatureCollection(sub.map(f)).flatten().getInfo()["features"]
        for ft in feats:
            p = ft["properties"]; d = dt.datetime.fromtimestamp(p["t"] / 1000, dt.timezone.utc).date()
            w.writerow([d.isoformat(), p["bioma"]] + [p.get(f"{v}_mean") for v in VERS] + [p.get(f"{v}_count") for v in VERS])
        out.flush(); print(ano, len(feats), flush=True)

# ------------------------------------------------------------------ 2. agregação mensal (mesma regra da base)
def agregar(comp):
    comp = comp.copy(); comp["data"] = pd.to_datetime(comp.data).dt.date; rows = []
    for b in BIOMAS:
        g = comp[comp.bioma == b].set_index("data")
        for ano in range(2001, 2026):
            for mes in range(1, 13):
                datas = [m._data_doy(ano, d) for d in m.JANELAS_BENFICA[mes]]; sel = g.reindex([d for d in datas if d in g.index])
                if len(sel) < 2: continue
                r = {"ano": ano, "mes": mes, "bioma": b}
                for v in VERS:
                    ok = sel[sel[f"{v}_count"].fillna(0) > 0]
                    r[f"tst_{v}"] = ok[f"{v}_mean"].mean() if len(ok) else np.nan   # média das médias das composições válidas
                    r[f"pix_{v}"] = sel[f"{v}_count"].fillna(0).sum()
                for v in VERS[1:]: r[f"retido_pct_{v}"] = 100 * r[f"pix_{v}"] / r["pix_sem_filtro"] if r["pix_sem_filtro"] else np.nan
                rows.append(r)
    return pd.DataFrame(rows)

def resumo(mensal, pre):
    """pre: DataFrame ano, mes, bioma, precip_mm (base atual) para definir trimestres chuvoso/seco por bioma"""
    linhas = []
    for b in BIOMAS:
        d = mensal[mensal.bioma == b].dropna(subset=[f"tst_{v}" for v in VERS])
        clim = pre[pre.bioma == b].groupby("mes").precip_mm.mean(); c3 = pd.Series({mm: sum(clim.get(((mm + k - 1) % 12) + 1, 0) for k in range(3)) for mm in range(1, 13)})
        chuv = [((c3.idxmax() + k - 1) % 12) + 1 for k in range(3)]; seco = [((c3.idxmin() + k - 1) % 12) + 1 for k in range(3)]
        for v in VERS[1:]:
            for rot, sub in (("ano todo", d), ("trimestre chuvoso " + "/".join(map(str, chuv)), d[d.mes.isin(chuv)]), ("trimestre seco " + "/".join(map(str, seco)), d[d.mes.isin(seco)])):
                dif = sub[f"tst_{v}"] - sub.tst_sem_filtro; i = dif.abs().idxmax()
                linhas.append(dict(bioma=b, versao=ROT[v], periodo=rot, n_meses=len(sub), dif_media_C=dif.mean(), dif_mediana_C=dif.median(), rmse_C=np.sqrt((dif ** 2).mean()),
                                   r_pearson=np.corrcoef(sub[f"tst_{v}"], sub.tst_sem_filtro)[0, 1], maior_dif_abs_C=dif.abs().max(), mes_maior_dif=f"{int(sub.loc[i, 'ano'])}-{int(sub.loc[i, 'mes']):02d}",
                                   pct_descartado_medio=100 - sub[f"retido_pct_{v}"].mean(), pct_descartado_max=100 - sub[f"retido_pct_{v}"].min(),
                                   rho_spearman_tst_vs_pct_descartado=pd.Series(sub.tst_sem_filtro.values).corr(pd.Series(100 - sub[f"retido_pct_{v}"].values), method="spearman")))
    return pd.DataFrame(linhas)

def enso(mensal, fases):
    from scipy import stats
    rows = []
    for b in BIOMAS:
        d = mensal[mensal.bioma == b].merge(fases, on=["ano", "mes"], how="inner")
        for v in VERS:
            s = d[f"tst_{v}"]; clim = d.groupby("mes")[f"tst_{v}"].transform("mean"); an = s - clim; anp = 100 * an / clim
            g = {f: an[d.fase == f].dropna() for f in ["El Niño", "La Niña", "Neutro"]}; gp = {f: anp[d.fase == f].dropna() for f in g}
            kw = stats.kruskal(*g.values()); p90 = np.nanpercentile(an, 90)
            for f in ["El Niño", "La Niña"]:
                mw = stats.mannwhitneyu(g[f], g["Neutro"])
                rows.append(dict(bioma=b, versao=ROT[v], fase=f, n=len(g[f]), anomalia_media_C=g[f].mean() - g["Neutro"].mean(), anomalia_media_pct=gp[f].mean() - gp["Neutro"].mean(),
                                 p_mannwhitney_vs_neutro=mw.pvalue, p_kruskal=kw.pvalue, pct_meses_acima_P90=100 * (g[f] > p90).mean(), pct_neutro_acima_P90=100 * (g["Neutro"] > p90).mean()))
    return pd.DataFrame(rows)

def analisar(comp_csv, out, base_longo, dados_modelo):
    out = Path(out); out.mkdir(exist_ok=True)
    comp = pd.read_csv(comp_csv); mensal = agregar(comp)
    base = pd.read_csv(base_longo); chk = mensal.merge(base[["ano", "mes", "bioma", "lst_dia_c", "precip_mm"]], on=["ano", "mes", "bioma"])
    print(f"checagem: |TST sem filtro - base atual| máx = {(chk.tst_sem_filtro - chk.lst_dia_c).abs().max():.4f} °C")
    mensal["data"] = pd.to_datetime(dict(year=mensal.ano, month=mensal.mes, day=1))
    cols = ["data", "ano", "mes", "bioma"] + [f"tst_{v}" for v in VERS] + [f"pix_{v}" for v in VERS] + [f"retido_pct_{v}" for v in VERS[1:]]
    mensal[cols].round(3).to_csv(out / "tst_qc_series_mensais.csv", index=False, encoding="utf-8-sig")
    res = resumo(mensal, base[["ano", "mes", "bioma", "precip_mm"]]); res.round(4).to_csv(out / "tst_qc_resumo.csv", index=False, encoding="utf-8-sig")
    dm = pd.read_excel(dados_modelo); dm.columns = dm.columns.str.strip(); fases = dm[["ANO", "MÊS", "Enso"]].rename(columns={"ANO": "ano", "MÊS": "mes", "Enso": "fase"})
    en = enso(mensal, fases); en.round(4).to_csv(out / "tst_qc_enso.csv", index=False, encoding="utf-8-sig")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 1, figsize=(15, 10), sharex=True)
    for ax, b in zip(axes, BIOMAS):
        d = mensal[mensal.bioma == b]
        for v in VERS: ax.plot(d.data, d[f"tst_{v}"], color=COR[v], lw=1.2 if v == "sem_filtro" else 1, alpha=0.9, label=ROT[v])
        ax.set_title(b); ax.set_ylabel("TST diurna (°C)"); ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, ncol=3); fig.suptitle("TST mensal MOD11A2 com três critérios de QC_Day"); fig.tight_layout(); fig.savefig(out / "tst_qc_series.png", dpi=150); plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(15, 9), sharex=True)
    for ax, b in zip(axes, BIOMAS):
        d = mensal[mensal.bioma == b]
        for v in VERS[1:]: ax.plot(d.data, d[f"retido_pct_{v}"], color=COR[v], lw=1, label=ROT[v])
        ax.set_ylim(0, 102); ax.set_title(b); ax.set_ylabel("pixels retidos (%)"); ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False); fig.suptitle("Percentual de pixels retidos pelos filtros de QC_Day"); fig.tight_layout(); fig.savefig(out / "tst_qc_pixels_retidos.png", dpi=150); plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, b in zip(axes, BIOMAS):
        d = mensal[mensal.bioma == b]
        for v in VERS[1:]: ax.scatter(d.tst_sem_filtro, 100 - d[f"retido_pct_{v}"], s=10, color=COR[v], alpha=0.6, label=ROT[v])
        ax.set_title(b); ax.set_xlabel("TST sem filtro (°C)"); ax.set_ylabel("pixels descartados (%)"); ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False); fig.suptitle("Relação entre temperatura do mês e fração descartada pelo filtro"); fig.tight_layout(); fig.savefig(out / "tst_qc_descartados_vs_tst.png", dpi=150); plt.close(fig)
    pd.set_option("display.width", 250); print(res.round(3).to_string(index=False)); print(en.round(4).to_string(index=False))

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--extrair", action="store_true"); p.add_argument("--analisar", action="store_true")
    p.add_argument("--project", default="decoded-agency-465400-g8"); p.add_argument("--ibge", default="/tmp/claude-0/-home-user-Controle-Gas/176caef1-394a-5444-8d64-0af8cd0ef5b0/scratchpad/ibge_flat")
    p.add_argument("--comp", default="sensibilidade_qc/tst_qc_compostos_8dias.csv"); p.add_argument("--saida", default="sensibilidade_qc")
    p.add_argument("--base", default="../resultados/base_final_2001_2025_longo.csv"); p.add_argument("--dados", default="Dados_base_nova_2001_2025.xlsx")
    a = p.parse_args()
    if a.extrair: extrair(a.project, a.ibge, a.comp)
    if a.analisar: analisar(a.comp, a.saida, a.base, a.dados)
