#!/usr/bin/env python3
"""
Automação: Meta Ads (Gerenciador de Anúncios) -> Trello (lista YGOR).

Lê métricas da conta de anúncios pela API de Marketing da Meta e publica um
resumo como comentário nos cartões da lista YGOR do quadro compartilhado.

Uso:
  python3 automacao/trafego_trello.py verificar            # testa credenciais e acesso
  python3 automacao/trafego_trello.py diario [--data AAAA-MM-DD] [--dry-run]
  python3 automacao/trafego_trello.py semanal [--data AAAA-MM-DD] [--dry-run]

Variáveis de ambiente (obrigatórias):
  META_ACCESS_TOKEN     token do usuário do sistema (ads_read, read_insights)
  META_AD_ACCOUNT_ID    ex.: act_878458868240738
  TRELLO_API_KEY        chave de API do Trello
  TRELLO_TOKEN          token do Trello (da conta do Ygor)
  TRELLO_BOARD_ID       id do quadro "My Trello Board" (ou o shortLink 8rYUh1ML)

Variáveis opcionais:
  META_API_VERSION            padrão v23.0
  TRELLO_LISTA                padrão "YGOR"
  TRELLO_CARTAO_DIARIO        padrão "(DIÁRIO) Acompanhamento dos anúncios"
  TRELLO_CARTAO_SEMANAL       padrão "(DOM) Relatório semanal de tráfego"
  ALERTA_CUSTO_POR_MENSAGEM   em R$, padrão 15
  ALERTA_GASTO_DIARIO         em R$, padrão 0 (desligado)
  FUSO_HORARIO                padrão America/Sao_Paulo

O script nunca toca em outras listas: ele localiza os cartões pelo nome dentro
da lista configurada e só publica comentários neles.
"""

import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------- configuração

META_API_VERSION = os.environ.get("META_API_VERSION", "v23.0")
TRELLO_LISTA = os.environ.get("TRELLO_LISTA", "YGOR")
CARTAO_DIARIO = os.environ.get("TRELLO_CARTAO_DIARIO", "(DIÁRIO) Acompanhamento dos anúncios")
CARTAO_SEMANAL = os.environ.get("TRELLO_CARTAO_SEMANAL", "(DOM) Relatório semanal de tráfego")
ALERTA_CUSTO_MSG = float(os.environ.get("ALERTA_CUSTO_POR_MENSAGEM", "15") or 0)
ALERTA_GASTO_DIA = float(os.environ.get("ALERTA_GASTO_DIARIO", "0") or 0)
FUSO = ZoneInfo(os.environ.get("FUSO_HORARIO", "America/Sao_Paulo"))

# Tipos de ação da Meta que contam como "mensagem/lead" para uma loja que vende
# pelo WhatsApp. O primeiro que existir no retorno é o usado.
ACOES_MENSAGEM = (
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.total_messaging_connection",
    "onsite_conversion.messaging_first_reply",
    "lead",
)

CAMPOS_INSIGHTS = (
    "campaign_id,campaign_name,objective,adset_name,ad_id,ad_name,spend,reach,impressions,"
    "clicks,inline_link_clicks,frequency,actions,cost_per_action_type"
)

# Objetivos em que "zero mensagens" é esperado (não geram alerta de conversão).
OBJETIVOS_SEM_MENSAGEM = ("OUTCOME_AWARENESS", "BRAND_AWARENESS", "REACH", "VIDEO_VIEWS", "OUTCOME_ENGAGEMENT")


class ErroAutomacao(Exception):
    pass


def env_obrigatoria(nome):
    valor = os.environ.get(nome, "").strip()
    if not valor:
        raise ErroAutomacao(f"Variável de ambiente {nome} não definida.")
    return valor


# ---------------------------------------------------------------- utilidades

def http_json(url, params=None, method="GET", dados=None):
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    req = urllib.request.Request(url, data=corpo, method=method)
    req.add_header("User-Agent", "controle-gas-automacao/1.0")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            texto = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")[:800]
        raise ErroAutomacao(f"HTTP {e.code} em {url.split('?')[0]}: {detalhe}") from None
    except urllib.error.URLError as e:
        raise ErroAutomacao(f"Falha de rede em {url.split('?')[0]}: {e.reason}") from None
    return json.loads(texto) if texto else {}


def brl(valor):
    """Formata 1234.5 -> 'R$ 1.234,50'."""
    s = f"{float(valor):,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def inteiro(valor):
    return f"{int(float(valor or 0)):,}".replace(",", ".")


def num(valor):
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def hoje_local():
    return dt.datetime.now(FUSO).date()


def parse_data(texto):
    return dt.date.fromisoformat(texto)


# ---------------------------------------------------------------- Meta Ads

