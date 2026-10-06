# Sensibilidade da TST diurna (MOD11A2) ao filtro de qualidade QC_Day

Script: `../sensibilidade_qc_tst.py` (`--extrair` baixa os compostos de 8 dias do GEE; `--analisar` gera as tabelas e figuras).
**Período, tabela de ONI e critério ENSO idênticos à rodada oficial** (`enso_oficial/`): 2001-01 a 2025-09
(297 meses), coluna ONI de `Dados_base_nova_2001_2025.xlsx`, fase pelo critério NOAA (≥ 5 trimestres
consecutivos): 76 meses de El Niño, 70 de La Niña, 151 neutros. Mesma máscara, mesma projeção nativa e mesma
agregação mensal (`JANELAS_BENFICA`) da base atual. **A série atual da base não foi alterada.**

Checagem de consistência: a linha "sem filtro" de `tst_qc_enso.csv` reproduz exatamente a linha TST de
`enso_oficial/B_enso_efeito_nas_variaveis.csv` (Mata Atlântica, El Niño: anomalia +0,7072 °C, +2,40 %,
diferença vs. neutro +3,02 %, p < 0,0001, ε² = 0,076).

## As três versões

| versão | critério por pixel | pixels descartados (média, 2001–2025) |
|---|---|---|
| sem filtro | apenas valor válido (7500–65535), como na base atual | 0 % |
| erro ≤ 3 K | bits 0–1 ∈ {0,1} e bits 6–7 ≤ 2 (erro ≤ 3 K) | **0 %** em todos os biomas |
| boa qualidade | bits 0–1 = 0 (pixel de boa qualidade, sem outras flags) | MA 71,7 % · CE 19,7 % · CA 36,3 % |

O filtro "erro ≤ 3 K" não descarta nenhum pixel porque, na Coleção 6.1 do MOD11A2, os pixels
com erro > 3 K ou com nuvem já saem do produto como valor de preenchimento (fill), de modo que o
campo QC_Day só contém erro ≤ 2 K para os pixels válidos (verificado: no composto 2011-10-08 da
Mata Atlântica, 89 % dos pixels têm QC = 65, isto é, "outra qualidade" com erro 1–2 K, 10 % têm QC = 0
e nenhum tem bits 6–7 = 3). Por isso as séries "sem filtro" e "erro ≤ 3 K" são idênticas (diferença
máxima 0,0006 °C) e o ρ de Spearman dessa versão é indefinido (NaN).

## Arquivos

- `tst_qc_series_mensais.csv` — 891 linhas (3 biomas × 297 meses): TST das três versões, pixels, % retido, ONI e fase ENSO.
- `tst_qc_resumo.csv` — resumo por bioma × versão × período (ano todo, trimestre chuvoso, trimestre seco).
- `tst_qc_enso.csv` — anomalias de TST por fase ENSO para as três versões, com as mesmas colunas de `B_enso_efeito_nas_variaveis.csv`.
- `tst_qc_series.png` — as três séries mensais por bioma.
- `tst_qc_pixels_retidos.png` — percentual de pixels retidos por filtro.
- `tst_qc_descartados_vs_tst.png` — dispersão TST (sem filtro) × % descartado pelo filtro "boa qualidade".
- `tst_qc_compostos_8dias.csv` — dado bruto por composto de 8 dias (médias e contagens de pixels), 2000–2025.

## Resultado principal

- O filtro "boa qualidade" **aquece** a série (os pixels descartados são, em média, mais frios: borda de nuvem,
  neblina, orvalho), com efeito maior na Mata Atlântica (+1,36 °C no ano; +2,01 °C no trimestre seco ago–out;
  máximo +4,15 °C em out/2011) e na Caatinga no trimestre seco (+1,23 °C); no Cerrado o efeito é pequeno (+0,23 °C).
- A correlação temporal entre as versões continua alta (r de Pearson 0,97–0,999): o filtro muda o
  nível e a amplitude, não a forma da série.
- Dentro de cada trimestre, o ρ de Spearman entre TST sem filtro e % descartado é negativo (−0,22 a −0,71):
  meses mais quentes/secos perdem menos pixels, meses mais nublados perdem mais.
- **ENSO, Mata Atlântica, El Niño (n = 76 vs. 151 neutros):**

| versão | anomalia média | anomalia (%) | dif. vs. neutro | p Mann-Whitney | ε² | meses acima do P90 |
|---|---|---|---|---|---|---|
| sem filtro | +0,707 °C | +2,40 % | +0,883 °C / +3,02 % | < 0,0001 | 0,076 | 25,0 % (neutro 6,0 %) |
| erro ≤ 3 K | +0,707 °C | +2,40 % | +0,883 °C / +3,02 % | < 0,0001 | 0,076 | 25,0 % |
| boa qualidade | +0,624 °C | +2,02 % | +0,776 °C / +2,54 % | 0,0007 | 0,048 | 22,4 % (neutro 7,3 %) |

  Sinal, significância e ordem de grandeza se mantêm nos três critérios. Cerrado (El Niño não significativo
  nas três versões; La Niña −0,41 → −0,35 °C, p 0,027 → 0,042) e Caatinga (La Niña −0,73 → −0,70 °C,
  p 0,012 → 0,005) também não mudam de sinal nem de significância.

Recomendação: manter a série sem filtro (idêntica à versão "erro ≤ 3 K") na base e citar este teste como
análise de sensibilidade; o filtro estrito descartaria 72 % dos pixels da Mata Atlântica (até 95 % em meses
nublados), com viés quente e menor representatividade espacial.
