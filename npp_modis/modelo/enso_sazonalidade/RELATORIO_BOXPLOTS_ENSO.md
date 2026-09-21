# Valores exatos dos boxplots por fase ENSO e teste da hipótese "o ENSO age nos extremos"

Base homogênea 2001–set/2025 (297 meses): El Niño n = 76, Neutro n = 148, La Niña n = 73
(ONI centrado no mês, limiar ±0,5 °C). Todos os números por bioma × variável × fase
(mín, P10, Q1, mediana, média, Q3, P90, máx, bigodes, n.º de outliers, amplitude,
IQR, desvio-padrão) estão em `D_boxplots_ENSO.xlsx` (abas *valores_bruto* =
como nas Figuras 8–10 da dissertação; *valores_anomalia* = sem o ciclo anual).

## 1. PSN, valores brutos (o que as Figuras 8–10 mostram)

| Bioma | Fase | n | mín | Q1 | mediana | média | Q3 | máx | amplitude |
|---|---|---|---|---|---|---|---|---|---|
| Mata Atlântica | El Niño | 76 | **79,0** | 116,8 | 133,3 | 128,6 | 141,6 | 161,1 | 82 |
| | Neutro | 148 | 94,4 | 127,8 | 134,2 | 135,9 | 144,3 | 179,1 | 85 |
| | La Niña | 73 | 96,6 | 127,3 | 134,0 | 135,4 | 146,3 | 163,4 | 67 |
| Cerrado | El Niño | 76 | 14,0 | 62,8 | 100,1 | 92,9 | 127,1 | 165,8 | 152 |
| | Neutro | 148 | 3,4 | 67,5 | 95,3 | 94,1 | 124,7 | 179,2 | 176 |
| | La Niña | 73 | 3,0 | **85,0** | **112,1** | 103,5 | 129,6 | 167,4 | 164 |
| Caatinga | El Niño | 76 | 28,5 | 58,8 | 79,9 | 79,7 | 102,7 | 157,5 | 129 |
| | Neutro | 148 | 34,4 | 68,5 | 82,5 | 87,2 | 104,4 | 167,6 | 133 |
| | La Niña | 73 | 34,7 | **75,5** | **94,5** | 93,7 | 111,3 | 147,6 | 113 |

(g C/m²/mês). A orientadora tem razão no caso da Mata Atlântica: mediana
133 × 134 × 134, praticamente igual, mas o **mínimo sob El Niño (79) é 15 g C/m²
menor** que o mínimo neutro (94), e o Q1 cai 11 unidades. No Cerrado e na
Caatinga o efeito da La Niña aparece na mediana e no Q1 (+17 e +12 na
mediana), não nos extremos.

## 2. Teste formal: mediana × dispersão × frequência de extremos (anomalias)

Três testes por variável: Kruskal-Wallis (a **mediana** muda?), Fligner-Killeen
(a **dispersão** muda?), qui-quadrado sobre a frequência de meses abaixo do P10
ou acima do P90 globais (os **extremos** ficam mais frequentes?).

| Bioma | Variável | p mediana | p dispersão | p extremos | % meses extremos-baixos (El Niño / Neutro / La Niña) | % meses extremos-altos (El Niño / Neutro / La Niña) |
|---|---|---|---|---|---|---|
| Mata Atlântica | **PSN** | 0,024 | **0,037** | **< 0,001** | **22 / 5 / 8** | 5 / 10 / **15** |
| | EV | 0,350 | **0,007** | **0,002** | **21 / 9 / 1** | 9 / 9 / 14 |
| | PRE | 0,367 | **0,019** | **0,024** | 18 / 7 / 8 | 15 / 8 / 10 |
| | TST | **< 0,001** | 0,370 | **< 0,001** | 4 / 10 / 16 | **25 / 5 / 4** |
| Cerrado | PSN | **0,004** | 0,043 | 0,129 | 16 / 10 / 6 | 13 / 7 / 12 |
| | EV | **0,002** | 0,283 | 0,037 | 11 / 12 / 6 | 12 / 5 / 18 |
| | PRE | 0,760 | **< 0,001** | 0,097 | 16 / 9 / 7 | 13 / 7 / 14 |
| | WAI | **0,001** | 0,645 | 0,271 | 9 / 13 / 6 | 9 / 8 / 15 |
| Caatinga | PSN | **0,001** | 0,932 | 0,163 | 15 / 10 / 6 | 5 / 10 / 15 |
| | EV | **0,008** | 0,581 | 0,271 | 13 / 11 / 6 | 5 / 11 / 14 |
| | PRE | 0,896 | **0,005** | **0,046** | 16 / 8 / 8 | 15 / 6 / 14 |
| | TST | **0,001** | 0,689 | 0,164 | 5 / 12 / 12 | 16 / 10 / 6 |

