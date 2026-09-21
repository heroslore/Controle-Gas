#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte a base final (formato longo de npp_modis_gee.py) para o layout de
entrada do Modelo_Ridge.py (Dados_Benfica_.xlsx): uma linha por mês, colunas
MÊS, ANO, ONI, Enso, NP_*, WAI_*, EV_*, PRE_*, TST_*, BURN_* para MA, CE, CA.

Uso:
  python preparar_entrada_modelo.py --base ../resultados/base_final_2001_2025_longo.csv \\
      --saida Dados_base_nova_2001_2025.xlsx [--inicio 2001 --fim 2020]
"""
import argparse
import numpy as np
import pandas as pd

SIGLA = {"Mata Atlântica": "MA", "Cerrado": "CE", "Caatinga": "CA"}
MAPA = {"psn_g_c_m2": "NP", "ida": "WAI", "et_mm": "EV", "precip_mm": "PRE",
        "lst_dia_c": "TST", "area_queimada_ha": "BURN"}


def enso(oni: float) -> str:
    if pd.isna(oni):
        return ""
    return "La Niña" if oni <= -0.5 else ("El Niño" if oni >= 0.5 else "Neutro")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base", required=True); p.add_argument("--saida", required=True)
    p.add_argument("--inicio", type=int, default=None); p.add_argument("--fim", type=int, default=None)
    a = p.parse_args()
    b = pd.read_csv(a.base)
    if a.inicio: b = b[b.ano >= a.inicio]
    if a.fim: b = b[b.ano <= a.fim]
    b["sigla"] = b.bioma.map(SIGLA)
    w = b.pivot_table(index=["ano", "mes"], columns="sigla", values=list(MAPA), dropna=False)
    w.columns = [f"{MAPA[v]}_{s}" for v, s in w.columns]
    oni = b.groupby(["ano", "mes"]).oni.first()
    out = pd.DataFrame({"MÊS": w.index.get_level_values("mes"), "ANO": w.index.get_level_values("ano"),
                        "ONI": oni.values, "Enso": [enso(x) for x in oni.values]})
    ordem = [f"{v}_{s}" for v in ["NP", "WAI", "EV", "PRE", "TST", "BURN"] for s in ["MA", "CE", "CA"]]
    for c in ordem:
        out[c] = w[c].values
    out.to_excel(a.saida, index=False)
    print(f"{a.saida}: {len(out)} linhas, {out.ANO.min()}-{out.ANO.max()}; vazios: "
          f"{out[ordem].isna().sum()[out[ordem].isna().sum() > 0].to_dict() or 'nenhum'}")


if __name__ == "__main__":
    main()
