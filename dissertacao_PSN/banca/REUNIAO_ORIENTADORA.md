# Roteiro para a reunião com a orientadora — estado da dissertação (17/09/2026)

Documento de apoio gerado a partir do repositório (`dissertacao_PSN/`). Todas as
páginas citadas referem-se ao PDF atual, `Trabalho_revisado_2001_2025.pdf`
(68 páginas). As páginas dos pareceres referem-se ao PDF da qualificação que os
avaliadores anotaram.

---

## 1. Resumo em cinco linhas

1. A base foi estendida de 2001–2020 (n = 240) para janeiro/2001–setembro/2025
   (n = 297) e **todo o pipeline foi rodado de novo** com scripts reproduzíveis.
2. O modelo melhorou na Mata Atlântica (R² de teste 62,3 % → 73,7 %) e ficou
   estável no Cerrado (95,7 → 96,7 %) e na Caatinga (94,0 → 94,2 %).
3. Análises novas: Y-randomization com a base nova, VIF completo, seleção do
   grau 1–5, busca exaustiva de conjuntos de variáveis, ablação da
   sazonalidade, fases ENSO pelo critério oficial da NOAA.
4. Os dois pareceres recebidos (Fernando, 30 destaques; Marcos Bernardes, 79
   notas) foram atendidos item a item no Word; o terceiro parecer ainda não
   chegou.
5. Duas decisões de mérito precisam do aval da orientação: o novo conjunto de
   variáveis da Mata Atlântica (EV + TST + WAI) e a ressalva sobre o grau 3.

---

## 2. Os dados: de onde vieram e o que mudou

### 2.1 Base antiga (qualificação)

- Planilha da coorientadora (`Dados_Benfica_.xlsx`), organizada para
  Benfica et al. (2022): 2001 a 2020, 240 meses por bioma.
- Já vinha com a coluna de fase ENSO pronta e a Tabela 1 citava como fonte
  "MOD17A2H / MOD16 / MOD11A2 / MCD64A1 / CHIRPS / Benfica et al. (2022)".
- **Essa planilha não está no repositório.** Se ela puder enviar o arquivo,
  eu comparo mês a mês os 240 meses em comum e digo exatamente onde os valores
  diferem (ver item 2.4).

### 2.2 Base nova (`base_final_2001_2025_plan1_excel_ptbr.csv`)

- 300 linhas (janeiro/2001 a dezembro/2025), separador `;`, decimal vírgula.
  Colunas por bioma: PSN, Evap, PET, IDA (= WAI), Temp, Precip, ÁreaQueimada,
  mais `ano`, `mes` e `ONI`.
- Os três últimos meses de 2025 (out–dez) não têm precipitação e foram
  removidos → **297 meses**. Os scripts fazem isso automaticamente.
- O ONI da planilha é **idêntico** ao da tabela oficial da NOAA nos 300 meses
  (conferido contra `oni_noaa_cpc.txt`).
- A fase ENSO não vinha pronta: foi calculada pelo critério **oficial** da
  NOAA/CPC (ONI ≥ |0,5| por pelo menos 5 trimestres móveis consecutivos), no
  módulo `enso_noaa.py`. Em relação ao limiar simples, só outubro/2016 mudou
  (La Niña → Neutro). Distribuição: 149 Neutro, 76 El Niño, 72 La Niña.
- A PET veio na planilha, mas foi **excluída dos preditores** por correlação
  de 0,73–0,80 com a temperatura (p. 24 da dissertação).
- **O que o repositório não registra:** de qual plataforma (AppEEARS, Google
  Earth Engine, Earthdata) e de qual coleção MODIS a base nova foi extraída, e
  qual produto de precipitação foi usado. O texto da dissertação diz CHIRPS
  (Tabela 1, p. 22), mas o handoff diz que os meses recentes de chuva "ainda
  não foram publicados pela NASA", o que aponta para um produto NASA
  (por exemplo GPM/IMERG). **Pergunta objetiva para a reunião: qual é a fonte
  da precipitação, e as séries MODIS vieram da Coleção 6.1?**

