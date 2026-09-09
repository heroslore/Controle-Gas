# Variáveis MODIS/GPM por bioma na Bahia (série de Benfica et al.) — Google Earth Engine

Script `npp_modis_gee.py`: automatiza em Python, via Google Earth Engine (GEE), o
fluxo manual (Earthdata → MRT → ArcGIS) usado em Benfica et al. (2022, *Geography,
Environment, Sustainability*) e Benfica et al. (2023, *J. South American Earth
Sciences*) para obter, por bioma (Mata Atlântica, Cerrado, Caatinga) no estado da
Bahia, **todas as variáveis mensais da planilha histórica 2001–2020** e o NPP anual:

| `--variavel` | Coleção GEE (v6.1 / atual) | Banda | Agregação mensal | Coluna | Validação 2001–2020 vs planilha |
|---|---|---|---|---|---|
| `psn` | `MODIS/061/MOD17A2HGF` | `PsnNet` ×0,1 | soma de 4 composições (janelas Benfica) | `psn_g_c_m2` | r = 1,000 (Caat., Cerr.), 0,936 (MA, 1 ponto atípico); erro mediano 0,2 % |
| `et` | `MODIS/061/MOD16A2GF` | `ET` ×0,1 | soma (janelas Benfica) | `et_mm` | r = 0,993; viés −3 % (v6.1 gap-filled) |
| `pet` | `MODIS/061/MOD16A2GF` | `PET` ×0,1 | soma (janelas Benfica) | `pet_mm` | (usada em `ida`) |
| `ida` | = `et` / `pet` | | razão das somas mensais | `ida` | r = 0,998; erro mediano +1,7 % — confirma IDA/WAI = ET/PET |
| `lst` | `MODIS/061/MOD11A2` | `LST_Day_1km` ×0,02 − 273,15 | média das composições (janelas Benfica) | `lst_dia_c` | r = 0,978; viés −0,5 °C (−1,1 °C na MA) |
| `precip` | `NASA/GPM_L3/IMERG_MONTHLY_V07` | `precipitation` (mm/h × horas) | produto mensal | `precip_mm` | planilha = IMERG **V06** (r = 0,994, p90 2,6 %); ver nota abaixo |
| `queimada` | `MODIS/061/MCD64A1` | `BurnDate` > 0 | n.º de pixels × 25 ha | `area_queimada_ha` | r = 0,9997; erro mediano +1 % |
| `oni` | NOAA CPC `oni.ascii.txt` | anomalia | mês central da estação de 3 meses | `oni` | |
| `npp` | `MODIS/061/MOD17A3HGF` | `Npp` ×0,1 | valor anual | `npp_g_c_m2` (CSV separado) | |

`--variavel todas` calcula todas as mensais + ONI. O CSV de saída tem uma
linha por ano × mês × bioma e uma coluna por variável (`--formato longo`), ou
o layout da aba *Plan1* da planilha: `ano, mes, oni, <bioma>_<variável>...`
(`--formato largo`).

**Nota sobre a precipitação.** A planilha usou GPM IMERG Final mensal **V06**
(citado em Benfica et al. 2022). O V06 foi descontinuado e no GEE só vai até
2021; o V07 (atual) reprocessou toda a série e difere do V06 em até ~50 % em
alguns meses aqui (r = 0,976 contra a planilha). Por isso o script usa V07 e
o recomendado é **reprocessar a chuva de 2001–2025 inteira em V07**
(`--variavel precip --inicio 2001`) em vez de emendar V06 + V07. Os resultados
em `resultados/` trazem as duas versões.

## Sobre a PSN: a série histórica é MENSAL (PsnNet), não NPP anual

