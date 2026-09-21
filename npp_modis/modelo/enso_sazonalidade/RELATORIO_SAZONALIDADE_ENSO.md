# Sazonalidade, ENSO e PSN: respostas às três perguntas da orientação

Base: série homogênea 2001–set/2025 (297 meses), MRMP-N grau 2 com Ridge, mesma
especificação da dissertação. Script: `modelo/analise_enso_sazonalidade.py`;
tabelas e figuras em `modelo/enso_sazonalidade/`. Todas as análises de ENSO
usam **anomalias mensais** (valor − média do mês do calendário), para que a
comparação entre fases não seja contaminada pela estação do ano.

---

## 1. Por que a importância das variáveis muda quando entram seno e cosseno

### 1.1 O que os dados mostram

Importância relativa (método da Figura 5: soma dos |coeficientes| padronizados, em %):

| Bioma | Variável | Sem seno/cosseno | Com seno/cosseno | O que acontece |
|---|---|---|---|---|
| Mata Atlântica | EV | 42 | 25 | continua a 1.ª entre as climáticas |
| | PRE | 28 | **11** | perde 60 % |
| | TST | 29 | 19 | perde, mas segue relevante |
| | seno + cosseno | — | 45 | |
| Cerrado | EV | 34 | **38** | única que **sobe** |
| | PRE | 29 | **10** | perde 65 % |
| | WAI | 37 | 17 | perde 55 % |
| | seno + cosseno | — | 35 | |
| Caatinga | EV | 50 | 43 | segue dominante |
| | PRE | 24 | **10** | perde 58 % |
| | TST | 27 | 16 | perde |
| | seno + cosseno | — | 31 | |

R² de validação cruzada: Mata Atlântica 46 → 72 %, Cerrado 93 → 95 %, Caatinga 92 → 93 %.

Duas medidas explicam a mudança:

| Bioma | Variável | % da variância que é ciclo anual | r com PSN (valores brutos) | r com PSN (anomalias) |
|---|---|---|---|---|
| Mata Atlântica | EV | 40 | 0,36 | **0,73** |
| | PRE | 9 | −0,24 | −0,14 |
| | TST | 65 | −0,34 | **−0,58** |
| | PSN | 3 | | |
| Cerrado | EV | 79 | 0,87 | **0,90** |
| | PRE | 59 | 0,28 | **0,02** |
| | WAI | 70 | 0,86 | 0,76 |
| | PSN | 61 | | |
| Caatinga | EV | 63 | 0,87 | **0,93** |
| | PRE | 32 | 0,28 | **0,16** |
| | TST | 54 | −0,74 | −0,77 |
| | PSN | 44 | | |

### 1.2 Interpretação ambiental

**Seno e cosseno representam o calendário ecológico.** Juntos descrevem o
ciclo anual determinístico: fotoperíodo, radiação solar incidente, alternância
regular de estação seca e chuvosa, fenologia (brotação, queda de folhas,
senescência). Nada disso é "clima do mês"; é o relógio astronômico e
fenológico que se repete todo ano.

**Sem esses termos, as variáveis climáticas recebem crédito pelo calendário.**
Precipitação, temperatura e WAI têm ciclo anual forte (54–79 % da variância no
Cerrado e na Caatinga). Como a PSN também tem ciclo anual, qualquer variável
que "sobe e desce com a estação" parece explicá-la. O modelo sem sazonalidade
está, em parte, usando a chuva de julho e a temperatura de janeiro como
substitutos do próprio mês.

**Com os termos, cada variável passa a ser julgada pelo que explica além do
normal da estação: as anomalias.** É aí que as importâncias se reordenam:

- **Precipitação (PRE) cai a ~10 % em todos os biomas** porque, uma vez
  removida a estação, a chuva do mês quase não se correlaciona com a PSN do mês
  (r = 0,02 no Cerrado, 0,16 na Caatinga). Ecologicamente: a chuva é um
  *fluxo de entrada* ruidoso e defasado. A planta não responde à chuva que cai,
  mas à água que ficou disponível no solo e que ela efetivamente usa nas
  semanas seguintes. Um mês chuvoso fora de época não vira fotossíntese
  imediata; um mês seco dentro da estação chuvosa não zera a produtividade,
  porque há água armazenada.