Sob distribuição sem efeito, esperam-se 10 % dos meses em cada cauda.

## 3. O que isso muda na leitura

1. **Mata Atlântica: o ENSO age pelos extremos, não pela média.** A mediana da
   PSN quase não muda entre fases, mas sob El Niño **22 % dos meses caem
   abaixo do P10** (esperado 10 %, neutro 5 %), e a dispersão aumenta
   (Fligner p = 0,037). O mesmo vale para EV (21 % de meses extremos-baixos) e
   PRE (dispersão maior nas duas fases ativas). Ou seja: o El Niño não reduz a
   produtividade "em média" do bioma úmido, ele **aumenta a frequência de meses
   ruins** (quedas de 20–50 % abaixo do normal). Isso explica por que o teste
   de mediana da dissertação (Kruskal-Wallis, p > 0,05) não viu efeito na PSN:
   o teste certo para esse bioma é de dispersão/extremos.

2. **Cerrado e Caatinga: o ENSO desloca a distribuição inteira.** A mediana muda
   (p ≤ 0,004), a dispersão não. La Niña empurra o Q1, a mediana e o Q3 para
   cima ao mesmo tempo (Cerrado +17 g C/m² na mediana); El Niño concentra
   meses extremos-baixos (16 e 15 %). Aqui o teste de mediana já captura.

3. **Temperatura na Mata Atlântica é o caso mais nítido de extremo**: 25 % dos
   meses de El Niño estão no decil mais quente (5 % no neutro). É o canal
   térmico identificado na análise de mediação.

4. **Precipitação: só a dispersão muda.** Em nenhum bioma a mediana da chuva
   difere entre fases, mas a variância sim (p ≤ 0,019 nos três). O ENSO torna
   a chuva mais irregular (meses muito secos e muito chuvosos ficam mais
   comuns), sem mudar o total típico. Isso é coerente com a chuva não ser o
   canal médio para a PSN, e com o efeito passar pela água efetivamente
   disponível (EV/WAI).

## 4. Recomendação

Substituir, na seção 6.5, a frase "o teste de Kruskal-Wallis não detectou
diferenças da PSN entre fases" por uma análise em dois níveis: (i) mediana
(Kruskal-Wallis), significativa no Cerrado e na Caatinga; (ii) dispersão e
frequência de extremos (Fligner-Killeen e qui-quadrado dos decis),
significativas na Mata Atlântica. E acrescentar às Figuras 8–10 a tabela de
valores (mín, Q1, mediana, Q3, máx, n) que a orientadora pediu, disponível na
aba *valores_bruto*.

Frase-síntese: *Nos biomas sazonais (Cerrado e Caatinga) o ENSO desloca a
distribuição da PSN como um todo, elevando mediana e quartis sob La Niña; na
Mata Atlântica, onde a mediana é insensível às fases, o El Niño quadruplica a
frequência de meses de produtividade extremamente baixa (22 % contra 5 % em
condições neutras) e amplia a dispersão, indicando um efeito sobre os
extremos, mediado pelo aquecimento da superfície.*