### 2.3 Diferenças entre as duas bases (o que dá para afirmar)

| | Base antiga | Base nova |
|---|---|---|
| Período | jan/2001 – dez/2020 | jan/2001 – set/2025 |
| n por bioma | 240 | 297 |
| Fase ENSO | coluna pronta na planilha | calculada pela regra oficial da NOAA |
| PET | ? | presente na planilha, excluída do modelo |
| Coleção MODIS | provavelmente 6 (v006), vigente até 2022 | necessariamente 6.1 (v061), única distribuída desde ago/2023 |
| Reprodutibilidade | planilha manual | CSV bruto → xlsx gerado pelos scripts, tudo versionado |

### 2.4 A "mudança na publicação da NASA": Coleção 6 → Coleção 6.1

Este é o ponto que explica por que valores de 2001–2020 podem não bater
exatamente entre a planilha antiga e a nova, mesmo sendo o mesmo produto.

- A NASA reprocessou **todo o arquivo MODIS** (desde 2000) na Coleção 6.1
  (Version 061). Os produtos da Coleção 6 (v006) tiveram o processamento
  encerrado no fim de 2022 e a **distribuição desativada em 31/07/2023**.
  Qualquer download feito em 2025 é, portanto, da Coleção 6.1.
- O que mudou na 6.1, segundo a documentação do MOD17A2H v061: recalibração
  do nível 1B (nova abordagem de resposta versus ângulo de varredura para
  Terra e Aqua), correção do *crosstalk* óptico nas bandas infravermelhas do
  Terra, correção da tabela de consulta do Terra para 2012–2017, correção de
  polarização nas bandas solares, e uso de climatologia de LAI/FPAR como
  reserva quando o LAI/FPAR operacional falha. Como GPP/PSN, ET, LST e área
  queimada são todos derivados dessas radiâncias, **as séries inteiras mudam
  um pouco, não só os anos novos**.
- Consequência prática: não é correto "colar" 2021–2025 da coleção nova na
  planilha antiga da coleção 6. A decisão de rodar tudo de novo com a base
  única 2001–2025 é a forma correta de lidar com isso.
- Um segundo fator, independente da coleção: o satélite Terra fez a última
  manobra de correção de órbita em fevereiro de 2020 e vem **derivando** desde
  então (horário de passagem saindo das 10h30 para cerca de 9h em dezembro de
  2025, e altitude reduzida para 694 km). A NASA mantém os produtos como
  "qualidade científica", mas com sombras maiores e cobertura levemente
  reduzida nos anos finais. Vale uma frase de limitação na dissertação.
- A missão Terra MODIS estava programada para gerar produtos até
  **dezembro de 2025**, e a Aqua até agosto de 2026; a série MOD17 não terá
  continuidade além disso. A continuidade oficial é o produto VNP17 (sensor
  VIIRS). Isso justifica setembro/2025 como fim da série e é um bom argumento
  para "perspectivas futuras".

