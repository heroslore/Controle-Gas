# Análise dos pareceres da banca de qualificação

Dois pareceres recebidos: **Fernando (FIOCRUZ-RO)**, 30 destaques no PDF, e
**Marcos Bernardes**, 79 notas no PDF. O terceiro parecer ainda não chegou.

Como usar: cada item tem um código (**F-n** ou **MB-n**), o que o avaliador
pede, minha opinião e a **proposta de texto** (ou ação). Marque a decisão em
cada um (por exemplo, "aceito F1, F2, F5; MB-1 não; MB-3 só a parte 2").
Nenhuma alteração foi feita no `Trabalho_revisado.docx` ainda.

Legenda da coluna **Tipo**: `texto` = só redação/formatação; `cálculo` = exige
rodar algo novo ou mudar o método; `figura` = nova figura ou figura refeita;
`verificar` = depende de fonte que não tenho aqui (artigo, dado, norma).

Os números novos usados nas propostas vêm da base 2001–2025 (n = 297), já
rodada e guardada em `resultados_2001_2025/RESULTADOS.md`.

> **Atualização de 12/09/2026 (após a aprovação do Ygor):** todas as mudanças
> marcadas como válidas foram aplicadas em `Trabalho_revisado_2001_2025.docx`
> (ver `REGISTRO_DE_MUDANCAS.md`). Duas coisas mudaram em relação ao que está
> escrito abaixo: (1) a busca exaustiva de combinações com a base nova mostrou
> que, na **Mata Atlântica, o conjunto ótimo passou a ser EV + TST + WAI**
> (R² de teste 73,7 % contra 71,0 % de EV + PRE + TST), então os números da
> MA no documento final são os desse conjunto; (2) com esse conjunto, na MA o
> grau 3 tem R² de teste 0,8 pp maior que o grau 2, mas com diferença
> treino–teste 1,7 pp maior, e o grau 2 continua sendo o ótimo pelo critério
> composto. Os números de CE e CA não mudaram.

---

## Visão geral dos dois pareceres

**Fernando** lê como coautor do modelo de referência (Guimarães et al., 2024)
e como metodólogo. Os pontos dele são de três tipos:

1. **Correções sobre o que o estudo de referência fez** (F16, F18, F20, F22,
   F27). Aqui ele está descrevendo o próprio trabalho dele, então o texto da
   dissertação está errado nesses trechos e precisa ser reescrito. Mas o que
   vai no texto tem de ser conferido no artigo, não só no comentário.
2. **Falta de transparência sobre treino/teste e dados** (F19, F21, F26,
   F28, F29). Pede os percentuais, quem é teste, e a tabela de dados. Tudo
   resolvível com texto e um apêndice.
3. **Fundamentação didática** (F1–F6, F9, F12, F15, F17, F25): explicar PSN,
   MODIS, QSAR, winsorização, mostrar a equação de grau > 1 e um esquema da
   validação cruzada.

Ele também levanta duas dúvidas técnicas sobre a sazonalidade (F13, F14) que,
na minha leitura, são mal-entendidos que o texto atual permite. A resposta é
explicar melhor, não mudar o método.

**Marcos Bernardes** lê como leitor não especialista e revisor de forma. Os
pontos dele:

1. **Resumo/abstract** incompleto e inconsistente com a metodologia (MB-1,
   4, 5, 7, 8, 9, 28, 48, 49, 50, 57, 65, 79). Resolve-se reescrevendo o
   resumo uma vez, no fim, com os números novos. Proposta completa abaixo.
2. **Linguagem acessível** e termos sem definição (MB-2, 5, 17, 25, 27, 36,
   43, 44, 52, 66, 71, 73). Cada um tem proposta de frase.
3. **Estrutura**: metodologia dentro da fundamentação (MB-20, 21, 22, 42,
   61), objetivos misturados com método (MB-33, 34), área de estudo curta
   demais (MB-15, 63, 77, 78).
4. **Formatação** (itálico, linhas de tabela, legenda, marcações de revisão):
   MB-10 a 14, 39, 40, 59, 72.
5. **Perguntas de mérito**: defasagem e intensidade do ENSO (MB-3, 74),
   ONI trimestral vs. mensal (MB-41), n = 240 (MB-53), semente 42 (MB-54),
   eucalipto como especulação (MB-76), hipóteses verificadas no fim (MB-32).

**Conflito entre os dois** que você precisa decidir: Fernando quer a
descrição da área de estudo **na introdução** (F10); Marcos quer a seção
**Área de Estudo ampliada** (MB-15, 63, 77, 78). Minha recomendação está em
F10.

---

## Parecer 1 — Fernando

### Fundamentação (Introdução e Fundamentação Teórica)

**F1** (p. 8) — *"Explicar o que é a fotossíntese líquida. Talvez um gráfico
explicativo... qual a teoria atual vigente."* Tipo: texto + figura.
Opinião: concordo. A definição atual aparece em uma frase. Proposta: novo
parágrafo na Fundamentação e uma figura conceitual (posso gerar).

> A fotossíntese bruta corresponde a todo o carbono que as plantas retiram
> da atmosfera pela fotossíntese (Produtividade Primária Bruta, GPP). Parte
> desse carbono é consumida imediatamente pela respiração das folhas e das
> raízes finas para manter os tecidos vivos. O que sobra é a **Fotossíntese
> Líquida (PSN)**: o carbono que a vegetação efetivamente acumula em escala
> de dias a semanas. Se, além disso, forem descontadas a respiração de
> manutenção dos demais tecidos (lenho, raízes grossas) e a respiração de
> crescimento, chega-se à Produtividade Primária Líquida (NPP), que é
> calculada anualmente. Em termos de fluxo: GPP → PSN → NPP, cada etapa
> descontando uma parcela de respiração (Figura X).

