# -*- coding: utf-8 -*-
"""Aplica as alterações (com controle de alterações) no docx revisado."""
import re, shutil, datetime, html
import pandas as pd

SRC = "docx_rev/word/document.xml"
AUT = "Claude (revisão de dados)"; DATE = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
_id = [90000]
def nid(): _id[0] += 1; return str(_id[0])
def esc(s): return html.escape(s, quote=False)
def ins_tag(): return f'<w:ins w:id="{nid()}" w:author="{AUT}" w:date="{DATE}">'
def del_tag(): return f'<w:del w:id="{nid()}" w:author="{AUT}" w:date="{DATE}">'
def mark_ins(): return f'<w:ins w:id="{nid()}" w:author="{AUT}" w:date="{DATE}"/>'

x = open(SRC, encoding="utf-8").read()
paras = re.findall(r"<w:p[ >].*?</w:p>", x, re.S)
assert len(paras) == 7369
def txt(p): return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", p, re.S))
RUN = re.compile(r"<w:r>.*?</w:r>|<w:r [^>]*>.*?</w:r>", re.S)
def rpr(run):
    m = re.search(r"<w:rPr>.*?</w:rPr>", run, re.S); return m.group(0) if m else ""
def run_text(run): return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", run, re.S))
def mk_run(text, rp=""): return f'<w:r>{rp}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'
def to_del(run): return del_tag() + re.sub(r"<w:t([^>]*)>(.*?)</w:t>", r"<w:delText\1>\2</w:delText>", run, flags=re.S) + "</w:del>"
def ppr(p):
    m = re.search(r"<w:pPr>.*?</w:pPr>", p, re.S); return m.group(0) if m else ""
def ppr_inserted(pp):
    """marca o parágrafo (sua marca de parágrafo) como inserido"""
    if not pp: return f"<w:pPr><w:rPr>{mark_ins()}</w:rPr></w:pPr>"
    if "<w:rPr>" in pp: return pp.replace("<w:rPr>", "<w:rPr>" + mark_ins(), 1)
    return pp.replace("</w:pPr>", f"<w:rPr>{mark_ins()}</w:rPr></w:pPr>")

edits = {}   # idx -> novo xml do parágrafo
after = {}   # idx -> xml a inserir depois do parágrafo

def replace_paragraph(i, new_text):
    p = paras[i]; pp = ppr(p); runs = RUN.findall(p); rp = rpr(runs[0]) if runs else ""
    body = p[p.index("</w:pPr>") + 8:-len("</w:p>")] if pp else p[p.index(">") + 1:-len("</w:p>")]
    body = RUN.sub(lambda m: to_del(m.group(0)), body)
    head = p[:p.index("<w:pPr>")] if pp else p[:p.index(">") + 1]
    edits[i] = head + pp + body + ins_tag() + mk_run(new_text, rp) + "</w:ins></w:p>"

def replace_substring(i, old, new):
    p = paras[i]; runs = list(RUN.finditer(p)); texts = [run_text(m.group(0)) for m in runs]
    full = "".join(texts); s = full.find(old); assert s >= 0, f"[{i}] não achei: {old[:40]}"; e = s + len(old)
    out, pos = p[:runs[0].start()], 0; inserted = False
    for m, t in zip(runs, texts):
        a, b = pos, pos + len(t); pos = b; r = m.group(0)
        if b <= s or a >= e or not t: out += r; continue
        rp = rpr(r); pre, mid, post = t[:max(0, s - a)], t[max(0, s - a):min(len(t), e - a)], t[min(len(t), e - a):]
        if pre: out += mk_run(pre, rp)
        out += to_del(mk_run(mid, rp))
        if not inserted: out += ins_tag() + mk_run(new, rp) + "</w:ins>"; inserted = True
        if post: out += mk_run(post, rp)
    edits[i] = out + p[runs[-1].end():]

def new_par(text, pp_ref, rp="", bold=False):
    pp = ppr_inserted(pp_ref); rp2 = rp or ("<w:rPr><w:b/><w:sz w:val=\"22\"/><w:szCs w:val=\"22\"/></w:rPr>" if bold else "")
    return f"<w:p>{pp}{ins_tag()}{mk_run(text, rp2)}</w:ins></w:p>"