def meta_insights(nivel, desde, ate):
    token = env_obrigatoria("META_ACCESS_TOKEN")
    conta = env_obrigatoria("META_AD_ACCOUNT_ID")
    if not conta.startswith("act_"):
        conta = "act_" + conta
    url = f"https://graph.facebook.com/{META_API_VERSION}/{conta}/insights"
    params = {
        "access_token": token,
        "level": nivel,
        "fields": CAMPOS_INSIGHTS,
        "time_range": json.dumps({"since": desde.isoformat(), "until": ate.isoformat()}),
        "limit": 500,
    }
    linhas = []
    resposta = http_json(url, params)
    while True:
        linhas.extend(resposta.get("data", []))
        proximo = resposta.get("paging", {}).get("next")
        if not proximo:
            break
        resposta = http_json(proximo)
    return linhas


def meta_status_campanhas():
    """Retorna {campaign_id: effective_status} para saber o que está pausado."""
    token = env_obrigatoria("META_ACCESS_TOKEN")
    conta = env_obrigatoria("META_AD_ACCOUNT_ID")
    if not conta.startswith("act_"):
        conta = "act_" + conta
    url = f"https://graph.facebook.com/{META_API_VERSION}/{conta}/campaigns"
    resposta = http_json(url, {"access_token": token, "fields": "name,effective_status", "limit": 500})
    return {c["id"]: c for c in resposta.get("data", [])}


def extrair_mensagens(linha):
    acoes = {a.get("action_type"): num(a.get("value")) for a in linha.get("actions", []) or []}
    for tipo in ACOES_MENSAGEM:
        if tipo in acoes:
            return acoes[tipo]
    return 0.0


def resumir(linhas, chave_nome):
    """Agrupa linhas de insights por nome (campanha ou anúncio)."""
    grupos = {}
    for l in linhas:
        nome = l.get(chave_nome) or "(sem nome)"
        g = grupos.setdefault(nome, {"nome": nome, "id": l.get("campaign_id"), "objetivo": l.get("objective") or "", "gasto": 0.0,
                                     "alcance": 0.0, "impressoes": 0.0, "cliques": 0.0,
                                     "mensagens": 0.0, "freq_soma": 0.0, "freq_n": 0})
        g["gasto"] += num(l.get("spend"))
        g["alcance"] += num(l.get("reach"))
        g["impressoes"] += num(l.get("impressions"))
        g["cliques"] += num(l.get("inline_link_clicks") or l.get("clicks"))
        g["mensagens"] += extrair_mensagens(l)
        if l.get("frequency"):
            g["freq_soma"] += num(l.get("frequency"))
            g["freq_n"] += 1
    for g in grupos.values():
        g["frequencia"] = g["freq_soma"] / g["freq_n"] if g["freq_n"] else 0.0
        g["custo_msg"] = g["gasto"] / g["mensagens"] if g["mensagens"] else None
    return sorted(grupos.values(), key=lambda g: g["gasto"], reverse=True)


def totais(grupos):
    t = {"gasto": 0.0, "alcance": 0.0, "impressoes": 0.0, "cliques": 0.0, "mensagens": 0.0}
    for g in grupos:
        for k in t:
            t[k] += g[k]
    t["custo_msg"] = t["gasto"] / t["mensagens"] if t["mensagens"] else None
    return t


# ---------------------------------------------------------------- Trello

def trello_auth():
    return {"key": env_obrigatoria("TRELLO_API_KEY"), "token": env_obrigatoria("TRELLO_TOKEN")}


def trello_quadro():
    board = env_obrigatoria("TRELLO_BOARD_ID")
    return http_json(f"https://api.trello.com/1/boards/{board}", {**trello_auth(), "fields": "name,url,idOrganization"})


def trello_localizar_cartoes():
    """Encontra os cartões de destino dentro da lista configurada. Nunca sai dela."""
    board = env_obrigatoria("TRELLO_BOARD_ID")
    auth = trello_auth()
    listas = http_json(f"https://api.trello.com/1/boards/{board}/lists", {**auth, "fields": "name"})
    lista = next((l for l in listas if l["name"].strip().upper() == TRELLO_LISTA.upper()), None)
    if not lista:
        raise ErroAutomacao(f"Lista '{TRELLO_LISTA}' não encontrada no quadro. Listas: {[l['name'] for l in listas]}")
    cartoes = http_json(f"https://api.trello.com/1/lists/{lista['id']}/cards", {**auth, "fields": "name,shortUrl"})
    por_nome = {c["name"].strip(): c for c in cartoes}

    def achar(nome):
        if nome in por_nome:
            return por_nome[nome]
        # tolera diferenças de acento/caixa
        alvo = nome.casefold()
        for n, c in por_nome.items():
            if n.casefold() == alvo:
                return c
        raise ErroAutomacao(f"Cartão '{nome}' não encontrado na lista {TRELLO_LISTA}. Cartões: {list(por_nome)}")

    return {"lista": lista, "diario": achar(CARTAO_DIARIO), "semanal": achar(CARTAO_SEMANAL)}


