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

## 6. Pareceres da banca de qualificação: quem pediu o quê, onde, e situação

Fonte: PDFs anotados `Qualificacao_Ygor_Oliveira_-_consideracoes_MB.pdf` (Prof. Marcos
Bernardes, 106 anotações) e `Trabalho_Final_comentarios_Fernando_1.pdf` (Prof. Fernando,
FIOCRUZ-RO, 30 anotações). **Os dois foram feitos sobre o mesmo texto do
`Trabalho_Final.pdf`, que é a versão que foi à banca**; por isso a coluna
"Situação" diz o que a atualização da base já resolve e o que depende de
edição do texto (que só posso conferir na versão revisada). Todas as 136
anotações, com página e trecho, estão em `pareceres_banca_anotacoes.csv`.

Legenda da situação: **RESOLVIDO (dados)** = a nova base/pipeline responde;
**TEXTO** = edição de redação/estrutura, verificar na versão revisada;
**DADOS + TEXTO** = a base fornece o conteúdo, falta escrever.

### 6.1 Prof. Marcos Bernardes (MB)

| # | Pág. | Local (trecho) | O que pediu | Situação / o que muda |
|---|---|---|---|---|
| MB-1 | 3 | Resumo, 1.ª frase | Frase de abertura sobre o uso de regressão para estudar fenômenos naturais | TEXTO |
| MB-2 | 3, 4, 22, 23, 27 | Resumo/Abstract e 5.4 | Resumo cita só R²; metodologia usa R², RMSE, MAE, resíduos, média e DP. Citar todas no resumo/abstract (repetido 6×) | DADOS + TEXTO: valores novos prontos (RMSE, MAE, IC 95 %, gap) na seção 5 deste roteiro |
| MB-3 | 3, 8, 13, 16, 24 | Resumo; 1; 2; 5.1; 5.4 | "Traduzir" para o público geral: MRMP-N, ONI, "resposta pulsada", "gap de overfitting", penalização L2 (repetido 7×) | TEXTO |
| MB-4 | 3 | Resumo, "resposta pulsada"; p. 34 Tabela 4 | O que é? | TEXTO: definir na fundamentação e na Tabela 4 |
| MB-5 | 3, 19, 37 | Resumo; 5.2 ONI; 6.5 | ENSO: fases neutro/El Niño/La Niña? com ou sem defasagem? ONI é trimestral, como conciliar com mensal? intensidades consideradas? | RESOLVIDO (dados) + TEXTO: ONI da NOAA atribuído ao mês central da estação de 3 meses; fases por limiar ±0,5; a coluna antiga estava deslocada 1 ano (corrigida). Falta escrever isso em 5.2 e testar defasagem (1–3 meses) se a orientadora quiser |
| MB-6 | 3, 43 | Resumo; 7 | Destacar a principal contribuição acadêmica; parte do parágrafo final merece ir ao resumo | TEXTO |
| MB-7 | 3 | Palavras-chave "Regressão Ridge Polinomial" | Mistura português/inglês? | TEXTO: "Regressão polinomial com regularização (Ridge)" |
| MB-8 | 5, 17 | Lista de siglas; 5.2 | Itálico em termos estrangeiros (repetido 5×) | TEXTO |
| MB-9 | 6 | Lista de figuras | Tirar as linhas de tabela | TEXTO |
| MB-10 | 7, 16, 33, 41 | Sumário; 5.1; 6.3; 6.6 | Área de estudo com uma página é pouco; incluir referências dos dados climáticos; levar para 5.1 os temas de 6.3/6.6 (uso do solo, Corredor Central, ZEE, PLANAVEG, restauração, povos indígenas) | TEXTO: ampliar 5.1; dados de área por bioma (IBGE) já calculados: MA 113 mil km², CE 105 mil, CA 360 mil |
| MB-11 | 8 | 1, 1.º parágrafo | "O estado da Bahia…" (não "a região") | TEXTO |
| MB-12 | 8 | 1, MRMP-N | Quais autores já usaram esses modelos? citar referências | TEXTO |
| MB-13 | 10, 13, 17 | 2 (MOD17); 2; 5.2 | Explicar o que é o MODIS na 1.ª citação; qual agência espacial; resolução espaço-temporal; metodologia fora do lugar (2 vs 5) | DADOS + TEXTO: NASA/Terra, 500 m, composições de 8 dias, Coleção 6.1, agregação em 4 composições (tudo em `RELATORIO_METODOLOGIA.md`) |
| MB-14 | 10 | 2 | "Escala mensal para 19 anos?" | RESOLVIDO (dados): agora 2001–2025, 25 anos, n = 297 |
| MB-15 | 11 | 2 (MapBiomas) | Recortes de uso do solo por bioma na Bahia | TEXTO (sugestão; pode ser feito no GEE com MapBiomas se quiserem) |
| MB-16 | 14 | 3.2 hipóteses | Definir "grau ótimo" e "parcela significativa"; especificar o tipo de produtividade | TEXTO |
| MB-17 | 15 | 3.2 / 7 | As hipóteses são verificadas no final com justificativas? | TEXTO: 7 já verifica; reforçar |
| MB-18 | 15 | 4.1 / 4.2 | Ecossistemas ou biomas? mais de um objetivo geral; metodologia misturada com objetivo específico | TEXTO |
| MB-19 | 18 | Tabela 1 | Retirar marcações de revisão; linha solta na tabela | TEXTO |
| MB-20 | 19 | 5.2 BURN | "Isso já é resultado" (distribuição assimétrica da área queimada) | TEXTO: mover a justificativa ou citar como pré-análise |
| MB-21 | 19 | 5.2 winsorização | O que é? como se chega ao percentil 3? esquema da metodologia | TEXTO: explicar (percentil 3 = 3 % menores valores substituídos pelo valor do percentil; escolha empírica); Figura 2 pode subir |
| MB-22 | 23 | 5.5 | "Reconhece-se, contudo…" | TEXTO |
| MB-23 | 24 | 5.4 resíduos | Por que n = 240? | RESOLVIDO (dados): n = 297 (2001–set/2025); 300 quando a NASA publicar a chuva de out–dez/2025 |
| MB-24 | 25 | 5.6 random_state = 42 | Por que esse valor? | TEXTO: semente arbitrária, fixa para reprodutibilidade |
| MB-25 | 26 | Figura 2 | Colocar a figura bem antes no capítulo | TEXTO |
| MB-26 | 27 | Tabela 2 | Como foi estimada a "PSN observada"? pelo MODIS? | DADOS + TEXTO: sim, MOD17A2HGF PsnNet, média por bioma, soma de 4 composições |
| MB-27 | 28 | 6.1 Cerrado | Onde está a análise PSN × preditoras? incluir linha na Tabela 3 | TEXTO; Figura 5 (importância) cobre; dados de correlação disponíveis |
| MB-28 | 28 | Tabela 3, Mata Atlântica | (destaque) "menor capacidade de extrapolação para períodos futuros" | RESOLVIDO (dados): com 2001–2025 a queda no TimeSeriesSplit cai de 15,7 para 7,0 pp; reescrever |
| MB-29 | 31 | 6.2 | Incluir trabalhos que corroboram o achado (limitação hídrica no Cerrado) | TEXTO |
| MB-30 | 32 | 6.3 WAI | A definição de WAI precisa estar na metodologia | RESOLVIDO (dados) + TEXTO: WAI = ET/PET (MOD16A2GF), confirmado pela validação (r = 0,998) |
| MB-31 | 34 | Tabela 4 | Tabela importante, síntese no resumo; "direta ou indiretamente proporcional?"; "o que são?" (componentes de sazonalidade) | TEXTO; atualizar R² da tabela (96,7 / 94,2 / 70,9) |
| MB-32 | 35 | 6.4 | Citar Figura 6 no texto; Ljung-Box não estava na metodologia; "o que é?" (memória temporal) | TEXTO + DADOS: incluir Ljung-Box em 5.4; resultados novos: autocorrelação em MA e CA |
| MB-33 | 36 | Figura 6 | Figura sem legenda | TEXTO |
| MB-34 | 36 | 6.4 Y-randomization | "Boiei aqui de novo" (R² permutado negativo) | TEXTO: explicar em linguagem simples |
| MB-35 | 40 | 6.6 | "Muito mais etnias do que Pataxó"; como isolar o efeito do eucalipto/fragmentação? | TEXTO: corrigir e marcar como hipótese, não resultado |