def new_table(header, rows, widths, font_sz=18):
    tot = sum(widths); cells_pp = '<w:pPr><w:keepNext/><w:spacing w:after="0"/><w:ind w:firstLine="0"/><w:jc w:val="center"/><w:rPr>' + mark_ins() + '</w:rPr></w:pPr>'
    def cell(t, w, b=False, bottom=False):
        rp = f'<w:rPr>{"<w:b/>" if b else ""}<w:sz w:val="{font_sz}"/><w:szCs w:val="{font_sz}"/></w:rPr>'
        bd = '<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/></w:tcBorders>' if bottom else ""
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{bd}</w:tcPr><w:p>{cells_pp}{ins_tag()}{mk_run(t, rp)}</w:ins></w:p></w:tc>'
    def tr(cells, b=False, bottom=False):
        return f'<w:tr><w:trPr><w:cantSplit/>{"<w:tblHeader/>" if b else ""}<w:jc w:val="center"/>{mark_ins()}</w:trPr>' + "".join(cell(t, w, b, bottom) for t, w in zip(cells, widths)) + "</w:tr>"
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    return (f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="{tot}" w:type="dxa"/><w:jc w:val="center"/><w:tblInd w:w="0" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
            f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
            + tr(header, True, True) + "".join(tr(r, False, k == len(rows) - 1) for k, r in enumerate(rows)) + "</w:tbl>")

CAP_PP = ppr(paras[379]); REF_PP = ppr(paras[7341]); BODY_PP = ppr(paras[515]); FIGCAP_PP = ppr(paras[517])
FIGCAP_RP = '<w:rPr><w:b/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr>'
def f1(v): return f"{v:.1f}".replace(".", ",")
def fp(v): return "< 0,001" if v < 0.001 else f"{v:.3f}".replace(".", ",")
D = "/home/user/Controle-Gas/npp_modis/modelo/enso_oficial/"

# ---------------------------------------------------------------- 1. siglas e 5.2
replace_substring(90, "CHIRPS – Climate Hazards Group InfraRed Precipitation with Station data",
                  "GEE – Google Earth Engine; IMERG – Integrated Multi-satellitE Retrievals for GPM (Global Precipitation Measurement)")
replace_paragraph(281,
 "Os dados utilizados neste estudo foram organizados em formato tabular, com uma observação mensal por bioma, a partir de produtos de sensoriamento remoto e de uma base de precipitação por satélite, todos de acesso público e gratuito, obtidos e processados na plataforma Google Earth Engine (GEE; Gorelick et al., 2017) por meio de sua interface em Python. A variável resposta, a Fotossíntese Líquida (PSN), provém do produto MOD17A2HGF, e a evapotranspiração real (EV) e a potencial (ETP) do produto MOD16A2GF, ambos da Coleção 6.1 do sensor MODIS a bordo do satélite Terra, da NASA, em suas versões com preenchimento de falhas consolidadas ao fim de cada ano (Running; Zhao, 2021; Running et al., 2021); a temperatura da superfície terrestre (TST) provém da banda diurna do produto MOD11A2 (Wan; Hook; Hulley, 2021) e a área queimada (BURN) do MCD64A1 (Giglio et al., 2018), ambos da mesma coleção. A precipitação (PRE) provém do produto GPM IMERG Final Run mensal, versão 07 (Huffman et al., 2023), que combina estimativas de múltiplos satélites calibradas por estações pluviométricas, com resolução espacial de 0,1°; essa versão reprocessou integralmente a série desde 1998 e substituiu a versão 06 utilizada por Benfica et al. (2022). O Índice Oceânico Niño (ONI) foi obtido da tabela oficial do Centro de Previsão Climática (CPC) da NOAA. Os produtos MOD17A2HGF e MOD16A2GF são distribuídos em compostos de oito dias com resolução espacial de 500 m (1 km no MOD11A2), e a PSN corresponde à diferença entre a Produtividade Primária Bruta (GPP) e a respiração de manutenção de folhas e raízes finas. Para cada composto calculou-se a média espacial dos pixels válidos de cada bioma, delimitado pelo mapa de biomas do IBGE na escala 1:250.000 (IBGE, 2019) recortado pelo limite estadual da Bahia, na projeção nativa de cada produto e com os fatores de escala oficiais. Os compostos foram então agregados em períodos mensais de quatro compostos consecutivos, em janelas fixas de dia do ano, reproduzindo a agregação empregada por Benfica et al. (2022): a PSN, a EV e a ETP foram somadas e a TST foi mediada em cada período; o WAI foi calculado como a razão EV/ETP e a área queimada como o número de pixels queimados no mês multiplicado pela área do pixel (25 ha). Toda a série de 2001 a 2025 foi processada de forma homogênea com essas coleções, em vez de se emendar a base original de 2001 a 2020 aos anos recentes; a reprodução da base de Benfica et al. (2022) por esse procedimento apresentou correlação superior a 0,97 com a série original para todas as variáveis, com erro mediano inferior a 3,5%. A base mensal consolidada está reproduzida integralmente no Apêndice A e o código-fonte está disponível em repositório público, permitindo a reprodução de todos os resultados. As variáveis dependentes e preditoras que compõem o modelo estão detalhadas na Tabela 1.")
