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

### Resumo/Abstract: métricas pedidas pelo Prof. Marcos (MB-7, 9, 28)
- Acrescentada uma frase curta ao Resumo e ao Abstract com R² ± desvio-padrão por bioma,
  faixa de RMSE e MAE de teste (gC·m⁻²·mês⁻¹), escala temporal (mensal) e espacial
  (agregação por bioma) e menção ao VIF atenuado pela regularização Ridge.
- Restaurados no script dois ajustes perdidos na revisão anterior: coorientadora nas
  fichas de referência (PT/EN) e quebra de página antes de "1 APRESENTAÇÃO E JUSTIFICATIVA".

## 6. Versão 7 (21/09/2026): integração da versão 6 do autor + análise do ENSO em anomalias

- Branch `claude/vigilant-goodall-0zmvla` (pipeline GEE, planilha antiga, análises) fundida nesta branch (pasta `npp_modis/`).
- 5.2 e Tabela 1: fontes reais (GEE, Coleção 6.1, MOD17A2HGF/MOD16A2GF, MOD11A2, MCD64A1, IMERG V07, IBGE 2019,
  agregação em 4 compostos, validação r > 0,97); motivo dos 3 meses excluídos (fim do IMERG V07); siglas GEE e IMERG
  (CHIRPS removido); Figura 3 (fluxo) regenerada com IMERG; 7 referências novas.
- 6.2: parágrafo novo sobre a importância das variáveis com e sem harmônicos, com números da Tabela A4 ampliada
  (R² ciclo anual, r bruto, r anomalias, importância sem/com harmônicos).
- 6.5 reescrita em anomalias mensais (`Analise_ENSO_Anomalias_PSN.py`, fase oficial): Tabela 6 (15 linhas), parágrafos
  por bioma, mediação, defasagem, Figura 14 (compósitos, 3 painéis) e Tabela A5 (valores dos boxplots).
- Resumo/Abstract (mantido o ± dp), H3, parágrafo dos objetivos e perspectivas atualizados; ferramentas (5.6) citam os testes novos.
- Correções em relação à versão 6: fases 149/76/72 (coerente com A1 e Figuras 11–13); citação da Tabela A4 corrigida;
  figuras em resolução original; Figura 14 legível; listas e sumário regenerados; sem revisões marcadas.

## 7. Versão 8 (21/09/2026): variabilidade interanual e reprodutibilidade

- Nova subseção 6.6 "Variabilidade interanual da produtividade" (Figura 15, Tabela 7) gerada por
  `Analise_Interanual_PSN.py`; "Implicações" passou a 6.7 e o Sumário ganhou a entrada nova.
  Frase de síntese acrescentada às Considerações Finais.
- `Modelo_PSN.py`: toggles por variável de ambiente e saídas com nomes fixos; `coletar_resultados.py`
  substitui o consolidador antigo (que dependia de um log fora do repositório); `reproduzir_tudo.sh`
  roda a cadeia inteira. Rodada completa refeita: reproduz as Tabelas 2 e 3 com diferença zero.

## 8. Versão 9 (22/09/2026): pente-fino de escrita, métodos e citações

Aplicado o parecer "Pente-fino da dissertação" (todos os itens, com as decisões delegadas resolvidas):

- **Métodos separados de Resultados**: ablação/importância dos harmônicos saíram da 5.2 para a nova 6.2.1;
  classificação ENSO, anomalias, testes, FDR (Benjamini-Hochberg por família), experimento de perturbação,
  defasagens e compósitos foram para a nova 5.4.1; CV, Sen/Mann-Kendall e agregação anual para a 5.4.2.
- **H1 reformulada** (sem regra prévia de grau ótimo; grau determinado empiricamente); **H3 e objetivo 4**
  incluem evapotranspiração e disponibilidade hídrica; retomada da H1 nas conclusões sem a ressalva longa.
- **"Mediação" → "experimento de perturbação baseado no modelo"** em todo o texto; Mata Atlântica reescrita
  (medianas brutas semelhantes, deslocamento negativo modesto após retirar a sazonalidade, extremos baixos).