- **Evapotranspiração (EV) mantém ou aumenta a importância** porque ela é a
  medida da água *efetivamente usada* pela vegetação (transpiração +
  evaporação). Sua anomalia se correlaciona fortemente com a anomalia de PSN
  (0,73–0,93). Fisiologicamente, transpiração e assimilação de carbono passam
  pelos mesmos estômatos: quando a planta transpira mais que o normal para a
  época, está fotossintetizando mais que o normal. A EV integra chuva
  acumulada, umidade do solo, demanda atmosférica e estado da vegetação num
  único número, por isso é o melhor indicador interanual.

- **WAI (ET/PET) no Cerrado cai porque divide a mesma informação com a EV.**
  70 % do WAI é ciclo anual e ele é o numerador da EV dividido pela demanda. Com
  seno/cosseno, a parte sazonal do WAI migra para os harmônicos e a parte
  interanual já está na EV; sobra pouco para o WAI sozinho (é o VIF alto entre
  EV e WAI no Cerrado, já discutido na dissertação).

- **Temperatura (TST) perde importância mas continua relevante na Mata
  Atlântica e na Caatinga**, com sinal negativo nas anomalias (−0,58 e −0,77):
  um mês mais quente que o normal reduz a PSN. Isso é estresse térmico e
  hídrico combinados: superfície mais quente indica menos água evaporando,
  céu mais limpo, maior déficit de pressão de vapor e fechamento estomático. Na
  Mata Atlântica, bioma úmido, a temperatura é o principal canal pelo qual o
  clima anômalo chega à fotossíntese, o que se confirma na análise de ENSO
  (seção 2).

- **Mata Atlântica é o caso especial**: a PSN tem quase nenhum ciclo anual
  (3 % da variância), mas o R² sobe de 46 para 72 % com os harmônicos. Não é
  porque a estação explica a PSN diretamente, e sim porque os termos de
  interação (grau 2) permitem que o *efeito* da EV e da TST dependa da época:
  a mesma anomalia de temperatura pesa diferente no verão e no inverno. A
  sazonalidade aqui modula a sensibilidade, não o nível.

**Frase-síntese para o texto:** *Os harmônicos de sazonalidade absorvem o
ciclo anual determinístico da produtividade (fotoperíodo, radiação e fenologia).
Na presença deles, os preditores climáticos passam a ser avaliados pela
informação interanual que carregam. A precipitação mensal, fluxo de entrada
ruidoso e defasado, perde relevância; a evapotranspiração, que integra a água
efetivamente utilizada pela vegetação, consolida-se como o controle dominante
nos três biomas; a temperatura mantém papel de modulador negativo na Mata
Atlântica e na Caatinga.*

---

## 2. Quanto o ENSO altera as variáveis que controlam a PSN, e quanto disso chega à PSN

### 2.1 Efeito nas variáveis (anomalias, diferença em relação à fase Neutra)

Fases pelo ONI (≥ +0,5 El Niño, n = 76 meses; ≤ −0,5 La Niña, n = 73; Neutro n = 148).
Negrito = p < 0,05 (Mann-Whitney vs Neutro). ε² = tamanho de efeito de Kruskal-Wallis
(fração da variância das anomalias explicada pela fase).

| Bioma | Variável | El Niño | La Niña | ε² |
|---|---|---|---|---|
| Mata Atlântica | TST | **+3,0 %** (≈ +0,9 °C) | −0,6 % | 0,08 |
| | PRE | −5,1 % | −0,6 % | 0,00 |
| | EV | −1,5 % | +1,5 % | 0,00 |
| | **PSN** | **−5,4 %** | +0,1 % | 0,02 |
| Cerrado | EV | +7,5 % (p = 0,08) | **+10,0 %** | 0,04 |
| | WAI | +7,6 % | **+13,4 %** | 0,04 |
| | PRE | +7,8 % | −7,8 % | 0,00 |
| | **PSN** | +5,3 % | **+11,8 %** | 0,03 |
| Caatinga | EV | +0,4 % | **+10,8 %** | 0,03 |
| | TST | +1,5 % | **−2,1 %** | 0,04 |
| | PRE | +2,5 % | +4,6 % | 0,00 |
| | **PSN** | −3,2 % | **+10,6 %** | 0,04 |

Leitura: o ENSO explica pouco da variância total (ε² de 2 a 8 %, coerente com o
"menos de 6 %" do teste anterior), **mas o efeito médio tem sinal e magnitude
claros**: La Niña eleva a PSN em ~11 % no Cerrado e na Caatinga; El Niño reduz
a PSN em ~5 % na Mata Atlântica. A precipitação mensal, de novo, não é o canal:
suas diferenças nunca são significativas. Os canais são a **EV** (Cerrado e
Caatinga) e a **temperatura** (Mata Atlântica, e secundariamente Caatinga).