for i, t in [(290, "MOD17A2HGF, Coleção 6.1 (NASA), via GEE"), (294, "MOD16A2GF, Coleção 6.1 (NASA), via GEE"), (298, "GPM IMERG Final mensal V07 (NASA GES DISC), via GEE"),
             (302, "MOD11A2, Coleção 6.1 (NASA), via GEE"), (306, "ETR/ETP do MOD16A2GF"), (310, "MCD64A1, Coleção 6.1 (NASA), via GEE")]:
    replace_paragraph(i, t)
replace_substring(323, "os três últimos meses de 2025 foram excluídos por ainda não haver dado de precipitação publicado",
                  "os três últimos meses de 2025 foram excluídos porque a NASA encerrou a versão 07 do IMERG Final Run em setembro de 2025, e os meses seguintes só serão publicados na versão 08, prevista para o fim de 2026 (NASA, 2026)")

# ---------------------------------------------------------------- 2. 6.2: parágrafo sobre a mudança de importância
after[445] = new_par(
 "A comparação entre os modelos com e sem as componentes harmônicas (Tabela A3) também esclarece por que a importância relativa das variáveis climáticas se reordena quando a sazonalidade é representada explicitamente. Sem os harmônicos, a precipitação e a temperatura recebem parte do crédito que pertence ao próprio calendário, pois oscilam com a estação juntamente com a PSN; na presença deles, cada preditor passa a ser avaliado pela informação que acrescenta além do ciclo anual, isto é, pelas anomalias. Nessa condição a importância da precipitação cai para cerca de 10% (de 29% para 10% no Cerrado e de 24% para 10% na Caatinga) e a da temperatura recua na Mata Atlântica (de 39% para 15%), porque, removida a estação, a chuva do próprio mês quase não se correlaciona com a anomalia de PSN (r = 0,02 no Cerrado e 0,16 na Caatinga; Tabela A4): a chuva é um fluxo de entrada ruidoso e defasado, e a vegetação responde à água que permaneceu disponível no solo nas semanas seguintes, não ao total precipitado no mês. A evapotranspiração, ao contrário, mantém ou amplia sua importância (de 34% para 38% no Cerrado) porque mede a água efetivamente utilizada pela vegetação, e sua anomalia acompanha de perto a anomalia de PSN (r entre 0,73 e 0,93): transpiração e assimilação de carbono ocorrem pelos mesmos estômatos, de modo que um mês em que a vegetação transpira mais que o normal para a época é um mês em que fotossintetiza mais que o normal. A temperatura permanece relevante na Mata Atlântica e na Caatinga como modulador negativo (correlação das anomalias de −0,58 e −0,77), expressão do estresse térmico e hídrico dos meses mais quentes que o usual. Em síntese, os harmônicos absorvem o ciclo anual determinístico da produtividade (fotoperíodo, radiação e fenologia foliar) e deixam às variáveis climáticas o papel de explicar os desvios em relação ao ano típico, que é justamente a informação relevante para a análise interanual e para o ENSO, tratada adiante.", BODY_PP)

# ---------------------------------------------------------------- 3. 6.5 reescrita + Tabela 6 + Figura 14
B = pd.read_csv(D + "B_enso_efeito_nas_variaveis.csv"); T = pd.read_csv(D + "D_boxplots_testes_dispersao_extremos.csv"); T = T[T.tipo == "anomalia"]
rows = []
for bio in ["Mata Atlântica", "Cerrado", "Caatinga"]:
    for v, rot in [("NP", "PSN"), ("EV", "EV"), ("PRE", "PRE"), ("TST", "TST"), ("WAI", "WAI")]:
        b = B[(B.bioma == bio) & (B.variavel == v)]; t = T[(T.bioma == bio) & (T.variavel == v)]
        if b.empty or t.empty: continue
        en = b[b.fase == "El Niño"].iloc[0]; ln = b[b.fase == "La Niña"].iloc[0]; tt = t.iloc[0]
        def s(val, p): return ("+" if val > 0 else "") + f1(val) + ("*" if p < 0.05 else "")
        rows.append([bio if v == "NP" else "", rot, s(en.dif_vs_neutro_pct, en.p_mannwhitney_vs_neutro), s(ln.dif_vs_neutro_pct, ln.p_mannwhitney_vs_neutro),
                     fp(tt.p_kruskal_mediana), fp(tt.p_fligner_dispersao), fp(tt.p_qui2_extremos), f"{tt['pct_meses_abaixo_P10_El Niño']:.0f} / {tt['pct_meses_abaixo_P10_Neutro']:.0f} / {tt['pct_meses_abaixo_P10_La Niña']:.0f}"])