- **6.5 reescrita em parágrafos curtos**: números sempre junto do bioma; defasagem em um parágrafo por bioma;
  episódios extremos em tabela (Tabela 7, nova); Tabela 6 com marca ‡ para significância após FDR; erro
  "terceiro mês" corrigido; citações inseridas (Cai et al. 2020; Rodrigues & McPhaden 2014; Marengo et al. 2018;
  Cunha et al. 2019; Schwinning & Sala 2004; Mendes et al. 2020, 2025; Oliveira et al. 2005; Fan et al. 2017;
  Lawson & Vialet-Chabrand 2019; D'Acunha et al. 2024; Borchert & Rivera 2001; Alberton et al. 2019; Wu et al. 2016;
  Cai et al. 2021 para as projeções do ENSO; O'Brien 2007 para os limiares de VIF; BRASIL/MMA 2017 para o PLANAVEG).
- **Validação**: "GroupKFold" passa a validação agrupada por ano; "temporal/cronológica" só para o
  TimeSeriesSplit; limiar de 60 pp retirado como critério formal; seleção não aninhada registrada como limitação;
  random_state reescrito; versões das bibliotecas e URL do repositório em 5.6.
- **Dados e modelo**: janelas de ~32 dias explicadas; critério de pixel válido e ausência de filtro por QC declarados;
  ordem do pipeline, grade de α e métrica do GridSearchCV; VIF sobre os cinco preditores originais; percentil 3
  justificado e análise de sensibilidade (0, 1, 3, 5%) na nova Tabela A6 (`Sensibilidade_Winsor_PSN.py`).
- **Tabela A4** recalculada com o mesmo procedimento da Figura 8 (Ridge com alfa médio na série completa), o que
  elimina as diferenças entre texto, figura e apêndice.
- **Redação**: BURN, grau 2, generalizações ecológicas, alerta precoce, "maior impacto", NPP "independente",
  p = 0,07 e "puxada" reescritos como sugerido; Hao et al. (2019) removido; pressões antrópicas condensadas
  (~20%); "overfitting" → sobreajuste; "Regressão Ridge" → regressão Ridge; "El Niño–Oscilação Sul" padronizado;
  "produtividade primária" restrita ao sentido genérico; citações acrescentadas na Apresentação.
- **[REF] para o autor** (7 marcas): IBGE (área e litoral), FUNAI/IBGE (etnias), Corredor Central, ZEE-BA e a
  edição/URL do PLANAVEG.

## 9. Versão 10 (22/09/2026): revisão final (oito pontos)

- **Referências no lugar de todas as marcas [REF]** (nenhuma restante), todas verificadas nas fontes oficiais:
  IBGE, *Cidades e Estados: Bahia* (2025b) para a área territorial (valor atualizado para 564.764 km², dado oficial
  vigente); SEMA-BA, *A zona costeira no Estado da Bahia* (2024) para o litoral ("mais de 1.100 km", em vez do valor
  não referenciado de 1.188 km); IBGE, *Censo Demográfico 2022: etnias e línguas indígenas* (2025a) para as etnias;
  MMA, *O Corredor Central da Mata Atlântica* (2006) para o Corredor Central; SEMA/SEPLAN-BA, *Relatório da Comissão
  Técnica do ZEE-BA* (2020) para o ZEE; PLANAVEG com a Portaria Interministerial nº 230/2017 e a página oficial do MMA.
- **Cruzamento citações ↔ lista nos dois sentidos**: Rodrigues e McPhaden (2014) passou a ser citado em 6.5
  (La Niña de 2011–2012 e seca no Nordeste); entrada INPE (não citada) removida; NASA e NOAA reposicionadas em
  ordem alfabética; entradas IBGE de 2025 diferenciadas em 2025a/2025b.
- **5.5**: apenas o TimeSeriesSplit é descrito como cronológico; o GroupKFold por ano é apresentado como validação
  agrupada (anos posteriores podem treinar anos anteriores) com o papel de cada esquema explicitado.
- **Considerações Finais**: tendência da Mata Atlântica reescrita como "tendência negativa de aproximadamente 6% em
  24 anos, não significativa ao nível de 5% (p = 0,070), embora com sinal sugestivo de declínio" (sem "marginalmente
  significativa"), em consonância com 6.6.
- **"Grau ótimo" e "conjunto ótimo" eliminados** (fundamentação, 5.3, 6.2 e conclusões): grau "selecionado/adotado"
  por "melhor compromisso entre desempenho preditivo, estabilidade e parcimônia"; conjuntos de variáveis "selecionados"
  ou "de melhor desempenho".
- **Figura 8**: legenda e texto reescritos como "índice de contribuição relativa" (descritivo, não causal), com a
  ressalva de que, como a padronização precede a expansão polinomial, termos quadráticos e de interação não têm a
  mesma escala dos lineares e o Ridge reparte o peso entre termos correlacionados. A ordem do pipeline
  (winsorização → StandardScaler → PolynomialFeatures → Ridge) foi conferida no código e **não** foi alterada; nada
  foi recalculado.
- **Varredura editorial**: "( TimeSeriesSplit)" corrigido; "produtividade primária" trocada por PSN onde o texto se
  refere aos resultados deste estudo (6.3, 6.5, conclusões), mantida no sentido genérico da literatura; abstract
  alinhado ao resumo ("PSN control", "Ridge regression"); sem "overfitting" ou "Regressão Ridge" fora das
  palavras-chave; unidades uniformes (gC·m⁻²·mês⁻¹, mm·mês⁻¹, °C).
- **Repositório**: seção "Versão citada na dissertação" no README apontando o commit desta versão (`9f6227b`) e o
  comando para criar a tag anotada `dissertacao-v10` e a *release* (o envio de tags não é permitido a partir do
  ambiente automatizado; a branch e o link citado no texto não mudam).

## 10. Versão 11 (22/09/2026): acabamento após leitura externa

- 5.2: "a TST foi mediada em cada período" → "a TST foi agregada pela média em cada período".
- 5.1 (área de estudo): citações inseridas no parágrafo do Corredor Central, PLANAVEG e ZEE
  (Brasil, 2006; Brasil, 2017; Bahia, 2020) e após a lista de povos indígenas (IBGE, 2025a).
- Apresentação: a afirmação de que abordagens flexíveis tendem a superar modelos lineares em respostas
  ecológicas passou a citar literatura ecológica/metodológica (Olden, Lawler e Poff, 2008; Pichler e Hartig,
  2023) em vez de Guimarães et al. (2024), que trata de QSAR e continua citado apenas nesse contexto.
- Pendentes de decisão do autor: folha de rosto ("Projeto de dissertação ... qualificação" vs. dissertação
  final/defesa) e eventual repositório exclusivo para a dissertação (o link atual permanece).