### 2.2 Propagação até a PSN pelo modelo (mediação)

Pergunta: se cada preditor assumir a anomalia média da fase, mantendo o resto
normal, quanto a PSN prevista muda?

| Bioma | Fase | via EV | via PRE | via TST/WAI | **Todos (modelo)** | **Observado** |
|---|---|---|---|---|---|---|
| Mata Atlântica | El Niño | −1,2 % | +0,4 % | **−2,0 %** (TST) | **−2,7 %** | −5,4 % |
| | La Niña | +1,1 % | −0,2 % | +0,4 % | +1,4 % | +0,1 % |
| Cerrado | El Niño | +4,6 % | −0,1 % | −0,2 % (WAI) | +4,3 % | +5,3 % |
| | La Niña | **+10,5 %** | −1,1 % | −0,8 % (WAI) | **+7,9 %** | +11,8 % |
| Caatinga | El Niño | −0,4 % | −0,1 % | −0,7 % (TST) | −1,2 % | −3,2 % |
| | La Niña | **+8,7 %** | −0,3 % | +1,0 % (TST) | **+9,7 %** | +10,6 % |

Conclusões:

- **Cerrado e Caatinga, La Niña**: o modelo reproduz 70–90 % do ganho observado
  de PSN, quase inteiramente via EV. Mecanismo: La Niña → mais água disponível
  (EV e WAI +10–13 %) → mais fotossíntese. A chuva mensal nem precisa aparecer
  como significativa: o que muda é o balanço hídrico integrado.
- **Mata Atlântica, El Niño**: o modelo explica metade da queda (−2,7 de −5,4 %),
  e o canal principal é a temperatura (+0,9 °C → −2 % de PSN). A outra metade
  não passa pelos preditores: candidatos são radiação/nebulosidade e a
  defasagem (seção 3), que o modelo mensal sem lag não captura.
- Isso responde diretamente à hipótese da dissertação: a influência do ENSO é
  **indireta e mediada**, por EV nos biomas sazonais e por TST no bioma úmido,
  e a "pequena explicação" do teste linear com ONI não significa efeito nulo:
  significa efeito real, de magnitude moderada (5–12 %), diluído numa
  variabilidade dominada pela estação.

---

## 3. Nos meses de ENSO a PSN sobe ou desce? E depois?

### 3.1 Correlação cruzada (ONI no mês t × anomalia de PSN no mês t + lag)

| Lag (meses) | Mata Atlântica | Cerrado | Caatinga |
|---|---|---|---|
| 0 | −0,14* | −0,10 | **−0,19*** |
| 1 | −0,15* | −0,12* | −0,19* |
| 2 | **−0,16*** | −0,13* | −0,17* |
| 3 | −0,15* | −0,12* | −0,15* |
| 4 | −0,14* | −0,12* | −0,12* |
| 6 | −0,11 | −0,12* | −0,07 |
| 9 | −0,07 | **−0,16*** | −0,09 |
| 12 | −0,03 | −0,16* | −0,09 |

(ρ de Spearman; * p < 0,05). Sinal negativo em todos: **ONI positivo (El Niño)
→ PSN abaixo do normal; ONI negativo (La Niña) → PSN acima.**

### 3.2 Compósitos (anomalia média de PSN, %, IC 95 %; ver figura `C_compositos_PSN_por_fase.png`)

| Bioma | Fase | lag 0 | lag 1–2 | lag 3–4 | lag 6 | lag 9 | lag 12 |
|---|---|---|---|---|---|---|---|
| Mata Atlântica | El Niño | **−4,0** | **−4,7 / −3,9** | **−4,3 / −4,1** | **−3,2** | −2,0 | **−2,7** |
| | La Niña | +1,5 | +1,6 / +2,4 | +1,0 / +0,6 | +0,4 | +0,2 | −0,6 |
| Cerrado | El Niño | +1,1 | −0,3 / −1,2 | −2,7 / −3,0 | −0,8 | −2,8 | −6,4 |
| | La Niña | **+7,6** | **+7,8 / +7,3** | **+5,1 / +5,2** | **+8,2** | **+10,3** | +3,2 |
| Caatinga | El Niño | −5,0 | −4,7 / −3,9 | −3,8 / −4,1 | −1,1 | −2,1 | −5,0 |
| | La Niña | **+8,8** | **+9,0 / +8,6** | **+5,7 / +4,9** | +4,3 | **+6,0** | +1,8 |