tab6 = new_table(["Bioma", "Variável", "Δ El Niño (%)", "Δ La Niña (%)", "p posição", "p dispersão", "p extremos", "% meses abaixo do P10 (EN / N / LN)"], rows, [1500, 900, 1050, 1050, 950, 1000, 1000, 1622])
cap6 = new_par("Tabela 6 - Anomalias médias (%) das variáveis nos meses de El Niño e de La Niña em relação aos meses neutros (* p < 0,05 no teste de Mann-Whitney) e valores-p dos testes de posição central (Kruskal-Wallis), dispersão (Fligner-Killeen) e frequência de meses extremos (qui-quadrado), com a proporção de meses abaixo do décimo percentil por fase, 2001–2025.", CAP_PP)
nota6 = new_par("EN = El Niño; N = Neutro; LN = La Niña. Anomalia = desvio em relação à média do mês do calendário em toda a série, em porcentagem dessa média. Sob ausência de efeito, esperam-se 10% dos meses abaixo do P10 em cada fase.", CAP_PP)

replace_paragraph(515,
 "A fase ENSO de cada mês foi classificada pelo critério oficial da NOAA (ONI igual ou superior a +0,5 °C, ou igual ou inferior a −0,5 °C, por pelo menos cinco trimestres móveis consecutivos), o que resultou em 151 meses neutros, 76 de El Niño e 70 de La Niña. Como os episódios de ENSO atingem o máximo entre o fim e o início do ano, as fases não se distribuem uniformemente pelo calendário: de 11% a 13% dos meses de El Niño e de La Niña ocorrem em cada um dos meses de novembro a fevereiro, contra 3% a 6% em maio, junho e julho, enquanto os meses neutros mostram o padrão inverso. A comparação direta de valores brutos entre fases confunde, portanto, o efeito do ENSO com o da estação do ano: a precipitação média do Cerrado, por exemplo, é de 124 mm nos meses de La Niña e de 59 mm nos neutros, mas essa diferença desaparece quase por completo quando se retira o ciclo anual. Por essa razão, a análise foi conduzida sobre anomalias mensais, definidas como o desvio de cada valor em relação à média do respectivo mês do calendário em toda a série e expressas em porcentagem dessa média (Tabela 6). Para cada variável, três propriedades da distribuição foram comparadas entre fases: a posição central (teste de Kruskal-Wallis entre as três fases e teste de Mann-Whitney de cada fase ativa contra a neutra), a dispersão (teste de Fligner-Killeen) e a frequência de meses extremos, definida como a proporção de meses abaixo do décimo percentil ou acima do nonagésimo percentil da série completa (teste de qui-quadrado). As Figuras 11 a 13 apresentam as distribuições brutas por fase; os valores exatos de cada diagrama de caixa (mínimo, quartis, mediana, média, máximo e número de meses) constam da Tabela A5 do Apêndice A.")
after[515] = cap6 + tab6 + nota6
replace_paragraph(516,
 "Na Mata Atlântica, a temperatura da superfície foi a variável mais sensível às fases do ENSO: nos meses de El Niño ela ficou, em média, 3,0% (cerca de 0,9 °C) acima do normal da época (p < 0,001), e 25% desses meses situaram-se no decil mais quente da série, contra 6% dos meses neutros (Figura 11). A evapotranspiração e a precipitação não diferiram na posição central (p = 0,43 e p = 0,35), mas ambas apresentaram maior dispersão nas fases ativas (Fligner-Killeen, p = 0,006 e p = 0,019). A PSN mostrou comportamento análogo ao dessas variáveis hídricas: sua mediana quase não muda entre fases (133,3, 134,4 e 133,6 gC·m⁻²·mês⁻¹ em El Niño, neutro e La Niña; Tabela A5), mas nos meses de El Niño a anomalia média foi de −5,5% (p = 0,009), a dispersão aumentou (p = 0,043) e a frequência de meses com produtividade extremamente baixa, abaixo do décimo percentil, chegou a 22%, contra 5% nos meses neutros e 9% nos de La Niña (p < 0,001); o mínimo observado sob El Niño (79,0 gC·m⁻²·mês⁻¹) é 15 unidades inferior ao mínimo dos meses neutros (94,4). O El Niño, portanto, não reduz a produtividade típica do bioma úmido, mas quadruplica a frequência de meses de produtividade muito baixa, o que explica por que o teste de posição central isolado, aplicado aos valores brutos, não detectava efeito. A La Niña não produziu resposta na Mata Atlântica em nenhuma das três propriedades. Vale distinguir que a sensibilidade da TST às fases do ENSO e a importância da TST como preditora da PSN são propriedades distintas: a primeira descreve como o fenômeno modula a temperatura, enquanto a segunda (Figura 8) reflete o peso da temperatura no controle direto da produtividade; a TST atua, assim, como elo entre a variabilidade climática de larga escala e a resposta produtiva local da vegetação.")
