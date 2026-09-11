# Dissertação × base nova: o que muda em cada resultado

Fonte: `Trabalho_Final.pdf` (versão de qualificação, 2001–2020) confrontado com
o MRMP-N rodado (mesma especificação: grau 2, Ridge, alpha por GridSearchCV,
winsorização 3 % só no treino, RepeatedKFold 5×30) em três conjuntos:

- **original**: planilha antiga, 2001–2020 (n = 240) — replica a dissertação;
- **nova 2020**: base reprocessada no GEE, 2001–2020 (n = 240);
- **nova 2025**: base reprocessada no GEE, 2001–2025 (n = 297; out–dez/2025 sem chuva).

A replicação da planilha antiga reproduz a dissertação com desvio ≤ 0,3 ponto
em todas as métricas (ex.: R² MA 62,3 % → 62,4 %; TimeSeriesSplit MA 46,7 % →
47,0 %), o que valida a comparação. Arquivos: `comparacao/*.csv`.

## Tabela 2 — desempenho preditivo (RepeatedKFold)

| Bioma | Métrica | Dissertação | nova 2020 | nova 2025 | O que muda no texto |
|---|---|---|---|---|---|
| Mata Atlântica | R² teste | 62,3 % | **72,9 %** | **70,9 %** | "desempenho moderado" continua válido, mas sobe ~10 pontos |
| | IC 95 % | 35,0–81,3 | 58,5–84,7 | 56,6–80,2 | limite inferior sobe 22 pontos: modelo muito mais estável |
| | RMSE / MAE | 9,90 / 7,10 | 8,03 / 6,24 | 8,38 / 6,58 | |
| | Gap (pp) | 10,20 | **5,59** | **5,05** | sai de "próximo ao patamar de 10 pp" para "reduzido" |
| Cerrado | R² teste | 95,7 % | 96,3 % | 96,7 % | mantém |
| | IC 95 % | 93,0–97,6 | 94,5–97,7 | 95,4–97,7 | |
| | RMSE / MAE | 7,45 / 6,00 | 6,89 / 5,59 | 6,74 / 5,43 | |
| | Gap (pp) | 1,05 | 0,77 | 0,59 | |
| Caatinga | R² teste | 94,0 % | 94,2 % | 94,2 % | mantém |
| | IC 95 % | 90,0–96,5 | 89,9–97,0 | 90,8–96,3 | |
| | RMSE / MAE | 6,70 / 5,06 | 6,58 / 5,01 | 6,69 / 5,08 | |
| | Gap (pp) | 1,36 | 1,31 | 1,03 | |

## Tabela 3 — validação temporal (R² teste)

| Bioma | Esquema | Dissertação | nova 2020 | nova 2025 |
|---|---|---|---|---|
| Mata Atlântica | GroupKFold (ano) | 61,8 % | 72,8 % | 70,6 % |
| | TimeSeriesSplit | 46,7 % | 59,5 % | **63,9 %** |
| | Queda máxima | 15,7 pp | 13,4 pp | **7,0 pp** |
| Cerrado | GroupKFold / TimeSeriesSplit | 95,6 / 95,1 % | 96,0 / 95,7 % | 96,4 / 95,7 % |
| Caatinga | GroupKFold / TimeSeriesSplit | 93,5 / 90,1 % | 93,3 / 91,9 % | 93,8 / 91,3 % |

