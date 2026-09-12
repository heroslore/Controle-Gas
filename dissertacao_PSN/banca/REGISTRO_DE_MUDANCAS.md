# Registro de mudanças — Trabalho_revisado_2001_2025.docx

Gerado por `banca/aplicar_revisao_docx.py` a partir de `Trabalho_revisado.docx`
(versão do Ygor) e de `resultados_2001_2025/`. Nada foi alterado no arquivo
original. Cada item indica o comentário da banca que atende (F = Fernando,
MB = Marcos Bernardes) ou "série nova" quando decorre da base 2001–2025.

## Ao abrir no Word

- O Word vai perguntar se deseja **atualizar os campos**: responda **Sim**, para
  o Sumário refletir as novas seções e páginas. As Listas de Figuras e de
  Tabelas já estão com as páginas (calculadas em PDF pelo LibreOffice; confira
  depois de atualizar o Sumário, pois a paginação do Word pode variar em 1).
- Conferir a **formatação das equações** (não foram tocadas) e a fonte das
  novas tabelas (Tabela 5 e Apêndice A), que usam o estilo TableGrid.
- O documento tem agora 67 páginas: 52 de texto, 13 de apêndice (paisagem)
  e 2 de referências.

## 1. Decisão de mérito tomada durante a revisão (reversível)

A busca exaustiva das 10 combinações de variáveis com a base nova
(`Selecao_Variaveis_PSN.py`, Tabela A2 do apêndice) mostrou que na
**Mata Atlântica o conjunto EV + TST + WAI** tem R² de teste
73,65 % contra 71,0 % do conjunto anterior
(EV + PRE + TST), com a mesma diferença treino–teste. Como a metodologia
declara que a seleção segue esse critério, o modelo da MA foi trocado para
EV + TST + WAI e todos os números da MA no documento (Tabelas 2 a 5,
Figuras 6 a 10, Y-randomization, VIF, resíduos) são desse conjunto.
Cerrado (EV + PRE + WAI) e Caatinga (EV + PRE + TST) confirmaram os conjuntos
da qualificação. **Para reverter:** trocar a linha `'x'` da MA em
`config_biomas` (`Modelo_PSN.py`), rodar `BIOMA_ATIVO=MA`, `consolidar_resultados.py`,
`Figuras_Dissertacao.py` e `banca/aplicar_revisao_docx.py`.

Consequência a discutir com o orientador: com esse conjunto, na MA o grau 3
tem R² de teste 0,8 pp maior que o grau 2 (74,4 % contra 73,6 %), mas com
diferença treino–teste 1,7 pp maior; o texto mantém o grau 2 pelo critério
composto e registra a ressalva (seção 6.2).

## 2. Números atualizados para a base 2001–2025 (série nova)

| | Mata Atlântica | Cerrado | Caatinga |
|---|---|---|---|
| Conjunto | EV + TST + WAI | EV + PRE + WAI | EV + PRE + TST |
| R² teste | 73,65 % | 96,66 % | 94,16 % |
| Dif. treino–teste | 5,19 pp | 0,59 pp | 1,03 pp |
| RMSE / MAE | 7,97 / 6,29 | 6,74 / 5,43 | 6,69 / 5,08 |
| GroupKFold / TimeSeriesSplit | 73,73 / 66,98 | 96,38 / 95,73 | 93,81 / 91,20 |
| Y-randomization Δ | 84,42 pp | 107,54 pp | 107,20 pp |
| Shapiro-Wilk p | 0,630 | 0,423 | 0,0015 |
| Ljung-Box p / ACF(1) | < 0,001 / 0,51 | 0,0052 / 0,20 | < 0,001 / 0,42 |
| VIF máximo | 4,23 | 36,99 | 5,02 |

Outras mudanças de resultado: n = 297 e período 2001–2025 em todo o texto;
Kruskal-Wallis da PSN agora **significativo na Caatinga** (p = 0,010);
Cerrado com EV, PRE e TST significativos entre fases; ONI explica no máximo
3 % (não 2 %) da variância climática; fases ENSO pelo critério oficial da
NOAA; autocorrelação residual nos três biomas; MA com resíduos normais.

## 3. Mudanças por comentário da banca

