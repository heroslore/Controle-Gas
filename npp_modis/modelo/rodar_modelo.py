#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roda Modelo_Ridge.py (sem alterar sua lógica) para cada bioma e cada conjunto
de dados, em pastas separadas, sem janelas gráficas, e resume as estatísticas.

Uso:
  python rodar_modelo.py --dados original=Dados_Benfica_original.xlsx \\
      --dados nova2020=Dados_base_nova_2001_2020.xlsx --dados nova2025=Dados_base_nova_2001_2025.xlsx
"""
import argparse, os, re, shutil, subprocess, sys
from pathlib import Path
import pandas as pd

AQUI = Path(__file__).resolve().parent
MODELO = AQUI / "Modelo_Ridge.py"


def rodar(rotulo: str, arquivo: Path, bioma: str, saida: Path) -> dict:
    pasta = saida / f"{rotulo}_{bioma}"; pasta.mkdir(parents=True, exist_ok=True)
    shutil.copy(arquivo, pasta / "Dados_Benfica_.xlsx")          # nome que o modelo espera
    codigo = MODELO.read_text(encoding="utf-8")
    codigo = re.sub(r"BIOMA_ATIVO = '..'", f"BIOMA_ATIVO = '{bioma}'", codigo)
    codigo = codigo.replace("plt.show()", "plt.close('all')")   # sem janelas
    (pasta / "Modelo_Ridge.py").write_text(codigo, encoding="utf-8")
    env = dict(os.environ, MPLBACKEND="Agg", PYTHONIOENCODING="utf-8")
    with open(pasta / "saida_completa.txt", "w", encoding="utf-8") as log:
        r = subprocess.run([sys.executable, "Modelo_Ridge.py"], cwd=pasta, env=env, stdout=log, stderr=subprocess.STDOUT)
    texto = (pasta / "saida_completa.txt").read_text(encoding="utf-8")
    if r.returncode != 0:
        print(texto[-1500:]); raise SystemExit(f"Modelo falhou em {rotulo}/{bioma}")
    def pega(padrao, conv=float):
        m = re.search(padrao, texto); return conv(m.group(1)) if m else None
    res = dict(dados=rotulo, bioma=bioma, n=len(pd.read_excel(arquivo)),
               r2_treino=pega(r"R2 Treino médio: ([\d.\-]+)"), r2_teste=pega(r"R2 Teste médio: ([\d.\-]+)"),
               r2_teste_dp=pega(r"R2 Teste desvio padrão: ([\d.\-]+)"), r2aj_treino=pega(r"R2 Ajustado Treino médio: ([\d.\-]+)"),
               rmse_teste=pega(r"RMSE Teste médio: ([\d.\-]+)"), mae_teste=pega(r"MAE Teste médio: ([\d.\-]+)"),
               ic95_inf=pega(r"IC 95% R² Teste: \[([\d.\-]+)%"), ic95_sup=pega(r"— ([\d.\-]+)%\]"),
               alpha_medio=pega(r"Alpha médio utilizado na análise de resíduos: ([\d.]+)"),
               shapiro_p=pega(r"Shapiro-Wilk: stat=[\d.]+, p=([\d.]+)"),
               yrand_delta_pp=pega(r"Diferença \(Δ\)\s+: ([\d.\-]+) pp"),
               vif_max=max(float(x) for x in re.findall(r"^\d+\s+\S+\s+([\d.]+)$", texto.split("===== VIF =====")[1].split("Alpha")[0], re.M)))
    return res


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dados", action="append", required=True, help="rotulo=arquivo.xlsx (repetível)")
    p.add_argument("--biomas", nargs="+", default=["MA", "CE", "CA"])
    p.add_argument("--saida", default="execucoes")
    a = p.parse_args()
    saida = AQUI / a.saida
    linhas = []
    for item in a.dados:
        rotulo, arq = item.split("=", 1)
        for b in a.biomas:
            print(f"rodando {rotulo} / {b} ...", flush=True)
            linhas.append(rodar(rotulo, AQUI / arq, b, saida))
    df = pd.DataFrame(linhas)
    df.to_csv(saida / "resumo_execucoes.csv", index=False, encoding="utf-8-sig")
    pd.set_option("display.width", 250)
    print(df.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