Figura X proposta: diagrama em blocos GPP → (− respiração de folhas e raízes
finas) → PSN → (− respiração de manutenção do lenho e de crescimento) → NPP,
com a indicação de qual produto MODIS fornece cada termo.

**F2** (p. 9) — *"O que é forçamento?"* Tipo: texto. Opinião: concordo; o
termo vem do inglês *forcing*. Proposta: trocar "a resposta deixa de ser
proporcional ao forçamento" por "a resposta deixa de ser proporcional à
forçante, isto é, ao fator externo que a provoca (por exemplo, o aumento da
temperatura ou a redução da chuva)". Manter "forçante" no resto do texto,
definido nesta primeira ocorrência.

**F3, F6** (p. 10) e **MB-19, MB-26, MB-38** — explicar MODIS, MOD17A2H e a
agência espacial na primeira menção. Tipo: texto. Opinião: concordo com os
dois avaliadores; é o dado central e não está explicado. Proposta, a inserir
antes da primeira menção a "MODIS/MOD17" na Fundamentação:

> O MODIS (*Moderate Resolution Imaging Spectroradiometer*) é um sensor
> orbital da NASA a bordo dos satélites Terra (lançado em 1999) e Aqua
> (2002). Ele observa toda a superfície terrestre a cada um ou dois dias, em
> 36 bandas espectrais e resoluções de 250 m a 1 km. A partir dessas imagens,
> a NASA gera produtos derivados, identificados por códigos: o MOD17A2H
> estima a Produtividade Primária Bruta (GPP) e a Fotossíntese Líquida (PSN)
> em compostos de oito dias e resolução de 500 m; o MOD16A2 estima a
> evapotranspiração real e potencial; o MOD11A2, a temperatura da superfície
> terrestre; e o MCD64A1, a área queimada mensal. Todos são distribuídos
> gratuitamente pelo portal NASA Earthdata.

**F4, F5** (p. 10) — *"subtrair, adicionalmente? reescrever"* e a equação
que ele propõe. Tipo: texto. Opinião: a frase está confusa e o avaliador
saiu com a equação errada (ele escreveu PSN = GPP − Resp − NPP, o que não é o
caso). Isso mostra que o texto precisa das equações explícitas. Proposta,
substituindo a frase "a Produtividade Primária Líquida (NPP) é obtida ao
subtrair, adicionalmente, ...":

> As três grandezas se relacionam por
> PSN = GPP − R_m(folhas) − R_m(raízes finas)
> NPP = PSN − R_m(lenho e raízes grossas) − R_g
> em que R_m é a respiração de manutenção e R_g a respiração de crescimento.
> A PSN é, portanto, um saldo intermediário entre a GPP e a NPP: desconta a
> respiração dos tecidos de vida curta, mas ainda não a dos tecidos lenhosos
> nem o custo de construir biomassa nova.

**F7** (p. 10) — *"Não estou vendo evidência de que o balanço hídrico exerce
controle no Cerrado. Deveria trazer algum dado para comparação."* Tipo:
texto (usa resultado que já temos). Opinião: concordo; o parágrafo cita
valores de GPP de Vourlitis et al. mas não mostra controle hídrico. Temos o
dado: a regressão simples PSN × variáveis (figura de dispersão) e o
Kruskal-Wallis. Proposta, acrescentar ao fim do parágrafo:

> Nos dados deste estudo esse controle é direto: no Cerrado baiano, a
> evapotranspiração explica sozinha 75% da variância mensal da PSN e o
> índice de disponibilidade hídrica (WAI) 74% (regressões simples, n = 297,
> p < 0,001), contra 59% da temperatura e 8% da precipitação do mês (Figura
> Y). A produtividade média mensal cai de cerca de 123 mm de chuva nos
> meses de La Niña para 59 mm nos meses neutros, com queda concomitante de
> EV (Tabela Z). Já na Mata Atlântica, a evapotranspiração explica apenas
> 13% da variância da PSN.

(Figura Y = `dispersao_psn_variaveis_biomas.png`, que Marcos também pede em
MB-58.)

**F8** (p. 12) — *"A vegetação de pasto transpira menos que árvores nativas?
mas o pasto tem mais folhas não?"* Tipo: texto. Opinião: a afirmação da
dissertação está correta, mas precisa do mecanismo. Pastagem tem raízes
rasas e perde área foliar na seca; a floresta/savana nativa acessa água
profunda e mantém transpiração no período seco. Proposta, acrescentar após
a citação de Dionizio et al. (2020):

> A redução ocorre porque as gramíneas das pastagens têm sistema radicular
> raso e perdem grande parte da área foliar na estação seca, enquanto a
> vegetação nativa, com raízes profundas, continua acessando a água do
> subsolo e transpirando ao longo do ano. Assim, embora o pasto possa ter
> índice de área foliar comparável no auge da estação chuvosa, sua
> evapotranspiração anual é menor, sobretudo nos meses secos.

Vale acrescentar uma referência de campo (por exemplo, medições de fluxo em
pasto × floresta). Não incluí citação para não inventar; você escolhe.

**F9** (p. 13) — explicar o que é QSAR. Tipo: texto. Opinião: concordo.
Proposta, na primeira menção:

> ...originalmente aplicada à predição quantitativa estrutura-atividade
> (QSAR), isto é, modelos que preveem a atividade biológica de uma molécula
> (no caso, o índice de inibição de atividade celular de compostos
> antimaláricos) a partir de características estruturais de moléculas
> sabidamente inibidoras e não inibidoras.

