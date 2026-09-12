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
| `Dados_base_nova_2001_2025.xlsx` | Base convertida (gerada automaticamente pelos scripts a partir do CSV). |
| `handoff_claude_code.md` | Resumo do estado do projeto, resultados confirmados e o que falta rodar. |

## Como rodar

```bash
cd dissertacao_PSN
pip install pandas numpy scipy statsmodels scikit-learn matplotlib openpyxl
BIOMA_ATIVO=TODOS python3 Modelo_PSN.py     # MA, CE e CA em paralelo
python3 Analise_Biomas_PSN.py               # análise ENSO
```

As saídas vão para `saidas_figuras/` (uma subpasta por bioma no modelo).
Essa pasta não é versionada aqui e nada dela é publicado no site do
Controle-Gás: o workflow de Pages copia apenas `index.html`, `manifest.json`
e os ícones.
