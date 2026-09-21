#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validação da base gerada pelo GEE contra a planilha histórica
(dados_graficos_Benfica_3.xlsx, aba "Planilha1", 12 blocos mensais 2001-2020).

Entrada:
  --planilha  xlsx da série histórica
  --gee       CSV longo gerado por npp_modis_gee.py (--variavel todas, formato longo)
  --gee-v06   (opcional) CSV de precipitação IMERG V06 gerado com
              --variavel precip --colecao NASA/GPM_L3/IMERG_MONTHLY_V06
Saída (na pasta --saida):
  validacao_pares.csv      um par planilha x GEE por ano, mês, bioma e variável
  validacao_resumo.csv     r de Pearson, erro mediano e p90 do |erro| por variável
  correcoes_planilha.csv   células da planilha com desvio material (> limiar)
  planilha_tidy.csv        a planilha reorganizada em formato longo
  planilha_corrigida.csv   idem, com as células atípicas substituídas pelo GEE

Uso:
  python validar_planilha.py --planilha dados_graficos_Benfica_3.xlsx \\
      --gee saida/variaveis_2001_2025_longo.csv --gee-v06 saida/precip_v06.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

BIOMAS = ["Mata Atlântica", "Cerrado", "Caatinga"]
# posição (coluna inicial) de cada bloco de variável dentro de cada bloco mensal
BLOCOS = {"psn_g_c_m2": 1, "ida": 5, "et_mm": 10, "precip_mm": 15,
          "lst_dia_c": 20, "area_queimada_ha": 25}
# limiares para marcar uma célula da planilha como atípica:
# |GEE - planilha| > absoluto  E  |GEE - planilha| / |planilha| > relativo
LIMIARES = {"psn_g_c_m2": (20, 0.30), "et_mm": (20, 0.30), "ida": (0.1, 0.30),
            "lst_dia_c": (3, 0.10), "precip_mm": (30, 0.30)}


def ler_planilha(caminho: Path) -> pd.DataFrame:
    """Converte os 12 blocos mensais da aba Planilha1 em formato longo."""
    df = pd.read_excel(caminho, sheet_name="Planilha1", header=None)
    cabecalhos = df[df[1].astype(str).str.contains("PSN|photos", case=False, na=False)].index
    if len(cabecalhos) != 12:
        raise SystemExit(f"Esperava 12 blocos mensais na planilha, achei {len(cabecalhos)}.")
    linhas = []
    for mes, i in enumerate(cabecalhos, 1):
        bloco = df.iloc[i + 2:i + 22]          # 20 anos (2001-2020)
        for _, r in bloco.iterrows():
            for j, bioma in enumerate(BIOMAS):
                d = {"ano": int(r[0]), "mes": mes, "bioma": bioma}
                for var, c0 in BLOCOS.items():
                    d[var] = pd.to_numeric(r[c0 + j], errors="coerce")
                linhas.append(d)
    return pd.DataFrame(linhas)


def validar(planilha: pd.DataFrame, gee: pd.DataFrame, v06: pd.DataFrame | None):
    chave = ["ano", "mes", "bioma"]
    g = gee.copy()
    if v06 is not None:
        g = g.merge(v06[chave + ["precip_mm"]].rename(columns={"precip_mm": "precip_v06_mm"}),
                    on=chave, how="left")
    x = planilha.merge(g, on=chave, suffixes=("_planilha", "_gee"))
    x = x[(x.ano >= 2001) & (x.ano <= 2020)]

    resumo, pares = [], []
    comparacoes = [(v, f"{v}_gee", "") for v in BLOCOS]
    if v06 is not None:
        comparacoes.append(("precip_mm", "precip_v06_mm", "IMERG V06"))
    for var, col_gee, fonte in comparacoes:
        a, b = x[f"{var}_planilha"], x[col_gee]
        ok = a.notna() & b.notna() & (a != 0)
        e = 100 * (b[ok] - a[ok]) / a[ok]
        resumo.append(dict(variavel=var, fonte=fonte or "GEE (coleção do script)", n=int(ok.sum()),
                           r_pearson=np.corrcoef(a[ok], b[ok])[0, 1],
                           erro_pct_mediano=e.median(), p90_abs_erro_pct=e.abs().quantile(.9)))
        p = x.loc[ok, chave].copy()
        p["variavel"], p["fonte"], p["planilha"], p["gee"], p["erro_pct"] = var, fonte or "GEE", a[ok], b[ok], e
        pares.append(p)
    return pd.DataFrame(resumo), pd.concat(pares), x


def corrigir(planilha: pd.DataFrame, x: pd.DataFrame, usa_v06: bool):
    """Substitui células atípicas pelo valor reproduzido; devolve tabela e log."""
    corr = planilha.copy()
    log = []
    for var, (absd, rel) in LIMIARES.items():
        col_gee = "precip_v06_mm" if (var == "precip_mm" and usa_v06) else f"{var}_gee"
        a, b = x[f"{var}_planilha"], x[col_gee]
        m = ((b - a).abs() > absd) & ((b - a).abs() / a.abs().replace(0, np.nan) > rel)
        for _, r in x[m].iterrows():
            idx = corr[(corr.ano == r.ano) & (corr.mes == r.mes) & (corr.bioma == r.bioma)].index[0]
            log.append(dict(variavel=var, ano=int(r.ano), mes=int(r.mes), bioma=r.bioma,
                            valor_planilha=corr.at[idx, var], valor_corrigido=round(r[col_gee], 4),
                            fonte_correcao=("IMERG V06 (GEE)" if col_gee == "precip_v06_mm"
                                            else "GEE, mesma regra de agregação"),
                            desvio_pct=round(100 * (r[col_gee] - corr.at[idx, var]) / corr.at[idx, var], 1)))
            corr.at[idx, var] = round(r[col_gee], 4)
    return corr, pd.DataFrame(log)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--planilha", required=True)
    p.add_argument("--gee", required=True)
    p.add_argument("--gee-v06", default=None)
    p.add_argument("--saida", default="resultados")
    a = p.parse_args()
    out = Path(a.saida); out.mkdir(parents=True, exist_ok=True)

    planilha = ler_planilha(Path(a.planilha))
    gee = pd.read_csv(a.gee)
    v06 = pd.read_csv(a.gee_v06) if a.gee_v06 else None
    resumo, pares, x = validar(planilha, gee, v06)
    corrigida, log = corrigir(planilha, x, v06 is not None)

    planilha.to_csv(out / "planilha_tidy.csv", index=False, encoding="utf-8-sig")
    corrigida.to_csv(out / "planilha_corrigida.csv", index=False, encoding="utf-8-sig")
    pares.round(4).to_csv(out / "validacao_pares.csv", index=False, encoding="utf-8-sig")
    resumo.round(4).to_csv(out / "validacao_resumo.csv", index=False, encoding="utf-8-sig")
    log.to_csv(out / "correcoes_planilha.csv", index=False, encoding="utf-8-sig")
    print("Validação planilha x GEE (2001-2020):")
    print(resumo.round(3).to_string(index=False))
    print(f"\nCélulas atípicas na planilha: {len(log)}")
    if len(log):
        print(log.to_string(index=False))


if __name__ == "__main__":
    main()
