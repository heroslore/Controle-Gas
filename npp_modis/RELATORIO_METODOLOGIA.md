# Relatório: atualização da base de dados 2001–2025 por bioma na Bahia via Google Earth Engine

Autor dos dados: Ygor (PPGCTA/UFSB-IFBA). Processamento: script `npp_modis_gee.py`,
08–09/09/2026, projeto GEE `decoded-agency-465400-g8`. Série de referência:
planilha `dados_graficos_Benfica_3.xlsx` (Benfica et al. 2022, *Geogr. Environ.
Sustain.* 15(4); Benfica et al. 2023, *J. South Am. Earth Sci.*).

## 1. O que foi feito

1. **Substituição do fluxo manual** (Earthdata Search → MRT → ArcGIS) por um
   pipeline reprodutível em Python + Earth Engine, com autenticação OAuth
   somente leitura, sem download de HDF.
2. **Limites dos biomas**: IBGE *Biomas e Sistema Costeiro-Marinho* 1:250.000
   (2019) ∩ malha estadual IBGE 2022 (BA), reprojetados para WGS-84 e
   simplificados a 0,0005° (~55 m, desprezível para pixels de 500 m–1 km).
   Áreas: Mata Atlântica 113.214 km², Cerrado 104.630 km², Caatinga 359.718 km².
3. **Engenharia reversa da agregação da planilha**: comparando 720 valores
   (12 meses × 20 anos × 3 biomas) por variável, identificou-se a fonte, a
   escala e a regra temporal exata de cada série (seção 3).
4. **Cálculo 2021–2025** de todas as variáveis com essa mesma regra, mais o NPP
   anual (MOD17A3HGF) e o ONI.
5. **Reprocessamento 2001–2020** de todas as variáveis no GEE, o que permitiu
   (a) validar o pipeline, (b) detectar 7 células atípicas na planilha e
   (c) entregar uma série 2001–2025 homogênea (Coleção 6.1 + IMERG V07).

## 2. Metodologia de cálculo

- **Média espacial** de cada variável por bioma, na projeção nativa do produto
  (sinusoidal MODIS, 463 m ou 927 m; 0,1° no IMERG), sem reamostragem. Um
  pixel entra na média se está dentro do polígono bioma ∩ Bahia e é válido
  (fora dos códigos de preenchimento: água, urbano, gelo, sem dado).
- **Escalas**: MOD17 DN × 0,0001 kg C/m² × 1000 = DN × 0,1 g C/m²
  (mesmo fator 0,1 do fluxo MRT/ArcGIS); MOD16 DN × 0,1 = mm por composição;
  MOD11 DN × 0,02 K − 273,15 = °C; IMERG mm/h × horas do mês; MCD64A1
  n.º de pixels com `BurnDate` > 0 × 25 ha (pixel de 500 m).
- **Agregação temporal dos produtos 8-dias (regra da planilha)**: cada mês é
  formado por 4 composições consecutivas em janelas fixas de dia-do-ano (DOY),
  sem ajuste de ano bissexto:

  | mês | DOY | mês | DOY | mês | DOY |
  |---|---|---|---|---|---|
  | jan | 361 (ano anterior), 1, 9, 17 | mai | 121–145 | set | 249–273 |
  | fev | 25–49 | jun | 153–177 | out | 281–305 |
  | mar | 57–81 | jul | 185–209 | nov | 313–337 |
  | abr | 89–113 | ago | 217–241 | dez | 337–361 |

  PSN, ET e PET são **somadas** nas 4 composições (pixel só entra se válido
  nas 4); a temperatura é a **média** das médias espaciais das composições
  válidas. A composição DOY 337 entra em novembro e em dezembro, como na
  planilha. O script também oferece `--agregacao calendario` (mês civil).
- **IDA (WAI)** = ET mensal ÷ PET mensal (razão das médias por bioma).
- **ONI**: NOAA CPC (ERSSTv5), valor da estação de 3 meses atribuído ao mês
  central.

## 3. Fonte identificada de cada variável e métricas de validação (2001–2020)

Comparação planilha × reprodução independente no GEE, n = 720 pares por
variável (668 na área queimada, excluídos zeros). r = correlação de Pearson;
erro = (GEE − planilha)/planilha.

| Variável da planilha | Fonte / coleção GEE | r | erro mediano | p90 do \|erro\| | Interpretação |
|---|---|---|---|---|---|
| PSN (net photosynthesis) | MOD17A2HGF v6.1, `PsnNet` | 0,995 (1,000 sem o ponto atípico) | −0,0 % | 0,8 % | reprodução exata; resíduo = Coleção 6 → 6.1 |
| Evapotranspiração | MOD16A2GF v6.1, `ET` | 0,993 | −3,4 % | 6,2 % | viés do gap-filling da v6.1 |
| IDA / WAI | ET ÷ PET (MOD16A2GF) | 0,998 | +1,7 % | 4,2 % | confirma a definição |
| Temperatura (TST) | MOD11A2 v6.1, `LST_Day_1km` | 0,978 | −1,2 % (−0,5 °C) | 5,6 % | viés −1,1 °C na Mata Atlântica (máscara de nuvem) |
| Precipitação | GPM IMERG Final mensal **V06** | 0,996 | +1,1 % | 2,6 % | fonte confirmada (citada no artigo de 2022) |
| Precipitação | GPM IMERG Final mensal **V07** | 0,985 | +0,2 % | 37,6 % | versão atual; difere do V06 mês a mês |
| Área queimada | MCD64A1 v6.1 × 25 ha | 0,995 | +0,8 % | 28 % | p90 alto só em valores pequenos (< 1.000 ha) |

