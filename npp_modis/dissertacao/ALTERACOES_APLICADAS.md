# Alterações aplicadas em `Trabalho_revisado_2001_2025_6_claude.docx`

Todas com controle de alterações (autor "Claude (revisão de dados)"), sobre a
versão `Trabalho_revisado_2001_2025_5.docx`. Abra em Word → Revisão → aceitar
ou rejeitar uma a uma. Dados de apoio em `modelo/enso_oficial/`
(critério oficial da NOAA, Mata Atlântica com EV + TST + WAI, como no texto).

| Onde | O que mudou | Por quê |
|---|---|---|
| Lista de siglas | CHIRPS → GEE e IMERG | a chuva nunca foi CHIRPS |
| 5.2, 1.º parágrafo | reescrito: Google Earth Engine, Coleção 6.1, produtos gap-filled (MOD17A2HGF, MOD16A2GF), MOD11A2 diurno, MCD64A1, **GPM IMERG V07**, limites IBGE 2019, agregação em 4 compostos, série 2001–2025 processada de forma homogênea, validação (r > 0,97) | reprodutibilidade (pedido do Prof. Fernando) e fontes corretas |
| Tabela 1, coluna Fonte | 6 células atualizadas (coleções e versões reais) | idem |
| 5.2, parágrafo do período | motivo dos 3 meses excluídos: NASA encerrou o IMERG V07 em set/2025; V08 no fim de 2026 (NASA, 2026) | resposta à orientadora |
| 6.2, após "A presença das componentes harmônicas…" | **novo parágrafo**: por que a importância se reordena com seno/cosseno (chuva cai a ~10 %, EV mantém, TST recua na MA), com r das anomalias | pedido da orientadora |
| 6.5, 1.º parágrafo | reescrito: 151/76/70 meses; fases concentradas em nov–fev; comparação bruta confunde ENSO com estação (ex.: chuva do Cerrado 124 vs 59 mm); análise em **anomalias** com três testes (posição, dispersão, extremos); remete à Tabela 6 e à Tabela A5 | corrige confundimento sazonal da versão atual |
| 6.5, **Tabela 6 (nova)** | anomalias por fase, p dos três testes e % de meses abaixo do P10, 15 linhas | pedido da orientadora (extremos) |
| 6.5, parágrafos MA, Cerrado, Caatinga | reescritos com anomalias: MA = El Niño age nos extremos (22 % vs 5 % de meses abaixo do P10; mediana igual); CE e CA = La Niña desloca a distribuição (+12,4 % e +10,5 %) via EV/WAI; chuva só muda em dispersão | substitui médias brutas confundidas pela estação |
| 6.5, **2 parágrafos novos** após a Figura 13 | mediação via modelo (70–90 % do efeito via EV nos biomas sazonais; ~metade via TST na MA) e defasagem (Caatinga curta ≤ 4 meses, Cerrado persistente até 9, MA responde só ao El Niño por 4–6 meses; eventos 2015–16 e 2010–11) | pedido da orientadora |
| 6.5, **Figura 14 (nova)** | compósitos da anomalia de PSN por fase e defasagem, IC 95 % | idem |
| 6.5, três últimos parágrafos | reescritos (ε² pequeno ≠ efeito nulo; canais por bioma; amortecimento) | coerência com os novos resultados |
| Resumo e Abstract | frase do ENSO atualizada | idem |
| 7, H3 e parágrafo dos objetivos | atualizados | idem |
| Apêndice A, **Tabela A5 (nova)** | valores exatos dos boxplots das Figuras 11–13 (n, mín, Q1, mediana, média, Q3, máx, outliers), 45 linhas | pedido da orientadora |
| Listas de figuras e tabelas | linhas Figura 14, Tabela 6, Tabela A5 (página em branco: atualize os números de página) | |
| Referências | GIGLIO 2018, GORELICK 2017, HUFFMAN 2023 (IMERG V07), IBGE 2019, NASA 2026, RUNNING et al. 2021 (MOD16), WAN 2021 (MOD11) | citadas no novo 5.2 |

**O que não foi alterado e você precisa conferir:**

- As Figuras 11–13 (boxplots brutos por fase) continuam; o texto agora diz que
  são brutas e remete à Tabela A5. Se quiser, substitua pelos boxplots de
  anomalias (`modelo/enso_oficial/D_boxplots_anomalias_por_fase.png`).
- A contagem 151/76/70 (minha classificação) substitui 149/76/72 da versão 5;
  se o seu script de fases der outro resultado, ajuste os n da Tabela A5.
- A Figura 8 (importância) e a Tabela A3/A4 não foram tocadas.
- Números de página das listas iniciais e do sumário: atualizar campos no Word.
- Não consegui renderizar o docx aqui (LibreOffice do ambiente não abre docx);
  o arquivo passou na validação XSD e de controle de alterações, mas confira a
  Tabela 6 e a Tabela A5 no Word (larguras de coluna).