replace_paragraph(520,
 "No Cerrado, retirado o ciclo anual, a precipitação mensal não diferiu entre fases na posição central (p = 0,46), embora sua dispersão tenha aumentado (p = 0,001); o sinal do ENSO manifestou-se nas variáveis que integram o balanço hídrico: nos meses de La Niña a evapotranspiração ficou 11,0% acima do normal da época e o WAI 15,4% (ambos p < 0,001), e nos de El Niño 7,7% e 8,0% (p = 0,07 e p = 0,20) (Figura 12). A PSN respondeu no mesmo sentido, com anomalia média de +12,4% nos meses de La Niña (p < 0,001; mediana de 112,3 contra 95,0 gC·m⁻²·mês⁻¹ nos meses neutros) e de +5,4% nos de El Niño (p = 0,36). O efeito da La Niña desloca a distribuição inteira, e não apenas os extremos: o primeiro quartil sobe de 66,7 para 86,6 gC·m⁻²·mês⁻¹ e a proporção de meses no decil mais baixo cai de 10% para 4%. Esse resultado é consistente com a literatura que documenta chuvas acima do normal no Brasil Central durante a La Niña e evidencia que, no Cerrado, o que transmite o sinal do ENSO à produtividade não é a chuva do próprio mês, e sim a água efetivamente disponível e utilizada pela vegetação, integrada ao longo de semanas.")
replace_paragraph(524,
 "Na Caatinga o padrão foi semelhante: nos meses de La Niña a evapotranspiração ficou 10,5% acima do normal (p = 0,003), a temperatura 2,2% abaixo (p = 0,012) e a PSN 10,5% acima (p = 0,002; mediana de 94,6 contra 82,4 gC·m⁻²·mês⁻¹), sem diferença de posição central na precipitação (p = 0,75), cuja dispersão, contudo, aumentou nas fases ativas (p = 0,007) (Figura 13). Nos meses de El Niño a PSN ficou 3,4% abaixo do normal, diferença não significativa (p = 0,46), ainda que 14% desses meses tenham caído no decil mais baixo, contra 11% dos neutros e 4% dos de La Niña. Esse comportamento é coerente com o regime pulsado do bioma semiárido, no qual a produtividade responde de forma quase imediata à disponibilidade de água, e com os achados de Silva et al. (2026), que associam anos de El Niño a reduções da produtividade na Caatinga.")
med = new_par(
 "Para quantificar quanto da resposta da PSN é explicado pelas variáveis intermediárias, o modelo ajustado foi utilizado como instrumento de mediação: prevendo-se a PSN com os preditores em sua climatologia mensal e, alternativamente, com cada preditor deslocado pela anomalia média observada na fase, obtém-se a mudança de PSN atribuível a cada canal. Nos meses de La Niña, o modelo reproduz +8,6% de PSN no Cerrado (observado +12,4%) e +9,2% na Caatinga (observado +10,5%), quase inteiramente pela via da evapotranspiração; nos meses de El Niño na Mata Atlântica, o modelo reproduz −3,1% (observado −5,5%), sobretudo pela via da temperatura. Assim, de 70% a 90% da resposta da PSN ao ENSO nos biomas sazonais é mediada pela água efetivamente utilizada pela vegetação, e cerca de metade da resposta no bioma úmido é mediada pelo aquecimento da superfície, restando nesse caso uma parcela não explicada pelos preditores do mês, possivelmente associada à radiação e à defasagem da resposta.", BODY_PP)