**F10** (p. 16) — *"Tudo isto aqui deve ser colocado na introdução."* (a
seção Área de Estudo). Tipo: estrutura. **Conflita com MB-15/63/77/78**, que
querem essa seção maior. Opinião: manter a seção "Área de Estudo" dentro da
Metodologia, como é padrão em dissertações, e **ampliá-la** conforme
Marcos; na Introdução, deixar só um parágrafo de contextualização
(a Bahia reúne três biomas com regimes distintos, o que motiva a comparação).
Isso atende ao espírito dos dois. Se preferir seguir Fernando ao pé da letra,
o custo é a seção de método ficar sem descrição da área, o que Marcos
criticaria. Decisão sua.

### Dados

**F11** (p. 17) — *"'bases climáticas regionais'. Quais? Não pode haver
indefinições."* Tipo: texto + verificar. Opinião: concordo. Proposta:
substituir por a lista exata. Pelo que consta na lista de siglas, seria:

> ...majoritariamente do sensor MODIS (PSN pelo MOD17A2H; evapotranspiração
> real e potencial pelo MOD16A2; temperatura da superfície pelo MOD11A2;
> área queimada pelo MCD64A1), complementados pela precipitação do produto
> CHIRPS (*Climate Hazards Group InfraRed Precipitation with Station data*)
> e pelo Índice Oceânico Niño (ONI) do Climate Prediction Center da NOAA.

**Preciso que você confirme a fonte da precipitação.** A lista de siglas
cita CHIRPS, mas o script diz que os meses recentes de chuva "ainda não
foram publicados pela NASA", o que sugere outro produto (GPM/IMERG?). O texto
tem de dizer o que foi realmente usado.

**F12** (p. 18) — *"Explicar se conseguimos acessar esses dados por web ou
necessitamos de acesso específico."* Tipo: texto. Opinião: concordo.
Proposta: acrescentar à Tabela 1 uma coluna "Fonte / acesso" e a frase:

> Todos os produtos são de acesso público e gratuito: os produtos MODIS pelo
> portal NASA Earthdata (ou pelas plataformas AppEEARS e Google Earth
> Engine), o CHIRPS pelo servidor da Universidade da Califórnia em Santa
> Bárbara e o ONI pela página do Climate Prediction Center da NOAA. A base
> mensal consolidada usada neste estudo e o código-fonte estão disponíveis
> em [repositório], permitindo reprodução integral dos resultados.

**F13** (p. 19) — *"se sin + cos, então nos meses 1 e 2 os valores serão
maiores que 1 (1,37) e nos meses 7 e 8 menores que −1."* Tipo: texto.
Opinião: é um mal-entendido que o texto permite. As duas componentes **não
são somadas em uma variável**; entram no modelo como **duas colunas
separadas**, cada uma entre −1 e +1, com coeficiente próprio. A combinação
β₁·sin + β₂·cos que o modelo estima é exatamente o que permite representar
qualquer ciclo anual com amplitude e fase livres. Proposta, logo após a
equação:

> As duas componentes entram no modelo como preditores distintos, cada um
> variando entre −1 e +1 ao longo do ano, e não como uma soma. Ao estimar um
> coeficiente para cada uma, o modelo ajusta livremente a amplitude e a fase
> do ciclo anual, pois β₁·saz_sin + β₂·saz_cos equivale a A·sin(2π·mês/12 + φ),
> com amplitude A e defasagem φ determinadas pelos dados.

**F14** (p. 19) — *"em contrapartida pode fornecer sazonalidades
artificiais, não?"* Tipo: texto. Opinião: não, porque os coeficientes são
estimados (e encolhidos pelo Ridge): se não houver ciclo anual nos dados, os
coeficientes tendem a zero. Mas o texto deve dizer isso. Proposta,
continuando o parágrafo acima:

> Essa parametrização não impõe sazonalidade ao modelo: a amplitude A é
> estimada a partir dos dados e, na ausência de ciclo anual, os coeficientes
> das duas componentes tendem a zero, tendência reforçada pela penalização
> L2 da regressão Ridge.

**F15** (p. 19) e **MB-43, MB-44** — explicar a winsorização e o percentil 3.
Tipo: texto. Opinião: concordo com os três comentários. Proposta, substituir
o parágrafo:

> Para reduzir a influência de meses com produtividade excepcionalmente
> baixa (por exemplo, após grandes queimadas ou secas severas) sobre a
> estimação dos coeficientes, a variável resposta foi submetida a
> winsorização unilateral inferior durante o treinamento. Winsorizar
> significa substituir os valores abaixo de um limite pelo próprio valor do
> limite, em vez de excluí-los. O limite adotado foi o percentil 3 da PSN do
> conjunto de treino, isto é, o valor abaixo do qual estão os 3% menores
> meses; em uma amostra de cerca de 240 meses de treino, isso afeta apenas
> os sete valores mais baixos. O percentil foi calculado exclusivamente com
> os dados de treino de cada partição e aplicado só a eles; os valores de
> teste permaneceram na escala original, para que a avaliação fosse feita
> sobre observações não modificadas e sem vazamento de informação.

### Especificação do modelo

**F16, F20** (p. 20–21) — *"o modelo de Guimarães também foi feito
empiricamente até o grau 8"* e *"não foi fixado... está errado!"* Tipo:
texto + verificar no artigo. Opinião: aceitar; ele está corrigindo a
descrição do próprio trabalho. Proposta para a adaptação (ii):

> (ii) comparação sistemática dos graus polinomiais 1 a 5, seguindo o mesmo
> princípio de determinação empírica do grau adotado por Guimarães et al.
> (2024), que avaliaram graus até 8; neste estudo o limite superior foi
> reduzido para 5 porque, com cerca de 300 observações e cinco preditores,
> graus superiores geram centenas de termos e sobreajuste severo;

E na p. 21: trocar "em substituição à fixação prévia do grau 4 adotada no
estudo de referência" por "como no estudo de referência".