Séries por ano/bioma do NPP anual (MOD17A3HGF) 2021–2025, em g C/m²/ano:
Mata Atlântica 1.139–1.289; Cerrado 768–980; Caatinga 734–907.

## 4. Problemas encontrados e como foram resolvidos

| Problema | Resolução |
|---|---|
| A série "NPP" da planilha é, na verdade, PSN mensal | Script calcula PSN (MOD17A2HGF) com a regra da planilha; NPP anual (MOD17A3HGF) sai em arquivo separado |
| Meses da planilha não são meses civis (janelas de DOY) | Regra reproduzida (`--agregacao benfica`, padrão) |
| 7 células atípicas na planilha (desvio > 30 % e materialmente relevante frente à reprodução independente): PSN out/2004 MA; chuva set/2001 Caat., jan/2003 Cerr. e Caat., out/2016 Cerr., abr/2020 MA; temperatura out/2011 MA | Substituídas pelo valor reproduzido na versão "concatenada corrigida"; lista completa em `resultados/correcoes_planilha_2001_2020.csv`. A versão original também é entregue |
| Coluna ONI da aba Plan1 deslocada (valores de 2000 nas linhas de 2001) | ONI refeito a partir da NOAA para 2001–2026 |
| IMERG V06 (fonte da planilha) descontinuado; no GEE só até set/2021 | 2021–2025 em V07 (única opção). **Recomendação: usar a série toda 2001–2025 em V07** (aba "RECOMENDADA"), evitando a emenda V06→V07, cujas diferenças chegam a 40 % em meses isolados |
| IMERG mensal Final ainda não publicado para out–dez/2025 | Deixado em branco. A estimativa pelas meias-horas (Late run) foi testada e ficou 35–85 % abaixo do Final nos meses secos de 2025, por isso não é usada por padrão (`--precip-provisoria` liga só para prévia). Reexecutar `--variavel precip --inicio 2025` quando a NASA publicar (~6 meses de latência) |
| Concorrência no GEE ("Too many concurrent aggregations") | Reduções em lotes de 12 por requisição; rodar uma execução por vez |
| Coleção 6 (planilha) × Coleção 6.1 (GEE) | Diferença medida ≤ 3 % em ET e < 1 % em PSN; para a dissertação, a série homogênea reprocessada é a mais defensável |

## 5. Arquivos entregues (`npp_modis/resultados/`)

| Arquivo | Uso |
|---|---|
| `variaveis_mensais_2001_2025_toda_gee_plan1.csv` | **série recomendada**: 2001–2025 inteira no GEE (v6.1, IMERG V07), layout Plan1 |
| `variaveis_mensais_2001_2025_concatenada_corrigida_plan1.csv` | planilha 2001–2020 com as 7 correções + GEE 2021–2025 |
| `variaveis_mensais_2001_2025_concatenada_plan1.csv` | planilha original + GEE 2021–2025 |
| `variaveis_mensais_2021_2025_plan1.csv` / `_longo.csv` | só os anos novos |
| `npp_anual_2021_2025.csv` | NPP anual |
| `correcoes_planilha_2001_2020.csv` | as 7 células alteradas, valor antigo/novo e motivo |
| `validacao_2001_2020_todas_variaveis.csv` | os 720 pares por variável |
| `variaveis_bahia_biomas_2001_2025.xlsx` | tudo em abas |

Layout Plan1: `ano, mes, ONI, FMA_PSN, Cerrado_PSN, Caatinga_PSN, FMA_Evap, …,
FMA_PET, …, FMA_IDA, …, FMA_Temp, …, FMA_Precip, …, FMA_AreaQueimada, …`
(FMA = Mata Atlântica). Versões `*_excel_ptbr.csv` com `;` e vírgula decimal.

## 6. Texto sugerido para a metodologia da dissertação

> Os dados de fotossíntese líquida (MOD17A2HGF, PsnNet), evapotranspiração
> real e potencial (MOD16A2GF, ET e PET), temperatura da superfície diurna
> (MOD11A2, LST_Day_1km), área queimada (MCD64A1) — todos MODIS Coleção 6.1,
> 500 m/1 km — e precipitação (GPM IMERG Final mensal V07, 0,1°) foram
> obtidos e processados na plataforma Google Earth Engine (Gorelick et al.,
> 2017) por meio da API Python. Para cada bioma (limites IBGE 1:250.000, 2019,
> recortados pelo limite estadual da Bahia) calculou-se a média espacial de
> cada composição na projeção nativa do produto, aplicando-se os fatores de
> escala oficiais e excluindo-se os valores de preenchimento. As composições
> de 8 dias foram agregadas em períodos mensais de quatro composições,
> mantendo-se a mesma janela temporal da série 2001–2020 de Benfica et al.
> (2022, 2023) para garantir continuidade; o índice de disponibilidade de
> água foi definido como a razão ET/PET e o ONI foi obtido do NOAA/CPC. A
> reprodução independente da série 2001–2020 apresentou r ≥ 0,978 para todas
> as variáveis (r = 0,995–1,000 para PSN, IDA e precipitação), com erro
> mediano inferior a 3,5 %.