lag = new_par(
 "A resposta não se restringe ao mês em fase ENSO. A correlação de Spearman entre o ONI de um mês e a anomalia de PSN dos meses seguintes é negativa nos três biomas (El Niño reduz e La Niña eleva a PSN) e decai em ritmos distintos: na Caatinga o efeito é máximo no próprio mês e no seguinte (ρ = −0,19) e deixa de ser significativo após quatro meses; na Mata Atlântica é máximo com um a dois meses de atraso (ρ = −0,16) e persiste por cerca de cinco meses; no Cerrado é fraco no mês corrente (ρ = −0,10, não significativo), mas significativo de um a doze meses depois, com um segundo máximo entre nove e onze meses (ρ = −0,16). Os compósitos por fase (Figura 14) confirmam essa distinção. Após meses de La Niña, a anomalia média de PSN na Caatinga é de +9% a +10% nos três primeiros meses, cai para +6% a +7% no terceiro e no quarto mês e deixa de ser significativa após seis meses, uma resposta pulsada e curta, típica da vegetação caducifólia do semiárido; no Cerrado, o ganho de +8% a +9% dos primeiros meses não decai, mantendo-se em +9% aos seis e +10% aos nove meses (p ≤ 0,001 em todas as defasagens até nove meses), o que sugere que o excedente hídrico da estação chuvosa em La Niña, armazenado em solos profundos e explorado por sistemas radiculares extensos, sustenta a produtividade da estação seca subsequente. Pelo mesmo mecanismo, o El Niño quase não aparece no Cerrado no mês corrente (+1%) e só se manifesta tardiamente (−3% aos três e quatro meses e −6% aos doze meses), como um déficit de recarga cobrado na estação seguinte. Na Mata Atlântica, o El Niño reduz a PSN em 4% a 5% de forma significativa do mês corrente até o sexto mês, com resíduo até doze meses, enquanto a La Niña não produz ganho em nenhuma defasagem, uma assimetria coerente com o canal térmico: o bioma úmido não é limitado por água em condições médias, de modo que água adicional não o beneficia, mas calor adicional o prejudica. Os eventos mais intensos ilustram o padrão: durante o El Niño de 2015–2016 (ONI máximo de 2,6 °C), a PSN ficou 8%, 6% e 10% abaixo do normal na Mata Atlântica, no Cerrado e na Caatinga, e 12%, 36% e 19% abaixo nos três meses seguintes; durante a La Niña de 2010–2011, ficou 18% e 16% acima no Cerrado e na Caatinga.", BODY_PP)