**F17** (p. 20) — *"faltou a representação do grau > 1."* Tipo: texto
(equação). Opinião: concordo. A equação geral está lá, mas sem a forma do
grau 2 realmente usado. Proposta, após a equação geral:

> Para o grau N = 2 e cinco preditores X₁…X₅, a expansão gera 20 termos
> além do intercepto:
> Ŷ = β₀ + Σᵢ βᵢXᵢ + Σᵢ βᵢᵢXᵢ² + Σᵢ<ⱼ βᵢⱼXᵢXⱼ
> (5 termos lineares, 5 quadráticos e 10 interações entre pares). Para o
> grau N genérico, o número de termos é C(5+N, N) − 1: 20 no grau 2, 55 no
> grau 3, 125 no grau 4 e 251 no grau 5.

**F18** (p. 21) — *"para verificar a colinearidade é feito um
pré-processamento... df.corr()... as com correlação repetida são
excluídas."* Tipo: texto + verificar. Opinião: ele descreve o que o estudo
de referência fez, e nós fizemos algo equivalente (excluímos a PET por
correlação de 0,73–0,80 com a TST). Proposta: dizer isso explicitamente na
seção de dados:

> Antes da modelagem, a matriz de correlação de Pearson entre as candidatas
> foi examinada para eliminar redundâncias, como no protocolo de Guimarães
> et al. (2024). A evapotranspiração potencial (PET) foi excluída nessa
> etapa por sua correlação de 0,73 a 0,80 com a temperatura da superfície na
> Mata Atlântica e na Caatinga. As variáveis restantes foram então
> submetidas ao diagnóstico de VIF descrito adiante.

**F19, F21, F28** (p. 21, 26) — *"Qual a % de separação treino/teste? Em
nenhum momento se fala"*, *"quantos e quais são treino e teste"*, *"Quem é o
grupo de teste?"* Tipo: texto. Opinião: concordo; é a falha mais objetiva
do capítulo. Proposta, na seção de validação:

> Em cada partição do RepeatedKFold (5 *folds*), 80% das observações
> compõem o treino e 20% o teste: com n = 297, cerca de 238 meses de treino
> e 59 de teste. As 30 repetições reembaralham a divisão, de modo que cada
> mês da série é usado como teste exatamente 30 vezes e como treino 120
> vezes ao longo das 150 partições. Não há, portanto, um único conjunto de
> teste fixo: as métricas reportadas são médias sobre as 150 partições,
> e o R² "fora da amostra" da Figura 3 usa a predição de cada mês feita
> pelo modelo que não o viu no treino. Nas validações temporais, o teste é
> formado por anos inteiros (GroupKFold, 5 grupos de 5 anos) ou pelo bloco
> final da série (TimeSeriesSplit, 5 blocos sucessivos).

**F22** (p. 22) — *"Errado de novo. Foram testados mais de 400 variáveis com
combinações de 3."* Tipo: texto + verificar. Opinião: aceitar a correção
sobre o estudo de referência. Proposta: trocar "Diferentemente do estudo de
referência, que adotou seleção a priori dos descritores" por:

> Seguindo a lógica de busca combinatória do estudo de referência, que
> avaliou mais de 400 descritores moleculares em combinações de três,
> a presente abordagem...

**F23** (p. 22) — *"a alta generalização é determinada pelo R² no grupo de
teste."* Tipo: texto. Proposta: "...evitando-se a escolha de modelos com
R² de treino elevado mas R² de teste baixo, pois é o R² no conjunto de
teste que mede a capacidade de generalização."

**F24** (p. 22) — *"sazsin e sazcos são correções. Deveriam ser fixas e as
combinações entre as outras 5?"* Tipo: texto (não precisa recalcular).
Opinião: concordo, é mais limpo. E não muda resultado: os três conjuntos
ótimos já continham as duas componentes, e as combinações de 5 entre 7 que
incluem ambas são exatamente as C(5,3) = 10 combinações de três entre EV,
PRE, TST, WAI e BURNlog, todas já avaliadas. Proposta:

> As duas componentes harmônicas de sazonalidade foram mantidas fixas em
> todos os modelos, por representarem o ciclo anual e não um controle
> ambiental. A seleção incidiu sobre as cinco variáveis ambientais
> candidatas (EV, PRE, TST, WAI e BURNlog), avaliando-se todas as C(5,3) = 10
> combinações de três variáveis por bioma, cada uma sob o mesmo protocolo de
> validação cruzada.

Atualizar também os trechos "C(7,5) = 21" nos Resultados.

**F25** (p. 23) e **MB-45** — esquema gráfico da divisão treino/teste e da
metodologia. Tipo: figura. Opinião: concordo. Proposta: nova figura
"Esquema da validação cruzada RepeatedKFold (5 × 30) e das validações
temporais", que posso gerar em Python, e antecipar a Figura 2 (fluxo
metodológico) para o início do capítulo (MB-55).

**F26, F29** (p. 24, 26) — *"onde estão estes dados?"* e *"mostrar a tabela
com os dados"*. Tipo: apêndice. Opinião: concordo. Proposta: Apêndice A com
a tabela mensal completa (297 linhas × ano, mês, ONI, fase ENSO e as 15
variáveis por bioma), gerada automaticamente da base, mais o link do
repositório. Posso gerar a tabela formatada.

**F27** (p. 25) — *"Não foi isso [o critério de 60 pp]. Foi feita a média
dos modelos permutados... existe um critério de que não pode haver diferença
entre os dois R² maior que 30%."* Tipo: texto + **verificar no artigo**.
Opinião: aceitar que a descrição do critério de Guimarães está errada, mas
o critério exato tem de ser lido no artigo (o comentário é ambíguo sobre
quais R² são comparados). Proposta de redação que não atribui o critério de
60 pp ao artigo:

> Adotaram-se dois critérios de validação. O primeiro, seguindo Guimarães et
> al. (2024), compara o R² de validação cruzada do modelo original com a
> média dos R² dos 100 modelos permutados; neste estudo exigiu-se diferença
> mínima de 60 pontos percentuais, limiar mais conservador que o do estudo
> de referência [confirmar]. O segundo é o p-valor empírico unilateral...

**F30** (p. 29) — *"grau 2 ótimo para os três biomas: não para a Caatinga."*
Tipo: cálculo (já rodado). Opinião e resultado: ver a seção "Comparação de
graus com a base nova", no fim deste documento.

---

## Parecer 2 — Marcos Bernardes

### Resumo e Abstract (MB-1, 4, 5, 6, 7, 8, 9, 28, 48, 49, 50, 57, 65, 79)

Todos esses itens se resolvem com um resumo novo. Pontos que ele exige:
frase de abertura sobre modelos de regressão em fenômenos naturais (MB-1);
contribuição acadêmica principal (MB-4); linguagem simples e em português
(MB-5, 6); citar todas as métricas e diagnósticos usados, com média e
desvio-padrão (MB-7, 9, 48, 49, 50, 57); escalas temporal e espacial
(MB-28); síntese da tipologia da Tabela 4 (MB-65); parte das implicações
para planejamento (MB-79); e normas do PPGCTA (MB-8, que você confere).

Proposta de novo RESUMO (com os números da base 2001–2025):

> Modelos de regressão são amplamente empregados para descrever fenômenos
> naturais a partir de variáveis mensuráveis, mas os modelos lineares
> convencionais não representam bem respostas ecológicas com limiares e
> interações. Este estudo desenvolveu e validou um Modelo de Regressão
> Múltipla Polinomial de ordem N (MRMP-N), estimado por regressão Ridge,
> para explicar a Fotossíntese Líquida (PSN), o carbono acumulado
> mensalmente pela vegetação, nos biomas Mata Atlântica, Cerrado e Caatinga
> da Bahia, em escala mensal, de 2001 a 2025 (297 meses por bioma). A PSN, a
> evapotranspiração, a temperatura da superfície e a área queimada foram
> obtidas de produtos do sensor orbital MODIS (NASA), a precipitação do
> produto [CHIRPS/confirmar] e o Índice Oceânico Niño (ONI) da NOAA. O grau
> do polinômio (1 a 5) e o conjunto de três variáveis ambientais, somadas a
> duas componentes de sazonalidade, foram escolhidos empiricamente. O
> desempenho foi medido pelo coeficiente de determinação (R²), pela raiz do
> erro quadrático médio (RMSE) e pelo erro absoluto médio (MAE), reportados
> como média e desvio-padrão em 150 partições de validação cruzada, e
> confirmado por validação temporal (anos inteiros e blocos cronológicos),
> diagnóstico de multicolinearidade (VIF), análise de resíduos
> (normalidade e autocorrelação) e teste de Y-randomization com 100
> permutações. O modelo de grau 2 explicou 96,7% da variância da PSN no
> Cerrado (RMSE 6,7 gC·m⁻²·mês⁻¹), 94,2% na Caatinga (RMSE 6,7) e 71,0% na
> Mata Atlântica (RMSE 8,4), com diferença entre treino e teste inferior a
> 1,1 ponto percentual nos dois primeiros e de 5,1 na Mata Atlântica. Os
> resultados definem três regimes de controle da produtividade: hídrico no
> Cerrado, em que a evapotranspiração e a disponibilidade hídrica dominam;
> pulsado na Caatinga, com resposta imediata à chuva; e multifatorial na
> Mata Atlântica, em que fatores de paisagem não climáticos reduzem a
> previsibilidade. O ENSO, analisado por fases oficiais (El Niño, La Niña e
> Neutro, sem defasagem) e pela intensidade do ONI, alterou a temperatura
> nos três biomas e a chuva no Cerrado e na Caatinga, mas explicou menos de
> 3% da variância dessas variáveis e afetou diretamente a PSN apenas na
> Caatinga. A principal contribuição do trabalho é um protocolo
> reprodutível de regressão polinomial regularizada para variáveis
> ambientais, com validação temporal explícita, que fornece critérios
> objetivos para priorizar conservação da disponibilidade hídrica no
> Cerrado, restauração da paisagem na Mata Atlântica e monitoramento
> contínuo por satélite na Caatinga.

Observações: (a) "gap de overfitting" foi trocado por "diferença entre
treino e teste" em todo o resumo, atendendo MB-6; (b) o abstract seria a
tradução direta; (c) confirmar o limite de palavras do PPGCTA (MB-8).

### Linguagem e definições (MB-2, 17, 25, 27, 36, 52, 66, 71, 73)

**MB-2 / MB-36** — *"resposta pulsada", "heterogeneidade estrutural": o que
é isso?* Proposta de definição na primeira ocorrência:
- "resposta pulsada aos eventos de precipitação, isto é, aumentos rápidos
  da produtividade logo após cada chuva, seguidos de queda igualmente
  rápida na estiagem";
- "heterogeneidade estrutural da paisagem, ou seja, o mosaico de
  fragmentos florestais, pastagens, plantios de eucalipto e áreas urbanas
  que compõe a Mata Atlântica baiana".

**MB-17** (p. 8) — *"Favor traduzir"* ("estratégias de gestão subótimas").
Proposta: "e, consequentemente, a decisões de gestão ambiental menos
eficazes do que poderiam ser".

**MB-25** (p. 13) — definir ONI na primeira menção. Proposta: "o Índice
Oceânico Niño (ONI), medida oficial da NOAA para o ENSO, que corresponde à
anomalia média de três meses da temperatura da superfície do mar na região
central do Pacífico equatorial (Niño 3.4)".