**Resumo/Abstract** (MB-1, 4, 5, 6, 7, 8, 9, 28, 48, 49, 50, 57, 65, 79):
reescritos por completo, em português claro, com todas as métricas e
diagnósticos, escalas, tipologia dos regimes, contribuição e implicações.
"gap de overfitting" trocado por "diferença treino–teste" em todo o texto.

**Fundamentação e introdução**: definição da PSN com equações e nova Figura 1
(GPP → PSN → NPP) (F1, F4, F5); "forçante" definida (F2); MODIS, produtos e
NASA explicados na primeira menção (F3, F6, MB-19, 26, 38); dado de controle
hídrico no Cerrado a partir das regressões simples (F7); mecanismo pasto ×
vegetação nativa (F8); QSAR explicado (F9); autores que usaram regressão
polinomial (MB-18); "O estado da Bahia" e frase "subótimas" traduzida
(MB-16, 17); ONI definido (MB-25); parágrafo do Ridge em linguagem simples
(MB-27); detalhes do produto MOD17A2H movidos para Dados (MB-20, 21, 22).

**Questão, hipóteses e objetivos**: "produtividade primária, medida pela PSN"
(MB-29); grau ótimo definido em H1 (MB-30); H2 quantificada em 60 % (MB-31);
objetivo geral único (MB-33); objetivos específicos sem nomes de técnica, em
quatro itens (MB-34).

**Área de estudo** (mantida na Metodologia e ampliada, conforme sua decisão):
Köppen citado (MB-35, parcial), "resposta pulsada" definida (MB-36),
hidrografia, Corredor Central, PLANAVEG/ZEE, uso do solo por bioma, povos
indígenas de várias etnias (MB-15, 63, 75, 77, 78). A Figura 3 (fluxo
metodológico, refeita com o pipeline atual) ficou logo após o mapa (MB-55).

**Dados e pré-processamento**: fontes exatas de cada variável, agência (NASA),
acesso público e Apêndice A com a base completa (F11, F12, F26, F29, MB-38);
WAI definido aqui (MB-61); período e n = 297 (MB-53); ONI trimestral → mês
central e classificação oficial das fases (MB-41, MB-3); explicação de que
as componentes sin/cos são preditores separados e não impõem sazonalidade
(F13, F14); área queimada como pré-processamento, não resultado (MB-42);
winsorização e percentil 3 explicados (F15, MB-43, 44); triagem por
correlação e exclusão da PET, como no estudo de referência (F18); Tabela 1
com coluna "Fonte / acesso" e unidade de BURN em ha.

**Especificação e análise estatística**: adaptação (ii) reescrita — o estudo
de referência também determinou o grau empiricamente, até 8 (F16, F20);
equação explícita do grau 2 e contagem de termos por grau (F17); estudo de
referência testou mais de 400 descritores em combinações de três (F22);
generalização medida pelo R² de teste (F23); sazonalidade fixa e busca sobre
C(5,3) = 10 combinações (F24); três métricas nomeadas (MB-47).

**Validação**: percentuais 80/20, ~238/59 meses, cada mês testado 30 vezes,
GroupKFold em 5 grupos de 5 anos e TimeSeriesSplit em blocos de 49 meses,
com nova Figura 4 (esquemas de particionamento) (F19, F21, F25, F28, MB-45);
"Reconhece-se, contudo" (MB-51); frase sobre autocorrelação traduzida
(MB-52); Shapiro-Wilk, Ljung-Box e ACF descritos na metodologia (MB-70);
critério de Y-randomization descrito sem atribuir os 60 pp ao artigo (F27);
semente 42 explicada (MB-54).

**Resultados**: nova Figura 5 (regressões simples PSN × variáveis) no início
(F7, MB-58); "PSN de referência (MODIS)" (MB-56); Figura 7 (grau) refeita e
texto com a ressalva da Caatinga e da MA (F30); conjuntos ótimos por bioma com
os números novos, incluindo a mudança da MA; linha que faltava no texto do
Cerrado e "BURNlog" que faltava (erros de digitação); "climaticamente
limitados" definido (MB-66); "diretamente proporcional" (MB-67); resíduos com
Figura 9 citada e "memória temporal" definida (MB-69, 71); Y-randomization
em linguagem simples (MB-73); Tabela 5 (VIF completo) nova; ENSO reescrito
com fases oficiais, intensidade do ONI e correlação de Pearson (MB-3, 74);
eucalipto/fragmentação como hipótese, não como achado (MB-76); Tabela 4 com
os R² novos e o controlador da MA.

