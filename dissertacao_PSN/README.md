# Dissertação — Modelagem MRMP-N (PSN nos biomas da Bahia)

Pasta independente do aplicativo Controle-Gás. Guarda os scripts e a base de
dados da dissertação (PPGCTA) para que o trabalho continue de onde parou.
Leia `handoff_claude_code.md` para o contexto completo e a lista de pendências.

## Arquivos

| Arquivo | O que é |
|---|---|
| `Modelo_PSN.py` | Script principal: Ridge polinomial (grau 2), GroupKFold por ano, TimeSeriesSplit, Ljung-Box, Y-randomization. |
| `Analise_Biomas_PSN.py` | Análise ENSO: Kruskal-Wallis por fase, Pearson ONI×variáveis, OLS ONI→variáveis, boxplots e dispersões. |
| `base_final_2001_2025_plan1_excel_ptbr.csv` | Base bruta (2001–2025, separador `;`, decimal `,`). |
| `Dados_base_nova_2001_2025.xlsx` | Base convertida (gerada automaticamente pelos scripts a partir do CSV), já com a coluna `Enso`. |
| `enso_noaa.py` | Classificação oficial das fases ENSO (NOAA/CPC: ONI ≥ \|0,5\| por ≥ 5 trimestres consecutivos). Usado pelos dois scripts. |
| `oni_noaa_cpc.txt` | Tabela ONI completa da NOAA (1950–presente), fonte das fases nas bordas do período. Atualizar com `curl -o oni_noaa_cpc.txt https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`. |
| `Selecao_Variaveis_PSN.py` | Busca exaustiva das 10 combinações C(5,3) de variáveis ambientais por bioma, mesmo pipeline do modelo. |
| `consolidar_resultados.py` | Junta logs e CSVs em `numeros_extra.json` / `enso_resumo.json` (usados pelo script do Word). |
| `Figuras_Dissertacao.py` | Monta as figuras da dissertação em `figuras_dissertacao/` a partir de `resultados_2001_2025/`. |
| `resultados_2001_2025/` | Resultados da rodada com a base 2001–2025 (ver `RESULTADOS.md`). |
| `banca/` | Pareceres da banca, análise comentário a comentário, script que aplica as mudanças no Word e o documento revisado. |
| `handoff_claude_code.md` | Resumo do estado do projeto, resultados confirmados e o que falta rodar. |

## Como rodar

```bash
cd dissertacao_PSN
pip install pandas numpy scipy statsmodels scikit-learn matplotlib openpyxl
BIOMA_ATIVO=TODOS python3 Modelo_PSN.py     # MA, CE e CA em paralelo
python3 Analise_Biomas_PSN.py               # análise ENSO
```

Para regenerar a dissertação revisada a partir dos resultados:

```bash
python3 Selecao_Variaveis_PSN.py      # opcional, lento (~15 min)
python3 consolidar_resultados.py
python3 Figuras_Dissertacao.py
python3 banca/aplicar_revisao_docx.py # gera banca/Trabalho_revisado_2001_2025.docx
banca/render_e_paginas.sh             # PDF via LibreOffice + páginas das listas (rodar o script de novo depois)
```

As saídas vão para `saidas_figuras/` (uma subpasta por bioma no modelo).
Essa pasta não é versionada aqui e nada dela é publicado no site do
Controle-Gás: o workflow de Pages copia apenas `index.html`, `manifest.json`
e os ícones.
