# Revisão da versão 6 (`Trabalho_revisado_2001_2025_6_claude.docx`, 21/09/2026)

Origem: outra sessão do Claude, branch `claude/vigilant-goodall-0zmvla`, pasta
`npp_modis/` (pipeline GEE, planilha antiga, análise ENSO em anomalias, script
`dissertacao/aplicar_alteracoes_docx.py`). Conferido contra a base e os
scripts desta branch (`dissertacao_PSN/`).

## O que está certo e deve ser adotado

- Fontes dos dados (5.2, Tabela 1, siglas): GEE, Coleção 6.1, MOD17A2HGF,
  MOD16A2GF, MOD11A2, MCD64A1, IMERG V07, IBGE 2019, agregação em 4 compostos.
- Base idêntica à desta branch (Apêndice A1 igual célula por célula; o CSV
  tem o mesmo md5 de `npp_modis/resultados/base_final_2001_2025_plan1_excel_ptbr.csv`).
- Análise em anomalias mensais (evita confundir ENSO com estação do ano),
  mediação pelo modelo, defasagens, Tabela 6, Figura 14, Tabela A5.
  Os Δ e p de posição da PSN reproduzem exatamente a partir da base.
- Motivo dos 3 meses excluídos (fim do IMERG V07 Final em set/2025).

## O que está errado ou incompleto

| # | Problema | Causa | Como resolver |
|---|---|---|---|
| 1 | Fases ENSO: texto, Tabela 6, A5 e Figura 14 usam 151/76/70; Apêndice A1, Figuras 11–13 e `enso_noaa.py` usam 149/76/72 | `classificar_fase(..., "noaa")` em `analise_enso_sazonalidade.py` só olha o ONI de 2001–2025; a La Niña 1998–2001 é cortada e jan–fev/2001 viram neutros | Rodar a análise com a coluna `Enso` do xlsx (critério oficial com a tabela completa da NOAA) e regerar Tabela 6, A5 e Figura 14; os Δ mudam ≤ 0,7 pp |
| 2 | Tabela 6 mistura definições sem dizer: Δ em % da média do mês; testes de dispersão, extremos e "% abaixo do P10" em anomalias absolutas (valor − média do mês) | `boxplots_enso.py` linha 35 | Manter, mas dizer na nota da tabela; ou padronizar tudo em % |
| 3 | Parágrafo novo de 6.2 cita "Tabela A4" para r das anomalias (0,02; 0,16; 0,73–0,93; −0,58; −0,77); a A4 só tem o R² do ciclo anual | Os r estão em `enso_oficial/A_ciclo_anual_e_correlacoes.csv` | Acrescentar as colunas "r bruto" e "r das anomalias" à Tabela A4 |
| 4 | Importâncias "sem harmônicos" (29→10 %, 24→10 %, 39→15 %, 34→38 %) vêm de um ajuste diferente do da Figura 8 (GridSearch cv=5 na série inteira, winsorização na base toda) | `ajustar()` em `analise_enso_sazonalidade.py` | Recalcular com o pipeline do `Modelo_PSN.py` (`Ablacao_Sazonalidade_PSN.py`) e citar a Tabela A3 |
| 5 | Figura 3 (fluxo) ainda diz "CHIRPS (PRE)" | figura não regenerada | Trocar para "IMERG (PRE)" em `Figuras_Dissertacao.py` e regerar |
| 6 | Figuras 3 e 6–13 em resolução reduzida (≈1.385 px de largura = 220 ppi em 16 cm) | o Word compactou as imagens ao salvar a versão 5 (12/09 23:27) | Regerar o docx pelo script desta branch, ou desligar "Compactar imagens" no Word (Opções → Avançado → Tamanho e qualidade da imagem → "Não compactar imagens no arquivo") |
| 7 | Figura 14 com 2.250 × 600 px fica ilegível a 16 cm | layout 1 × 3 | Redesenhar em 3 linhas (uma por bioma) ou 2 colunas, dpi 300 |
| 8 | Resumo e Abstract perderam o "± desvio-padrão" dos R² (pedido do Prof. Marcos) | reescrita da frase do ENSO | Restaurar |
| 9 | Listas: Figura 14, Tabela 6 e Tabela A5 sem página; Sumário desatualizado; página 46 meio em branco (Tabela 6 não coube); Tabela A5 em retrato enquanto A1–A4 estão em paisagem | | Regerar pelo pipeline (duas passagens) ou atualizar campos no Word |
| 10 | Tudo está como revisão marcada (1.350 inserções, 29 exclusões) | | Aceitar no Word antes de gerar o PDF |
| 11 | `Modelo_PSN.py` enviado ao outro chat estava com grau 3 e MA = EV + PRE + TST | cópia local antiga | O oficial é o de `dissertacao_PSN/Modelo_PSN.py` (grau 2, MA = EV + TST + WAI); apagar a cópia antiga |
| 12 | Dois pipelines em duas branches (`dissertacao_PSN/` aqui; `npp_modis/` lá) | trabalho paralelo | Fazer o merge de `claude/vigilant-goodall-0zmvla` nesta branch (nenhum arquivo em conflito) e portar 5.2, 6.2, 6.5, Tabela 6, A5 e Figura 14 para `aplicar_revisao_docx.py`, com um `Analise_ENSO_Anomalias_PSN.py` que use a coluna `Enso` oficial |

## Observações menores

- A "correlação > 0,97 com a série original" citada em 5.2 tem base em
  `npp_modis/resultados/referencia/validacao_resumo.csv` (r de 0,978 a 0,998).
- Sete células da planilha antiga estavam erradas; a PSN da MA em out/2004
  (51,3 vs 142,6) explica o antigo "evento extremo" da qualificação. Vale
  uma frase em 6.4.
- O resumo da conversa fala em R² da MA "de 46 para 72 %" com os harmônicos;
  o CSV da mesma análise diz 51,5 → 70,0 % e a Tabela A3 desta branch diz
  51,9 → 73,6 %. Usar os números da Tabela A3.