def trello_comentar(card_id, texto):
    return http_json(f"https://api.trello.com/1/cards/{card_id}/actions/comments",
                     trello_auth(), method="POST", dados={"text": texto})


# ---------------------------------------------------------------- relatórios

def linha_campanha(g):
    custo = brl(g["custo_msg"]) if g["custo_msg"] is not None else "—"
    return (f"- **{g['nome']}**: gasto {brl(g['gasto'])} · msgs {inteiro(g['mensagens'])} · "
            f"custo/msg {custo} · cliques {inteiro(g['cliques'])} · freq {g['frequencia']:.2f}")


def alertas_do_dia(campanhas, t):
    avisos = []
    if ALERTA_GASTO_DIA and t["gasto"] > ALERTA_GASTO_DIA:
        avisos.append(f"Gasto do dia {brl(t['gasto'])} acima do limite de {brl(ALERTA_GASTO_DIA)}.")
    for g in campanhas:
        if g["objetivo"] in OBJETIVOS_SEM_MENSAGEM:
            continue  # campanha de alcance/engajamento: não se cobra mensagem dela
        if g["gasto"] > 0 and g["mensagens"] == 0:
            avisos.append(f"'{g['nome']}' gastou {brl(g['gasto'])} e não gerou nenhuma mensagem.")
        elif ALERTA_CUSTO_MSG and g["custo_msg"] and g["custo_msg"] > ALERTA_CUSTO_MSG:
            avisos.append(f"'{g['nome']}' com custo por mensagem de {brl(g['custo_msg'])}, "
                          f"acima de {brl(ALERTA_CUSTO_MSG)}.")
        if g["frequencia"] >= 3:
            avisos.append(f"'{g['nome']}' com frequência {g['frequencia']:.1f}: público saturando, avaliar novo criativo.")
    return avisos


def relatorio_diario(dia):
    campanhas = resumir(meta_insights("campaign", dia, dia), "campaign_name")
    anuncios = resumir(meta_insights("ad", dia, dia), "ad_name")
    t = totais(campanhas)
    ativos = [a for a in anuncios if a["mensagens"] > 0]
    melhor = min(ativos, key=lambda a: a["custo_msg"]) if ativos else (anuncios[0] if anuncios else None)

    partes = [f"**Acompanhamento diário — {dia.strftime('%d/%m/%Y')}** (automático)", ""]
    if not campanhas:
        partes.append("Nenhuma campanha com entrega neste dia.")
        return "\n".join(partes), []
    custo = brl(t["custo_msg"]) if t["custo_msg"] is not None else "—"
    partes += [
        f"Gasto: {brl(t['gasto'])} · Alcance: {inteiro(t['alcance'])} · Impressões: {inteiro(t['impressoes'])}",
        f"Cliques: {inteiro(t['cliques'])} · Mensagens/leads: {inteiro(t['mensagens'])} · Custo por mensagem: {custo}",
        "",
        "**Por campanha**",
    ]
    partes += [linha_campanha(g) for g in campanhas]
    if melhor:
        partes += ["", f"**Melhor criativo do dia:** {melhor['nome']} "
                       f"({inteiro(melhor['mensagens'])} msgs, {brl(melhor['gasto'])})"]
    avisos = alertas_do_dia(campanhas, t)
    if avisos:
        partes += ["", "**⚠️ Atenção**"] + [f"- {a}" for a in avisos]
    return "\n".join(partes), avisos


