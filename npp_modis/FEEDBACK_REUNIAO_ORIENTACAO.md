# Roteiro para a reunião de orientação — atualização da base de dados e do MRMP-N

Ygor Augusto dos Santos Oliveira · PPGCTA UFSB/IFBA · setembro/2026
Material de apoio: pasta `npp_modis/` (código, resultados, relatórios).

---

## 1. Resumo do que foi feito

1. **Automatizei a obtenção dos dados** que antes eram baixados e processados à mão (Earthdata → MRT → ArcGIS). Agora um script Python consulta o Google Earth Engine (GEE), recorta os biomas da Bahia e calcula todas as variáveis mensais por bioma. Rodar tudo do zero leva cerca de uma hora e é reproduzível.
2. **Descobri a regra exata de agregação da planilha original** (Benfica et al. 2022): cada mês da série é a soma de 4 composições MODIS de 8 dias em janelas fixas de dia-do-ano. Reproduzi essa regra no código, para que a série nova seja comparável à antiga.
3. **Validei o pipeline contra a planilha 2001–2020** (720 pares por variável) e identifiquei a fonte real de cada variável: PSN, ET, PET, temperatura, chuva, área queimada e ONI.
4. **Estendi a série até 2025** (PSN, ET, PET, IDA, temperatura, chuva, área queimada, ONI) e reprocessei 2001–2020 na mesma coleção, produzindo uma **base homogênea 2001–2025** (300 meses).
5. **Encontrei 7 células com erro de digitação na planilha original** e um deslocamento de um ano na coluna ONI; ambos eliminados na base nova.
6. **Rodei o MRMP-N** (o mesmo `Modelo_Ridge.py`, sem alterar a lógica) na planilha antiga, na base nova 2001–2020 e na base nova 2001–2025, e repliquei todas as análises da dissertação (validação temporal, grau, resíduos, Y-randomization, ENSO).

## 2. De onde vieram os dados novos

| Variável | Antes (planilha da Profa. Nayanne) | Agora (GEE) | Como validei |
|---|---|---|---|
| PSN | MOD17A2H, Coleção 6, HDF via MRT/ArcGIS | `MODIS/061/MOD17A2HGF` (Coleção 6.1, gap-filled), banda PsnNet | r = 1,000; erro mediano 0,2 % |
| Evapotranspiração | MOD16A2, Coleção 6 | `MODIS/061/MOD16A2GF`, banda ET | r = 0,993; −3 % |
| PET (nova) | não existia na planilha | `MODIS/061/MOD16A2GF`, banda PET | usada no IDA |
| IDA / WAI | Benfica et al. 2022 (definição não explicitada) | **ET ÷ PET**, mesma coleção | r = 0,998; +1,7 % → confirma a definição |
| Temperatura (TST) | MOD11A2, Coleção 6 | `MODIS/061/MOD11A2`, LST diurna, média das composições | r = 0,978; −0,5 °C |
| Chuva | GPM IMERG Final mensal **V06** (a dissertação cita CHIRPS, mas é IMERG) | `NASA/GPM_L3/IMERG_MONTHLY_V07` | V06: r = 0,996; V07: r = 0,985 |
| Área queimada | MCD64A1, Coleção 6 | `MODIS/061/MCD64A1`, pixels × 25 ha | r = 0,995; +0,8 % |
| ONI | NOAA/INPE (coluna deslocada 1 ano na planilha) | NOAA CPC, mês central da estação | realinhado |
| NPP anual (nova) | — | `MODIS/061/MOD17A3HGF` | — |

Limites: biomas IBGE 1:250.000 (2019) recortados pelo limite estadual IBGE 2022. Áreas: Mata Atlântica 113 mil km², Cerrado 105 mil km², Caatinga 360 mil km².

## 3. Diferença entre os dados novos e os antigos (2001–2020, 240 meses × 3 biomas)

- **PSN, IDA, ET e temperatura**: praticamente iguais. Média de longo prazo difere ≤ 3,5 %, correlação mês a mês ≥ 0,97. A ET fica ~3 % mais baixa (versão gap-filled da coleção 6.1) e a temperatura ~0,5 °C mais baixa (máscara de nuvem diferente; −1,2 °C na Mata Atlântica).
- **Chuva**: mesma média de longo prazo (933 vs 945 mm/ano), mas em 135 dos 720 meses a diferença passa de 20 %. É a variável que mais muda, pela troca de versão do IMERG (item 4).
- **Área queimada**: idêntica no Cerrado (r = 1,000). Na Caatinga e na Mata Atlântica a média cai 8 % com r ≈ 0,9, porque ali os valores são pequenos e poucos pixels pesam em porcentagem.
- **Correções**: 7 células atípicas na planilha (desvio > 30 % contra a reprodução, com os vizinhos batendo). A mais grave: PSN de out/2004 na Mata Atlântica, 51,3 na planilha contra 142,6 reproduzido. As outras: temperatura out/2011 MA; chuva set/2001 Caat., jan/2003 Cerr. e Caat., out/2016 Cerr., abr/2020 MA. Lista com valor antigo e novo em `resultados/referencia/correcoes_planilha.csv`.
- **Período**: 2001–2025 em vez de 2001–2020. Única lacuna: chuva de out–dez/2025, que a NASA ainda não publicou.

