# Modelo_PSN.py: o script que gerou os números da dissertação

`Modelo_PSN.py` é o script completo enviado pelo autor em 21/09/2026 (winsorização
calculada só no treino de cada partição, GroupKFold e TimeSeriesSplit, Ljung-Box,
Y-randomization fora da amostra, seleção de grau). `Dados_base_nova_2001_2025.xlsx`
é idêntico à base do repositório (mais três colunas de PET que o modelo ignora).

**Atenção:** o arquivo foi enviado com `GRAU_MODELO = 3` e Mata Atlântica =
`EV_MA, PRE_MA, TST_MA`. Os números da dissertação (Tabelas 2, 3 e seção 6.4)
correspondem a `GRAU_MODELO = 2` e Mata Atlântica = `EV_MA, TST_MA, WAI_MA`.
`Modelo_PSN_config_tese.py` é a cópia com esses dois ajustes (e sem abrir
janelas gráficas); `saida_config_tese.txt` é a saída da execução.

| Bioma | Métrica | Dissertação (docx v5) | Modelo_PSN_config_tese.py |
|---|---|---|---|
| Mata Atlântica | R² teste / RMSE / MAE | 73,7 / 7,97 / 6,29 | 73,65 / 7,97 / 6,29 |
| | GroupKFold / TimeSeriesSplit | 73,73 / 66,98 | 73,73 / 66,98 |
| | Shapiro W, p / ACF lag 1 | 0,996, 0,630 / 0,51 | 0,9959, 0,6299 / 0,505 |
| Cerrado | R² teste / RMSE / MAE | 96,7 / 6,74 / 5,43 | 96,66 / 6,74 / 5,43 |
| | GroupKFold / TimeSeriesSplit | 96,38 / 95,73 | 96,38 / 95,73 |
| | Shapiro W, p / ACF lag 1 | 0,995, 0,423 / 0,20 | 0,9949, 0,4232 / 0,201 |
| Caatinga | R² teste / RMSE / MAE | 94,2 / 6,69 / 5,08 | 94,16 / 6,69 / 5,08 |
| | GroupKFold / TimeSeriesSplit | 93,81 / 91,20 | 93,81 / 91,20 |
| | Shapiro W, p / ACF lag 1 | 0,983, 0,002 / 0,42 | 0,9833, 0,0015 / 0,420 |

Reprodução exata. Para repetir: `BIOMA_ATIVO=TODOS python3 Modelo_PSN_config_tese.py`.