def relatorio_semanal(fim):
    inicio = fim - dt.timedelta(days=6)
    campanhas = resumir(meta_insights("campaign", inicio, fim), "campaign_name")
    anuncios = resumir(meta_insights("ad", inicio, fim), "ad_name")
    status = meta_status_campanhas()
    t = totais(campanhas)

    com_msg = [c for c in campanhas if c["mensagens"] > 0]
    melhor_camp = min(com_msg, key=lambda c: c["custo_msg"]) if com_msg else (campanhas[0] if campanhas else None)
    pior_camp = max(campanhas, key=lambda c: (c["mensagens"] == 0, c["custo_msg"] or 0)) if campanhas else None
    an_msg = [a for a in anuncios if a["mensagens"] > 0]
    melhor_an = min(an_msg, key=lambda a: a["custo_msg"]) if an_msg else (anuncios[0] if anuncios else None)
    # Só campanhas que tiveram entrega na semana; o histórico da conta não entra.
    def situacao(c):
        return status.get(c["id"] or "", {}).get("effective_status", "")
    pausadas = [c["nome"] for c in campanhas if situacao(c) in ("PAUSED", "CAMPAIGN_PAUSED", "ADSET_PAUSED")]
    ativas = [c["nome"] for c in campanhas if situacao(c) == "ACTIVE"]

    def nome(x):
        return x["nome"] if x else "______"

    custo = brl(t["custo_msg"]) if t["custo_msg"] is not None else "______"
    partes = [
        f"**Relatório semanal de tráfego — {inicio.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}** (automático)",
        "",
        f"- Investimento total: {brl(t['gasto'])}",
        f"- Leads/mensagens: {inteiro(t['mensagens'])}",
        f"- Custo médio por lead: {custo}",
        "- Quantidade de vendas: ______ (preencher com Gustavo)",
        "- Faturamento atribuído ao tráfego: R$ ______ (preencher com Gustavo)",
        "- Custo por venda: R$ ______ (investimento ÷ vendas)",
        f"- Melhor campanha: {nome(melhor_camp)}",
        f"- Melhor anúncio/criativo: {nome(melhor_an)}",
        "- Produto mais procurado: ______",
        f"- Produto com pior resultado: ______ (campanha com pior resultado: {nome(pior_camp)})",
        f"- Campanhas pausadas: {', '.join(pausadas) if pausadas else 'nenhuma'}",
        f"- Campanhas que devem continuar: {', '.join(ativas) if ativas else '______'}",
        "- O que será melhorado na próxima semana: ______",
        "",
        "**Campanhas da semana**",
    ]
    partes += [linha_campanha(g) for g in campanhas] or ["- Nenhuma campanha com entrega na semana."]
    return "\n".join(partes)


# ---------------------------------------------------------------- comandos

def cmd_verificar(_args):
    problemas = []
    for nome in ("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID", "TRELLO_API_KEY", "TRELLO_TOKEN", "TRELLO_BOARD_ID"):
        print(f"{nome}: {'ok' if os.environ.get(nome) else 'FALTANDO'}")
        if not os.environ.get(nome):
            problemas.append(nome)
    if problemas:
        print("\nDefina as variáveis acima antes de continuar.")
        return 2

    quadro = trello_quadro()
    print(f"\nTrello: quadro '{quadro['name']}' ({quadro['url']})")
    alvos = trello_localizar_cartoes()
    print(f"  lista {TRELLO_LISTA}: id {alvos['lista']['id']}")
    print(f"  cartão diário : {alvos['diario']['shortUrl']}")
    print(f"  cartão semanal: {alvos['semanal']['shortUrl']}")

    ontem = hoje_local() - dt.timedelta(days=1)
    linhas = meta_insights("campaign", ontem, ontem)
    print(f"\nMeta: conta {os.environ['META_AD_ACCOUNT_ID']} respondeu, {len(linhas)} campanha(s) com entrega em {ontem}.")
    print("\nTudo pronto.")
    return 0


def cmd_diario(args):
    dia = parse_data(args.data) if args.data else hoje_local() - dt.timedelta(days=1)
    texto, avisos = relatorio_diario(dia)
    print(texto)
    if args.dry_run:
        print("\n[dry-run] nada foi publicado no Trello.")
        return 0
    alvos = trello_localizar_cartoes()
    trello_comentar(alvos["diario"]["id"], texto)
    print(f"\nComentário publicado em {alvos['diario']['shortUrl']} ({len(avisos)} alerta(s)).")
    return 0


def cmd_semanal(args):
    fim = parse_data(args.data) if args.data else hoje_local() - dt.timedelta(days=1)
    texto = relatorio_semanal(fim)
    print(texto)
    if args.dry_run:
        print("\n[dry-run] nada foi publicado no Trello.")
        return 0
    alvos = trello_localizar_cartoes()
    trello_comentar(alvos["semanal"]["id"], texto)
    print(f"\nComentário publicado em {alvos['semanal']['shortUrl']}.")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="comando", required=True)
    sub.add_parser("verificar", help="testa credenciais e acesso ao quadro e à conta de anúncios")
    for nome, ajuda in (("diario", "resumo do dia anterior no cartão diário"),
                        ("semanal", "relatório dos últimos 7 dias no cartão de domingo")):
        s = sub.add_parser(nome, help=ajuda)
        s.add_argument("--data", help="data de referência AAAA-MM-DD (padrão: ontem)")
        s.add_argument("--dry-run", action="store_true", help="só imprime, não publica")
    args = p.parse_args(argv)
    try:
        return {"verificar": cmd_verificar, "diario": cmd_diario, "semanal": cmd_semanal}[args.comando](args)
    except ErroAutomacao as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
