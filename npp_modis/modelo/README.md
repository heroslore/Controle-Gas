# Modelo Ridge polinomial (MRMP-N) rodado na base nova

- `Modelo_Ridge.py`: o modelo do autor, sem alteração de lógica.
- `preparar_entrada_modelo.py`: converte `resultados/base_final_2001_2025_longo.csv` para o layout de entrada do modelo (`MÊS, ANO, ONI, Enso, NP_*, WAI_*, EV_*, PRE_*, TST_*, BURN_*`).
- `rodar_modelo.py`: executa o modelo para cada bioma e conjunto de dados em pastas separadas (`execucoes/<dados>_<bioma>/`), sem janelas gráficas, e resume em `execucoes/resumo_execucoes.csv`.
- Entradas: `Dados_Benfica_original.xlsx` (planilha antiga, 240 meses), `Dados_base_nova_2001_2020.xlsx` (240) e `Dados_base_nova_2001_2025.xlsx` (297 meses; out–dez/2025 removidos por falta da chuva IMERG Final).

Reproduzir:

```bash
python preparar_entrada_modelo.py --base ../resultados/base_final_2001_2025_longo.csv --saida Dados_base_nova_2001_2025.xlsx
python rodar_modelo.py --dados original=Dados_Benfica_original.xlsx --dados nova_2001_2025=Dados_base_nova_2001_2025.xlsx
```

Configuração do modelo como recebida: grau 2, RepeatedKFold 5×30 (150 folds), alpha por GridSearchCV em {0.1, 1, 10, 50, 100}, winsorização de 3 % na resposta, preditores por bioma: MA e CA = EV, PRE, TST + sazonalidade; CE = EV, PRE, WAI + sazonalidade.