(negrito = IC 95 % não inclui zero e p < 0,05 vs Neutro)

### 3.3 Resposta por bioma

- **Caatinga: resposta imediata e curta.** La Niña eleva a PSN em ~9 % já no
  próprio mês e nos 2 seguintes, decaindo para ~5 % no 3.º–4.º mês e
  desaparecendo em 6 meses. É a "resposta pulsada" do semiárido: a vegetação
  caducifólia reage em semanas à água disponível e volta ao normal assim que a
  água acaba. El Niño reduz ~4–5 % nos primeiros 4 meses, mas com dispersão
  grande (não significativo): a Caatinga já opera perto do limite hídrico, e a
  seca extra do El Niño se confunde com a seca normal.

- **Cerrado: resposta imediata e persistente.** La Niña dá +7,5 % de imediato e
  o efeito **não decai**: continua +5 % aos 3–4 meses, +8 % aos 6 e chega a
  +10 % aos 9 meses. Interpretação: o Cerrado tem raízes profundas e solos
  espessos que armazenam a água excedente; um período La Niña na estação
  chuvosa sustenta a produtividade na estação seca seguinte. Pelo mesmo
  mecanismo, o El Niño quase não aparece no mês (+1 %) e só se manifesta
  tardiamente (−3 % aos 3–4 meses, −6 % aos 12): o déficit de recarga cobra
  depois. A correlação cruzada com segundo máximo em 9–11 meses confirma.

- **Mata Atlântica: responde ao El Niño, não à La Niña.** El Niño reduz a PSN
  em 4–5 % de forma significativa por 4 a 6 meses, com resíduo até 12 meses.
  La Niña não produz ganho (+1 a +2 %, n.s.). É assimétrico e coerente com o
  canal térmico: o bioma úmido não é limitado por água na média, então água a
  mais não ajuda, mas calor a mais (El Niño, +0,9 °C) prejudica.

### 3.4 Eventos individuais

Os eventos fortes seguem o padrão; os fracos, não sempre (por isso ε² é
baixo). El Niño 2015–16 (ONI 2,59, 20 meses): PSN −8 % (MA), −6 % (CE), −10 %
(CA) durante, e −12 / −36 / −19 % nos 3 meses seguintes. El Niño 2023–24 (1,99):
−8 / −12 / −18 %. La Niña 2010–11 (−1,57): +1 / +18 / +16 %. La Niña 2021–23
(17 meses): Caatinga +16 % durante; Mata Atlântica e Cerrado +16 / +18 % nos 3
meses seguintes. Exceção notável: El Niño 2009–10, com PSN +40 % no Cerrado, ano
de chuvas extremas no Nordeste apesar do El Niño. Tabela completa em
`C_eventos_ENSO_e_PSN.csv`.

**Frase-síntese para o texto:** *Embora o ENSO explique fração pequena da
variância mensal da PSN (ε² ≤ 0,04), os compósitos por fase revelam efeito
sistemático e defasado: La Niña eleva a PSN em cerca de 9–12 % no Cerrado e na
Caatinga, com resposta imediata e curta (≤ 4 meses) na Caatinga e persistente
(até 9 meses) no Cerrado; El Niño reduz a PSN em 4–5 % na Mata Atlântica por 4
a 6 meses, mediado pelo aquecimento da superfície. A precipitação mensal não
é o canal dessa influência; a evapotranspiração, expressão da água
efetivamente utilizada, é.*

---

## 4. Arquivos

| Arquivo | Conteúdo |
|---|---|
| `A_importancia_variaveis.csv`, `A_importancia_com_sem_sazonalidade.png` | importância por variável com/sem harmônicos (coeficientes e permutação) |
| `A_ciclo_anual_e_correlacoes.csv` | % de ciclo anual e correlação bruta × anomalias |
| `B_enso_efeito_nas_variaveis.csv` | anomalias por fase, testes e ε² |
| `B_enso_propagacao_para_PSN.csv` | mediação via modelo |
| `C_correlacao_cruzada_lags.csv`, `C_correlacao_cruzada_ONI_PSN.png` | ρ por lag, PSN e preditores |
| `C_compositos_PSN_lags.csv`, `C_compositos_PSN_por_fase.png` | anomalia média de PSN por fase e lag |
| `C_eventos_ENSO_e_PSN.csv` | 16 eventos ENSO e a PSN durante / depois |
