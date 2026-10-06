# Sensibilidade da TST diurna (MOD11A2) ao filtro de qualidade QC_Day

Script: `../sensibilidade_qc_tst.py` (`--extrair` baixa os compostos de 8 dias do GEE; `--analisar` gera as tabelas e figuras).
Período 2001-01 a 2025-12 (300 meses), três biomas da Bahia, mesma máscara, mesma projeção nativa e
mesma agregação mensal (`JANELAS_BENFICA`) da base atual. **A série atual da base não foi alterada.**

## As três versões

| versão | critério por pixel | pixels descartados (média, 2001–2025) |
|---|---|---|
| sem filtro | apenas valor válido (7500–65535), como na base atual | 0 % |
| erro ≤ 3 K | bits 0–1 ∈ {0,1} e bits 6–7 ≤ 2 (erro ≤ 3 K) | **0 %** em todos os biomas |
| boa qualidade | bits 0–1 = 0 (pixel de boa qualidade, sem outras flags) | MA 71,8 % · CE 19,7 % · CA 36,3 % |

O filtro "erro ≤ 3 K" não descarta nenhum pixel porque, na Coleção 6.1 do MOD11A2, os pixels
com erro > 3 K ou com nuvem já saem do produto como valor de preenchimento (fill), de modo que o
campo QC_Day só contém erro ≤ 2 K para os pixels válidos (verificado: no composto 2011-10-08 da
Mata Atlântica, 89 % dos pixels têm QC = 65, isto é, "outra qualidade" com erro 1–2 K, 10 % têm QC = 0
e nenhum tem bits 6–7 = 3). Por isso as séries "sem filtro" e "erro ≤ 3 K" são idênticas (diferença
máxima 0,0006 °C) e o ρ de Spearman dessa versão é indefinido (NaN).

## Arquivos

- `tst_qc_series_mensais.csv` — 900 linhas (3 biomas × 300 meses): TST das três versões, diferenças, % de pixels retidos/descartados, fase ENSO.
- `tst_qc_resumo.csv` — resumo por bioma × versão × período (ano todo, trimestre chuvoso, trimestre seco).
- `tst_qc_enso.csv` — anomalias de TST por fase ENSO (critério NOAA) para as três versões.
- `tst_qc_series.png` — as três séries mensais por bioma.
- `tst_qc_pixels_retidos.png` — percentual de pixels retidos por filtro.
- `tst_qc_descartados_vs_tst.png` — dispersão TST (sem filtro) × % descartado pelo filtro "boa qualidade".
- `tst_qc_compostos_8dias.csv` — dado bruto por composto de 8 dias (médias e contagens de pixels).

## Resultado principal

- O filtro "boa qualidade" **aquece** a série (os pixels descartados são, em média, mais frios: borda de nuvem,
  neblina, orvalho), com efeito maior na Mata Atlântica (+1,36 °C no ano; +2,02 °C no trimestre seco ago–out;
  máximo +4,15 °C em out/2011) e na Caatinga no trimestre seco (+1,23 °C); no Cerrado o efeito é pequeno (+0,23 °C).
- A correlação temporal entre as versões continua alta (r de Pearson 0,97–0,999), ou seja, o filtro muda o
  nível e a amplitude, não a forma da série.
- Dentro de cada trimestre, o ρ de Spearman entre TST sem filtro e % descartado é negativo (−0,23 a −0,69):
  meses mais quentes/secos perdem menos pixels, meses mais nublados perdem mais.
- **ENSO, Mata Atlântica, El Niño:** anomalia média +0,888 °C (p < 0,0001; 25,0 % dos meses acima do P90) nas versões
  "sem filtro" e "erro ≤ 3 K", e +0,776 °C (p = 0,0007; 22,4 % acima do P90) na versão "boa qualidade".
  Sinal, significância e ordem de grandeza se mantêm nos três critérios. Cerrado (El Niño ns) e Caatinga
  (La Niña −0,72 → −0,69 °C, p = 0,012 → 0,005) também não mudam de sinal nem de significância.

Recomendação: manter a série sem filtro (idêntica à versão "erro ≤ 3 K") na base e citar este teste como
análise de sensibilidade; o filtro estrito descartaria 72 % dos pixels da Mata Atlântica (até 95 % em meses
nublados), com viés quente e menor representatividade espacial.