O parágrafo sobre a Mata Atlântica ("menor capacidade de extrapolação para
períodos futuros") enfraquece: com 2001–2025 a queda no TimeSeriesSplit cai de
15,7 para 7,0 pp e o R² temporal sobe para 64 %.

## Figura 4 — seleção do grau

Grau 2 continua ótimo nos três biomas e em todos os conjuntos. Na base nova o
argumento fica mais forte: com 2001–2025, graus 4 e 5 colapsam na Mata
Atlântica (R² 28 % e negativo) e na Caatinga (64 % e 48 %), enquanto o grau 2
mantém 71 % e 94 %. Ganho do grau 2 sobre o linear: MA +5 a +6 pp (era +11),
CE +6,6 pp (era +7,2), CA +0,4 a +1,3 pp (era +0,7).

## Seção 6.4 — diagnóstico dos resíduos

| Diagnóstico | Dissertação | nova 2020 | nova 2025 | Implicação |
|---|---|---|---|---|
| Shapiro-Wilk MA | W 0,858, p < 0,001 (não normal, "evento extremo de PSN muito baixa") | W 0,99, p = 0,25 (normal) | W 1,00, p = 0,62 (normal) | **o "evento extremo" era o valor errado de out/2004 na planilha (51,3 vs 142,6)**; o parágrafo deve ser reescrito |
| Shapiro-Wilk CE | p = 0,427 (normal) | p = 0,11 | p = 0,26 | mantém |
| Shapiro-Wilk CA | p = 0,001 (não normal) | p < 0,001 | p < 0,001 | mantém (cauda esquerda) |
| Ljung-Box (autocorrelação) | só CA (p < 0,001; lag-1 = 0,35) | CA (0,38) **e MA (p < 0,001; lag-1 = 0,30)** | CA (0,42), MA (0,30), CE limiar (p = 0,01, lag-1 = 0,20) | a memória temporal aparece também na MA; comentar |
| Cauda esquerda < −2 dp | MA 3,3 %, CA 2,9 % | MA 3,8 %, CA 2,5 % | MA 3,0 %, CA 3,0 % | mantém |
| VIF Cerrado (EV, WAI) | 25,8 / 24,0 | ~36 | ~37 | mantém, um pouco maior |

## Figura 7 — Y-randomization (fora da amostra, 100 permutações)

Aprovado em todos os casos. Δ = R² real − R² permutado médio: MA 67 → 77 / 75 pp;
CE 100 → 100 / 99 pp; CA 99 → 99 / 98 pp; R² permutado negativo (−3 a −5 %);
p empírico 0,01. (Os Δ da dissertação, 109/111/74 pp, usam outra forma de
cálculo do R² permutado; a conclusão é a mesma.)

## Seção 6.5 — ENSO (Kruskal-Wallis por fase; p < 0,05 = significativo)

| Bioma | Variável | Dissertação | nova 2020 | nova 2025 | Mudança |
|---|---|---|---|---|---|
| todos | **PSN** | não significativa | não (0,15 / 0,36 / 0,07) | não (0,07 / 0,14 / 0,02 na CA) | **conclusão central mantém**: efeito indireto. Na CA com 2001–2025 fica no limiar (p = 0,015) — mencionar |
| MA | TST | sim | sim | sim | mantém |
| MA | PRE, EV | não | PRE não; **EV sim (0,03)** | PRE não; EV sim (0,005) | EV passa a responder ao ENSO |
| CE | PRE | sim | sim | sim | mantém |
| CE | EV | "apenas tendência (p = 0,071)" | **sim (0,003)** | sim (< 0,001) | texto precisa mudar |
| CE | WAI | não | **sim (0,013)** | sim (0,001) | idem |
| CA | TST, PRE | sim | sim | sim | mantém |
| CA | EV | não | sim (0,015) | sim (0,002) | |
| Regressão linear ONI → variável | "< 2 % da variância" | até 5 % (PSN MA 5,2 %; TST MA 2,9 %) | até 6 % | trocar "< 2 %" por "< 6 %"; conclusão (efeito não linear/indireto) mantém |

## Metodologia (5.2, Tabela 1) — correções factuais necessárias

- PRE: a fonte não é CHIRPS; a planilha usou **GPM IMERG Final mensal V06** (Benfica et al. 2022) e a base nova usa **V07** (validação: V06 r = 0,996 com a planilha; CHIRPS r = 0,967).
- EV: MOD16A2GF, Coleção 6.1; PSN: MOD17A2HGF, Coleção 6.1; TST: MOD11A2 (LST diurna); BURN: MCD64A1 em **hectares** (pixels × 25 ha), não m².
- WAI = ET/PET (MOD16), definição que a Tabela 1 não explicita.
- Período 2001–2025 (n = 297 até a publicação da chuva de out–dez/2025), processamento em Google Earth Engine, limites IBGE 2019; agregação mensal por janelas fixas de 4 composições de 8 dias (ver `RELATORIO_METODOLOGIA.md`).
- Resumo/abstract e conclusões: atualizar R² (MA 70,9 %, CE 96,7 %, CA 94,2 %), gap da MA (5 pp) e período.

## Síntese

Nenhuma conclusão da dissertação é contrariada pela base nova. Três se
fortalecem (desempenho e estabilidade temporal da Mata Atlântica, escolha do
grau 2, ausência de efeito direto do ENSO sobre a PSN) e três parágrafos
precisam ser reescritos por terem se apoiado em artefatos da planilha antiga:
a não normalidade dos resíduos da Mata Atlântica (erro de digitação de
out/2004), a "tendência" da evapotranspiração no Cerrado sob ENSO (agora
significativa) e a fonte da precipitação (IMERG, não CHIRPS).