**MB-27** (p. 13) — "traduzir" o parágrafo sobre penalização L2. Proposta,
substituindo o parágrafo:

> A primeira é o uso da regressão Ridge no lugar dos mínimos quadrados
> ordinários. Quando se criam termos quadráticos e de interação a partir de
> variáveis que já são correlacionadas entre si (por exemplo,
> evapotranspiração e disponibilidade hídrica), o modelo passa a ter
> muitas variáveis que carregam quase a mesma informação. Na regressão
> clássica isso torna os coeficientes instáveis: pequenas mudanças nos
> dados produzem coeficientes muito diferentes. A regressão Ridge acrescenta
> uma penalidade que impede os coeficientes de crescerem demais, trocando um
> pequeno viés por muito mais estabilidade, o que a torna adequada a
> preditores correlacionados.

**MB-52** (p. 24) — "traduzir" *"artefato de vazamento por autocorrelação
temporal"*. Proposta: "...evidência de que o bom desempenho não decorre
apenas de meses vizinhos, muito parecidos entre si, terem caído ao mesmo
tempo no treino e no teste".

**MB-66** (p. 34) — *"biomas climaticamente limitados": o que são?*
Proposta: "biomas climaticamente limitados, isto é, aqueles em que a
produtividade é controlada principalmente pela água ou pela temperatura,
como o Cerrado e a Caatinga".

**MB-71** (p. 35) — *"memória temporal": o que é?* Proposta: "memória
temporal não modelada, ou seja, a produtividade de um mês depende em parte
das condições dos meses anteriores (por exemplo, a água acumulada no solo),
efeito que preditores do mesmo mês não capturam".

**MB-73** (p. 36) — "Boiei" no parágrafo do Y-randomization. Proposta de
reescrita (números novos):

> O teste de Y-randomization responde a uma pergunta simples: o modelo
> encontraria um ajuste parecido se a PSN fosse embaralhada ao acaso? Para
> isso, a coluna da PSN foi permutada 100 vezes e, a cada vez, o modelo foi
> reajustado e avaliado por validação cruzada. Os modelos com dados
> embaralhados tiveram R² médio negativo (−10% na Mata Atlântica, −11% no
> Cerrado e −13% na Caatinga), ou seja, previram pior do que a simples
> média, enquanto os modelos reais alcançaram 71%, 97% e 94%. A diferença
> (81, 108 e 107 pontos percentuais) supera com folga o mínimo de 60
> adotado, e nenhuma das 100 permutações igualou o modelo real (p = 0,0099).
> Conclui-se que o desempenho reflete relação genuína entre clima e PSN, não
> coincidência numérica (Figura 7).

### Estrutura (MB-20, 21, 22, 42, 61, 33, 34, 55)

**MB-20, 21, 22** (p. 10) — detalhes do produto MOD17A2H estão na
Fundamentação, "com menos informação que o mínimo". Tipo: estrutura.
Opinião: concordo. Proposta: na Fundamentação, manter só a definição
conceitual de GPP/PSN/NPP (ver F1/F4); mover a frase "fornecida em escala
de oito dias pelo produto MOD17A2H" para Dados, ampliada: "produto MOD17A2H,
versão 6.1, compostos de 8 dias, resolução de 500 m, agregados à escala
mensal pela média espacial dos pixels de cada bioma dentro da Bahia".
**Confirmar com você como foi feita a agregação mensal e espacial** (soma
dos compostos de 8 dias? média dos pixels? qual máscara de bioma?), pois
Marcos cobra exatamente isso.

**MB-42** (p. 19) — a descrição da distribuição da área queimada "já é
resultado". Proposta: reescrever como justificativa de pré-processamento:
"Como a área queimada mensal tem muitos zeros e alguns picos muito altos,
aplicou-se a transformação log(1 + x) antes da modelagem, procedimento
usual para esse tipo de variável."

**MB-61** (p. 32) — definição do WAI deve estar na Metodologia. Proposta:
mover a frase "razão entre a evapotranspiração real e a potencial
(ETR/ETP)..." para a Tabela 1 e o texto de Dados; nos Resultados, manter só
"o WAI (definido na seção 5.2)".

**MB-33** (p. 15) — *"Ecossistemas ou biomas? Parece haver mais de um
objetivo geral."* Proposta de objetivo geral único:

> Desenvolver e validar um Modelo de Regressão Múltipla Polinomial de ordem
> N (MRMP-N), estimado por regressão Ridge, para quantificar a influência de
> variáveis ambientais sobre a Fotossíntese Líquida nos biomas Mata
> Atlântica, Cerrado e Caatinga da Bahia.

**MB-34** (p. 15) — metodologia misturada nos objetivos específicos.
Proposta de objetivos específicos sem nomes de técnica:

> 1. Determinar empiricamente o grau polinomial e o conjunto de variáveis
>    ambientais de melhor desempenho preditivo em cada bioma.
> 2. Avaliar a robustez e a capacidade de generalização do modelo,
>    inclusive sob validação que respeita a ordem cronológica dos dados.
> 3. Comparar o desempenho e os controles ambientais da PSN entre os três
>    biomas.
> 4. Investigar a influência do ENSO sobre a PSN e sobre as variáveis
>    climáticas intermediárias nos três biomas.

**MB-55** (p. 26) — antecipar a Figura 2 (fluxo metodológico) para o começo
do capítulo. Aceitar.

### Hipóteses e objetivos (MB-29, 30, 31, 32)

**MB-29** — "produtividade" → "produtividade primária, medida pela
Fotossíntese Líquida". Aceitar.

**MB-30** — o que é grau "ótimo"? Proposta em H1: "...com o grau ótimo
definido como aquele que maximiza o R² de teste mantendo a diferença
treino–teste abaixo de 10 pontos percentuais".