## 4. Como explicar a mudança de versão dos produtos da NASA

**MODIS Coleção 6 → 6.1.** A NASA reprocessa periodicamente todo o acervo MODIS. A Coleção 6.1 (2017–2021) corrigiu a calibração dos sensores Terra e Aqua (degradação dos detectores, polarização, faixas de varredura), atualizou os insumos meteorológicos do MOD16/MOD17 e o mapa de cobertura MCD12Q1. A Coleção 6 foi descontinuada e removida dos servidores; só a 6.1 está disponível. Para PSN, ET e temperatura a diferença medida aqui é pequena (≤ 3,5 %).

**GPM IMERG V06 → V07.** O IMERG (Integrated Multi-satellitE Retrievals for GPM) é a chuva estimada por satélite da NASA. A V07 (lançada em 2023) reprocessou toda a série desde 1998 com novo algoritmo de calibração por pluviômetros (GPCC), nova correção de órbita e inclusão de mais satélites. A V06 foi encerrada em setembro de 2021 e não recebe dados novos. Consequências práticas:

- os anos 2021–2025 só existem em V07;
- a V07 muda o valor mês a mês em relação à V06 (aqui, até 40 % em meses isolados, sem viés na média anual);
- emendar V06 (2001–2020) com V07 (2021–2025) criaria uma quebra artificial na série;
- por isso a base final usa **V07 em toda a série 2001–2025**.

Frase para o texto: *"A precipitação foi obtida do produto GPM IMERG Final Run mensal, versão 07, que reprocessou integralmente a série a partir de 1998 e substituiu a versão 06 utilizada em Benfica et al. (2022); para manter a homogeneidade temporal, toda a série 2001–2025 foi extraída na versão 07."*

Detalhe de latência: o IMERG Final mensal sai com ~6 meses de atraso; out–dez/2025 será preenchido quando publicado (um comando no script).

## 5. Efeito no modelo (MRMP-N, mesma especificação da dissertação)

| Bioma | Planilha 2001–2020 (dissertação) | Base nova 2001–2020 | Base nova 2001–2025 |
|---|---|---|---|
| Mata Atlântica, R² teste | 62,3 % | 72,9 % | 70,9 % |
| MA, gap de overfitting | 10,2 pp | 5,6 pp | 5,1 pp |
| MA, TimeSeriesSplit | 46,7 % | 59,5 % | 63,9 % |
| Cerrado, R² teste | 95,7 % | 96,3 % | 96,7 % |
| Caatinga, R² teste | 94,0 % | 94,2 % | 94,2 % |

Nenhum bioma piorou; a Mata Atlântica melhorou ~10 pontos e ficou estável no tempo. Grau 2 continua ótimo. Y-randomization aprovado em todos os casos. Coeficientes coerentes entre bases (correlação 0,93–0,96) e estáveis ao estender para 2025 (0,97–0,999).

## 6. Pareceres da banca de qualificação

**Não recebi os pareceres da banca.** O PDF `Trabalho_Final.pdf` não contém anotações nem seção de parecer, e nenhum outro documento com as observações dos membros foi enviado. Por isso **não consigo listar o que cada membro pontuou** nem cruzar com o que foi alterado.

Assim que você me enviar os pareceres (arquivo, fotos ou texto, um por membro), eu monto a tabela *membro → observação → o que foi alterado → página e trecho*. Com o que existe, a única coisa que posso afirmar é o que a nova base obriga a mudar no texto, que está na seção 7.

## 7. Alterações no texto exigidas pela nova base (página e local no `Trabalho_Final.pdf`)