# figura 14
shutil.copy(D + "C_compositos_PSN_por_fase.png", "docx_rev/word/media/image18.png")
cx = 5753100; cy = int(cx * 600 / 2250)
drawing = (f'<w:drawing><wp:inline distT="0" distB="0" distL="114300" distR="114300"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
           f'<wp:docPr id="1174108001" name="Imagem 39"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
           f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
           f'<pic:nvPicPr><pic:cNvPr id="1174108001" name="Imagem 39"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rId51"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
           f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>')
fig_pp = ppr_inserted('<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="0"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr>')
fig14 = f"<w:p>{fig_pp}{ins_tag()}<w:r>{drawing}</w:r></w:ins></w:p>" + new_par("Figura 14 - Anomalia média da PSN (%) durante e após meses de El Niño e de La Niña, por defasagem de 0 a 12 meses, com intervalo de confiança de 95% (bootstrap), nos três biomas.", FIGCAP_PP, FIGCAP_RP)
after[524] = med + lag + fig14   # depois do parágrafo da Caatinga (antes da legenda da Figura 13? não: 525 é a legenda) 
# corrige: inserir depois da Figura 13 (parágrafos 525-527), ou seja, após 527
after[527] = after.pop(524)
replace_paragraph(528,
 "Quando a intensidade do ONI é usada como preditor contínuo, o poder explicativo permanece baixo: a regressão linear simples do ONI sobre cada variável climática explicou no máximo 3,0% de sua variância (temperatura da Mata Atlântica), e os tamanhos de efeito das fases sobre as anomalias (ε² de Kruskal-Wallis) ficaram entre 0,02 e 0,08. Esses valores indicam que o ENSO responde por uma fração pequena da variabilidade mensal, dominada pelo ciclo anual e pela variabilidade meteorológica local; não indicam, contudo, ausência de efeito, pois os desvios médios associados às fases (de 5% a 12% da PSN) são sistemáticos, coerentes entre variáveis e biomas e, no caso da Mata Atlântica, concentrados nos extremos. A influência do ENSO sobre o sistema regional não se manifesta, portanto, de forma linear e direta, mas por relações indiretas, defasadas e, em parte, assimétricas entre as fases, mais adequadamente representadas pela classificação em fases e pela análise de anomalias.")
replace_paragraph(529,
 "A interpretação conjunta desses resultados sustenta um padrão de influência indireta, na qual o ENSO atua como forçante de larga escala que modula variáveis intermediárias, com canais distintos por bioma: a evapotranspiração e o WAI, expressões da água efetivamente disponível, no Cerrado e na Caatinga, onde a La Niña eleva a produtividade típica em cerca de 10% a 12%; e a temperatura da superfície na Mata Atlântica, onde o El Niño não altera a produtividade típica, mas aumenta a frequência de meses de produtividade muito baixa.")
replace_paragraph(530,
 "A ausência de deslocamento da produtividade típica da Mata Atlântica, apesar da resposta significativa da temperatura, sugere que esse ecossistema apresenta capacidade parcial de amortecimento frente às oscilações climáticas de larga escala, decorrente de sua maior reserva hídrica e da menor amplitude de seu ciclo anual; esse amortecimento, contudo, falha nos meses mais quentes, quando a produtividade cai de forma abrupta. No Cerrado e na Caatinga, onde a produtividade é governada pelo balanço hídrico, o amortecimento é menor e o sinal do ENSO chega à PSN de forma sistemática, com persistência de vários meses no Cerrado.")

# ---------------------------------------------------------------- 4. resumo, abstract, conclusões
replace_substring(64, "A análise do El Niño–Oscilação Sul (ENSO) indicou influência predominantemente indireta sobre a produtividade, com efeito direto sobre a PSN detectado apenas na Caatinga.",
 "A análise do El Niño–Oscilação Sul (ENSO), conduzida sobre anomalias mensais, indicou influência indireta e defasada sobre a produtividade: a La Niña elevou a PSN típica em 10% a 12% no Cerrado e na Caatinga, mediada pela evapotranspiração, com persistência de até nove meses no Cerrado; na Mata Atlântica, o El Niño não alterou a produtividade típica, mas quadruplicou a frequência de meses de produtividade extremamente baixa, mediado pelo aquecimento da superfície.")
replace_substring(74, "The analysis of the El Niño–Southern Oscillation (ENSO) indicated a predominantly indirect influence on productivity, with a direct effect on PSN detected only in the Caatinga.",
 "The analysis of the El Niño–Southern Oscillation (ENSO), performed on monthly anomalies, indicated an indirect and lagged influence on productivity: La Niña raised typical PSN by 10–12% in the Cerrado and Caatinga, mediated by evapotranspiration, with persistence of up to nine months in the Cerrado; in the Atlantic Forest, El Niño did not change typical productivity but quadrupled the frequency of months with extremely low productivity, mediated by surface warming.")
replace_paragraph(543,
 "A H3 confirmou-se em sua essência: o ONI explicou no máximo 3% da variância das variáveis climáticas e não atua de forma linear e direta sobre a PSN. A análise em anomalias mensais, porém, revelou um efeito sistemático e mediado: a La Niña elevou a PSN típica em 10% a 12% no Cerrado e na Caatinga, por meio da evapotranspiração e do WAI, com resposta imediata e curta na Caatinga e persistente por até nove meses no Cerrado; na Mata Atlântica, o El Niño não alterou a produtividade típica, mas elevou de 5% para 22% a frequência de meses de produtividade extremamente baixa, por meio do aquecimento da superfície. O padrão é, portanto, o de uma influência indireta, defasada e assimétrica entre fases, transmitida pela água efetivamente utilizada pela vegetação nos biomas sazonais e pela temperatura no bioma úmido.")
replace_substring(545, "Adicionalmente, a investigação do efeito do ENSO confirmou sua atuação como forçante climática indireta, mediada principalmente pelas variáveis de temperatura e precipitação, com efeito direto sobre a PSN detectado apenas na Caatinga.",
 "Adicionalmente, a investigação do efeito do ENSO confirmou sua atuação como forçante climática indireta, transmitida pela evapotranspiração no Cerrado e na Caatinga e pela temperatura na Mata Atlântica, com respostas da PSN de sinais opostos entre as fases e defasadas em até nove meses.")

# ---------------------------------------------------------------- 5. Tabela A5 (apêndice) e referências
Lb = pd.read_csv(D + "D_boxplots_valores_exatos.csv"); Lb = Lb[Lb.tipo == "bruto"]
rowsA = []
for bio in ["Mata Atlântica", "Cerrado", "Caatinga"]:
    for v, rot in [("NP", "PSN"), ("EV", "EV"), ("PRE", "PRE"), ("TST", "TST"), ("WAI", "WAI")]:
        for f in ["El Niño", "Neutro", "La Niña"]:
            r = Lb[(Lb.bioma == bio) & (Lb.variavel == v) & (Lb.fase == f)].iloc[0]
            dec = 3 if v == "WAI" else 1; fmt = lambda z: f"{z:.{dec}f}".replace(".", ",")
            rowsA.append([bio if (v == "NP" and f == "El Niño") else "", rot if f == "El Niño" else "", f, str(int(r.n)), fmt(r.minimo), fmt(r.Q1), fmt(r.mediana), fmt(r.media), fmt(r.Q3), fmt(r.maximo), str(int(r.n_outliers))])
tabA5 = new_table(["Bioma", "Variável", "Fase", "n", "Mín.", "Q1", "Mediana", "Média", "Q3", "Máx.", "Outliers"], rowsA, [1400, 800, 850, 500, 800, 800, 850, 800, 800, 800, 672], font_sz=16)
capA5 = new_par("Tabela A5 - Valores dos diagramas de caixa das Figuras 11 a 13: estatísticas descritivas das variáveis por fase ENSO (critério oficial da NOAA), valores brutos mensais, 2001–2025. PSN em gC·m⁻²·mês⁻¹, EV e PRE em mm·mês⁻¹, TST em °C, WAI adimensional; outliers = valores além de 1,5 vez o intervalo interquartil.", CAP_PP)
after[7339] = capA5 + tabA5
refs = {
 7348: ["GIGLIO, L.; BOSCHETTI, L.; ROY, D. P.; HUMBER, M. L.; JUSTICE, C. O. The Collection 6 MODIS burned area mapping algorithm and product. Remote Sensing of Environment, v. 217, p. 72-85, 2018. DOI: 10.1016/j.rse.2018.08.005.",
        "GORELICK, N.; HANCHER, M.; DIXON, M.; ILYUSHCHENKO, S.; THAU, D.; MOORE, R. Google Earth Engine: planetary-scale geospatial analysis for everyone. Remote Sensing of Environment, v. 202, p. 18-27, 2017. DOI: 10.1016/j.rse.2017.06.031."],
 7350: ["HUFFMAN, G. J.; STOCKER, E. F.; BOLVIN, D. T.; NELKIN, E. J.; TAN, J. GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree V07. Greenbelt: Goddard Earth Sciences Data and Information Services Center (GES DISC), 2023. DOI: 10.5067/GPM/IMERG/3B-MONTH/07."],
 7351: ["INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Biomas e sistema costeiro-marinho do Brasil: compatível com a escala 1:250 000. Rio de Janeiro: IBGE, 2019. (Relatórios Metodológicos, v. 45)."],
 7361: ["NATIONAL AERONAUTICS AND SPACE ADMINISTRATION (NASA). IMERG V08 transition schedule. Greenbelt: NASA Global Precipitation Measurement, 2026. Disponível em: https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule. Acesso em: 17 set. 2026."],
 7365: ["RUNNING, S. W.; MU, Q.; ZHAO, M.; MORENO, A. User's guide: MODIS global terrestrial evapotranspiration (ET) product (MOD16A2/A3 and year-end gap-filled MOD16A2GF/A3GF), Collection 6.1. Missoula: Numerical Terradynamic Simulation Group, University of Montana, 2021."],
 7368: ["WAN, Z.; HOOK, S.; HULLEY, G. MODIS/Terra Land Surface Temperature/Emissivity 8-Day L3 Global 1 km SIN Grid V061 (MOD11A2). Sioux Falls: NASA EOSDIS Land Processes DAAC, 2021. DOI: 10.5067/MODIS/MOD11A2.061."],
}
for i, lst in refs.items(): after[i] = after.get(i, "") + "".join(new_par(t, REF_PP) for t in lst)

# ---------------------------------------------------------------- aplica
out = []; pos = 0
for i, m in enumerate(re.finditer(r"<w:p[ >].*?</w:p>", x, re.S)):
    out.append(x[pos:m.start()]); out.append(edits.get(i, m.group(0))); out.append(after.get(i, "")); pos = m.end()
out.append(x[pos:]); y = "".join(out)
open(SRC, "w", encoding="utf-8").write(y)
rels = open("docx_rev/word/_rels/document.xml.rels", encoding="utf-8").read()
rels = rels.replace("</Relationships>", '<Relationship Id="rId51" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image18.png"/></Relationships>')
open("docx_rev/word/_rels/document.xml.rels", "w", encoding="utf-8").write(rels)
print("edits:", len(edits), "inserções:", len(after), "| ins:", y.count("<w:ins "), "del:", y.count("<w:del "))