**MB-31** — "parcela significativa" → quantificar. Proposta: "explicará
pelo menos 60% da variância mensal da PSN em cada bioma". Com a base nova
(71%, 97%, 94%) a hipótese se confirma nos três.

**MB-32** — as hipóteses são verificadas no fim? Hoje não explicitamente.
Proposta: parágrafo nas Considerações Finais, "Retomando as hipóteses":

> H1 confirmou-se, com ressalva: o grau 2 superou o grau 1 nos três biomas
> (ganho de 5,2, 6,6 e 1,3 pontos de R² de teste em MA, CE e CA), mantendo a
> diferença treino–teste abaixo de 10 pontos; na Caatinga o ganho foi
> marginal. H2 confirmou-se: o
> modelo explicou entre 71% e 97% da variância, e o conjunto ótimo diferiu
> entre biomas (WAI no lugar da TST no Cerrado). H3 confirmou-se: o ONI
> explicou no máximo 3% da variância das variáveis climáticas e, apesar de
> alterar a temperatura nos três biomas, só se associou a diferenças diretas
> da PSN na Caatinga.

### Área de estudo (MB-15, 16, 24, 35, 63, 75, 77, 78)

**MB-15, 63, 77, 78** — ampliar a seção: hidrografia (nascentes do São
Francisco e bacias regionais), Corredor Central da Mata Atlântica,
iniciativas de restauração, uso do solo por bioma. Tipo: texto + verificar
fontes. Opinião: concordo; e isso resolve o conflito com F10 (ver acima).
Proposta: mover para a Área de Estudo os trechos que hoje estão na Discussão
(nascentes do Cerrado; Corredor Central; PLANAVEG/ZEE-BA) e acrescentar um
parágrafo sobre uso do solo com dados do MapBiomas por bioma dentro da Bahia
(MB-24). Preciso que você levante os números estaduais no MapBiomas; não vou
inventá-los.

**MB-16** — "A região da Bahia" → "O estado da Bahia". Aceitar.

**MB-35** — referências para os dados climáticos (240–1.500 mm etc.). Você
precisa indicar a fonte (INEMA, SEI-BA, Alvares et al. 2013?).

**MB-75** — *"Muito mais etnias do que Pataxó."* Proposta: "abriga povos
indígenas de diversas etnias (entre elas Pataxó, Pataxó Hã-Hã-Hãe,
Tupinambá, Kiriri, Tuxá, Pankararé, Truká e Kaimbé), comunidades
quilombolas e agricultores familiares". Conferir a lista com a FUNAI/IBGE.

### Método e mérito (MB-3, 41, 53, 54, 56, 58, 60, 70, 74, 76)

**MB-3 / MB-74** — *"Para ENSO: fases? Com ou sem defasagem? Foram
consideradas as intensidades do ONI?"* Tipo: texto (+ cálculo opcional).
Opinião: o que existe hoje é sem defasagem, com fases categóricas e com a
intensidade via ONI contínuo (a regressão ONI → variáveis). Isso deve ser
dito claramente. Proposta (Metodologia):

> A influência do ENSO foi avaliada de duas formas complementares, ambas
> sem defasagem temporal (mês a mês): (i) comparando a PSN e as variáveis
> climáticas entre as fases El Niño, La Niña e Neutro, classificadas pelo
> critério oficial da NOAA (ONI ≥ +0,5 ou ≤ −0,5 °C por pelo menos cinco
> trimestres móveis consecutivos), pelo teste de Kruskal-Wallis; e (ii)
> usando a intensidade do ONI como variável contínua em correlação de
> Pearson e regressão linear simples com cada variável climática.

Extra opcional (cálculo): posso acrescentar uma análise de defasagem
(correlação do ONI com a PSN com atraso de 0 a 6 meses). Responderia
diretamente ao "com ou sem defasagem" com um resultado, não só com uma
declaração. Leva minutos.

**MB-41** (p. 19) — *"O ONI é trimestral; como conciliar com dados
mensais?"* Proposta:

> O ONI é publicado pela NOAA como média móvel de três meses (por exemplo,
> DJF, JFM), atribuída ao mês central do trimestre. Cada mês da série
> recebeu, portanto, o valor do trimestre centrado nele (janeiro = DJF,
> fevereiro = JFM, e assim por diante), o que mantém a resolução mensal sem
> interpolação.

**MB-53** (p. 24) — *"Por que n = 240?"* Com a base nova: "n = 297 meses,
de janeiro de 2001 a setembro de 2025; os três últimos meses de 2025 foram
excluídos por ainda não haver dado de precipitação publicado".

**MB-54** (p. 25) — *"Por que random_state = 42?"* Proposta: "O valor da
semente é arbitrário (42 é uma convenção difundida na comunidade Python);
qualquer valor fixo garante que as partições e permutações sejam
reproduzíveis exatamente. O resultado não depende do valor escolhido."

**MB-56** (p. 27) — *"Como foi estimada a PSN observada? Pelo MODIS?"*
Proposta: em toda a dissertação, trocar "PSN observada" por "PSN de
referência (produto MODIS MOD17A2H)" na primeira ocorrência de cada seção e
explicar na Metodologia que a "observação" é ela própria uma estimativa por
satélite.

**MB-58** (p. 28) — *"Onde podemos encontrar a análise PSN × variáveis
preditoras?"* Proposta: incluir a figura de dispersão (15 painéis, já
gerada: `dispersao_psn_variaveis_biomas.png`) como nova figura no início
dos Resultados, com a tabela de R² ajustado e inclinação por variável.
Atende também F7.