Fontes: [MOD17A2H v061 (NASA Earthdata)](https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod17a2h-061);
[MODIS v6 land data processing ends late 2022](https://www.earthdata.nasa.gov/data/alerts-outages/modis-version-6-land-data-processing-ends-late-2022);
[MODIS v6.0 land products decommissioned July 31 2023](https://www.earthdata.nasa.gov/data/alerts-outages/final-notice-modis-version-6-0-land-data-products-decommissioned-july-31-2023);
[MODIS to VIIRS transition (LAADS DAAC)](https://ladsweb.modaps.eosdis.nasa.gov/learn/modis-to-viirs-transition);
[Terra MODIS acquisition plan through December 2025](https://www.earthdata.nasa.gov/data/alerts-outages/terra-modis-acquisition-plan-through-december-2025);
[Terra/Aqua orbit changes (NSIDC)](https://nsidc.org/data/user-resources/data-announcements/ongoing-changes-terra-and-aqua-orbits-impacting-modis-snow-and-sea-ice-products);
[Endsley et al. 2023, continuidade MOD17/VIIRS](https://agupubs.onlinelibrary.wiley.com/doi/10.1029/2023JG007457).

---

## 3. Resultados: antes e depois

### 3.1 Desempenho (Tabela 2, p. 34)

| Bioma | R² teste antes | R² teste agora | RMSE antes → agora | MAE antes → agora | Dif. treino–teste antes → agora |
|---|---|---|---|---|---|
| Mata Atlântica | 62,3 % | **73,7 %** | 9,90 → 7,97 | 7,10 → 6,29 | 10,20 → 5,19 pp |
| Cerrado | 95,7 % | **96,7 %** | 7,45 → 6,74 | 6,00 → 5,43 | 1,05 → 0,59 pp |
| Caatinga | 94,0 % | **94,2 %** | 6,70 → 6,69 | 5,06 → 5,08 | 1,36 → 1,03 pp |

### 3.2 Validação temporal (Tabela 3, p. 35)

| Bioma | GroupKFold antes → agora | TimeSeriesSplit antes → agora | Queda máxima antes → agora |
|---|---|---|---|
| Mata Atlântica | 61,78 → 73,73 % | 46,69 → 66,98 % | 15,65 → 6,66 pp |
| Cerrado | 95,60 → 96,38 % | 95,07 → 95,73 % | 0,65 → 0,93 pp |
| Caatinga | 93,53 → 93,81 % | 90,09 → 91,20 % | 3,90 → 2,97 pp |

### 3.3 O que é novo em relação à qualificação

| Análise | Resultado | Onde está |
|---|---|---|
| Y-randomization (100 permutações) | Δ = 84, 108 e 107 pp; p = 0,0099 nos três; aprovado | 6.4, p. 43–44, Figura 10 |
| VIF completo | MA ≤ 4,2; CA ≤ 5,0; CE com EV 37,0 e WAI 31,6 (mitigado pelo Ridge) | Tabela 5, p. 45 |
| Seleção do grau 1–5 | grau 2 ótimo nos três; na CA o ganho sobre o linear é de só 1,3 pp | 6.2, p. 36–37, Figura 7 |
| Busca exaustiva C(5,3) = 10 conjuntos por bioma | CE e CA confirmam a qualificação; **MA muda para EV + TST + WAI** | 6.2, p. 38; Tabela A2, p. 63 |
| Ablação da sazonalidade | modelo sem SAZsin/SAZcos e ciclo anual de cada variável | 5.2, p. 23; Tabelas A3 e A4, p. 65 |
| Resíduos | autocorrelação (Ljung-Box) agora nos **três** biomas; MA passou a resíduos normais; CA segue não normal | 6.4, p. 42–43, Figura 9 |
| ENSO com fases oficiais da NOAA | Kruskal-Wallis da PSN **significativo na Caatinga** (p = 0,010); CE com EV, PRE e TST diferindo entre fases; ONI explica no máximo 3 % da variância climática | 6.5, p. 45–47, Figuras 11–13 |
| Regressões simples PSN × variáveis | EV explica 75 % (CE) e 76 % (CA), mas só 12,5 % na MA | Figura 5, p. 33 |

### 3.4 Duas decisões para a orientação

1. **Conjunto da Mata Atlântica.** A busca exaustiva mostrou EV + TST + WAI
   com R² de teste 73,7 % contra 71,0 % do conjunto anterior (EV + PRE + TST),
   com a mesma diferença treino–teste. Como a metodologia declara que a seleção
   segue esse critério, o documento já usa o conjunto novo. Reverter é trocar
   uma linha em `Modelo_PSN.py` e rodar de novo (registrado em
   `REGISTRO_DE_MUDANCAS.md`, seção 1).
2. **Grau 3 na Mata Atlântica.** Com o conjunto novo, o grau 3 tem R² de teste
   0,8 pp maior que o grau 2 (74,4 contra 73,6 %), mas diferença treino–teste
   1,7 pp maior. O texto mantém o grau 2 pelo critério composto e registra a
   ressalva (6.2, p. 36; Considerações Finais, p. 50). A H1 não foi reescrita.

---

## 4. Pareceres da banca: o que cada um pediu e o que foi feito

Legenda: **Feito** = aplicado no Word; **Feito (confirmar)** = aplicado, mas
depende de dado ou fonte que só você/orientação pode validar; **Pendente** =
não aplicado.

### 4.1 Parecer de Fernando (FIOCRUZ-RO) — 30 destaques

| Cód. | Página do parecer | O que pediu | O que foi feito | Onde está agora |
|---|---|---|---|---|
| F1 | 8 | Explicar o que é PSN, com gráfico | Parágrafo GPP → PSN → NPP e **Figura 1** nova (diagrama conceitual) | 2, p. 11–12 |
| F2 | 9 | O que é "forçamento" | "forçante" definida na primeira ocorrência | 2, p. 11 |
| F3, F6 | 10 | Explicar MODIS / produto / agência | Parágrafo sobre MODIS, Terra/Aqua, NASA e os produtos MOD17A2H, MOD16A2, MOD11A2, MCD64A1 | 2, p. 11 |
| F4, F5 | 10 | Frase confusa; propôs equação | Equações explícitas PSN = GPP − Rm(folhas, raízes finas) e NPP = PSN − Rm(lenho) − Rg | 2, p. 11 |
| F7 | 10 | Evidência de controle hídrico no Cerrado | Frase com R² das regressões simples (EV 75 %, WAI 74 % no CE; 13 % na MA) e nova **Figura 5** | 2, p. 12; Figura 5, p. 33 |
| F8 | 12 | Pasto transpira menos que árvores? | Mecanismo (raízes rasas × acesso à água profunda) acrescentado | 2, p. 14 |
| F9 | 13 | O que é QSAR | Definição na primeira menção | 2, p. 15 |
| F10 | 16 | Área de estudo para a introdução | **Não seguido**: mantida em 5.1 e ampliada (decisão sua, atende Marcos) | 5.1, p. 18–20 |
| F11 | 17 | "Bases climáticas regionais": quais? | Fontes exatas de cada variável | 5.2, p. 21–22; Tabela 1, p. 22 |
| F12 | 18 | Acesso aos dados é público? | Frase sobre acesso público e coluna "Fonte / acesso" na Tabela 1; repositório citado | 5.2, p. 21–22 |
| F13 | 19 | sin + cos passaria de 1 | Explicado que entram como dois preditores separados | 5.2, p. 23 |
| F14 | 19 | Sazonalidade artificial? | Explicado que a amplitude é estimada (tende a zero sem ciclo) + teste de ablação (Tabelas A3/A4) | 5.2, p. 23; p. 65 |
| F15 | 19 | Explicar winsorização / percentil 3 | Parágrafo reescrito em linguagem simples | 5.2, p. 24 |
| F16, F20 | 20–21 | Guimarães também escolheu o grau empiricamente (até 8) | Adaptação (ii) reescrita; "grau 4 fixado" removido | 5.3, p. 25 |
| F17 | 20 | Faltou a equação do grau > 1 | Equação do grau 2 com 20 termos e contagem por grau (20/55/125/251) | 5.3, p. 25 |
| F18 | 21 | Pré-processamento por correlação | Triagem por correlação e exclusão da ETP explicadas | 5.2, p. 24 |
| F19, F21, F28 | 21, 26 | % treino/teste, quem é teste | 80/20 (≈238/59 meses), cada mês testado 30 vezes; grupos de anos e blocos cronológicos | 5.5, p. 29 |
| F22 | 22 | Referência testou > 400 variáveis em trios | Texto corrigido | 5.4, p. 27 |
| F23 | 22 | Generalização = R² de teste | Frase corrigida | 5.4, p. 27 |
| F24 | 22 | Sazonalidade fixa; combinar só as outras | Sazonalidade fixa e C(5,3) = 10 combinações (era "C(7,5) = 21") | 5.4, p. 27; 6.2, p. 38 |
| F25 | 23 | Esquema gráfico da validação | **Figura 4** nova (RepeatedKFold, GroupKFold, TimeSeriesSplit) | 5.5, p. 30 |
| F26, F29 | 24, 26 | Onde estão os dados? Mostrar tabela | **Apêndice A** com os 297 meses (Tabela A1) | p. 53–62 |
| F27 | 25 | Critério de Y-randomization descrito errado | Texto não atribui mais os 60 pp ao artigo; **confirmar** no artigo o critério exato | 5.5, p. 31 |
| F30 | 29 | Grau 2 não é ótimo na Caatinga | Graus 1–5 rodados com a base nova; texto registra ganho marginal na CA (1,3 pp) e ressalva da MA; Figura 7 refeita | 6.2, p. 36–37; p. 50 |

### 4.2 Parecer de Marcos Bernardes — 79 notas

| Cód. | Página do parecer | O que pediu | O que foi feito | Onde está agora |
|---|---|---|---|---|
| MB-1, 4, 5, 6, 7, 8, 9, 28, 48–50, 57, 65, 79 | 1–2 | Resumo: abertura, contribuição, linguagem simples, todas as métricas com média e dp, escalas, tipologia, implicações | Resumo e Abstract reescritos (redação sua) + frase com R² ± dp, RMSE, MAE, escalas e VIF | p. 3–4 |
| MB-6 | 1 | "gap de overfitting" | Trocado por "diferença treino–teste" em todo o texto | todo o documento |
| MB-10 a 13, 37 | várias | Itálico em termos estrangeiros | Aplicado no texto e na lista de siglas | p. 5 e texto |
| MB-14 | 3 | Tirar as linhas da Lista de Figuras | Listas sem bordas, com páginas | p. 6 |
| MB-15, 63, 77, 78 | 16, 32, 41 | Ampliar Área de Estudo (hidrografia, Corredor Central, restauração, uso do solo) | Seção ampliada; trechos da Discussão movidos para cá | 5.1, p. 18–20 |
| MB-16 | 8 | "Região" → "Estado da Bahia" | Feito | 1, p. 9 |
| MB-17 | 8 | Traduzir "estratégias subótimas" | "decisões de gestão menos eficazes" | 1, p. 9 |
| MB-18 | 9 | Autores que usaram regressão polinomial | Citações acrescentadas | 2, p. 10–11 |
| MB-19, 26, 38 | 10, 13, 17 | Explicar MODIS/NASA | Mesmo parágrafo de F3 | 2, p. 11 |
| MB-20, 21, 22 | 10 | Detalhes do MOD17A2H fora da fundamentação | Movidos para Dados, ampliados (8 dias, 500 m, agregação) | 5.2, p. 21 |
| MB-24 | 12 | Dados do MapBiomas por bioma na Bahia | **Pendente (confirmar)**: parágrafo qualitativo; faltam os números estaduais | 5.1, p. 19 |
| MB-25 | 13 | Definir ONI | Definido (anomalia trimestral na região Niño 3.4) | 2, p. 15 |
| MB-27 | 13 | "Traduzir" o parágrafo do Ridge | Parágrafo em linguagem simples | 2, p. 16 |
| MB-29 | 15 | "produtividade" → "primária, medida pela PSN" | Feito | 3, p. 17 |
| MB-30 | 15 | O que é grau "ótimo" | Definido em H1 (maior R² de teste com diferença < 10 pp) | 3.2, p. 17 |
| MB-31 | 15 | Quantificar "parcela significativa" | H2 = pelo menos 60 % da variância | 3.2, p. 17 |
| MB-32 | 15 | Hipóteses verificadas no fim? | Parágrafo "Retomando as hipóteses" (H1 com ressalva, H2, H3) | 7, p. 50 |
| MB-33 | 15 | Mais de um objetivo geral | Objetivo geral único | 4.1, p. 17 |
| MB-34 | 15 | Método misturado nos objetivos específicos | Quatro objetivos sem nomes de técnica | 4.2, p. 18 |
| MB-35 | 16 | Fonte dos dados climáticos | Alvares et al. (2013) para Köppen; **valores de chuva ainda sem fonte** | 5.1, p. 18 |
| MB-36 / MB-2 | 16, 1 | "resposta pulsada", "heterogeneidade estrutural" | Definidas na primeira ocorrência | p. 19 e p. 34 |
| MB-39 | várias | Marcações de revisão | Aceitas | todo o documento |
| MB-40 | 18 | Linha solta na Tabela 1 | Tabela 1 refeita (larguras fixas, unidades sem quebra) | p. 22 |
| MB-41 | 19 | ONI trimestral × dados mensais | Explicado: trimestre atribuído ao mês central | 5.2, p. 23 |
| MB-42 | 19 | Área queimada "já é resultado" | Reescrito como justificativa da transformação log(1 + x) | 5.2, p. 24 |
| MB-43, 44 | 19 | Winsorização / percentil 3 | Mesmo parágrafo de F15 | 5.2, p. 24 |
| MB-45 | 23 | Esquema gráfico | Figura 4 | p. 30 |
| MB-47 | 23 | Nomear as três métricas | R², RMSE e MAE nomeados | 5.4, p. 27–28 |
| MB-51 | 24 | "Reconhece-se, contudo" | Feito | 5.5, p. 30 |
| MB-52 | 24 | Traduzir "artefato de vazamento por autocorrelação" | Frase em linguagem simples | 5.5, p. 30 |
| MB-53 | 24 | Por que n = 240? | n = 297, período e motivo dos 3 meses excluídos | 5.2, p. 23 |
| MB-54 | 25 | Por que random_state = 42? | Explicado (semente arbitrária, reprodutibilidade) | 5.6, p. 32 |
| MB-55 | 26 | Antecipar o fluxo metodológico | Figura 3 (fluxo, refeita) logo após o mapa | p. 21 |
| MB-56 | 27 | Como foi estimada a PSN "observada"? | "PSN de referência (MODIS MOD17A2H)" | 6.1, p. 34 |
| MB-58 | 28 | Onde está PSN × preditoras? | Figura 5 (15 painéis de regressão simples) | 6.1, p. 33 |
| MB-59 | 28 | Linha faltante na Tabela 3 | Tabela refeita | p. 35 |
| MB-60 | 31 | Trabalhos que corroboram (Cerrado) | Bucci et al., Arruda et al. repetidos após a afirmação | 6.3, p. 39 |
| MB-61 | 32 | Definição do WAI na metodologia | Movida para 5.2 e Tabela 1 | p. 22–23 |
| MB-66 | 34 | "biomas climaticamente limitados" | Definido | 6.3, p. 41 |
| MB-67 | 34 | "diretamente proporcional" | Corrigido | 6.3 |
| MB-69 | 35 | Citar a figura de resíduos no texto | Figura 9 citada | 6.4, p. 42 |
| MB-70 | 35 | Ljung-Box não está na metodologia | Shapiro-Wilk, Ljung-Box(12) e ACF descritos em 5.5 | p. 30 |
| MB-71 | 35 | "memória temporal" | Definida | 6.4, p. 42 |
| MB-72 | 36 | Legenda na figura | Todas as figuras com legenda acima e na mesma página | todo o documento |
| MB-73 | 36 | Y-randomization ininteligível | Parágrafo reescrito em linguagem simples, números novos | 6.4, p. 43; Figura 10, p. 44 |
| MB-3, 74 | 2, 38 | ENSO: fases? defasagem? intensidade? | Metodologia diz: fases oficiais NOAA, sem defasagem, intensidade via ONI contínuo (Pearson e OLS) | 5.4, p. 28; 6.5, p. 45–47 |
| MB-75 | 39 | Mais etnias que Pataxó | Lista de etnias acrescentada; **confirmar com FUNAI/IBGE** | 5.1, p. 19 |
| MB-76 | 40 | Eucalipto/fragmentação: especulação? | Reescrito como hipótese a testar com variáveis de uso do solo | 6.6, p. 48 |
| MB-23, 46, 62, 64, 68 | — | Elogios / "desconsiderar" | Sem ação | — |

### 4.3 Mudanças exigidas pela série nova (independentes da banca)

| Item | Onde |
|---|---|
| Todos os R², RMSE, MAE, intervalos e diferenças treino–teste | Resumo p. 3; Tabelas 2 e 3, p. 34–35; 6.1; 7 |
| n = 240 → 297; "2001 a 2020" → "2001 a 2025" (as quatro comparações com a série antiga mantêm "2001 a 2020") | p. 12, 23, 29, 30, 33 |
| Ljung-Box: "apenas na Caatinga" → "nos três biomas"; MA com resíduos normais | 6.4, p. 42–43 |
| VIF do Cerrado 25,8/24,0 → 37,0/31,6 e Tabela 5 nova | p. 45 |
| Y-randomization Δ 74/109/111 → 84/108/107 pp | 6.4, p. 43–44 |
| Kruskal-Wallis da PSN significativo na Caatinga; Cerrado com EV/PRE/TST diferindo entre fases | 6.5, p. 45–46 |
| "ONI explica < 2 %" → "< 3 %" | 6.5, p. 47; 7, p. 50 |
| Tabela 4 (tipologia) com os R² novos e controlador da MA | p. 41 |
| Considerações Finais: limitação (o modelo não prevê o futuro sozinho; autocorrelação residual) e perspectivas (defasagem do ENSO, termos autorregressivos) | 7, p. 49–52 |

---

## 5. O que ainda depende de você ou da orientação

1. Fonte da precipitação (CHIRPS ou produto NASA?) e coleção MODIS da base nova.
2. Como a PSN foi agregada (compostos de 8 dias → mês: soma ou média? pixels →
   bioma: média? qual máscara?). O texto hoje diz "seguindo Benfica et al.
   (2022)".
3. Enviar a planilha antiga (`Dados_Benfica_.xlsx`) para comparação mês a mês.
4. Referências para os valores de chuva da área de estudo (MB-35).
5. Números do MapBiomas por bioma dentro da Bahia (MB-24).
6. Critério exato de Y-randomization em Guimarães et al. (2024) (F27).
7. Lista de etnias indígenas (MB-75).
8. Aval para o conjunto EV + TST + WAI na Mata Atlântica e para a ressalva do
   grau 3.
9. Parecer do terceiro avaliador.
10. Ao abrir o .docx no Word, aceitar a atualização de campos para o Sumário
    recalcular as páginas.

---

## 6. Onde está cada coisa no repositório

| Arquivo | Conteúdo |
|---|---|
| `resultados_2001_2025/RESULTADOS.md` | Todos os números da rodada nova, seções 1–9 |
| `banca/analise_pareceres.md` | Cada comentário da banca, opinião e texto proposto |
| `banca/REGISTRO_DE_MUDANCAS.md` | Registro do que foi aplicado no Word e pendências |
| `banca/aplicar_revisao_docx.py` | Script que gera o Word revisado a partir do original e dos resultados |
| `banca/Trabalho_revisado_2001_2025.docx / .pdf` | Documento atual |
| `banca/Trabalho_revisado.docx` | Sua versão original, intocada |
