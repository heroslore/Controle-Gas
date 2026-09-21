#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monta a base final (CSV + Excel) a partir das saídas de npp_modis_gee.py e de
validar_planilha.py, no layout da aba "Plan1" da planilha histórica:

    ano, mes, ONI, FMA_PSN, Cerrado_PSN, Caatinga_PSN, FMA_Evap, ..., Caatinga_AreaQueimada

Base final = série mensal 2001-2025 calculada inteira no GEE (mesma coleção e
versão em todos os anos, sem valores herdados da planilha). Na subpasta
referencia/ ficam, só para comparação, a planilha original/corrigida 2001-2020
emendada aos anos novos, e as métricas de validação.

Uso:
  python montar_base.py --gee saida/variaveis_2001_2025_longo.csv \\
      --npp saida/npp_anual_2001_2025.csv --validacao resultados --saida resultados
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BIOMAS = ["Mata Atlântica", "Cerrado", "Caatinga"]
ROTULO_BIOMA = {"Mata Atlântica": "FMA", "Cerrado": "Cerrado", "Caatinga": "Caatinga"}
VARS = {"psn_g_c_m2": "PSN", "et_mm": "Evap", "pet_mm": "PET", "ida": "IDA",
        "lst_dia_c": "Temp", "precip_mm": "Precip", "area_queimada_ha": "AreaQueimada"}
CHAVE = ["ano", "mes", "bioma"]


def layout_plan1(df: pd.DataFrame) -> pd.DataFrame:
    """Formato longo (ano, mes, bioma, variáveis, oni) -> layout Plan1."""
    w = df.pivot_table(index=["ano", "mes"], columns="bioma", values=list(VARS), dropna=False)
    cols = [(v, b) for v in VARS for b in BIOMAS]
    w = w.reindex(columns=pd.MultiIndex.from_tuples(cols))
    w.columns = [f"{ROTULO_BIOMA[b]}_{VARS[v]}" for v, b in w.columns]
    w.insert(0, "ONI", df.groupby(["ano", "mes"]).oni.first())
    return w.round(4).reset_index()


def salvar(df: pd.DataFrame, pasta: Path, nome: str) -> None:
    df.to_csv(pasta / f"{nome}.csv", index=False, encoding="utf-8-sig")
    df.to_csv(pasta / f"{nome}_excel_ptbr.csv", index=False, encoding="utf-8-sig",
              sep=";", decimal=",")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gee", required=True, help="CSV longo 2001-2025 de npp_modis_gee.py (--variavel todas)")
    p.add_argument("--npp", default=None, help="CSV do NPP anual (--variavel npp)")
    p.add_argument("--validacao", default=None,
                   help="pasta com planilha_tidy.csv, planilha_corrigida.csv, correcoes_planilha.csv "
                        "e validacao_resumo.csv (saída de validar_planilha.py)")
    p.add_argument("--saida", default="resultados")
    a = p.parse_args()
    out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)

    gee = pd.read_csv(a.gee)
    for c in list(VARS) + ["oni"]:
        if c not in gee.columns:
            gee[c] = np.nan
    gee = gee[CHAVE + list(VARS) + ["oni"]].sort_values(CHAVE)
    ano_ini, ano_fim = int(gee.ano.min()), int(gee.ano.max())

    abas = {}
    # ---- BASE FINAL: série homogênea calculada inteira no GEE -------------
    salvar(gee.round(4), out, f"base_final_{ano_ini}_{ano_fim}_longo")
    final = layout_plan1(gee); salvar(final, out, f"base_final_{ano_ini}_{ano_fim}_plan1")
    abas[f"BASE_FINAL_{ano_ini}_{ano_fim}"] = final
    faltas = gee[list(VARS)].isna().sum(); faltas = faltas[faltas > 0]
    if len(faltas):
        print("Células vazias na base final (aguardando publicação do produto):",
              faltas.to_dict())

    # ---- Referência: comparação com a planilha histórica ------------------
    if a.validacao:
        val = Path(a.validacao); ref = out / "referencia"; ref.mkdir(exist_ok=True)
        oni = gee[["ano", "mes", "oni"]].drop_duplicates()
        novos = gee[gee.ano > 2020]
        for nome, arq in (("planilha_corrigida", "planilha_corrigida.csv"),
                          ("planilha_original", "planilha_tidy.csv")):
            pl = pd.read_csv(val / arq).merge(oni, on=["ano", "mes"], how="left")
            pl["pet_mm"] = np.nan
            serie = pd.concat([pl[CHAVE + list(VARS) + ["oni"]], novos]).sort_values(CHAVE)
            w = layout_plan1(serie); salvar(w, ref, f"{nome}_2001_2020_mais_gee_2021_{ano_fim}_plan1")
            abas[f"ref_{nome}"[:31]] = w
        for nome, arq in (("ref_correcoes_planilha", "correcoes_planilha.csv"),
                          ("ref_validacao_resumo", "validacao_resumo.csv"),
                          ("ref_validacao_pares", "validacao_pares.csv")):
            if (val / arq).exists():
                abas[nome] = pd.read_csv(val / arq)

    if a.npp:
        npp = pd.read_csv(a.npp)
        w = npp.pivot_table(index="ano", columns="bioma", values="npp_g_c_m2")[BIOMAS].round(3).reset_index()
        w.columns = ["ano"] + [f"{ROTULO_BIOMA[b]}_NPP" for b in BIOMAS]
        salvar(w, out, f"npp_anual_{int(npp.ano.min())}_{int(npp.ano.max())}")
        abas["NPP_anual"] = w

    abas["Leia-me"] = pd.DataFrame({
        "campo": ["PSN", "Evap / PET", "IDA", "Temp", "Precip", "AreaQueimada", "ONI", "NPP anual",
                  "agregação mensal", "limites", "código"],
        "valor": ["MODIS/061/MOD17A2HGF PsnNet x0,1 (g C/m²), soma de 4 composições 8-dias",
                  "MODIS/061/MOD16A2GF ET e PET x0,1 (mm), soma de 4 composições",
                  "ET/PET (razão das somas mensais) = IDA/WAI da planilha",
                  "MODIS/061/MOD11A2 LST_Day_1km x0,02 - 273,15 (°C), média das composições",
                  "GPM IMERG mensal Final V07, mm/h x horas do mês (planilha 2001-2020 usou V06)",
                  "MODIS/061/MCD64A1: n.º de pixels queimados x 25 ha",
                  "NOAA CPC ONI, mês central da estação de 3 meses",
                  "MODIS/061/MOD17A3HGF Npp x0,1 (g C/m²/ano)",
                  "janelas fixas de DOY da planilha (jan = DOY 361 do ano anterior + 1, 9, 17; ...; dez = 337-361)",
                  "IBGE Biomas 1:250.000 (2019) ∩ IBGE malha estadual 2022 (BA)",
                  "npp_modis_gee.py + validar_planilha.py + montar_base.py (Google Earth Engine)"]})
    abas["Leia-me"].loc[len(abas["Leia-me"])] = ["base final", "série 2001-2025 inteira calculada no GEE; a planilha só serviu para validar o método"]

    xlsx = out / f"base_bahia_biomas_{ano_ini}_{ano_fim}.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as xw:
        for nome, df in abas.items():
            df.to_excel(xw, sheet_name=nome[:31], index=False)
    print(f"Base montada em {out}/  (Excel: {xlsx.name}; abas: {', '.join(abas)})")


if __name__ == "__main__":
    main()