A planilha `dados_graficos_Benfica_3.xlsx` tem 12 blocos ("Jan - net
photosynthesis", "Fev - PSN", ..., "Dez - PSN"), 2001–2020, com valores de
~40 a 180 g C/m² **por mês**. Isso é a **fotossíntese líquida (PsnNet) 8-dias
do MOD17A2H somada por mês**, não o NPP anual do MOD17A3 (que daria ~1.000 a
1.600 g C/m² **por ano**; a soma dos 12 meses da sua planilha dá ≈1.594, 1.161
e 1.047 g C/m²/ano para Mata Atlântica, Cerrado e Caatinga, coerente com isso).

Por isso a PSN mensal (`--variavel psn`) é a variável que continua a planilha; o NPP anual (`--variavel npp`) sai em CSV separado. Nos dois casos o fator de escala já é aplicado: DN × 0,0001 kg C/m² × 1000 = DN × 0,1 g C/m².

### Como a planilha agregou as composições 8-dias (regra reproduzida)

Comparando a saída do GEE com os 720 valores 2001–2020 da planilha, a regra
usada na série histórica ficou clara: cada mês é a **soma de 4 composições
8-dias consecutivas em janelas fixas de dia-do-ano (DOY)**, sem ajuste de ano
bissexto, e não os meses do calendário:

| Mês | DOY das composições | Mês | DOY das composições |
|---|---|---|---|
| jan | **361 do ano anterior**, 1, 9, 17 | jul | 185, 193, 201, 209 |
| fev | 25, 33, 41, 49 | ago | 217, 225, 233, 241 |
| mar | 57, 65, 73, 81 | set | 249, 257, 265, 273 |
| abr | 89, 97, 105, 113 | out | 281, 289, 297, 305 |
| mai | 121, 129, 137, 145 | nov | 313, 321, 329, 337 |
| jun | 153, 161, 169, 177 | dez | **337**, 345, 353, 361 |

Ou seja, "janeiro" cobre 27/dez a 24/jan, "abril" cobre 30/mar a 30/abr, e a
composição DOY 337 (3/dez) entra em novembro **e** em dezembro. É o que se
obtém agrupando os 46 arquivos do ano de 4 em 4 a partir do último arquivo do
ano anterior. `--agregacao benfica` (padrão) reproduz exatamente isso para PSN, ET, PET e
LST (erro mediano < 0,3 % na PSN; o resíduo é Coleção 6 × 6.1). `--agregacao
calendario` soma as composições iniciadas dentro do mês civil, mais defensável
para uma série nova, mas **não** comparável à planilha em jan, abr, mai, out e nov.

## Instalação

Requer Python 3.9+.

```bash
cd npp_modis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuração do projeto GEE (fazer uma vez)

Desde 2024 o Earth Engine exige um projeto Google Cloud, mesmo para uso
acadêmico (gratuito, "noncommercial").

1. Entre com sua conta Google em <https://code.earthengine.google.com/register>.
2. Escolha **Unpaid usage → Academia & Research**, e crie um projeto novo
   (ou selecione um existente). Anote o **ID do projeto** (ex.: `ee-ygornayty`).
   O registro já habilita a API Earth Engine nesse projeto.
3. Se preferir criar o projeto direto no console
   (<https://console.cloud.google.com>): crie o projeto, habilite a API
   **Earth Engine** em *APIs e serviços* e registre-o no link do passo 1.

Nada mais é necessário: o catálogo MODIS é público e o script só faz leitura.
Você pode passar o ID com `--project` ou exportar `EE_PROJECT=<id>`.

## Autenticação (primeira vez)

Opção A — pelo script (abre o navegador ou imprime um link):

```bash
python npp_modis_gee.py --project SEU-PROJETO --apenas-verificar
```

Opção B — pela CLI do earthengine-api:

```bash
earthengine authenticate                      # abre navegador
earthengine authenticate --auth_mode=notebook # servidor/terminal sem navegador
```

As credenciais ficam em `~/.config/earthengine/credentials` e valem para as
próximas execuções. Use `--autenticar` para refazer, ou `--auth-mode notebook`
se o modo automático reclamar de `gcloud`. Para rodar sem interação (cluster),
use conta de serviço: `--service-account EMAIL --chave-json chave.json`
(a conta de serviço também precisa ser registrada no link acima).

## Uso

### 1) Conferir o último ano disponível (ex.: se o dado de 2025 já saiu)

```bash
python npp_modis_gee.py --project SEU-PROJETO --apenas-verificar --variavel todas npp
```

Imprime, por coleção, a última imagem e o último ano completo (46 composições
nos produtos 8-dias, 12 meses nos mensais). Os produtos `*GF` (gap-filled) de
um ano só saem após o fim do ano; o ano corrente está nos produtos sem
gap-fill (`--variavel psn --colecao MODIS/061/MOD17A2H`).

### 2) Baixar os limites oficiais dos biomas e da Bahia (IBGE) e calcular

```bash
# todas as variáveis mensais + ONI, 2021 até o último ano disponível,
# no layout da aba Plan1 da planilha (uma coluna por bioma x variável)
python npp_modis_gee.py --project SEU-PROJETO --variavel todas \
    --baixar-ibge dados_ibge --formato largo --decimal ,

# só a PSN, formato longo
python npp_modis_gee.py --project SEU-PROJETO --variavel psn --baixar-ibge dados_ibge

# NPP anual (MOD17A3HGF)
python npp_modis_gee.py --project SEU-PROJETO --variavel npp --baixar-ibge dados_ibge

# chuva reprocessada em IMERG V07 para toda a série
python npp_modis_gee.py --project SEU-PROJETO --variavel precip --inicio 2001 --baixar-ibge dados_ibge
```

`--baixar-ibge PASTA` baixa e extrai, só na primeira vez:

- Biomas 1:250.000 (IBGE, 2019): `Biomas_250mil.zip` → `lm_bioma_250.shp`
  (campo `Bioma`: Amazônia, Caatinga, Cerrado, Mata Atlântica, Pampa, Pantanal)
  <https://geoftp.ibge.gov.br/informacoes_ambientais/estudos_ambientais/biomas/vetores/Biomas_250mil.zip>
- Limite estadual da Bahia (malha municipal 2022): `BA_UF_2022.zip` → `BA_UF_2022.shp`
  <https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/UFs/BA/BA_UF_2022.zip>

O recorte bioma ∩ Bahia é feito localmente (geopandas) e enviado ao GEE
simplificado com tolerância de 0,0005° (~55 m, irrelevante para pixel de
500 m; `--tolerancia 0` desativa). Áreas resultantes: Mata Atlântica ≈113 mil
km², Cerrado ≈105 mil km², Caatinga ≈360 mil km².

Se você recuperar os shapefiles usados na dissertação, use-os no lugar do
IBGE para manter a comparabilidade com 2001–2020:

```bash
python npp_modis_gee.py --project SEU-PROJETO --variavel todas \
    --biomas caminho/biomas_ba.shp --campo-bioma NOME_DO_CAMPO \
    --biomas-nomes "Mata Atlântica" Cerrado Caatinga
```

`--biomas` também aceita um asset do GEE (`projects/.../assets/biomas_ba`), útil
se o polígono for muito detalhado; nesse caso o recorte pela Bahia é feito no
GEE (com `--bahia arquivo.shp` ou, sem ele, o limite FAO GAUL 2015 do catálogo).

### 3) Concatenar com a série histórica

Saída padrão: `variaveis_biomas_bahia_<inicio>_<fim>.csv` (e
`npp_anual_biomas_bahia_<...>.csv` para o NPP), UTF-8 com BOM, ordenado por
ano, mês e bioma. Com `--decimal ,` o separador de campos passa a `;`. Com
`--formato largo` sai `ano, mes, oni, Mata Atlântica_psn_g_c_m2, Cerrado_psn_g_c_m2,
...`, o mesmo arranjo da aba Plan1. `--stats-extras` acrescenta n_pixels,
desvio, mínimo, máximo e n.º de composições.

### Opções úteis

| Opção | Efeito |
|---|---|
| `--variavel psn et lst` | escolhe as variáveis (ver tabela no topo); `todas` = todas as mensais + oni |
| `--inicio 2021 --fim 2025` | intervalo de anos (padrão: 2021 até o último disponível; anos sem dado são avisados e pulados) |
| `--agregacao calendario` | meses civis em vez das janelas da planilha (produtos 8-dias) |
| `--qc-max 30` | (npp) descarta pixels com `Npp_QC` > 30 % de entradas preenchidas |
| `--colecao` / `--banda` | troca coleção ou banda de uma única variável (ex.: `--variavel psn --banda Gpp`) |
| `--tile-scale 8` | se o GEE reclamar de memória |
| `--saida arquivo.csv` | nome do CSV |

## O que muda em relação ao fluxo MRT + ArcGIS (para registrar na metodologia)

- **Coleção 6.1 em vez de 6**: a comparação 2001–2020 (720 pares mês × bioma)
  com `--agregacao benfica` mostrou diferença mediana de ~0,2 % e p90 abaixo
  de 1 %, ou seja, v6 e v6.1 são praticamente idênticas aqui. Ainda assim, o
  mais limpo para a dissertação é regenerar toda a série 2001–2025 com o
  script (`--inicio 2001`), para que fique 100 % v6.1 e reproduzível.
- **Projeção**: a média é calculada na grade sinusoidal nativa (≈463 m), sem
  reprojetar para WGS84 como fazia o MRT; evita reamostragem.
- **Valores de preenchimento** (32761–32767: água, urbano, gelo, etc.) são
  mascarados antes da média. Confira se o fluxo antigo fazia o mesmo.
- **Agregação mensal**: `--agregacao benfica` reproduz a planilha (janelas
  fixas de DOY, ver tabela acima); `--agregacao calendario` usa o mês civil.
  Nos dois casos o pixel só entra se todas as composições do mês forem válidas.
- **Limites**: IBGE 1:250.000 (2019) ∩ malha estadual 2022, salvo se você
  informar os shapefiles originais.

## Erros tratados

- sem `--project`, projeto inexistente, conta não registrada, API desabilitada,
  credencial expirada (o script tenta reautenticar e explica o que falhou);
- pacote `earthengine-api`/`geopandas` ausente ou quebrado;
- shapefile ausente, campo de bioma inexistente, bioma não encontrado ou fora
  da Bahia, geometria grande demais para o GEE;
- ano pedido sem dado (avisa e pula), mês sem composições, mês incompleto,
  bioma sem pixel válido (fica fora do CSV e o script termina com código 2);
- falta de memória no GEE (sugere `--tile-scale`).

## Resultados já gerados (pasta `resultados/`)

Processados em 08–09/09/2026 com o projeto do autor, limites IBGE e as coleções
da tabela do topo. Último ano disponível: **2025** para todas as variáveis
(a chuva IMERG V07 vai até set/2025; out–dez/2025 ficam vazios até a NASA
publicar). ONI vai até JJA/2026.

| Arquivo | Conteúdo |
|---|---|
| `variaveis_mensais_2021_2025_plan1.csv` | **as 7 variáveis mensais + ONI, 2021–2025, no layout da aba Plan1** (`ano, mes, ONI, FMA_PSN, Cerrado_PSN, Caatinga_PSN, FMA_Evap, ..., Caatinga_AreaQueimada`) |
| `variaveis_mensais_2021_2025_longo.csv` | o mesmo em formato longo (ano, mes, bioma, uma coluna por variável) |
| `variaveis_mensais_2001_2025_concatenada_plan1.csv` | planilha 2001–2020 + GEE 2021–2025 (chuva 2021+ em V07) |
| `variaveis_mensais_2001_2025_toda_gee_plan1.csv` / `_longo.csv` | toda a série 2001–2025 reprocessada no GEE (v6.1, IMERG V07), homogênea |
| `npp_anual_2021_2025[_largo].csv` | NPP anual MOD17A3HGF |
| `validacao_2001_2020_todas_variaveis.csv` | planilha × GEE, 720 linhas, todas as variáveis (inclui chuva V06 e V07) |
| `variaveis_bahia_biomas_2001_2025.xlsx` | tudo acima em abas, com resumo da validação |
| `psn_*.csv`, `psn_npp_bahia_biomas_2001_2025.xlsx` | entregas anteriores só de PSN/NPP |

Os `*_excel_ptbr.csv` usam `;` e vírgula decimal.

### Validação 2001–2020 (planilha × GEE, mesma regra de agregação)

| Variável | r | erro mediano | p90 do erro | Observação |
|---|---|---|---|---|
| PSN | 1,000 / 0,936 (MA) | 0,2 % | < 1 % | out/2004 MA = 51,30 na planilha vs 142,59 (provável digitação); nov/2001 +5 a +18 % |
| ET | 0,993 | −3 % | 6 % | MOD16 v6.1 gap-filled vs v6 |
| IDA (ET/PET) | 0,998 | +1,7 % | 4 % | |
| Temperatura (LST dia) | 0,978 | −0,5 °C | ~1,7 °C | viés −1,1 °C na Mata Atlântica; mascaramento de nuvem diferente |
| Chuva IMERG V06 | 0,996 | +1 % | 2,6 % | é a fonte da planilha; alguns pontos atípicos na planilha (out/2016 Cerrado, jan/2003, set/2001 Caatinga, abr/2020 MA) |
| Chuva IMERG V07 | 0,985 | 0 % | 38 % | versão atual; única disponível após set/2021 |
| Área queimada | 0,995 | +1 % | 28 % (valores pequenos) | pixels MCD64A1 × 25 ha |

A coluna ONI da aba Plan1 da planilha parece deslocada (os valores em 2001
são os de 2000). Os arquivos aqui usam o ONI atual da NOAA (ERSSTv5), no mês
central de cada estação.