### 6.2 Prof. Fernando (FIOCRUZ-RO)

| # | Pág. | Local (trecho) | O que pediu | Situação / o que muda |
|---|---|---|---|---|
| F-1 | 8 | 1, definição de PSN | Explicar o que é fotossíntese líquida; talvez um gráfico da teoria vigente | TEXTO |
| F-2 | 9 | 1 | O que é "forçamento"? | TEXTO |
| F-3 | 10 | 2, GPP/PSN/NPP | Fundamentar; reescrever "subtrair, adicionalmente"; ele propõe PSN = GPP − Rm(folhas e raízes finas), e NPP = PSN − Rcrescimento | TEXTO: a definição do MOD17 é PSN = GPP − Rm; NPP = PSN − Rg (anual). A base nova traz NPP anual (MOD17A3HGF) e PSN para ilustrar |
| F-4 | 10 | 2, Cerrado | Não vê evidência de controle hídrico no Cerrado; trazer dado para comparação | DADOS + TEXTO: na base nova a correlação PSN × WAI e PSN × PRE no Cerrado e a Figura 5 fornecem o dado |
| F-5 | 12 | 2 | Pasto transpira menos que árvores? | TEXTO |
| F-6 | 13, 20, 21, 22, 25 | 2 e 5.3–5.5, referência a Guimarães et al. (2024) | Explicar que o QSAR original previa inibição de atividade celular; corrigir: Guimarães testou graus até 8 empiricamente (não fixou grau 4); testou > 400 variáveis em combinações de 3 (não "seleção a priori"); o Y-randomization de Guimarães comparou a média dos permutados, critério de 30 % entre R² de CV e de treino/teste | TEXTO: 5 correções de descrição do trabalho de referência (p. 13, 20, 21, 22, 25) |
| F-7 | 16 | 5.1 | Área de estudo deve ir para a introdução | TEXTO (conflita em parte com MB-10, que pede ampliar 5.1; decidir com a orientadora) |
| F-8 | 17 | 5.2 "bases climáticas regionais" | Quais? Não pode haver indefinição; reprodutibilidade | RESOLVIDO (dados): todas as fontes identificadas (Tabela da seção 2 deste roteiro), pipeline reproduzível em um comando |
| F-9 | 18 | Tabela 1 | Os dados são acessíveis pela web ou precisam de acesso específico? | RESOLVIDO (dados): catálogo público do Google Earth Engine, conta gratuita acadêmica; script no repositório |
| F-10 | 19 | 5.2 sazonalidade | sin + cos somados passam de 1 (1,37) | TEXTO: esclarecer que são dois preditores separados, cada um em [−1, 1], nunca somados |
| F-11 | 19 | 5.2 sazonalidade | Pode criar sazonalidade artificial? | TEXTO: argumentar (harmônicos ortogonais; o modelo estima o peso de cada um) |
| F-12 | 19 | 5.2 winsorização | Explicar | TEXTO (= MB-21) |
| F-13 | 20 | 5.3 equação | Faltou a representação de grau > 1 (termos quadráticos X_i²) | TEXTO |
| F-14 | 21 | 5.3 Ridge | Pré-processar colinearidade com df.corr() e excluir variáveis redundantes | DADOS + TEXTO: VIF já é feito; posso gerar a matriz de correlação da base nova (EV × WAI no Cerrado r alto) |
| F-15 | 21, 26 | 5.3 e Figura 2 | Qual a proporção treino/teste? quem é o grupo de teste? | TEXTO: RepeatedKFold com 5 partes = 80 % treino / 20 % teste em cada fold (192/48 com n = 240; 238/59 com n = 297), 30 repetições |
| F-16 | 22 | 5.4 seleção de variáveis | sazsin e sazcos deveriam ser fixas e as combinações feitas entre as outras 5 | TEXTO: o script atual já usa as 5 variáveis fixas (C(5,5) = 1); descrever assim |
| F-17 | 22 | 5.4 | Generalização é determinada pelo R² de teste | TEXTO |
| F-18 | 23 | 5.5 RepeatedKFold | Esquema gráfico da divisão | TEXTO (figura) |
| F-19 | 24, 26 | 5.4 e Figura 2 | Onde estão os dados? mostrar a tabela com os dados | RESOLVIDO (dados): `resultados/base_final_2001_2025_plan1.csv` e `.xlsx`; apêndice ou repositório |
| F-20 | 29 | 6.2 grau ótimo | "Não pra Caatinga" (grau 2 não seria ótimo) | DADOS: na base nova o grau 2 é o máximo na Caatinga (94,2 % contra 93,8 % do grau 1 e 93,4 % do grau 3), mas a vantagem é pequena; reconhecer no texto que grau 1 e 2 são equivalentes ali |

### 6.3 Síntese para a reunião

- 8 itens ficam **resolvidos pela nova base**: fontes indefinidas (F-8, F-9, F-19), ONI trimestral/deslocado (MB-5), n = 240 (MB-23), WAI sem definição (MB-30), extrapolação temporal da MA (MB-28), "19 anos" (MB-14).
- 7 itens são **dados prontos que faltam escrever**: RMSE/MAE no resumo (MB-2), MODIS/NASA/resolução (MB-13), PSN observada (MB-26), Tabela 4 (MB-31), Ljung-Box (MB-32), controle hídrico no Cerrado (F-4), correlação entre preditores (F-14).
- Os demais (~40) são **redação, estrutura e explicações didáticas**, sem dependência dos dados.
- **Um conflito a decidir com a orientadora**: MB pede ampliar a área de estudo (5.1); Fernando pede levá-la para a introdução.

## 7. Alterações no texto exigidas pela nova base (independentes da banca) (página e local no `Trabalho_Final.pdf`)

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
