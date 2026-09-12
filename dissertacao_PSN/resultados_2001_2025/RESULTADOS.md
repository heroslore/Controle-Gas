# Resultados — base 2001–2025 (n = 297)

Rodada em 12/09/2026 com `Modelo_PSN.py` (BIOMA_ATIVO=TODOS, grau 2,
RODAR_YRANDOMIZATION=True, TESTAR_GRAUS=False) e `Analise_Biomas_PSN.py`.
Base: `base_final_2001_2025_plan1_excel_ptbr.csv`, 300 linhas; removidas
out/nov/dez de 2025 (precipitação ainda não publicada) → 297 linhas.
Logs completos em `log_modelo_psn.txt` e `log_analise_biomas.txt`.

## 1. Desempenho do modelo (RepeatedKFold, 150 rodadas)

| Bioma | R² treino | R² teste | IC95% teste | Gap (pp) | RMSE | MAE | GroupKFold ano | TimeSeriesSplit | Queda TS (pp) |
|---|---|---|---|---|---|---|---|---|---|
| MA | 76,10 | **70,96** | 56,55–80,19 | 5,14 | 8,37 | 6,57 | 70,54 | 63,47 | 7,49 |
| CE | 97,25 | **96,66** | 95,40–97,71 | 0,59 | 6,74 | 5,43 | 96,38 | 95,73 | 0,93 |
| CA | 95,19 | **94,16** | 90,79–96,25 | 1,03 | 6,69 | 5,08 | 93,81 | 91,20 | 2,97 |

Confere com a tabela do handoff (MA 70,96 / CE 96,66 / CA 94,16; gaps 5,14 /
0,59 / 1,03). R² out-of-fold da Figura 3: MA 71,41 %, CE (ver log), CA 94,65 %.

## 2. Y-randomization (100 permutações, validação cruzada) — NOVO

| Bioma | R² CV original | R² CV permutados (média ± dp) | Δ (pp) | p empírico | Status |
|---|---|---|---|---|---|
| MA | 71,38 % | −9,91 ± 3,05 % | 81,30 | 0,0099 | APROVADO |
| CE | 96,66 % | −10,88 ± 2,64 % | 107,54 | 0,0099 | APROVADO |
| CA | 94,16 % | −13,04 ± 3,07 % | 107,20 | 0,0099 | APROVADO |

p = 0,0099 = 1/(100+1): o modelo original superou todas as 100 permutações.
Critério operacional de 60 pp atingido nos três biomas. Figuras:
`MA/yrandomization_MA.png`, `CE/…`, `CA/…`.

## 3. VIF completo por bioma — NOVO (`vif_por_bioma.csv`)

| Variável | MA | CE | CA |
|---|---|---|---|
| EV | 1,93 | **36,99** | 5,02 |
| PRE | 1,25 | 4,02 | 1,68 |
| TST / WAI | TST 3,29 | WAI **31,61** | TST 3,90 |
| saz_sin | 1,66 | 4,49 | 2,63 |
| saz_cos | 3,76 | 3,59 | 3,76 |

MA e CA: todos abaixo de 5 (CA EV = 5,02, no limite). CE: EV_CE e WAI_CE
com colinearidade grave, como já descrito no handoff.

## 4. Diagnóstico dos resíduos

| Bioma | Shapiro-Wilk p | Normais | Ljung-Box(12) p | ACF lag1 | Alpha Ridge |
|---|---|---|---|---|---|
| MA | 0,5709 | Sim | 0,0000 | +0,299 | 4,48 |
| CE | 0,4232 | Sim | 0,0052 | +0,201 | 0,10 |
| CA | 0,0015 | Não | 0,0000 | +0,420 | 0,10 |

Autocorrelação residual nos três biomas, idêntica ao achado do handoff.
CA é o único com resíduos não normais (caudas mais pesadas no QQ-plot).

## 5. Coeficientes Ridge (Figura 5) — NOVO

Arquivos: `MA/coeficientes_ridge_MA.csv`, `CE/…`, `CA/…` (20 termos cada:
5 lineares, 5 quadráticos, 10 interações). Importância relativa dos termos
lineares (|coef| / soma |coef| lineares):

