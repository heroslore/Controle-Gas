#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reproduz a base de dados completa de ponta a ponta:

  1. npp_modis_gee.py  --variavel todas  2001-2025   (7 variáveis mensais + ONI)
  2. npp_modis_gee.py  --variavel npp    2001-2025   (NPP anual)
  3. npp_modis_gee.py  --variavel precip com IMERG V06 2001-2020 (só para validação)
  4. validar_planilha.py                            (planilha x GEE, correções)
  5. montar_base.py                                 (CSV + Excel no layout Plan1)

Uso:
  python reproduzir_base.py --project SEU-PROJETO --planilha dados_graficos_Benfica_3.xlsx
Opções: --baixar-ibge PASTA (padrão dados_ibge), --inicio/--fim, --pular-gee
(reaproveita CSVs já existentes em saida/), --saida (padrão resultados).
As etapas 1-3 levam ~1 h no GEE; execute uma de cada vez (o script já faz isso).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def rodar(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=AQUI)
    if r.returncode not in (0, 2):        # 2 = terminou com avisos (meses sem dado)
        sys.exit(f"Etapa falhou (código {r.returncode}): {' '.join(cmd)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", required=True, help="ID do projeto Google Cloud registrado no GEE")
    p.add_argument("--planilha", default=None, help="xlsx da série histórica (para validar/corrigir)")
    p.add_argument("--baixar-ibge", default="dados_ibge")
    p.add_argument("--inicio", type=int, default=2001)
    p.add_argument("--fim", type=int, default=None)
    p.add_argument("--pular-gee", action="store_true", help="não reexecuta o GEE; usa CSVs em saida/")
    p.add_argument("--saida", default="resultados")
    a = p.parse_args()

    py = sys.executable
    saida = AQUI / "saida"; saida.mkdir(exist_ok=True)
    fim = [] if a.fim is None else ["--fim", str(a.fim)]
    base = [py, "npp_modis_gee.py", "--project", a.project, "--baixar-ibge", a.baixar_ibge]
    csv_gee = saida / "variaveis_2001_2025_longo.csv"
    csv_npp = saida / "npp_anual_2001_2025.csv"
    csv_v06 = saida / "precip_v06_2001_2020.csv"

    if not a.pular_gee:
        rodar(base + ["--variavel", "todas", "--inicio", str(a.inicio)] + fim + ["--saida", str(csv_gee)])
        rodar(base + ["--variavel", "npp", "--inicio", str(a.inicio)] + fim + ["--saida", str(csv_npp)])
        if a.planilha:
            rodar(base + ["--variavel", "precip", "--colecao", "NASA/GPM_L3/IMERG_MONTHLY_V06",
                          "--inicio", "2001", "--fim", "2020", "--saida", str(csv_v06)])

    if a.planilha:
        rodar([py, "validar_planilha.py", "--planilha", a.planilha, "--gee", str(csv_gee),
               "--gee-v06", str(csv_v06), "--saida", a.saida])
    rodar([py, "montar_base.py", "--gee", str(csv_gee), "--npp", str(csv_npp),
           "--saida", a.saida] + (["--validacao", a.saida] if a.planilha else []))
    print("\nConcluído. Base em", a.saida)


if __name__ == "__main__":
    main()