**Considerações finais**: hipóteses retomadas uma a uma (MB-32); numeração
com os R² novos; limitação de que o modelo não prevê o futuro sozinho e a
autocorrelação residual; perspectivas atualizadas (série já estendida;
defasagem do ENSO; termos autorregressivos).

**Forma**: itálico em termos estrangeiros no texto e na lista de siglas
(MB-10 a 13, 37); Listas de Figuras e Tabelas sem bordas e com páginas
(MB-14); marcação de revisão aceita (MB-39); legenda em todas as figuras
(MB-72); todas as figuras agora ficam com a legenda acima e na mesma página
(imagens convertidas de flutuantes para em linha); "RESULTADOS E DISCUSSÃO"
corrigido; siglas NASA, NOAA, CPC e ACF acrescentadas.

## 4. O que ficou para você confirmar

1. **Fonte da precipitação**: o texto diz CHIRPS (como na Tabela 1 original).
   Se a base de Benfica et al. usou outro produto, corrigir na seção 5.2 e na
   Tabela 1.
2. **Agregação da PSN**: o texto diz que os compostos de 8 dias foram
   agregados ao mês e os pixels de cada bioma agregados espacialmente,
   "seguindo Benfica et al. (2022)". Confirmar se é soma ou média e ajustar.
3. **Referências dos dados climáticos da área de estudo** (240–1.500 mm etc.)
   (MB-35): inseri só Alvares et al. (2013) para os tipos climáticos; os
   números de chuva continuam sem fonte.
4. **Números do MapBiomas por bioma dentro da Bahia** (MB-24): o parágrafo de
   uso do solo é qualitativo; inserir os valores estaduais se quiser.
5. **Critério de Y-randomization de Guimarães et al. (2024)** (F27): o texto
   agora só diz que o critério de 60 pp foi adotado neste estudo. Conferir no
   artigo se vale citar o critério deles.
6. **Etnias indígenas** (MB-75): lista conferir com FUNAI/IBGE.
7. **Sumário**: atualizar campos no Word.
8. A decisão da seção 1 (conjunto da MA).

## 5. Correções do tutorial de revisão (segunda rodada)

Aplicadas na fonte (scripts), não no XML, e o documento foi regenerado:

1. **Datas**: as quatro comparações com a série antiga voltaram a dizer
   "2001 a 2020" (Dados; 6.2; 6.4; 6.5). A causa era uma substituição
   global no script, que foi removida. "2001 a 2025" só aparece agora onde
   descreve a base atual.
2. **Ponto solto no pé das páginas**: não eram parágrafos fantasmas, era um
   "." dentro dos rodapés do modelo original (footer2, 4, 5 e 6). O script
   agora limpa esse texto dos rodapés.
3. **Centralização das imagens**: os parágrafos de imagem e legenda herdavam
   o recuo de primeira linha (1,25 cm) do estilo Normal, o que empurrava a
   figura para a direita. Recuo zerado em todos os parágrafos com imagem e
   nas legendas.
4. **Fontes das figuras**: Figuras 6 (observado × predito) e 9 (resíduos)
   passaram a ser geradas diretamente dos dados em `Figuras_Dissertacao.py`,
   com fontes 11,5–15 pt e figuras maiores (os números reproduzem os do
   `Modelo_PSN.py`: R² fora da amostra, Shapiro-Wilk, Ljung-Box e ACF
   idênticos). Figura 5 (regressões simples) com fontes 10–15 pt, títulos
   "R²aj = …, b = …, p < 0,001", 300 dpi; Figuras 11–13 (ENSO) com fontes
   maiores; Figura 8 com fontes maiores; Figura 1 redesenhada com mais espaço
   entre as caixas e o texto vermelho quebrado em linhas curtas, sem invadir
   a caixa do NPP.
5. **Validação**: XML validado contra o esquema (sem erros); PDF renderizado
   e conferido nas páginas das Figuras 1, 2, 5 e 9 e nas quatro frases de
   datas.