| Termo | MA | CE | CA |
|---|---|---|---|
| EV | +12,13 (32,7 %) | +56,48 (59,7 %) | +33,12 (61,1 %) |
| PRE | −5,95 (16,0 %) | −12,18 (12,9 %) | −4,54 (8,4 %) |
| TST / WAI | TST −9,08 (24,5 %) | WAI −6,57 (6,9 %) | TST −4,08 (7,5 %) |
| saz_sin | −6,64 (17,9 %) | −7,73 (8,2 %) | −5,94 (11,0 %) |
| saz_cos | +3,30 (8,9 %) | −11,62 (12,3 %) | −6,49 (12,0 %) |

Maiores interações: CE `WAI_CE×saz_sin` +16,50 e `EV_CE×WAI_CE` −13,04
(reflexo da colinearidade EV×WAI); MA `saz_sin×saz_cos` +5,64; CA
`EV_CA×saz_cos` +5,52.

## 6. Análise ENSO (classificação OFICIAL NOAA/CPC) — NOVO

Fase por mês definida pela regra operacional da NOAA: ONI >= +0,5 (El Niño)
ou <= −0,5 (La Niña) por pelo menos 5 trimestres móveis consecutivos, usando
a tabela completa oni.ascii.txt (cópia em `oni_noaa_cpc.txt`) para as bordas.
O ONI do CSV é idêntico ao da NOAA nos 300 meses. Em relação ao limiar
simples, só **um mês mudou**: outubro/2016 (ONI −0,51, sequência de 1 mês)
passou de La Niña para Neutro. Distribuição: Neutro 149, El Niño 76,
La Niña 72 meses.

Kruskal-Wallis por fase (médias La Niña | Neutro | El Niño):

| Var | MA | CE | CA |
|---|---|---|---|
| PSN | 135,3 \| 136,0 \| 128,6 — p=0,065 ns | 104,2 \| 93,8 \| 92,9 — p=0,094 ns | 94,2 \| 87,0 \| 79,7 — **p=0,010 \*** |
| EV | p=0,006 ** | p=0,0003 *** | p=0,0015 ** |
| PRE | p=0,349 ns | p<0,0001 *** | p=0,0003 *** |
| TST | p<0,0001 *** | p=0,003 ** | p<0,0001 *** |

Pearson ONI × PSN (não depende da fase): MA r=−0,240 (p<0,0001), CE
r=−0,071 (ns), CA r=−0,155 (p=0,007). ONI × TST positivo em MA (0,175 **)
e CA (0,134 *).

OLS ONI → variáveis: R² máximo 3,05 % (TST_MA); EV_MA 2,00 %; todos os
demais abaixo de 2 %. Sustenta a afirmação de que o ONI explica menos de
~3 % da variância das variáveis climáticas.

Regressão simples PSN × variáveis (R² ajustado): EV explica 74,8 % (CE) e
76,2 % (CA) mas só 12,5 % em MA; WAI 81,5 % em CA; TST 59,2 % (CE) e 54,2 %
(CA), 11,2 % em MA. Área queimada (log) negativa nos três biomas.

Observação: na tabela ONI atual da NOAA (período-base atualizado), o evento
frio de 2016-17 não alcança 5 trimestres com ONI <= −0,5 (set −0,42,
out −0,51, nov −0,49), por isso não conta como La Niña aqui. Se a
dissertação citar a lista histórica de episódios da NOAA, vale registrar
essa nuance.

## 7. Observações sobre os scripts enviados

- O `Modelo_PSN.py` enviado ainda **numera** as saídas (`_1`, `_2`…) via
  `proximo_nome`, e está com `TESTAR_GRAUS=False`. O handoff descreve uma
  versão com nomes fixos e `TESTAR_GRAUS=True`. Os resultados não mudam,
  mas a versão no repositório não é a "final" descrita no handoff.
- Corrigido: os dois scripts agora gravam o mesmo
  `Dados_base_nova_2001_2025.xlsx`, com a coluna `Enso` oficial (módulo
  `enso_noaa.py`).
- Comparação de graus (1 a 5) não foi rodada nesta execução.