| Página | Local | O que está | O que muda |
|---|---|---|---|
| 3 | Resumo, linhas "entre 2001 e 2020" e "R² = 95,7 % … 94,0 % … 62,3 %" | período e R² antigos | 2001–2025; R² CE 96,7 %, CA 94,2 %, MA 70,9 %; gap da MA "reduzido (~5 pp)" em vez de "próximo a 10 pp" |
| 4 | Abstract, mesmas frases | idem | idem em inglês |
| 17 | 5.2, 1.º parágrafo: "dados disponibilizados em formato tabular… MOD17A2H e MOD16" | fluxo manual, Coleção 6 | acrescentar: processamento no Google Earth Engine, Coleção 6.1, produtos gap-filled (MOD17A2HGF, MOD16A2GF), limites IBGE, agregação em janelas de 4 composições, série 2001–2025 |
| 18 | Tabela 1, linha PRE, coluna Fonte: "CHIRPS" | fonte errada | "GPM IMERG Final mensal V07 (NASA)" |
| 18 | Tabela 1, linha WAI | sem definição | "ET/PET (MOD16A2GF)" |
| 18 | Tabela 1, linha BURN, unidade "m²" | unidade errada | "ha (pixels MCD64A1 × 25 ha)" |
| 18 | 5.2, "O conjunto abrange o período de 2001 a 2020" | período | 2001–2025, n = 297 (out–dez/2025 aguardando IMERG) |
| 27 | Tabela 2 (R², IC, RMSE, MAE, gap) | valores da planilha | valores da base nova (tabela em `modelo/COMPARACAO_DISSERTACAO.md`) |
| 27–29 | Texto após Tabela 2: "R² = 62,3 %" (3 ocorrências) e "gap de 10,20 pp" | | 70,9 % e 5,1 pp; suavizar "desempenho inferior" para "moderado, com estabilidade temporal" |
| 28 | Tabela 3 (GroupKFold / TimeSeriesSplit / queda máxima) e parágrafo "menor capacidade de extrapolação" da MA | queda de 15,7 pp | queda de 7,0 pp; TimeSeriesSplit MA 63,9 % |
| 29–30 | 6.2 e Figura 4 | grau 2 ótimo | mantém; acrescentar que graus 4–5 colapsam com n = 297 |
| 34 | Tabela 4, coluna R² | 95,7 / 94,0 / 62,3 | 96,7 / 94,2 / 70,9 |
| 35 | 6.4, "Na Mata Atlântica (W = 0,858; p < 0,001) … evento extremo de produtividade muito baixa" | explicação baseada no erro de out/2004 | resíduos da MA normais (W = 1,00; p = 0,62); reescrever o parágrafo; manter a não normalidade da Caatinga |
| 35 | 6.4, Ljung-Box "apenas na Caatinga" | | autocorrelação também na MA (p < 0,001; lag-1 = 0,30); Cerrado no limiar |
| 36–37 | Y-randomization (Δ = 109 / 111 / 74 pp) | | aprovado; recalcular Δ com a base nova (75–99 pp fora da amostra) |
| 37 | 6.4, "VIF de 25,8 e 24,0" | | ~37 na base nova; interpretação mantém |
| 38 | 6.5, Cerrado: "evapotranspiração… apenas tendência (p = 0,071)" | | EV significativa (p < 0,001) e WAI também (p = 0,001); reescrever |
| 38 | 6.5, Mata Atlântica: "precipitação e evapotranspiração não exibiram diferenças" | | EV passa a ser significativa (p = 0,005); PRE mantém não significativa |
| 39 | 6.5, "responsável por menos de 2 % da variância" | | "menos de 6 %" (PSN MA 5,7 %); conclusão mantém |
| 39–40 | 6.5, Caatinga: PSN não significativa | | com 2001–2025 fica no limiar (p = 0,015); comentar como efeito fraco |
| 41–43 | 7, Considerações finais: período, R², gap da MA, "ENSO sem efeito direto" | | atualizar números; conclusões mantêm |
| 45+ | Referências | | acrescentar: Gorelick et al. 2017 (GEE); Huffman et al. 2023 (IMERG V07); Running & Zhao 2019 (MOD17 C6.1); Running et al. 2021 (MOD16 C6.1); Wan et al. 2021 (MOD11 C6.1); Giglio et al. 2021 (MCD64A1 C6.1); IBGE 2019 (biomas) |

## 8. Perguntas para levar à orientadora

1. Ela tem os arquivos originais (shapefiles dos biomas, HDFs) usados em 2022? Se sim, posso rodar o pipeline com os mesmos limites para fechar o resíduo de área.
2. Ela concorda em usar a série homogênea 2001–2025 (tudo no GEE) como base da dissertação, em vez de emendar a planilha antiga com os anos novos?
3. Como ela prefere tratar as 7 células corrigidas: nota metodológica ou apenas substituir?
4. Os pareceres da banca: quem os tem, para eu cruzar com as alterações.
