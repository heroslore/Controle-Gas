# Automação: Meta Ads → Trello

Publica, na lista **YGOR** do quadro compartilhado, um comentário diário com as
métricas do Gerenciador de Anúncios e, aos domingos, o relatório semanal.
Não toca nas listas BRUNO SEMANAL e GUSTAVO: o script localiza os cartões pelo
nome dentro da lista YGOR e só escreve comentários neles.

## Cartões usados

| Cartão | O que recebe |
|---|---|
| `(DIÁRIO) Acompanhamento dos anúncios` | comentário com gasto, alcance, impressões, cliques, mensagens, custo por mensagem, melhor criativo e alertas do dia anterior |
| `(DOM) Relatório semanal de tráfego` | comentário com os 13 campos do relatório, preenchidos com o que a Meta fornece; vendas e faturamento ficam para preencher com o Gustavo |

## Variáveis de ambiente

Obrigatórias (cadastrar no ambiente do Claude Code, em Credenciais de API ou variáveis de ambiente; nunca no código):

| Nome | Valor |
|---|---|
| `META_ACCESS_TOKEN` | token do usuário do sistema da Meta com `ads_read` e `read_insights` |
| `META_AD_ACCOUNT_ID` | `act_` + número da conta de anúncios |
| `TRELLO_API_KEY` | chave de API gerada em trello.com/power-ups/admin |
| `TRELLO_TOKEN` | token gerado a partir da chave, com a conta do Ygor |
| `TRELLO_BOARD_ID` | id ou shortLink do quadro (`8rYUh1ML`) |

Opcionais: `ALERTA_CUSTO_POR_MENSAGEM` (R$, padrão 15), `ALERTA_GASTO_DIARIO`
(R$, padrão desligado), `TRELLO_LISTA`, `TRELLO_CARTAO_DIARIO`,
`TRELLO_CARTAO_SEMANAL`, `META_API_VERSION` (padrão `v23.0`), `FUSO_HORARIO`.

Sobre a chave do Trello: ela é gerada dentro de um Power-Up ligado a uma área de
trabalho, mas o acesso é dado pelo **token**, que é da conta do usuário. Como o
Ygor é membro do "My Trello Board", o token enxerga o quadro mesmo com o Power-Up
criado em outra área de trabalho.

## Comandos

```bash
python3 automacao/trafego_trello.py verificar             # confere credenciais, quadro, lista, cartões e conta Meta
python3 automacao/trafego_trello.py diario --dry-run      # mostra o resumo de ontem sem publicar
python3 automacao/trafego_trello.py diario                # publica o resumo de ontem
python3 automacao/trafego_trello.py semanal --dry-run     # mostra os últimos 7 dias
python3 automacao/trafego_trello.py semanal --data 2026-09-20   # semana que termina nessa data
```

Só usa a biblioteca padrão do Python 3.11+. Sem dependências para instalar.

## Agendamento

A rotina no Claude Code roda `diario` todo dia às 08:00 (horário de Brasília) e
`semanal` aos domingos logo depois. Se uma execução falhar, o erro aparece na
saída do script com a causa (credencial faltando, cartão não encontrado, resposta
da Meta).

## O que a Meta conta como "mensagem"

O script usa, nesta ordem, o primeiro tipo de ação presente no retorno:
`messaging_conversation_started_7d`, `total_messaging_connection`,
`messaging_first_reply`, `lead`. Para campanhas de WhatsApp o primeiro é o normal.
