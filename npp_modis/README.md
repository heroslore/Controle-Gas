# NPP / PSN MODIS (MOD17, Coleção 6.1) por bioma na Bahia — Google Earth Engine

Script `npp_modis_gee.py`: automatiza em Python, via Google Earth Engine (GEE), o
fluxo manual da metodologia de Benfica et al. (2022) (Earthdata → MRT → ArcGIS)
para obter a produtividade MODIS média por bioma (Mata Atlântica, Cerrado e
Caatinga) no estado da Bahia, pronta para concatenar com a série histórica.

## Antes de tudo: sua série histórica é MENSAL (PsnNet), não NPP anual

A planilha `dados_graficos_Benfica_3.xlsx` tem 12 blocos ("Jan - net
photosynthesis", "Fev - PSN", ..., "Dez - PSN"), 2001–2020, com valores de
~40 a 180 g C/m² **por mês**. Isso é a **fotossíntese líquida (PsnNet) 8-dias
do MOD17A2H somada por mês**, não o NPP anual do MOD17A3 (que daria ~1.000 a
1.600 g C/m² **por ano**; a soma dos 12 meses da sua planilha dá ≈1.594, 1.161
e 1.047 g C/m²/ano para Mata Atlântica, Cerrado e Caatinga, coerente com isso).

Por isso o script tem dois modos:

| `--produto` | Coleção GEE (v6.1)        | Banda   | Agregação                          | CSV                                |
|-------------|---------------------------|---------|------------------------------------|------------------------------------|
| `anual`     | `MODIS/061/MOD17A3HGF`    | `Npp`   | valor anual do produto             | `ano, bioma, npp_g_c_m2`           |
| `mensal`    | `MODIS/061/MOD17A2HGF`    | `PsnNet`| soma das composições 8-dias do mês | `ano, mes, bioma, psn_g_c_m2`      |

`anual` é o que você pediu e é o padrão. **Para continuar a série da planilha,
use `--produto mensal --agregacao benfica`** (e `--formato largo` para sair com
uma coluna por bioma, como na planilha). Nos dois modos o fator de escala já é
aplicado: DN × 0,0001 kg C/m² × 1000 = DN × 0,1 g C/m² (o mesmo 0,1 do fluxo
MRT/ArcGIS).

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
ano anterior. `--agregacao benfica` reproduz exatamente isso (erro mediano
< 0,3 % em todos os meses; o resíduo é Coleção 6 × 6.1). `--agregacao
calendario` (padrão) soma as composições iniciadas dentro do mês civil, que é
o mais defensável para uma série nova, mas **não** é comparável à planilha em
jan, abr, mai, out e nov.

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
python npp_modis_gee.py --project SEU-PROJETO --apenas-verificar                    # NPP anual
python npp_modis_gee.py --project SEU-PROJETO --apenas-verificar --produto mensal   # PsnNet 8-dias
```

Imprime, no modo anual, `ÚLTIMO ANO DISPONÍVEL: <ano>`; no mensal, a data da
última composição e o `ÚLTIMO ANO COMPLETO (46 composições)`. Os produtos
`*GF` (gap-filled) de um ano só são publicados após o fim do ano; o ano
corrente, se precisar, está no produto não gap-filled
(`--colecao MODIS/061/MOD17A2H`).

### 2) Baixar os limites oficiais dos biomas e da Bahia (IBGE) e calcular

```bash
# série mensal continuando a planilha, de 2021 até o último ano completo
python npp_modis_gee.py --project SEU-PROJETO --produto mensal --agregacao benfica \
    --baixar-ibge dados_ibge --formato largo --decimal ,

# NPP anual, 2021 até o último disponível
python npp_modis_gee.py --project SEU-PROJETO --produto anual --baixar-ibge dados_ibge
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
python npp_modis_gee.py --project SEU-PROJETO --produto mensal \
    --biomas caminho/biomas_ba.shp --campo-bioma NOME_DO_CAMPO \
    --biomas-nomes "Mata Atlântica" Cerrado Caatinga
```

`--biomas` também aceita um asset do GEE (`projects/.../assets/biomas_ba`), útil
se o polígono for muito detalhado; nesse caso o recorte pela Bahia é feito no
GEE (com `--bahia arquivo.shp` ou, sem ele, o limite FAO GAUL 2015 do catálogo).

### 3) Concatenar com a série histórica

Saída padrão: `<produto>_biomas_bahia_<inicio>_<fim>.csv`, UTF-8 com BOM
(abre direto no Excel), ordenado por ano, mês e bioma. Com `--decimal ,` o
separador de campos passa a `;` (padrão pt-BR). Com `--formato largo` as
colunas são `ano[,mes],Mata Atlântica,Cerrado,Caatinga`. Com `--stats-extras`
entram `n_pixels`, desvio-padrão, mínimo, máximo (e `n_composicoes` no mensal).

### Opções úteis

| Opção | Efeito |
|---|---|
| `--inicio 2021 --fim 2025` | intervalo de anos (padrão: 2021 até o último disponível; anos sem dado são avisados e pulados) |
| `--qc-max 30` | (anual) descarta pixels com `Npp_QC` > 30 % de entradas preenchidas; padrão não filtra, como no método original |
| `--banda Gpp` | usa GPP em vez de Npp/PsnNet |
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

Processados em 08/09/2026 com o projeto do autor, limites IBGE e Coleção 6.1:

| Arquivo | Conteúdo |
|---|---|
| `psn_mensal_2021_2025_regra_planilha[_largo].csv` | PsnNet mensal 2021–2025 na regra da planilha (continua a série) |
| `psn_mensal_serie_2001_2025_concatenada.csv` | planilha 2001–2020 + GEE 2021–2025, formato largo |
| `psn_mensal_serie_2001_2025_toda_v61.csv` | toda a série 2001–2025 reprocessada em v6.1 |
| `psn_mensal_2021_2025_mes_civil_largo.csv` | alternativa com meses civis (`--agregacao calendario`) |
| `npp_anual_2021_2025[_largo].csv` | NPP anual MOD17A3HGF 2021–2025 |
| `validacao_2001_2020_planilha_vs_gee.csv` | 720 pares mês × bioma: planilha vs GEE |
| `psn_npp_bahia_biomas_2001_2025.xlsx` | tudo acima em abas |

Os `*_excel_ptbr.csv` usam `;` e vírgula decimal. Último ano disponível em
08/09/2026: **2025** (MOD17A3HGF anual e MOD17A2HGF com 46/46 composições).

Validação 2001–2020 (regra da planilha): Caatinga e Cerrado r = 1,000 e
diferença mediana de 0,2 g C/m²; Mata Atlântica r = 0,936 por causa de um
ponto isolado, **out/2004 = 51,30 na planilha contra 142,59 reproduzido**
(provável erro de digitação; conferir). Nov/2001 também difere (+5 a +18 %)
nos três biomas, provavelmente uma composição faltante na Coleção 6.