**MB-60** (p. 31) — incluir trabalhos que corroboram (limitação hídrica no
Cerrado). Você já cita Bucci et al. (2008) e Arruda et al. (2016) no
parágrafo anterior; basta repeti-los após a afirmação e, se quiser,
acrescentar Vourlitis et al. (2022), já citado na Fundamentação.

**MB-70** (p. 35) — Ljung-Box não está na Metodologia. Proposta, na análise
de resíduos:

> A normalidade dos resíduos foi avaliada pelo teste de Shapiro-Wilk e a
> autocorrelação temporal pelo teste de Ljung-Box com 12 defasagens, além
> da função de autocorrelação (ACF) nas três primeiras defasagens.

**MB-76** (p. 40) — *"Como isolar o efeito do eucalipto ou da fragmentação?
Ou são especulações?"* Opinião: ele tem razão; o modelo não testou isso.
Proposta: trocar "revela a influência da expansão da monocultura de
eucalipto e da fragmentação" por "é compatível com a hipótese de que
fatores de paisagem, como a expansão do eucalipto e a fragmentação, expliquem
parte da variância não capturada pelo clima; testar essa hipótese exigiria
incluir variáveis de uso do solo no modelo, o que se recomenda para
trabalhos futuros".

### Formatação (MB-10, 11, 12, 13, 14, 37, 39, 40, 51, 59, 67, 69, 72)

Todos aceitáveis, sem discussão: itálico em termos estrangeiros (MB-10–13,
37); tirar as linhas da Lista de Figuras (MB-14); remover marcações de
revisão (MB-39); linha solta na Tabela 1 (MB-40); "Reconhece-se, contudo"
(MB-51); linha faltante na Tabela 3 (MB-59); "diretamente proporcional"
(MB-67); citar a Figura 6 no texto (MB-69); legenda na figura da p. 36
(MB-72).

### Sem ação (MB-23, 46, 62, 64, 68)

Elogios ou "desconsiderar".

---

## Mudanças obrigatórias por causa da série nova (2001–2025)

Independentemente da banca, estes trechos ficaram **incorretos** com a base
nova e precisam mudar:

1. Todos os R², RMSE, MAE, gaps e intervalos (Tabelas 2 e 3, Resumo,
   Resultados, Conclusões): MA 62,3 → **71,0%**; CE 95,7 → **96,7%**; CA
   94,0 → **94,2%**; gaps 10,20/1,05/1,36 → **5,14/0,59/1,03** pp.
2. "n = 240" → **n = 297**; "2001 a 2020" → **2001 a 2025**.
3. Ljung-Box: "apenas na Caatinga" → **nos três biomas** (MA p < 0,001,
   ACF1 0,30; CE p = 0,005, ACF1 0,20; CA p < 0,001, ACF1 0,42).
4. Shapiro-Wilk: MA passou a **normal** (p = 0,57); CE normal (0,42); CA
   continua não normal (p = 0,0015). O parágrafo sobre o "evento extremo
   da Mata Atlântica" precisa ser revisto.
5. VIF do Cerrado: 25,8/24,0 → **36,99 (EV) / 31,61 (WAI)**.
6. Y-randomization: Δ 74,2/109,4/110,9 → **81,3/107,5/107,2** pp.
7. **Kruskal-Wallis da PSN**: "não detectou diferenças em nenhum dos três
   biomas" → **detectou na Caatinga** (p = 0,010; La Niña 94 > El Niño 80
   gC·m⁻²·mês⁻¹); MA p = 0,065 e CE p = 0,094 continuam não significativos.
8. Cerrado: EV agora **difere** entre fases (p = 0,0003), não mais "apenas
   tendência (p = 0,071)". Mata Atlântica: precipitação não difere
   (p = 0,35); EV difere (p = 0,006).
9. "ONI explica menos de 2% da variância" → **menos de ~3%** (máximo 3,05%
   na TST da Mata Atlântica).
10. Classificação das fases ENSO: agora pelo critério oficial da NOAA
    (descrever na Metodologia, ver MB-3).

---

## Comparação de graus com a base nova (responde F30)

Rodada agora com a base 2001–2025 (150 partições por grau, mesmo protocolo).
R² de teste médio e diferença treino–teste:

| Grau | Termos | MA R² teste (gap) | CE R² teste (gap) | CA R² teste (gap) |
|---|---|---|---|---|
| 1 | 5 | 65,8% (0,8) | 90,1% (1,2) | 92,9% (0,6) |
| **2** | 20 | **71,0% (5,1)** | **96,7% (0,6)** | **94,2% (1,0)** |
| 3 | 55 | 68,4% (9,0) | 96,4% (1,0) | 93,4% (2,4) |
| 4 | 125 | 29,3% (49,0) | 96,1% (1,6) | 63,8% (31,4) |
| 5 | 251 | −349,9% (432,8) | 93,7% (3,9) | 52,3% (42,8) |

Com a série nova, **o grau 2 tem o maior R² de teste nos três biomas**, mas
o Fernando tem razão no essencial: na Caatinga o ganho sobre o grau 1 é
marginal (1,3 ponto de R² de teste; RMSE de 7,39 para 6,69 gC·m⁻²·mês⁻¹),
enquanto no Cerrado é de 6,6 pontos e na Mata Atlântica de 5,2. Na Figura 4
da qualificação (2001–2020) esse empate na Caatinga era ainda mais visível.
Proposta de redação: "o grau 2 apresentou o maior R² de teste nos três
biomas e foi adotado como grau comum para permitir a comparação entre eles;
na Caatinga, porém, o ganho em relação ao modelo linear foi pequeno (1,3
ponto percentual), indicando resposta quase linear da vegetação semiárida
às variáveis hídricas". A Figura 4 foi refeita com a base nova.

Isso também fecha o H1 (MB-32): o grau 2 superou o grau 1 nos três biomas
com diferença treino–teste abaixo de 10 pontos.
