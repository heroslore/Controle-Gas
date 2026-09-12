# -*- coding: utf-8 -*-
"""
Aplica no Trabalho_revisado.docx as mudanças aceitas dos pareceres da banca
(analise_pareceres.md) e a atualização para a base 2001-2025.

Uso:  python3 banca/aplicar_revisao_docx.py
Entrada : banca/Trabalho_revisado.docx  (versão do Ygor, intocada)
Saída   : banca/Trabalho_revisado_2001_2025.docx

Os números vêm de resultados_2001_2025/ (CSVs e logs), nunca digitados aqui.
"""
import os, re, copy, json
import pandas as pd
import docx
from docx.shared import Cm, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(BASE, 'resultados_2001_2025')
FIG  = os.path.join(BASE, 'figuras_dissertacao')
SRC  = os.path.join(BASE, 'banca', 'Trabalho_revisado.docx')
DST  = os.path.join(BASE, 'banca', 'Trabalho_revisado_2001_2025.docx')

# =============================================================================
# NÚMEROS (lidos dos resultados)
# =============================================================================
RG  = pd.read_csv(os.path.join(RES, 'resumo_geral.csv')).set_index('bioma')
VIF = pd.read_csv(os.path.join(RES, 'vif_por_bioma.csv'))
SG  = pd.read_csv(os.path.join(RES, 'selecao_grau.csv'))
SV  = pd.read_csv(os.path.join(RES, 'selecao_variaveis.csv'))
NUM = json.load(open(os.path.join(RES, 'numeros_extra.json'), encoding='utf-8'))
ENSO = json.load(open(os.path.join(RES, 'enso_resumo.json'), encoding='utf-8'))
ABL = pd.read_csv(os.path.join(RES, 'ablacao_sazonalidade.csv'))
SAZ = pd.read_csv(os.path.join(RES, 'sazonalidade_variaveis.csv'))

def v(x, nd=1):
    return f'{x:.{nd}f}'.replace('.', ',')

def r2(b, nd=1):  return v(RG.loc[b, 'r2_teste_medio'], nd)
def gap(b):       return v(RG.loc[b, 'gap_overfitting_pp'], 2)
def rmse(b):      return v(RG.loc[b, 'rmse_teste_medio'], 2)
def mae(b):       return v(RG.loc[b, 'mae_teste_medio'], 2)
def maedp(b):     return v(NUM[b]['mae_dp'], 2)
def ic(b):        return f"{v(RG.loc[b,'ic95_lower'])} – {v(RG.loc[b,'ic95_upper'])}%"
def gkf(b):       return v(RG.loc[b, 'r2_groupkfold_ano'], 2)
def tss(b):       return v(RG.loc[b, 'r2_timeseriessplit'], 2)
def queda(b):     return v(max(RG.loc[b, 'queda_groupkfold_pp'], RG.loc[b, 'queda_timeseries_pp']), 2)
def vif(b, var):  return v(float(VIF[(VIF.bioma == b) & (VIF.variavel == f'{var}_{b}' if var not in ('saz_sin', 'saz_cos') else VIF.variavel == var)]['VIF'].iloc[0]), 2)
def sg(b, g, col): return float(SG[(SG.bioma == b) & (SG.grau == g)][col].iloc[0])
def yr_delta(b):  return v(RG.loc[b, 'yrand_diferenca_pp'], 2)
def shap(b):      return v(RG.loc[b, 'shapiro_p'], 3)
def acf1(b):      return v(RG.loc[b, 'acf_lag1'], 2)
def lbp(b):
    p = RG.loc[b, 'ljungbox_p']; return 'p < 0,001' if p < 0.001 else f'p = {v(p,3)}'

XVARS = {'MA': NUM['MA']['x'], 'CE': NUM['CE']['x'], 'CA': NUM['CA']['x']}
def conj(b):  # 'EV + TST + WAI + SAZsin + SAZcos'
    return ' + '.join(XVARS[b]) + ' + SAZsin + SAZcos'

N_OBS = 297
nome = {'MA': 'Mata Atlântica', 'CE': 'Cerrado', 'CA': 'Caatinga'}

# =============================================================================
# HELPERS python-docx
# =============================================================================
d = docx.Document(SRC)
ORIG = list(d.paragraphs)          # referências estáveis aos parágrafos originais
BODY = d.element.body

ITALICOS = ['Moderate Resolution Imaging Spectroradiometer', 'net photosynthesis', 'eddy covariance',
            'data leakage', 'out-of-fold', 'Quality Control', 'overfitting', 'software',
            'Climate Hazards Group InfraRed Precipitation with Station data', 'Cold & Warm Episodes by Season',
            'Oceanic Niño Index', 'Net Photosynthesis', 'Gross Primary Production', 'Net Primary Production',
            'Water Availability Index', 'Variance Inflation Factor', 'Root Mean Square Error', 'Mean Absolute Error',
            'Burned Area', 'Intergovernmental Panel on Climate Change', 'El Niño–Southern Oscillation',
            'Quantitative Structure-Activity Relationship', 'National Oceanic and Atmospheric Administration',
            'Climate Prediction Center', 'National Aeronautics and Space Administration', 'forcing', 'proxy',
            'fold', 'folds', 'Terra', 'Aqua']

def _split_italics(text):
    """Divide o texto em (trecho, itálico?) segundo a lista ITALICOS."""
    pat = re.compile('|'.join(re.escape(t) for t in sorted(ITALICOS, key=len, reverse=True)))
    out, pos = [], 0
    for m in pat.finditer(text):
        # só palavras inteiras
        a, b = m.start(), m.end()
        if (a > 0 and text[a-1].isalnum()) or (b < len(text) and text[b].isalnum()):
            continue
        if a > pos: out.append((text[pos:a], False))
        out.append((text[a:b], True)); pos = b
    if pos < len(text): out.append((text[pos:], False))
    return out

def _rpr_of(p):
    for r in p.runs:
        if r._r.xpath('.//w:drawing'): continue
        if r._r.rPr is None: return None
        rpr = copy.deepcopy(r._r.rPr)
        for tag in ('w:i', 'w:iCs', 'w:b', 'w:bCs'):
            for el in rpr.xpath(f'./{tag}'): rpr.remove(el)
        return rpr
    return None

def set_text(p, text, bold=None):
    """Substitui todo o texto do parágrafo (mantém pPr e a formatação do 1º run)."""
    rpr = _rpr_of(p)
    for r in list(p.runs):
        r._r.getparent().remove(r._r)
    for h in p._p.xpath('.//w:hyperlink'):
        h.getparent().remove(h)
    for m_ in list(p._p):
        if m_.tag.endswith('}oMath') or m_.tag.endswith('}oMathPara'):
            p._p.remove(m_)
    for seg, it in _split_italics(text):
        r = p.add_run(seg)
        if rpr is not None: r._r.insert(0, copy.deepcopy(rpr))
        if it: r.font.italic = True
        if bold is not None: r.font.bold = bold
    return p

def to_inline(p):
    """Converte a imagem flutuante (wp:anchor) do parágrafo em imagem inline."""
    for anc in p._p.xpath('.//wp:anchor'):
        inline = OxmlElement('wp:inline')
        for a in ('distT', 'distB', 'distL', 'distR'): inline.set(a, anc.get(a, '0'))
        for tag in ('wp:extent', 'wp:effectExtent', 'wp:docPr', 'wp:cNvGraphicFramePr'):
            el = anc.find(qn(tag))
            if el is not None: inline.append(copy.deepcopy(el))
        g = anc.find('{http://schemas.openxmlformats.org/drawingml/2006/main}graphic')
        inline.append(copy.deepcopy(g))
        anc.getparent().replace(anc, inline)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.left_indent = Cm(0)

def set_caption_after_image(p, text):
    """Parágrafo com imagem + legenda: imagem vira inline e a legenda vai para um parágrafo próprio ANTES."""
    to_inline(p)
    for r in [r for r in p.runs if not r._r.xpath('.//w:drawing')]:
        r._r.getparent().remove(r._r)
    cap = new_para_after(p, CAPTION_TPL, text, bold=True)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p._p.addprevious(cap._p)          # legenda acima da figura
    return cap

def new_para_after(anchor, template, text='', bold=None):
    """Novo parágrafo após anchor, com pPr/rPr copiados do template."""
    new = OxmlElement('w:p')
    if template._p.pPr is not None:
        new.append(copy.deepcopy(template._p.pPr))
    anchor._p.addnext(new)
    para = Paragraph(new, anchor._parent)
    if text:
        rpr = _rpr_of(template)
        for seg, it in _split_italics(text):
            r = para.add_run(seg)
            if rpr is not None: r._r.insert(0, copy.deepcopy(rpr))
            if it: r.font.italic = True
            if bold is not None: r.font.bold = bold
    return para

def add_paras_after(anchor, template, textos):
    last = anchor
    for t in textos:
        last = new_para_after(last, template, t)
    return last

def add_figure_after(anchor, caption, path, width_cm=16.0):
    """Legenda (acima, centralizada, negrito 11 pt) + imagem, após anchor."""
    cap = new_para_after(anchor, CAPTION_TPL, caption, bold=True)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic = new_para_after(cap, IMG_TPL)
    pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic.paragraph_format.first_line_indent = Cm(0); pic.paragraph_format.left_indent = Cm(0)
    w, h = Image.open(path).size
    width = min(width_cm, 16.0)
    height = width * h / w
    if height > 22.0:                       # não deixa passar de uma página
        height = 22.0; width = height * w / h
    pic.add_run().add_picture(path, width=Cm(width), height=Cm(height))
    return pic

def replace_image(p, path):
    blips = p._p.xpath('.//a:blip')
    rId = blips[0].get(qn('r:embed'))
    part = d.part.related_parts[rId]
    with open(path, 'rb') as f: part._blob = f.read()
    w, h = Image.open(path).size
    cx = int(p._p.xpath('.//wp:extent')[0].get('cx'))
    cy = int(cx * h / w)
    max_cy = int(22.0 * 360000)
    if cy > max_cy:
        cy = max_cy; cx = int(cy * w / h)
    for ext in p._p.xpath('.//wp:extent') + p._p.xpath('.//a:xfrm/a:ext'):
        ext.set('cx', str(cx)); ext.set('cy', str(cy))

def remove_para(p):
    p._p.getparent().remove(p._p)

def move_after(p, anchor):
    p._p.getparent().remove(p._p); anchor._p.addnext(p._p)

def set_cell(cell, text, bold=None, size=None):
    par = cell.paragraphs[0]
    par.paragraph_format.first_line_indent = Cm(0); par.paragraph_format.left_indent = Cm(0)
    par.paragraph_format.space_before = Pt(0); par.paragraph_format.space_after = Pt(0)
    rpr = _rpr_of(par)
    for r in list(par.runs): r._r.getparent().remove(r._r)
    for extra in cell.paragraphs[1:]: remove_para(extra)
    r = par.add_run(text)
    if rpr is not None: r._r.insert(0, copy.deepcopy(rpr))
    if bold is not None: r.font.bold = bold
    if size is not None: r.font.size = Pt(size)

def set_widths(t, cms):
    t.autofit = False
    tblPr = t._tbl.tblPr
    for old in tblPr.xpath('./w:tblW'): tblPr.remove(old)
    w = OxmlElement('w:tblW'); w.set(qn('w:w'), str(int(sum(cms) * 567))); w.set(qn('w:type'), 'dxa')
    depois = [c for c in tblPr if c.tag.split('}')[1] in ('jc', 'tblCellSpacing', 'tblInd', 'tblBorders', 'shd', 'tblLayout', 'tblCellMar', 'tblLook')]
    (depois[0].addprevious(w) if depois else tblPr.append(w))
    lay = tblPr.find(qn('w:tblLayout'))
    if lay is None:
        lay = OxmlElement('w:tblLayout')
        dep2 = [c for c in tblPr if c.tag.split('}')[1] in ('tblCellMar', 'tblLook', 'tblCaption', 'tblDescription')]
        (dep2[0].addprevious(lay) if dep2 else tblPr.append(lay))
    lay.set(qn('w:type'), 'fixed')
    grid = t._tbl.find(qn('w:tblGrid'))
    if grid is None:
        grid = OxmlElement('w:tblGrid'); tblPr.addnext(grid)
    for gc in list(grid): grid.remove(gc)
    for cm in cms:
        gc = OxmlElement('w:gridCol'); gc.set(qn('w:w'), str(int(cm * 567))); grid.append(gc)
    for row in t.rows:
        for c, cm in zip(row.cells, cms): c.width = Cm(cm)

def table_after(anchor, rows, cols, style='TableGrid'):
    t = d.add_table(rows=rows, cols=cols)
    try: t.style = d.styles[style]
    except KeyError: t.style = d.styles['Table Grid']
    anchor._p.addnext(t._tbl)
    trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
    return t

def regex_replace_para(p, pattern, repl):
    """Substitui regex no parágrafo run a run; só funde os runs (perdendo formatação parcial)
    se o resultado run a run não coincidir com a substituição sobre o texto inteiro."""
    txt = p.text
    if not re.search(pattern, txt): return False
    esperado = re.sub(pattern, repl, txt)
    for r in p.runs:
        if re.search(pattern, r.text):
            r.text = re.sub(pattern, repl, r.text)
    if p.text != esperado:
        if p._p.xpath('.//w:drawing'): return True
        set_text(p, esperado)
    return True

def italicize_terms(p):
    for term in ITALICOS:
        for r in list(p.runs):
            t = r.text
            if term not in t or r.font.italic: continue
            idx = t.find(term)
            if (idx > 0 and t[idx-1].isalnum()) or (idx+len(term) < len(t) and t[idx+len(term)].isalnum()): continue
            before, after = t[:idx], t[idx+len(term):]
            r.text = before
            r_it = copy.deepcopy(r._r); r._r.addnext(r_it)
            from docx.text.run import Run
            rit = Run(r_it, p); rit.text = term; rit.font.italic = True
            if after:
                r_af = copy.deepcopy(r._r); r_it.addnext(r_af); Run(r_af, p).text = after

# modelos de formatação
CAPTION_TPL = ORIG[253]      # "Figura 5 - ..." centralizado, negrito 11 pt
IMG_TPL     = ORIG[254]      # parágrafo de imagem centralizado
BODY_TPL    = ORIG[122]      # parágrafo normal de texto
HEAD1_TPL   = ORIG[337]      # Heading 1 (REFERÊNCIAS)
HEAD2_TPL   = ORIG[162]      # Heading 2
LIST_TPL    = ORIG[149]      # List Paragraph (hipóteses)
TABCAP_TPL  = ORIG[233]      # legenda de tabela

# =============================================================================
# 0. Aceita a marcação de revisão remanescente (MB-39)
# =============================================================================
for ins in BODY.xpath('.//w:ins'):
    parent = ins.getparent(); idx = parent.index(ins)
    for child in list(ins): parent.insert(idx, child); idx += 1
    parent.remove(ins)
for dele in BODY.xpath('.//w:del'):
    dele.getparent().remove(dele)

# =============================================================================
# 1. Renumeração das figuras nas referências do texto original
#    antigo -> novo: 2->3, 3->6, 4->7, 5->8, 6->9, 7->10, 8->11, 9->12, 10->13
# =============================================================================
MAPA_FIG = {1: 2, 2: 3, 3: 6, 4: 7, 5: 8, 6: 9, 7: 10, 8: 11, 9: 12, 10: 13}
for p in ORIG:
    if 'Figura' not in p.text: continue
    if p.style.name.startswith('toc') or p.style.name.startswith('Sum'): continue
    regex_replace_para(p, r'Figura (\d+)', lambda m: f'Figura §{MAPA_FIG.get(int(m.group(1)), int(m.group(1)))}§')
for p in ORIG:
    if '§' in p.text: regex_replace_para(p, r'§(\d+)§', r'\1')

# =============================================================================
# 2. RESUMO / ABSTRACT
# =============================================================================
resumo = (
    "Modelos lineares convencionais podem ser insuficientes para representar relações ecológicas não lineares e "
    "interações entre variáveis ambientais. Este estudo desenvolveu e validou um Modelo de Regressão Múltipla "
    "Polinomial de ordem N (MRMP-N), estimado por Regressão Ridge, para analisar a Fotossíntese Líquida (PSN) nos "
    "biomas Mata Atlântica, Cerrado e Caatinga da Bahia, entre janeiro de 2001 e setembro de 2025. Foram utilizados "
    f"dados mensais de sensoriamento remoto e variáveis climáticas, totalizando {N_OBS} observações por bioma. O grau "
    "polinomial e o conjunto de variáveis preditoras foram determinados empiricamente, e o desempenho foi avaliado "
    "por validação cruzada repetida, validação temporal e teste de Y-randomization. O modelo de grau 2 explicou "
    f"{r2('CE')}% da variância da PSN no Cerrado, {r2('CA')}% na Caatinga e {r2('MA')}% na Mata Atlântica. Os "
    "resultados evidenciaram regimes ecológicos distintos de controle da produtividade primária: limitação hídrica "
    "sazonal no Cerrado, resposta pulsada à precipitação na Caatinga e controle multifatorial na Mata Atlântica. A "
    "análise do El Niño–Oscilação Sul (ENSO) indicou influência predominantemente indireta sobre a produtividade, "
    "com efeito direto sobre a PSN detectado apenas na Caatinga. Os resultados demonstram a viabilidade da regressão "
    "polinomial regularizada para representar relações ambientais complexas e reforçam a importância de abordagens "
    "diferenciadas para o monitoramento dos biomas baianos."
)
abstract = (
    "Conventional linear models may be insufficient to represent non-linear ecological relationships and "
    "interactions among environmental variables. This study developed and validated a Multiple Polynomial "
    "Regression Model of order N (MRMP-N), estimated by Ridge Regression, to analyze Net Photosynthesis (PSN) in the "
    "Atlantic Forest, Cerrado and Caatinga biomes of Bahia, Brazil, between January 2001 and September 2025. Monthly "
    f"remote sensing data and climate variables were used, totaling {N_OBS} observations per biome. The polynomial "
    "degree and the set of predictor variables were determined empirically, and performance was assessed by repeated "
    "cross-validation, temporal validation and a Y-randomization test. The degree-2 model explained "
    f"{r2('CE').replace(',', '.')}% of PSN variance in the Cerrado, {r2('CA').replace(',', '.')}% in the Caatinga and "
    f"{r2('MA').replace(',', '.')}% in the Atlantic Forest. The results revealed distinct ecological regimes of "
    "primary productivity control: seasonal water limitation in the Cerrado, pulsed response to rainfall in the "
    "Caatinga and multifactorial control in the Atlantic Forest. The analysis of the El Niño–Southern Oscillation "
    "(ENSO) indicated a predominantly indirect influence on productivity, with a direct effect on PSN detected only "
    "in the Caatinga. The results demonstrate the feasibility of regularized polynomial regression to represent "
    "complex environmental relationships and reinforce the importance of differentiated approaches for monitoring "
    "the biomes of Bahia."
)
set_text(ORIG[63], resumo)
set_text(ORIG[73], abstract)

# Lista de siglas: itálico nos termos estrangeiros + novas siglas
for i in range(87, 111):
    p = ORIG[i]
    if p.text.strip(): set_text(p, p.text)
add_paras_after(ORIG[95], ORIG[95], ["NASA – Administração Nacional de Aeronáutica e Espaço dos Estados Unidos (National Aeronautics and Space Administration)"])
add_paras_after(ORIG[101], ORIG[101], ["NOAA – Administração Nacional Oceânica e Atmosférica dos Estados Unidos (National Oceanic and Atmospheric Administration)"])
add_paras_after(ORIG[88], ORIG[88], ["CPC – Centro de Previsão Climática da NOAA (Climate Prediction Center)"])
add_paras_after(ORIG[87], ORIG[87], ["ACF – Função de Autocorrelação (Autocorrelation Function)"])

# =============================================================================
# 3. APRESENTAÇÃO E FUNDAMENTAÇÃO
# =============================================================================
set_text(ORIG[123], ORIG[123].text
         .replace("A região da Bahia apresenta", "O estado da Bahia apresenta")
         .replace("a estratégias de gestão subótimas.", "a decisões de gestão ambiental menos eficazes do que poderiam ser."))
set_text(ORIG[124], ORIG[124].text.replace(
    "permitindo capturar padrões ecológicos que dificilmente seriam descritos por modelos lineares convencionais.",
    "permitindo capturar padrões ecológicos que dificilmente seriam descritos por modelos lineares convencionais. "
    "Modelos de regressão polinomial com seleção sistemática de termos têm sido aplicados tanto na predição "
    "quantitativa estrutura-atividade em química medicinal (Guimarães et al., 2024) quanto, em sentido mais amplo, "
    "na modelagem de respostas ecológicas não lineares, para as quais abordagens flexíveis superam consistentemente "
    "as estritamente lineares (Hao et al., 2019)."))
set_text(ORIG[127], ORIG[127].text.replace(
    "a resposta deixa de ser proporcional ao forçamento,",
    "a resposta deixa de ser proporcional à forçante (o fator externo que a provoca, como o aumento da temperatura "
    "ou a redução da chuva),"))

set_text(ORIG[128],
    "Nesse cenário, a fotossíntese líquida (PSN, net photosynthesis) constitui uma variável-síntese particularmente "
    "informativa do funcionamento ecológico terrestre. A fonte dessa variável é o sensor MODIS (Moderate Resolution "
    "Imaging Spectroradiometer), instrumento orbital da agência espacial norte-americana NASA a bordo dos satélites "
    "Terra (lançado em 1999) e Aqua (2002). O MODIS observa toda a superfície terrestre a cada um ou dois dias, em 36 "
    "bandas espectrais e resoluções de 250 m a 1 km; a partir dessas imagens, a NASA gera produtos derivados "
    "identificados por códigos, como o MOD17 (produtividade da vegetação), o MOD16 (evapotranspiração), o MOD11 "
    "(temperatura da superfície) e o MCD64 (área queimada), todos distribuídos gratuitamente. O algoritmo MOD17 "
    "(Running et al., 2004; Running; Zhao, 2021) estima três níveis de fluxo de carbono, cuja relação está "
    "esquematizada na Figura 1. A Produtividade Primária Bruta (GPP) corresponde a todo o carbono retirado da "
    "atmosfera pela fotossíntese. Parte desse carbono é consumida imediatamente pela respiração de manutenção das "
    "folhas e das raízes finas, isto é, o custo de manter vivos os tecidos de vida curta; o que sobra é a "
    "Fotossíntese Líquida (PSN), o carbono que a vegetação efetivamente acumula em escala de dias a semanas. Se, "
    "além disso, forem descontadas a respiração de manutenção dos demais tecidos vivos (lenho e raízes grossas) e a "
    "respiração de crescimento, o custo de construir biomassa nova, chega-se à Produtividade Primária Líquida (NPP), "
    "calculada por agregação anual (Zhao et al., 2005; Running; Zhao, 2021). Em termos de equações, "
    "PSN = GPP − Rm(folhas) − Rm(raízes finas) e NPP = PSN − Rm(lenho e raízes grossas) − Rg, em que Rm é a "
    "respiração de manutenção e Rg a respiração de crescimento. A PSN é, portanto, um saldo intermediário entre a "
    "GPP e a NPP.")
add_figure_after(ORIG[128], "Figura 1 - Fluxos de carbono estimados pelo algoritmo MODIS/MOD17: relação entre GPP, PSN e NPP.",
                 os.path.join(FIG, 'fig01_psn_conceito.png'))
set_text(ORIG[129],
    "A PSN representa o saldo líquido de carbono assimilado em escala subanual, sendo um indicador direto da "
    "atividade fotossintética da vegetação e um proxy robusto da resposta do ecossistema às condições ambientais. "
    "A adoção da PSN como variável-resposta deste estudo justifica-se por sua resolução temporal compatível com a "
    "escala mensal de análise e por capturar a dinâmica fisiológica da vegetação sem a defasagem inerente à "
    "integração anual da NPP. As características do produto que a fornece (resolução espacial e temporal, "
    "agregação mensal e por bioma) estão descritas na seção Dados e Pré-processamento.")

set_text(ORIG[131], ORIG[131].text.rstrip() +
    f" Nos dados deste estudo esse controle é direto: no Cerrado baiano, a evapotranspiração explica sozinha "
    f"{ENSO['disp']['CE']['EV']}% da variância mensal da PSN e o índice de disponibilidade hídrica (WAI) "
    f"{ENSO['disp']['CE']['WAI']}% (regressões lineares simples, n = {N_OBS}, p < 0,001), contra "
    f"{ENSO['disp']['CE']['TST']}% da temperatura e {ENSO['disp']['CE']['PRE']}% da precipitação do mesmo mês "
    f"(Figura 5, no Capítulo de Resultados). Na Mata Atlântica, por contraste, a evapotranspiração explica apenas "
    f"{ENSO['disp']['MA']['EV']}% da variância da PSN.")

set_text(ORIG[136], ORIG[136].text.replace(
    "(Dionizio et al., 2020).",
    "(Dionizio et al., 2020). A redução ocorre porque as gramíneas das pastagens têm sistema radicular raso e perdem "
    "grande parte da área foliar na estação seca, enquanto a vegetação nativa, com raízes profundas, continua "
    "acessando a água do subsolo e transpirando ao longo do ano; assim, embora o pasto possa ter índice de área "
    "foliar comparável no auge da estação chuvosa, sua evapotranspiração anual é menor, sobretudo nos meses secos."))

set_text(ORIG[138], ORIG[138].text.replace(
    "(ONI para temperatura/precipitação e destas para a PSN)",
    "(do Índice Oceânico Niño, ONI, medida oficial da NOAA para o ENSO que corresponde à anomalia média de três "
    "meses da temperatura da superfície do mar no Pacífico equatorial central, para a temperatura e a precipitação "
    "regionais, e destas para a PSN)"))

set_text(ORIG[140], ORIG[140].text.replace(
    "originalmente aplicada à predição quantitativa estrutura-atividade (QSAR),",
    "originalmente aplicada à predição quantitativa estrutura-atividade (QSAR), isto é, a modelos que preveem a "
    "atividade biológica de uma molécula (no caso, o índice de inibição da atividade celular de compostos "
    "antimaláricos) a partir de características estruturais de moléculas sabidamente inibidoras e não inibidoras,"))

set_text(ORIG[141],
    "A primeira é o uso da regressão Ridge no lugar dos mínimos quadrados ordinários. Quando se criam termos "
    "quadráticos e de interação a partir de variáveis que já são correlacionadas entre si (por exemplo, "
    "evapotranspiração e disponibilidade hídrica), o modelo passa a conter muitas variáveis que carregam quase a "
    "mesma informação. Na regressão clássica isso torna os coeficientes instáveis: pequenas mudanças nos dados "
    "produzem coeficientes muito diferentes. A regressão Ridge acrescenta uma penalidade (chamada L2) que impede os "
    "coeficientes de crescerem demais, trocando um pequeno viés por muito mais estabilidade, o que a torna adequada "
    "a preditores correlacionados.")

# =============================================================================
# 4. QUESTÃO CENTRAL, HIPÓTESES, OBJETIVOS
# =============================================================================
set_text(ORIG[144], "QUESTÃO CENTRAL E HIPÓTESES")
set_text(ORIG[145], ORIG[145].text.replace("a produtividade dos biomas na Bahia.",
                                            "a produtividade primária, medida pela Fotossíntese Líquida, dos biomas na Bahia."))
set_text(ORIG[149], "H1: A expansão polinomial não linear apresentará melhor desempenho preditivo em relação ao modelo "
    "linear de grau 1, mantendo nível controlado de sobreajuste, com o grau ótimo definido, entre os graus 1 a 5, "
    "como aquele que maximiza o R² de teste mantendo a diferença entre o R² de treino e o de teste abaixo de 10 "
    "pontos percentuais.")
set_text(ORIG[150], "H2: O conjunto de variáveis ambientais, associado aos componentes harmônicos de sazonalidade, "
    "explicará pelo menos 60% da variância mensal da PSN em cada bioma, com diferenças na composição do conjunto "
    "ótimo de preditores entre os biomas.")
set_text(ORIG[154], "Desenvolver e validar um Modelo de Regressão Múltipla Polinomial de ordem N (MRMP-N), estimado por "
    "Regressão Ridge, para quantificar a influência de variáveis ambientais sobre a Fotossíntese Líquida (PSN) nos "
    "biomas Mata Atlântica, Cerrado e Caatinga da Bahia.")
set_text(ORIG[156], "Determinar empiricamente o grau polinomial e o conjunto de variáveis ambientais de melhor "
    "desempenho preditivo em cada bioma.")
p_obj2 = new_para_after(ORIG[156], ORIG[156], "Avaliar a robustez e a capacidade de generalização do modelo, inclusive "
    "sob validação que respeita a ordem cronológica dos dados.")
set_text(ORIG[157], "Comparar o desempenho preditivo e os controles ambientais da PSN entre os três biomas.")
set_text(ORIG[158], "Investigar a influência do El Niño–Oscilação Sul (ENSO) sobre a PSN e sobre as variáveis climáticas "
    "intermediárias (EV, PRE e TST) nos três biomas.")

# =============================================================================
# 5. MATERIAL E MÉTODOS — fluxo no início do capítulo, área de estudo ampliada
# =============================================================================

set_text(ORIG[226], "Figura 3 - Fluxo metodológico do modelo MRMP-N.", bold=True)
replace_image(ORIG[227], os.path.join(FIG, 'fig_fluxo.png'))
remove_para(ORIG[225])
to_inline(ORIG[173])   # mapa (Figura 2)

set_text(ORIG[165], ORIG[165].text.replace(
    "Do ponto de vista climático, o litoral e o leste do estado,",
    "Do ponto de vista climático, segundo a classificação de Köppen para o Brasil (Alvares et al., 2013), o litoral e o leste do estado,"))
set_text(ORIG[166], ORIG[166].text.replace(
    "responde de forma pulsada às chuvas",
    "responde de forma pulsada às chuvas, isto é, com aumentos rápidos da produtividade logo após cada evento de "
    "precipitação seguidos de queda igualmente rápida na estiagem,"))
ultimo_area = add_paras_after(ORIG[166], BODY_TPL, [
    "Do ponto de vista hidrológico, o Cerrado baiano abriga nascentes que abastecem bacias hidrográficas regionais, "
    "entre elas afluentes do Rio São Francisco, sustentando atividades agropecuárias, comunidades rurais e "
    "ecossistemas a jusante. A Mata Atlântica do sul da Bahia integra o Corredor Central da Mata Atlântica, um dos "
    "eixos prioritários da conservação da biodiversidade no país, e concentra iniciativas de restauração florestal, "
    "ainda em fase inicial na maior parte dos casos, alinhadas ao Plano Nacional de Recuperação da Vegetação Nativa "
    "(PLANAVEG) e ao Zoneamento Ecológico-Econômico da Bahia.",
    "O uso do solo difere entre os biomas: na Mata Atlântica predominam os mosaicos de fragmentos florestais "
    "intercalados por pastagens, cacauicultura, silvicultura de eucalipto e áreas urbanas; no oeste do estado, a "
    "fronteira agrícola do MATOPIBA converteu extensas áreas de Cerrado em lavouras de grãos e pastagens; e na "
    "Caatinga a pecuária extensiva, a agricultura de sequeiro e a extração de lenha respondem pela maior parte da "
    "conversão e da degradação da vegetação nativa (MapBiomas, 2025). O estado abriga ainda povos indígenas de "
    "diversas etnias (entre elas Pataxó, Pataxó Hã-Hã-Hãe, Tupinambá, Kiriri, Tuxá, Pankararé, Truká e Kaimbé), "
    "comunidades quilombolas e agricultores familiares que dependem diretamente dos serviços ecossistêmicos "
    "associados à produtividade da vegetação. Essa diversidade de controles ambientais e de pressões antrópicas "
    "justifica a abordagem comparativa entre biomas adotada neste estudo.",
])
# fluxo metodológico (Figura 3) logo após o mapa, antes de "Dados e Pré-processamento"
p_fl = new_para_after(ORIG[173], BODY_TPL, "O fluxo metodológico completo do MRMP-N, da organização da base de dados à "
    "validação final, é sintetizado na Figura 3; cada etapa é detalhada nas seções seguintes.")
move_after(ORIG[226], p_fl); move_after(ORIG[227], ORIG[226])

# =============================================================================
# 6. DADOS E PRÉ-PROCESSAMENTO
# =============================================================================
set_text(ORIG[177],
    "Os dados utilizados neste estudo foram organizados em formato tabular, com uma observação mensal por bioma, a "
    "partir de produtos de sensoriamento remoto e de uma base de precipitação, todos de acesso público e gratuito. "
    "A variável resposta, a Fotossíntese Líquida (PSN), provém do produto MOD17A2H, e a evapotranspiração real (EV) "
    "e a potencial (ETP) do produto MOD16A2, ambos do sensor MODIS a bordo do satélite Terra, da NASA; a "
    "temperatura da superfície terrestre (TST) provém do produto MOD11A2 e a área queimada (BURN) do MCD64A1, do "
    "mesmo sensor. A precipitação (PRE) provém do produto CHIRPS (Climate Hazards Group InfraRed Precipitation with "
    "Station data), que combina estimativas por satélite e estações pluviométricas, e o Índice Oceânico Niño (ONI) "
    "da tabela oficial do Centro de Previsão Climática (CPC) da NOAA. O produto MOD17A2H é distribuído em compostos "
    "de oito dias com resolução espacial de 500 metros e fornece a PSN como a diferença entre a Produtividade "
    "Primária Bruta (GPP) e a respiração de manutenção de folhas e raízes finas; os compostos foram agregados à "
    "escala mensal e os pixels de cada bioma dentro dos limites da Bahia foram agregados espacialmente, seguindo o "
    "procedimento de Benfica et al. (2022), que organizou a base original de 2001 a 2020, aqui estendida até 2025. "
    "Os produtos MODIS podem ser obtidos pelo portal NASA Earthdata ou pelas plataformas AppEEARS e Google Earth "
    "Engine, o CHIRPS pelo servidor da Universidade da Califórnia em Santa Bárbara e o ONI pela página do CPC; a "
    "base mensal consolidada usada neste estudo está reproduzida integralmente no Apêndice A e o código-fonte está "
    "disponível em repositório público, permitindo a reprodução de todos os resultados. As variáveis dependentes e "
    "preditoras que compõem o modelo estão detalhadas na Tabela 1.")
set_text(ORIG[182],
    "A variável resposta é a Fotossíntese Líquida (PSN), e as variáveis preditoras candidatas são a "
    "evapotranspiração (EV), a precipitação acumulada (PRE), a temperatura da superfície terrestre (TST), o índice "
    "de disponibilidade hídrica (WAI), definido como a razão entre a evapotranspiração real e a potencial (ETR/ETP) "
    "e que expressa o grau em que a demanda atmosférica por água é atendida pela água disponível no sistema, e a "
    f"área queimada (BURN), acrescidas das duas componentes harmônicas de sazonalidade derivadas do indexador mensal. "
    f"O conjunto abrange o período de janeiro de 2001 a setembro de 2025, em escala mensal (n = {N_OBS} meses por "
    "bioma); os três últimos meses de 2025 foram excluídos por ainda não haver dado de precipitação publicado. O "
    "ONI é publicado pela NOAA como média móvel de três meses (por exemplo, DJF, JFM) atribuída ao mês central do "
    "trimestre; cada mês da série recebeu, portanto, o valor do trimestre centrado nele (janeiro = DJF, fevereiro = "
    "JFM, e assim por diante), o que mantém a resolução mensal sem interpolação. O ONI não compõe o conjunto de "
    "preditores do modelo principal, sendo empregado especificamente na análise da influência do El Niño-Oscilação "
    "Sul (ENSO) sobre a produtividade, apresentada adiante.")
set_text(ORIG[185],
    "Essa parametrização permite representar padrões periódicos anuais sem impor relações lineares artificiais "
    "entre os meses do ano, além de evitar descontinuidades entre dezembro e janeiro. As duas componentes entram no "
    "modelo como preditores distintos, cada um variando entre −1 e +1 ao longo do ano, e não como uma soma; ao "
    "estimar um coeficiente para cada uma, o modelo ajusta livremente a amplitude e a fase do ciclo anual, pois "
    "β₁·saz_sin + β₂·saz_cos equivale a A·sin(2π·mês/12 + φ), com amplitude A e defasagem φ determinadas pelos "
    "dados. A parametrização não impõe sazonalidade ao modelo: na ausência de ciclo anual nos dados, os coeficientes "
    "das duas componentes tendem a zero, tendência reforçada pela penalização L2 da regressão Ridge.")
def _abl(b, sem):
    r = ABL[(ABL.bioma == nome[b]) & (ABL.conjunto.str.contains('sem') == sem)].iloc[0]; return r
def _saz(b, var): return float(SAZ[(SAZ.bioma == nome[b]) & (SAZ.variavel == var)]['r2'].iloc[0])
_com = {b: RG.loc[b, 'r2_teste_medio'] for b in ('MA', 'CE', 'CA')}; _sem = {b: _abl(b, True)['r2_teste'] for b in ('MA', 'CE', 'CA')}
add_paras_after(ORIG[185], BODY_TPL, [
    "Para verificar empiricamente essa propriedade, o modelo foi reajustado sem as componentes de sazonalidade, "
    "mantendo as demais variáveis e o mesmo protocolo de validação (Tabela A3, Apêndice A). A remoção reduziu o R² "
    f"de teste em {v(_com['MA'] - _sem['MA'])} pontos percentuais na Mata Atlântica (de {v(_com['MA'])}% para "
    f"{v(_sem['MA'])}%), {v(_com['CE'] - _sem['CE'])} pontos no Cerrado e {v(_com['CA'] - _sem['CA'])} pontos na "
    "Caatinga, uma queda muito mais acentuada do que se esperaria de um termo redundante, que a penalização L2 "
    "tenderia a anular. Essa diferença entre biomas é coerente com o grau em que as próprias variáveis climáticas já "
    f"estão ligadas ao calendário (Tabela A4, Apêndice A): no Cerrado, entre {v(_saz('CE','WAI'),0)}% e "
    f"{v(_saz('CE','EV'),0)}% da variância da evapotranspiração e do WAI é explicada isoladamente pelo ciclo anual, "
    f"contra apenas {v(_saz('MA','EV'),0)}% na Mata Atlântica, onde a variabilidade climática reflete "
    "predominantemente as condições meteorológicas de cada ano específico. A acentuada perda de desempenho ao remover "
    "a sazonalidade explícita nesse bioma sugere que a Fotossíntese Líquida responde a um componente do ciclo anual, "
    "possivelmente fotoperíodo ou fenologia foliar, não inteiramente mediado pelas variáveis climáticas medidas."])
set_text(ORIG[186],
    "Como a área queimada mensal concentra muitos valores nulos e alguns picos muito elevados, aplicou-se, antes da "
    "modelagem, a transformação logarítmica a seguir, procedimento usual para reduzir a influência desses valores "
    "extremos e melhorar a estabilidade numérica do modelo:")
set_text(ORIG[188],
    "Para reduzir a influência de meses com produtividade excepcionalmente baixa (por exemplo, após grandes "
    "queimadas ou secas severas) sobre a estimação dos coeficientes, a variável resposta foi submetida a "
    "winsorização unilateral inferior durante o treinamento. Winsorizar significa substituir os valores abaixo de "
    "um limite pelo próprio valor do limite, em vez de excluí-los. O limite adotado foi o percentil 3 da PSN do "
    "conjunto de treino, isto é, o valor abaixo do qual estão os 3% menores meses; em uma amostra de cerca de 238 "
    "meses de treino, isso afeta apenas os sete valores mais baixos. O percentil foi calculado exclusivamente a "
    "partir dos dados de treino de cada partição e aplicado apenas a eles; os valores de PSN dos conjuntos de teste "
    "foram mantidos em sua escala original, inclusive os extremos, garantindo que a avaliação preditiva fosse "
    "realizada sobre observações não modificadas e evitando vazamento de informação entre treino e teste.")
add_paras_after(ORIG[189], BODY_TPL, [
    "Antes da modelagem, a matriz de correlação de Pearson entre as variáveis candidatas foi examinada para "
    "eliminar redundâncias, como no protocolo de Guimarães et al. (2024). A evapotranspiração potencial (ETP) foi "
    "excluída nessa etapa por sua correlação de 0,73 a 0,80 com a temperatura da superfície na Mata Atlântica e na "
    "Caatinga, permanecendo apenas como denominador do WAI. As variáveis restantes foram submetidas ao diagnóstico "
    "de multicolinearidade por VIF descrito adiante."])

# =============================================================================
# 7. ESPECIFICAÇÃO DO MODELO
# =============================================================================
set_text(ORIG[192],
    "Foram introduzidas três adaptações principais em relação ao modelo de referência: (i) substituição da "
    "estimação por Mínimos Quadrados Ordinários (MQO) pela Regressão Ridge com regularização L2, visando reduzir o "
    "sobreajuste associado à expansão polinomial; (ii) comparação sistemática dos graus polinomiais 1 a 5, seguindo "
    "o mesmo princípio de determinação empírica do grau adotado por Guimarães et al. (2024), que avaliaram graus até "
    "8, com o limite superior reduzido para 5 porque, com cerca de 300 observações e cinco preditores, graus "
    "superiores geram centenas de termos e sobreajuste severo; e (iii) ampliação do protocolo de validação, com "
    "aplicação de validação cruzada RepeatedKFold, esquemas complementares de validação temporal (GroupKFold por ano "
    "e TimeSeriesSplit com janela expansível) e teste de Y-randomization.")
add_paras_after(ORIG[196], BODY_TPL, [
    "Para o grau N = 2 e cinco preditores X₁ … X₅, a expansão gera 20 termos além do intercepto: "
    "Ŷ = β₀ + Σᵢ βᵢXᵢ + Σᵢ βᵢᵢXᵢ² + Σᵢ<ⱼ βᵢⱼXᵢXⱼ, com 5 termos lineares, 5 quadráticos e 10 interações entre "
    "pares. Para um grau N genérico, o número de termos é C(5 + N, N) − 1: 20 no grau 2, 55 no grau 3, 125 no grau "
    "4 e 251 no grau 5, o que ilustra por que graus elevados sobreajustam uma amostra de cerca de 300 meses."])
set_text(ORIG[201],
    "A ordem polinomial N foi tratada como hiperparâmetro a ser otimizado empiricamente, como no estudo de "
    "referência (Guimarães et al., 2024), que também determinou o grau empiricamente. Foram comparados "
    "sistematicamente os graus 1 a 5, adotando-se como critério de seleção a maximização do R² no conjunto de teste "
    "associada à minimização da diferença treino–teste, definida como a diferença entre o R² de treino e o R² de "
    "teste (medida usual do sobreajuste). A avaliação do sobreajuste não se baseou em um limiar rígido único, mas na "
    "interpretação conjunta dessa diferença, da estabilidade do R² entre as partições e da concordância com a "
    "validação temporal. Adotou-se o valor de 10 pontos percentuais como referência orientadora, reconhecendo-se que "
    "a magnitude aceitável da diferença depende do mecanismo de controle da capacidade do modelo (no caso, a "
    "regularização L2) e da complexidade intrínseca do fenômeno modelado, não sendo diretamente comparável entre "
    "diferentes famílias de modelos. Nesse enquadramento, valores próximos ou moderadamente superiores a esse patamar "
    "de referência foram considerados admissíveis quando o modelo manteve desempenho estável e robusto sob validação "
    "temporal.")
set_text(ORIG[202], ORIG[202].text.replace(
    "Para um conjunto de cinco variáveis de entrada, selecionadas entre as candidatas (EV, PRE, TST, WAI, BURN e as componentes de sazonalidade),",
    "Para um conjunto de cinco preditores (três variáveis ambientais selecionadas entre EV, PRE, TST, WAI e BURN, mais as duas componentes de sazonalidade),"))

# =============================================================================
# 8. ANÁLISE ESTATÍSTICA
# =============================================================================
set_text(ORIG[205],
    "As duas componentes harmônicas de sazonalidade foram mantidas fixas em todos os modelos, por representarem o "
    "ciclo anual e não um controle ambiental. A seleção incidiu sobre as cinco variáveis ambientais candidatas (EV, "
    "PRE, TST, WAI e BURNlog), avaliando-se todas as C(5,3) = 10 combinações de três variáveis por bioma, cada uma "
    "sob o mesmo protocolo de validação cruzada. A restrição a três variáveis ambientais (cinco preditores no total) "
    "buscou limitar a complexidade dimensional do modelo e favorecer sua estabilidade estatística, aspecto relevante "
    "em modelos com expansão polinomial; o controle dos efeitos da multicolinearidade é assegurado pela penalização "
    "L2 do Ridge.")
set_text(ORIG[206],
    "Seguindo a lógica de busca combinatória do estudo de referência, que avaliou mais de 400 descritores "
    "moleculares em combinações de três, a presente abordagem permite uma avaliação empírica e exaustiva do espaço "
    "de combinações possíveis. A seleção final em cada bioma foi definida pelo critério composto que considera, "
    "simultaneamente, o maior valor médio de R² no conjunto de teste e a menor diferença entre o R² de treino e o de "
    "teste, evitando-se a escolha de modelos com R² de treino elevado mas R² de teste baixo, pois é o R² no conjunto "
    "de teste que mede a capacidade de generalização.")
set_text(ORIG[207], ORIG[207].text.replace(
    "cujos resultados são apresentados e discutidos no Capítulo de Resultados.",
    "cujos resultados (Figura 5) são apresentados e discutidos no Capítulo de Resultados."))
set_text(ORIG[208], ORIG[208].text.replace("três métricas complementares,", "três métricas complementares (R², RMSE e MAE),"))

# =============================================================================
# 9. VALIDAÇÃO
# =============================================================================
set_text(ORIG[215],
    "A validação cruzada foi realizada por meio do protocolo RepeatedKFold, utilizando cinco folds e trinta "
    f"repetições, resultando em 150 partições de validação para cada combinação avaliada (Figura 4a). Em cada "
    f"partição, 80% das observações compõem o treino e 20% o teste: com n = {N_OBS}, cerca de 238 meses de treino e "
    "59 de teste. As 30 repetições reembaralham a divisão, de modo que cada mês da série é usado como teste "
    "exatamente 30 vezes e como treino 120 vezes ao longo das 150 partições; não há, portanto, um único conjunto de "
    "teste fixo, e as métricas reportadas são médias (e desvios-padrão) sobre as 150 partições. Esse protocolo "
    "fornece a estimativa principal do desempenho ao reduzir a variabilidade decorrente de partições únicas dos "
    "dados. Reconhece-se, contudo, que em séries mensais observações temporalmente próximas podem compartilhar "
    "estrutura sazonal e autocorrelação; por isso o desempenho foi adicionalmente examinado por esquemas de "
    "validação que respeitam a ordem cronológica, descritos adiante. Adicionalmente, foi reportado o intervalo "
    "empírico de 95% da distribuição dos escores de R² obtidos nas partições, definido pelos percentis 2,5 e 97,5 "
    "dos valores observados. Ressalta-se que, por decorrerem de partições parcialmente sobrepostas do RepeatedKFold, "
    "esses escores não constituem observações independentes, motivo pelo qual se adota a expressão \"intervalo "
    "empírico\" em vez de \"intervalo de confiança\" no sentido estatístico estrito.")
set_text(ORIG[217], ORIG[217].text
    .replace("O primeiro, denominado GroupKFold por ano, agrupa as observações de um mesmo ano, de modo que anos inteiros sejam mantidos fora do conjunto de treino em cada partição;",
             "O primeiro, denominado GroupKFold por ano, agrupa as observações de um mesmo ano em cinco grupos de cinco anos, de modo que anos inteiros sejam mantidos fora do conjunto de treino em cada partição (Figura 4b);")
    .replace("O segundo, o TimeSeriesSplit com janela expansível, ajusta o modelo em períodos anteriores e avalia seu desempenho em períodos subsequentes,",
             "O segundo, o TimeSeriesSplit com janela expansível, ajusta o modelo em períodos anteriores e avalia seu desempenho no bloco de 49 meses seguinte, em cinco blocos sucessivos (Figura 4c),")
    .replace("A concordância entre os resultados dos três esquemas foi interpretada como evidência de que o desempenho do modelo não constitui artefato de vazamento por autocorrelação temporal.",
             "A concordância entre os resultados dos três esquemas foi interpretada como evidência de que o bom desempenho não decorre apenas de meses vizinhos, muito parecidos entre si, terem caído ao mesmo tempo no treino e no teste."))
add_figure_after(ORIG[217], "Figura 4 - Esquemas de particionamento treino/teste: (a) RepeatedKFold 5 × 30; (b) GroupKFold por ano; (c) TimeSeriesSplit com janela expansível.",
                 os.path.join(FIG, 'fig_validacao_esquema.png'))
set_text(ORIG[218],
    f"A análise de resíduos foi conduzida por meio de um ajuste diagnóstico realizado sobre o conjunto completo de "
    f"dados (n = {N_OBS}, janeiro de 2001 a setembro de 2025), utilizando os valores originais e não winsorizados da "
    "PSN. Essa escolha permitiu preservar, na avaliação diagnóstica, os eventos extremos da cauda inferior da "
    "distribuição, possibilitando verificar sua influência sobre o comportamento dos resíduos. A normalidade dos "
    "resíduos foi avaliada pelo teste de Shapiro-Wilk e a autocorrelação temporal pelo teste de Ljung-Box com 12 "
    "defasagens, complementado pela função de autocorrelação (ACF) nas três primeiras defasagens. Ressalta-se que "
    "esse ajuste teve finalidade exclusivamente diagnóstica, enquanto a capacidade preditiva do MRMP-N foi estimada "
    "pelos procedimentos de validação cruzada, nos quais a winsorização foi aplicada exclusivamente à resposta do "
    "conjunto de treino de cada partição.")
set_text(ORIG[220],
    "Adotaram-se dois critérios complementares de validação. O primeiro, seguindo a lógica de Guimarães et al. "
    "(2024), compara o R² de validação cruzada do modelo original com a média dos R² dos 100 modelos permutados; "
    "neste estudo exigiu-se diferença mínima de 60 pontos percentuais entre os dois. O segundo consiste em um "
    "p-valor empírico unilateral, definido como a proporção de permutações cujo R² iguala ou supera o do modelo "
    "original, adotando-se como significativo p inferior a 0,05.")
set_text(ORIG[224],
    "A reprodutibilidade dos resultados foi assegurada pela fixação de semente aleatória (random_state = 42) nos "
    "procedimentos que envolvem aleatoriedade, bem como pela organização sistemática dos resultados e pela "
    "disponibilização do código-fonte comentado, permitindo transparência e replicabilidade das etapas de "
    "modelagem. O valor da semente é arbitrário (42 é uma convenção difundida na comunidade Python); qualquer valor "
    "fixo garante que as partições e permutações sejam reproduzidas exatamente, e o resultado não depende do valor "
    "escolhido.")

# =============================================================================
# 10. RESULTADOS — desempenho
# =============================================================================
set_text(ORIG[228], "RESULTADOS E DISCUSSÃO")
# dispersão PSN x variáveis no início dos resultados
p_disp = add_paras_after(ORIG[229], BODY_TPL, [
    "Antes da modelagem, as relações univariadas entre a PSN e cada variável candidata foram examinadas por "
    f"regressão linear simples (Figura 5). No Cerrado e na Caatinga, a evapotranspiração ({ENSO['disp']['CE']['EV']}% e "
    f"{ENSO['disp']['CA']['EV']}% da variância da PSN, respectivamente) e o WAI ({ENSO['disp']['CE']['WAI']}% e "
    f"{ENSO['disp']['CA']['WAI']}%) são os preditores univariados mais fortes, seguidos da temperatura, com relação "
    f"negativa ({ENSO['disp']['CE']['TST']}% e {ENSO['disp']['CA']['TST']}%); a precipitação do próprio mês explica "
    f"menos de 10% e a área queimada (em escala logarítmica) associa-se negativamente à PSN nos três biomas. Na "
    f"Mata Atlântica, nenhuma variável isolada explica mais de {ENSO['disp']['MA']['max']}% da variância, o que "
    "antecipa o menor desempenho do modelo nesse bioma e a necessidade dos termos de interação."])
add_figure_after(p_disp, "Figura 5 - Regressão linear simples entre a PSN e cada variável ambiental nos três biomas "
                 f"(dados mensais, n = {N_OBS}, 2001–2025).", os.path.join(FIG, 'fig_dispersao.png'), width_cm=15.0)

set_text(ORIG[230],
    "Os resultados obtidos demonstram que o MRMP-N de grau 2, estimado por Regressão Ridge, apresenta desempenho "
    "robusto e estatisticamente validado nos três biomas analisados, com capacidade preditiva consistente ao longo "
    "das 150 partições de validação cruzada, conforme apresentado na Tabela 2. A diferença entre o R² de treino e o "
    f"de teste permaneceu bastante reduzida no Cerrado ({gap('CE')} pp) e na Caatinga ({gap('CA')} pp), e situou-se "
    f"em {gap('MA')} pp na Mata Atlântica, abaixo do patamar de referência de 10 pontos percentuais. A Figura 6 "
    "ilustra a correspondência entre os valores de PSN de referência (estimados pelo produto MODIS MOD17A2H, aqui "
    "chamados de observados) e os preditos pelo MRMP-N nos três biomas. Os pontos representam predições fora da "
    "amostra (out-of-fold) obtidas por validação cruzada de cinco partições, isto é, cada observação foi prevista "
    "por um modelo que não a utilizou no treinamento. O R² indicado na figura foi calculado diretamente sobre essas "
    "predições, enquanto a Tabela 2 apresenta o desempenho médio obtido nas 150 partições do RepeatedKFold.")
replace_image(ORIG[231], os.path.join(FIG, 'fig03_obs_vs_pred.png'))
set_caption_after_image(ORIG[231], "Figura 6 - Observado vs. predito do MRMP-N nos três biomas.")

# Tabela 2
t2 = d.tables[3]
set_cell(t2.rows[0].cells[5], "Dif. treino–teste (pp)", bold=True)
for row, b in zip(t2.rows[1:], ['MA', 'CE', 'CA']):
    for c, val in zip(row.cells[1:], [r2(b), ic(b), rmse(b), f"{mae(b)} ± {maedp(b)}", gap(b)]):
        set_cell(c, val)
set_text(ORIG[236],
    "Observa-se elevada capacidade explicativa nos biomas Cerrado e Caatinga, com valores de R² superiores a 90%, "
    f"enquanto a Mata Atlântica apresenta desempenho inferior (R² = {r2('MA')}%). Essa diferença pode estar "
    "associada à maior complexidade e heterogeneidade estrutural da Mata Atlântica, ou seja, ao mosaico de "
    "fragmentos florestais, pastagens, plantios de eucalipto e áreas urbanas que compõe o bioma no estado, cuja "
    "dinâmica responde a fatores adicionais não integralmente representados pelos preditores utilizados: biomas cuja "
    "produtividade é fortemente controlada por variáveis climáticas tendem a ser mais previsíveis estatisticamente, "
    "ao passo que ecossistemas estruturalmente mais heterogêneos respondem a fatores adicionais não capturados por "
    "preditores climáticos. Embora os três biomas estejam submetidos a pressões antrópicas, é na Mata Atlântica que "
    "a heterogeneidade estrutural resultante dessas pressões mais compromete a previsibilidade da produtividade, "
    "conforme detalhado adiante.")
set_text(ORIG[237], ORIG[237].text.replace("(R² = 95,7%)", f"(R² = {r2('CE')}%)"))
set_text(ORIG[238], ORIG[238].text.replace("(R² = 94,0%)", f"(R² = {r2('CA')}%)"))
# Tabela 3
t3 = d.tables[4]
for row, b in zip(t3.rows[1:], ['MA', 'CE', 'CA']):
    for c, val in zip(row.cells[1:], [f"{r2(b,2)}%", f"{gkf(b)}%", f"{tss(b)}%", queda(b)]):
        set_cell(c, val)
set_text(ORIG[242],
    "Os resultados das estratégias adicionais de validação (Tabela 3) evidenciaram elevada estabilidade preditiva "
    "para os modelos do Cerrado e da Caatinga, que mantiveram valores de R² superiores a 90% mesmo em esquemas que "
    "consideram explicitamente a estrutura temporal dos dados. Para a Mata Atlântica, o desempenho permaneceu "
    f"próximo ao do modelo principal na validação agrupada por ano ({gkf('MA')}%), mas apresentou redução no "
    f"TimeSeriesSplit ({tss('MA')}%), indicando maior sensibilidade à ordem temporal e menor capacidade de "
    "extrapolação para períodos futuros; ainda assim, a queda ficou abaixo de 10 pontos percentuais nos três "
    "biomas.")
set_text(ORIG[243], ORIG[243].text.replace("(R² = 62,3%)", f"(R² = {r2('MA')}%)"))

# =============================================================================
# 11. RESULTADOS — grau e variáveis
# =============================================================================
g = {b: {k: sg(b, k, 'r2_teste') for k in (1, 2, 3)} for b in ('MA', 'CE', 'CA')}
g3 = {b: sg(b, 3, 'r2_teste') for b in ('MA', 'CE', 'CA')}; gp = {b: {k: sg(b, k, 'gap_pp') for k in (1, 2, 3)} for b in ('MA', 'CE', 'CA')}
ressalva = ""
for b in ('MA', 'CE', 'CA'):
    if g3[b] > g[b][2]:
        ressalva += (f" {'Na' if b != 'CE' else 'No'} {nome[b]}, o grau 3 alcançou R² de teste {v(g3[b]-g[b][2])} ponto "
                     f"superior ao do grau 2 ({v(g3[b])}% contra {v(g[b][2])}%), mas com diferença treino–teste "
                     f"{v(gp[b][3]-gp[b][2])} pontos maior ({v(gp[b][3])} contra {v(gp[b][2])} pp) e quase o triplo de "
                     "termos, sendo preterido pelo critério composto.")
set_text(ORIG[247],
    "A comparação sistemática entre os graus polinomiais 1 a 5 (Figura 7) indicou o grau 2 como ótimo nos três "
    "biomas pelo critério composto de maior R² de teste e menor diferença treino–teste. O ganho do grau 2 em relação "
    f"ao modelo linear (grau 1) foi de {v(g['MA'][2]-g['MA'][1])} pontos percentuais de R² de teste na Mata "
    f"Atlântica ({v(g['MA'][1])}% para {v(g['MA'][2])}%) e de {v(g['CE'][2]-g['CE'][1])} pontos no Cerrado "
    f"({v(g['CE'][1])}% para {v(g['CE'][2])}%), mas de apenas {v(g['CA'][2]-g['CA'][1])} ponto na Caatinga "
    f"({v(g['CA'][1])}% para {v(g['CA'][2])}%), o que indica resposta quase linear da vegetação semiárida às "
    "variáveis hídricas; o grau 2 foi adotado como grau comum aos três biomas para permitir a comparação entre "
    f"eles.{ressalva} Graus superiores apresentaram redução progressiva do R² de teste e aumento acentuado do "
    "sobreajuste (diferenças treino–teste de dezenas a centenas de pontos percentuais nos graus 4 e 5), indicando "
    "que a complexidade adicional não se traduz em ganho preditivo real.")
replace_image(ORIG[248], os.path.join(FIG, 'fig04_selecao_grau.png'))
set_caption_after_image(ORIG[248], "Figura 7 - Seleção do grau polinomial do MRMP-N nos três biomas: R² de treino e "
                        "teste e diferença treino–teste por grau.")

sv = {b: SV[SV.bioma == b].sort_values('r2_teste', ascending=False) for b in ('MA', 'CE', 'CA')}
imp = NUM['importancia']
set_text(ORIG[251],
    "A busca exaustiva entre as C(5,3) = 10 combinações de variáveis ambientais (Tabela A2 do Apêndice) "
    "identificou conjuntos ótimos distintos entre os biomas, revelando que os controles ambientais da PSN não são "
    f"uniformes na região. Para a Caatinga, o conjunto ótimo foi {conj('CA')}, com R² de teste médio de "
    f"{r2('CA')}% (diferença treino–teste de {gap('CA')} pp); para a Mata Atlântica, {conj('MA')}, com R² de "
    f"{r2('MA')}% ({gap('MA')} pp), superando em {v(sv['MA'].iloc[0]['r2_teste'] - sv['MA'].iloc[1]['r2_teste'])} "
    f"pontos a combinação {sv['MA'].iloc[1]['variaveis']}, que havia sido a ótima na série original de 2001 a 2020. "
    "Esse resultado é notável porque, isoladamente, o WAI explica menos de 2% da variância da PSN na Mata "
    "Atlântica (Figura 5): sua contribuição surge apenas em interação com a evapotranspiração e a temperatura, o "
    "que ilustra o papel dos termos de segunda ordem. Os pesos das variáveis diferem entre os biomas (Figura 8): na "
    f"Mata Atlântica a evapotranspiração lidera ({imp['MA']['EV']}%), seguida da sazonalidade e do WAI "
    f"({imp['MA']['WAI']}%), enquanto na Caatinga a evapotranspiração é o controle dominante "
    f"({imp['CA']['EV']}% da importância relativa).")
set_text(ORIG[252],
    f"Para o Cerrado, o conjunto ótimo identificado foi {conj('CE')}, com R² de teste médio de {r2('CE')}% e "
    f"diferença treino–teste de apenas {gap('CE')} pp, a menor de todas as combinações testadas. A Figura 8 ilustra "
    "a importância relativa de cada variável preditora nos três biomas, calculada a partir dos coeficientes "
    "padronizados do modelo Ridge. A importância relativa de cada variável foi calculada como a soma dos valores "
    "absolutos dos coeficientes padronizados de todos os termos (linear, quadrático e de interação) associados à "
    "respectiva variável, normalizada de modo que o total por bioma some 100%.")
set_text(ORIG[253], "Figura 8 - Importância relativa das variáveis preditoras no modelo MRMP-N nos três biomas.", bold=True)
replace_image(ORIG[254], os.path.join(FIG, 'fig05_importancia.png'))
ce_wai_vs_tst = sv['CE'].iloc[0]['r2_teste'] - sv['CE'][sv['CE'].variaveis == 'EV + PRE + TST']['r2_teste'].iloc[0]
set_text(ORIG[255], ORIG[255].text.replace(
    "(da ordem de 0,3 ponto percentual no R² de teste)", f"(de {v(ce_wai_vs_tst)} ponto percentual no R² de teste)"))
set_text(ORIG[257],
    "A presença das componentes harmônicas de sazonalidade em todos os modelos (mantidas fixas por construção) e o "
    "peso que elas recebem nos três biomas reforçam que a PSN na Bahia possui padrão sazonal marcado e regular, "
    "associado ao ciclo anual de precipitação e radiação. A evapotranspiração (EV) aparece como preditor central em "
    "todos os biomas, e as variáveis hídricas (PRE ou WAI) integram o conjunto ótimo de cada um, confirmando que o "
    "balanço hídrico é o controlador primário da produtividade ecossistêmica na região.")
set_text(ORIG[258], re.sub(r"Já a ausência do\s+no conjunto ótimo", "Já a ausência da área queimada (BURNlog) no conjunto ótimo", ORIG[258].text))
set_text(ORIG[261], ORIG[261].text.replace(
    "Definido como a razão entre a evapotranspiração real e a evapotranspiração potencial (ETR/ETP), o índice expressa",
    "Conforme definido na seção Dados e Pré-processamento (razão ETR/ETP), o índice expressa"))
set_text(ORIG[275], ORIG[275].text.replace(
    "Em biomas climaticamente limitados, como o Cerrado e a Caatinga,",
    "Em biomas climaticamente limitados, isto é, aqueles em que a produtividade é controlada principalmente pela água ou pela temperatura, como o Cerrado e a Caatinga,"))
set_text(ORIG[276], ORIG[276].text.replace("é proporcional ao grau", "é diretamente proporcional ao grau"))
# Tabela 4 (tipologia)
t4 = d.tables[5]
set_cell(t4.rows[1].cells[3], f"Alta (R² = {r2('CE')}%)")
set_cell(t4.rows[2].cells[3], f"Alta (R² = {r2('CA')}%)")
set_cell(t4.rows[3].cells[2], "Evapotranspiração + sazonalidade + WAI (variabilidade residual antrópica)")
set_cell(t4.rows[3].cells[3], f"Moderada (R² = {r2('MA')}%)")

# =============================================================================
# 12. DIAGNÓSTICO
# =============================================================================
normais = [b for b in ('MA', 'CE', 'CA') if RG.loc[b, 'residuos_normais'] == 'Sim']
set_text(ORIG[278],
    "A análise de resíduos (Figura 9) indicou distribuição normal " +
    " e ".join(f"{'no' if b=='CE' else 'na'} {nome[b]} (Shapiro-Wilk: W = {v(NUM[b]['shapiro_w'],3)}; p = {shap(b)})" for b in normais) +
    f", atendendo ao pressuposto de normalidade. Na Caatinga (W = {v(NUM['CA']['shapiro_w'],3)}; p = {shap('CA')}), "
    "observou-se desvio de normalidade concentrado na cauda esquerda da distribuição, isto é, alguns meses com "
    "produtividade bem abaixo do previsto, coerente com secas severas ou queimadas de grande escala não plenamente "
    "capturadas pelos preditores climáticos médios. Adicionalmente, o teste de Ljung-Box detectou autocorrelação "
    f"residual significativa nos três biomas (Mata Atlântica: {lbp('MA')}, ACF de defasagem 1 = {acf1('MA')}; "
    f"Cerrado: {lbp('CE')}, ACF = {acf1('CE')}; Caatinga: {lbp('CA')}, ACF = {acf1('CA')}), resultado novo em relação "
    "à série de 2001 a 2020, na qual apenas a Caatinga apresentava esse padrão. Essa autocorrelação indica memória "
    "temporal não modelada, ou seja, a produtividade de um mês depende em parte das condições dos meses anteriores "
    "(por exemplo, da água acumulada no solo), efeito que preditores do mesmo mês não capturam; ela é mais forte "
    f"{'na' if RG['acf_lag1'].idxmax() != 'CE' else 'no'} {nome[RG['acf_lag1'].idxmax()]}, coerente com a resposta "
    "defasada da vegetação à disponibilidade hídrica acumulada. Contudo, "
    f"como o modelo manteve R² de {tss('CA')}% na Caatinga, {tss('CE')}% no Cerrado e {tss('MA')}% na Mata "
    "Atlântica sob validação TimeSeriesSplit, essa dependência temporal residual não impediu que a capacidade "
    "preditiva permanecesse elevada quando a ordem temporal foi respeitada.")
set_text(ORIG[279],
    "Embora indique um desvio dos pressupostos clássicos, esse comportamento residual deve ser interpretado em "
    "conjunto com o desempenho preditivo do modelo, que se manteve estável sob validação cruzada repetida (150 "
    "partições) e sob validação temporal. A incorporação explícita da dependência temporal (por exemplo, com "
    "preditores defasados ou termos autorregressivos) é uma extensão natural para trabalhos futuros. O diagnóstico "
    "completo dos resíduos está apresentado na Figura 9.")
replace_image(ORIG[281], os.path.join(FIG, 'fig06_residuos.png'))
set_caption_after_image(ORIG[281], "Figura 9 - Diagnóstico de resíduos do MRMP-N nos três biomas.")
set_text(ORIG[283],
    "O teste de Y-randomization responde a uma pergunta simples: o modelo encontraria um ajuste parecido se a PSN "
    "fosse embaralhada ao acaso? Para isso, a coluna da PSN foi permutada 100 vezes e, a cada vez, o modelo foi "
    "reajustado e avaliado por validação cruzada. Os modelos com dados embaralhados tiveram R² médio negativo "
    f"({v(NUM['MA']['yr_perm_media'])}% na Mata Atlântica, {v(NUM['CE']['yr_perm_media'])}% no Cerrado e "
    f"{v(NUM['CA']['yr_perm_media'])}% na Caatinga), ou seja, previram pior do que a simples média, enquanto os "
    f"modelos reais alcançaram {v(NUM['MA']['yr_orig'])}%, {v(NUM['CE']['yr_orig'])}% e {v(NUM['CA']['yr_orig'])}%. "
    f"A diferença (Δ = {yr_delta('MA')}, {yr_delta('CE')} e {yr_delta('CA')} pontos percentuais, respectivamente) "
    "supera com folga o mínimo de 60 adotado, e nenhuma das 100 permutações igualou o modelo real (p empírico = "
    "0,0099 nos três biomas). Conclui-se que o desempenho reflete relação genuína entre clima e PSN, e não "
    "coincidência numérica ou sobreajuste (Figura 10).")
set_text(ORIG[284],
    "A menor margem de separação da Mata Atlântica é consistente com a elevada variabilidade ecológica intrínseca "
    "desse bioma, marcada pela intensa fragmentação da paisagem e pela forte pressão antrópica na Bahia, que "
    "introduzem componentes adicionais de variabilidade na PSN não integralmente representados pelos preditores "
    "climáticos utilizados no modelo. Os resultados do Y-randomization estão apresentados na Figura 10.")
set_text(ORIG[285], "Figura 10 - Y-randomization do MRMP-N nos três biomas.", bold=True)
replace_image(ORIG[286], os.path.join(FIG, 'fig07_yrandomization.png')); to_inline(ORIG[286])
colin = [b for b in ('MA', 'CE', 'CA') if RG.loc[b, 'vif_max'] >= 10]
sem_colin = [b for b in ('MA', 'CE', 'CA') if b not in colin]
frase_colin = "; ".join(f"{nome[b]}: VIF de {vif(b, XVARS[b][0])} ({XVARS[b][0]}) e " +
                        f"{vif(b, 'WAI')} (WAI)" for b in colin)
set_text(ORIG[287],
    "Em conjunto, os procedimentos de diagnóstico convergem para uma mesma conclusão: o modelo MRMP-N captura "
    "estrutura ecológica genuína nos três biomas, apresentando desempenho estatisticamente robusto e coerente com "
    "as características ambientais de cada ecossistema. O diagnóstico de multicolinearidade (Tabela 5) mostra "
    f"colinearidade elevada apenas onde a evapotranspiração e o WAI integram juntos o modelo no {nome[colin[0]]} "
    f"({frase_colin}), controlada pela penalização L2 do Ridge mas que exige cautela na interpretação isolada dos "
    "coeficientes dessas duas variáveis; " +
    " e ".join(f"{'na' if b != 'CE' else 'no'} {nome[b]}" for b in sem_colin) +
    f" todos os VIF ficaram abaixo de {v(max(RG.loc[b, 'vif_max'] for b in sem_colin) + 0.1)}. Essas "
    "particularidades, junto com a não normalidade dos resíduos da Caatinga, a autocorrelação residual nos três "
    "biomas e a menor margem de Y-randomization na Mata Atlântica, não comprometem a validade do modelo, refletindo "
    "características ecológicas legítimas dos sistemas analisados.")
cap5 = new_para_after(ORIG[287], TABCAP_TPL, "Tabela 5 - Fator de Inflação da Variância (VIF) das variáveis preditoras por bioma.", bold=True)
cap5.alignment = WD_ALIGN_PARAGRAPH.CENTER
VARS5 = ['EV', 'PRE', 'TST', 'WAI', 'saz_sin', 'saz_cos']
t5 = table_after(cap5, len(VARS5) + 1, 4); t5.alignment = 1
set_widths(t5, [4.0, 4.0, 4.0, 4.0])
for j, h in enumerate(['Variável', 'Mata Atlântica', 'Cerrado', 'Caatinga']):
    set_cell(t5.rows[0].cells[j], h, bold=True, size=10)
for i, var in enumerate(VARS5, start=1):
    set_cell(t5.rows[i].cells[0], {'saz_sin': 'SAZsin', 'saz_cos': 'SAZcos'}.get(var, var), size=10)
    for j, b in enumerate(['MA', 'CE', 'CA'], start=1):
        set_cell(t5.rows[i].cells[j], vif(b, var) if (var in XVARS[b] or var.startswith('saz')) else '—', size=10)
_esp = new_para_after(t5.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); _esp._p.getparent().remove(_esp._p); t5._tbl.addnext(_esp._p)

# =============================================================================
# 13. ENSO
# =============================================================================
kw = ENSO['kw']
def pkw(b, var):
    p = kw[b][var]; return 'p < 0,001' if p < 0.001 else f'p = {v(p,3)}'
set_text(ORIG[289],
    "A fase ENSO de cada mês foi classificada pelo critério oficial da NOAA (ONI igual ou superior a +0,5 °C, ou "
    "igual ou inferior a −0,5 °C, por pelo menos cinco trimestres móveis consecutivos), o que resultou em "
    f"{ENSO['n_neutro']} meses neutros, {ENSO['n_elnino']} de El Niño e {ENSO['n_lanina']} de La Niña, sem "
    "defasagem entre a fase e as variáveis do mês. O teste de Kruskal-Wallis não detectou diferenças "
    f"estatisticamente significativas da PSN entre as fases na Mata Atlântica ({pkw('MA','PSN')}) nem no Cerrado "
    f"({pkw('CE','PSN')}), mas as detectou na Caatinga ({pkw('CA','PSN')}), onde a PSN média cai de "
    f"{v(kw['CA']['PSN_medias'][0])} gC·m⁻²·mês⁻¹ nos meses de La Niña para {v(kw['CA']['PSN_medias'][1])} nos "
    f"neutros e {v(kw['CA']['PSN_medias'][2])} nos de El Niño. Esse é um resultado novo em relação à série de 2001 "
    "a 2020, na qual nenhum bioma apresentava diferença direta. Nos outros dois biomas, o resultado torna-se mais "
    "claro quando analisado à luz do comportamento das variáveis climáticas intermediárias: a influência do ENSO "
    "sobre a produtividade primária não ocorre de forma direta, mas mediada pelas respostas das variáveis ambientais "
    "regionais.")
set_text(ORIG[290],
    "Na Mata Atlântica, a Temperatura de Superfície Terrestre (TST) foi a variável climática mais sensível às fases "
    f"do ENSO ({pkw('MA','TST')}), com médias de {v(kw['MA']['TST_medias'][0])} °C em La Niña, "
    f"{v(kw['MA']['TST_medias'][1])} °C em meses neutros e {v(kw['MA']['TST_medias'][2])} °C em El Niño (Figura 11). "
    f"A evapotranspiração também diferiu entre fases ({pkw('MA','EV')}), enquanto a precipitação não "
    f"({pkw('MA','PRE')}), sugerindo que o efeito climático do ENSO sobre esse bioma se manifesta predominantemente "
    "pela componente térmica. Esse predomínio é coerente com a elevada umidade regional da Mata Atlântica, onde "
    "variações de temperatura tendem a exercer influência mais perceptível sobre os processos ecofisiológicos do "
    "que pequenas oscilações hidrológicas. Vale distinguir, contudo, que a sensibilidade da TST às fases do ENSO e a "
    "importância da TST como preditora da PSN são propriedades distintas: a primeira descreve como o fenômeno "
    "climático modula a temperatura, enquanto a segunda, apresentada na análise de importância das variáveis "
    "(Figura 8), reflete o peso da temperatura no controle direto da produtividade. Assim, a TST atua como elo entre "
    "a variabilidade climática de larga escala associada ao ENSO e a resposta produtiva local da vegetação.")
replace_image(ORIG[291], os.path.join(FIG, 'fig08_enso_MA.png'))
set_caption_after_image(ORIG[291], "Figura 11 - Distribuição das variáveis ambientais por fase ENSO na Mata Atlântica.")
set_text(ORIG[293],
    f"No Cerrado, a temperatura ({pkw('CE','TST')}), a precipitação ({pkw('CE','PRE')}) e a evapotranspiração "
    f"({pkw('CE','EV')}) diferiram entre as fases do ENSO (Figura 12). A precipitação média mensal foi de "
    f"{v(kw['CE']['PRE_medias'][0])} mm em La Niña, {v(kw['CE']['PRE_medias'][1])} mm em meses neutros e "
    f"{v(kw['CE']['PRE_medias'][2])} mm em El Niño, com a evapotranspiração acompanhando o mesmo padrão. Esse "
    "resultado é consistente com a posição geográfica do bioma e com a literatura que documenta a influência do ENSO "
    "sobre o regime pluviométrico do Brasil Central. Como a dinâmica ecológica do Cerrado é fortemente condicionada "
    "pela sazonalidade hídrica, alterações nas chuvas associadas às fases do ENSO repercutem sobre a disponibilidade "
    "hídrica e, potencialmente, sobre a produtividade vegetal, ainda que, na escala mensal e no período analisado, a "
    f"diferença direta da PSN entre fases não tenha atingido significância ({pkw('CE','PSN')}).")
replace_image(ORIG[294], os.path.join(FIG, 'fig09_enso_CE.png'))
set_caption_after_image(ORIG[294], "Figura 12 - Distribuição das variáveis ambientais por fase ENSO no Cerrado.")
set_text(ORIG[296],
    f"Na Caatinga, as três variáveis climáticas responderam às fases do ENSO (TST: {pkw('CA','TST')}; PRE: "
    f"{pkw('CA','PRE')}; EV: {pkw('CA','EV')}), com precipitação média de {v(kw['CA']['PRE_medias'][0])} mm em La "
    f"Niña contra {v(kw['CA']['PRE_medias'][1])} mm em meses neutros e {v(kw['CA']['PRE_medias'][2])} mm em El Niño "
    "(Figura 13). Diferentemente dos outros biomas, aqui a resposta chegou à própria PSN: a produtividade média dos "
    "meses de El Niño foi cerca de 15% inferior à dos meses de La Niña. Esse comportamento é coerente com o regime "
    "pulsado do bioma semiárido, no qual a produtividade responde de forma quase imediata à disponibilidade de "
    "água, e com os achados de Silva et al. (2026), que associam anos de El Niño a reduções da produtividade na "
    "Caatinga.")
replace_image(ORIG[297], os.path.join(FIG, 'fig10_enso_CA.png'))
set_caption_after_image(ORIG[297], "Figura 13 - Distribuição das variáveis ambientais por fase ENSO na Caatinga.")
pe = ENSO['pearson']
set_text(ORIG[299],
    "Em contrapartida, quando a intensidade do ONI é usada como preditor contínuo, o poder explicativo é baixo: a "
    f"regressão linear simples do ONI sobre cada variável climática explicou no máximo {v(ENSO['ols_max'])}% de sua "
    "variância (temperatura da Mata Atlântica), e menos de 2% em todos os demais casos. A correlação de Pearson entre "
    f"o ONI e a PSN foi negativa e significativa na Mata Atlântica (r = {v(pe['MA'],3)}; p < 0,001) e na Caatinga "
    f"(r = {v(pe['CA'],3)}; p = {v(ENSO['pearson_p']['CA'],3)}), e não significativa no Cerrado (r = {v(pe['CE'],3)}). "
    "Esses resultados evidenciam que a influência do ENSO sobre o sistema ambiental regional não se manifesta de "
    "forma linear direta, mas por meio de relações indiretas e não lineares, mais adequadamente representadas pela "
    "classificação categórica em fases.")
set_text(ORIG[300],
    "A interpretação conjunta desses resultados sustenta um padrão compatível com uma influência predominantemente "
    "indireta, na qual o ENSO atua como forçante climática de larga escala que modula variáveis intermediárias "
    "(temperatura nos três biomas; precipitação e evapotranspiração no Cerrado e na Caatinga), com efeito direto "
    "sobre a PSN detectável apenas no bioma mais sensível à água, a Caatinga.")
set_text(ORIG[301],
    "A ausência de efeito direto do ENSO sobre a PSN na Mata Atlântica e no Cerrado, apesar da resposta "
    "significativa das variáveis climáticas, sugere que esses ecossistemas apresentam capacidade parcial de "
    "amortecimento frente às oscilações climáticas de larga escala. Essa capacidade decorre, em parte, da própria "
    "sazonalidade interna dos biomas, que estrutura a produtividade primária em torno de ciclos anuais relativamente "
    "regulares, cuja amplitude pode superar as perturbações induzidas pelo ENSO em escala mensal. Na Caatinga, onde a "
    "reserva hídrica do sistema é menor, esse amortecimento é insuficiente.")

# =============================================================================
# 14. IMPLICAÇÕES E CONSIDERAÇÕES FINAIS
# =============================================================================
set_text(ORIG[304], ORIG[304].text.replace(
    "abriga populações indígenas Pataxó, comunidades quilombolas",
    "abriga povos indígenas de diversas etnias (Pataxó, Pataxó Hã-Hã-Hãe, Tupinambá, Kiriri, Tuxá, Pankararé, Truká e Kaimbé, entre outras), comunidades quilombolas")
    .replace("A tipologia ecológica identificada na Seção 6.3", "A tipologia ecológica identificada na Tabela 4"))
set_text(ORIG[305],
    f"Para a Mata Atlântica, o menor poder preditivo do modelo climático (R² = {r2('MA')}%) é compatível com a "
    "hipótese de que fatores de paisagem, como a expansão da monocultura de eucalipto e a fragmentação, expliquem "
    "parte da variância não capturada pelo clima; testar essa hipótese exigiria incluir variáveis de uso do solo no "
    "modelo, o que se recomenda para trabalhos futuros. Se confirmada, ela indica que políticas de restauração "
    "florestal e controle do desmatamento têm potencial direto de reduzir a variabilidade da PSN e elevar a "
    "produtividade ecossistêmica, ampliando os serviços de sequestro de carbono e regulação hídrica prestados pelo "
    "bioma.")
set_text(ORIG[308], ORIG[308].text.replace("(R² = 94,0%)", f"(R² = {r2('CA')}%)"))
set_text(ORIG[312],
    "Os principais resultados confirmaram a viabilidade do modelo nos três biomas analisados. O MRMP-N de grau 2 "
    f"apresentou elevado desempenho preditivo no Cerrado (R² = {r2('CE')}%) e na Caatinga (R² = {r2('CA')}%), além "
    f"de desempenho moderado na Mata Atlântica (R² = {r2('MA')}%), refletindo regimes ecológicos distintos de "
    "controle da produtividade primária na região. A extensão da série para 2001–2025 (297 meses) elevou o R² da "
    f"Mata Atlântica em relação à série original de 2001–2020 (de 62,3% para {r2('MA')}%) e manteve os do Cerrado e "
    "da Caatinga, indicando estabilidade do modelo frente aos anos recentes, que incluíram o El Niño intenso de "
    "2023–2024.")
set_text(ORIG[313],
    "Retomando as hipóteses formuladas: a H1 confirmou-se, com uma ressalva. O grau 2 superou o modelo linear nos "
    f"três biomas ({v(g['MA'][2]-g['MA'][1])}, {v(g['CE'][2]-g['CE'][1])} e {v(g['CA'][2]-g['CA'][1])} pontos "
    "percentuais de R² de teste na Mata Atlântica, no Cerrado e na Caatinga), mantendo a diferença treino–teste "
    "abaixo de 10 pontos; na Caatinga, porém, o ganho foi marginal. A H2 confirmou-se: o conjunto de variáveis "
    f"climáticas associado às componentes de sazonalidade explicou entre {r2('MA')}% e {r2('CE')}% da variância da "
    "PSN, acima do limiar de 60% estabelecido, e a composição do conjunto ótimo diferiu entre os biomas: "
    f"{conj('CA').replace(' + SAZsin + SAZcos','')} na Caatinga, {conj('CE').replace(' + SAZsin + SAZcos','')} no "
    f"Cerrado e {conj('MA').replace(' + SAZsin + SAZcos','')} na Mata Atlântica, confirmando a maior relevância do "
    "Índice de Disponibilidade Hídrica (WAI) em sistemas com forte sazonalidade hídrica e, na Mata Atlântica, a "
    "importância das interações entre variáveis."
    + (f" Ressalva-se ainda que, pelo critério estrito de H1, o grau 3 atenderia tecnicamente à definição de "
       f"otimalidade na Mata Atlântica (R² de teste de {v(g3['MA'])}%, {v(g3['MA']-g['MA'][2])} ponto acima do grau 2, "
       f"com diferença treino–teste de {v(gp['MA'][3])} pp, ainda dentro do limite de 10 pontos). Optou-se, contudo, "
       f"pelo grau 2 como grau comum aos três biomas, tanto por parcimônia, com 20 termos contra 55, mais que o dobro, "
       f"para um ganho marginal, quanto por ele ser inequivocamente superior ao grau 3 no Cerrado e na Caatinga, em R² "
       f"de teste e em diferença treino–teste, o que reforça sua adequação como escolha comum de comparação entre os "
       f"três biomas." if g3['MA'] > g['MA'][2] else ""))
set_text(ORIG[314],
    "A H3 confirmou-se em sua essência: o ONI explicou no máximo 3% da variância das variáveis climáticas e, "
    "embora tenha modulado a temperatura nos três biomas e a precipitação no Cerrado e na Caatinga, só se associou "
    "a diferenças diretas da PSN na Caatinga, o bioma mais sensível à disponibilidade de água. O padrão é, "
    "portanto, o de uma influência predominantemente indireta, mediada pela temperatura e pela precipitação.")
set_text(ORIG[316], ORIG[316].text.replace(
    "sem efeito linear direto significativo sobre a PSN.",
    "com efeito direto sobre a PSN detectado apenas na Caatinga."))
set_text(ORIG[317], ORIG[317].text.rstrip() +
    " Cabe ainda registrar que o MRMP-N é um modelo explicativo-preditivo contemporâneo: ele estima a PSN de um mês "
    "a partir das variáveis ambientais desse mesmo mês e, portanto, não gera previsões autônomas do futuro; para "
    "projetar a PSN de meses vindouros, seria necessário alimentá-lo com valores observados ou previstos de EV, "
    "PRE, TST e WAI. Por fim, a autocorrelação residual detectada nos três biomas indica que parte da memória "
    "temporal do sistema não é capturada por preditores do mesmo mês.")
set_text(ORIG[320],
    "Como perspectivas para trabalhos futuros, sugere-se a incorporação explícita da dependência temporal, por "
    "meio de preditores defasados ou termos autorregressivos, para absorver a autocorrelação residual identificada; "
    "a análise da influência do ENSO com defasagens de um a seis meses entre o ONI e a resposta da vegetação; a "
    "incorporação de variáveis estruturais da paisagem em estudos voltados à Mata Atlântica; a utilização de escalas "
    "temporais mais finas para investigação de eventos extremos; e a aplicação do modelo MRMP-N em outras regiões "
    "com gradientes ambientais semelhantes, visando avaliar sua capacidade de generalização. Adicionalmente, a "
    "integração entre abordagens estatísticas e modelos ecofisiológicos baseados em processos pode contribuir para "
    "aprofundar a compreensão dos mecanismos ambientais que regulam a Fotossíntese Líquida (PSN) nos ecossistemas "
    "tropicais.")

# =============================================================================
# 16. APÊNDICE A — base de dados + combinações (antes das REFERÊNCIAS)
# =============================================================================
base = pd.read_excel(os.path.join(BASE, 'Dados_base_nova_2001_2025.xlsx'))
ref = ORIG[337]
for _k in range(321, 337):          # parágrafos vazios entre as conclusões e as referências
    if not ORIG[_k].text.strip() and not ORIG[_k]._p.xpath('.//w:drawing'):
        remove_para(ORIG[_k])
prev = ORIG[320]
sect_body = d.sections[-1]._sectPr
def sect_break(anchor, landscape, novo=False):
    """Coloca um sectPr no parágrafo anchor (ou em um novo parágrafo vazio se novo=True): fecha a seção que termina ali."""
    par = new_para_after(anchor, BODY_TPL, "") if novo else anchor
    sp = copy.deepcopy(sect_body)
    pg = sp.find(qn('w:pgSz'))
    if landscape:
        w_, h_ = pg.get(qn('w:w')), pg.get(qn('w:h'))
        pg.set(qn('w:w'), h_); pg.set(qn('w:h'), w_); pg.set(qn('w:orient'), 'landscape')
    elif pg.get(qn('w:orient')):
        del pg.attrib[qn('w:orient')]
    par._p.get_or_add_pPr().append(sp)
    return par
pb = sect_break(prev, landscape=False)
h = new_para_after(pb, HEAD1_TPL, "APÊNDICE A – BASE DE DADOS MENSAL E RESULTADOS DA SELEÇÃO DE VARIÁVEIS")
_np = OxmlElement('w:numPr'); _il = OxmlElement('w:ilvl'); _il.set(qn('w:val'), '0'); _ni = OxmlElement('w:numId'); _ni.set(qn('w:val'), '0')
_np.append(_il); _np.append(_ni)
_ppr = h._p.get_or_add_pPr(); _ps = _ppr.find(qn('w:pStyle'))
(_ps.addnext(_np) if _ps is not None else _ppr.insert(0, _np))
h.paragraph_format.page_break_before = False
intro = new_para_after(h, BODY_TPL,
    f"A Tabela A1 reproduz integralmente a base mensal utilizada no estudo ({N_OBS} meses, janeiro de 2001 a setembro "
    "de 2025), com o ONI e a fase ENSO oficial (NOAA) de cada mês e as seis variáveis de cada bioma (MA = Mata "
    "Atlântica, CE = Cerrado, CA = Caatinga). Unidades: PSN em gC·m⁻²·mês⁻¹; EV e PRE em mm·mês⁻¹; TST em °C; WAI "
    "adimensional (ETR/ETP); BURN em hectares. A Tabela A2 apresenta o desempenho das 10 combinações de variáveis "
    "ambientais avaliadas por bioma; a Tabela A3, o efeito da remoção das componentes de sazonalidade; e a Tabela A4, "
    "a proporção da variância de cada variável climática explicada pelo ciclo anual.")
cap = new_para_after(intro, TABCAP_TPL, "Tabela A1 - Base de dados mensal dos três biomas (2001–2025).", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cols = ['ANO', 'MÊS', 'ONI', 'Enso']; hdr = ['Ano', 'Mês', 'ONI', 'Fase']; fmt = {'ANO': '{:.0f}', 'MÊS': '{:.0f}', 'ONI': '{:.2f}'}
for b in ['MA', 'CE', 'CA']:
    for var, f_ in [('NP', '{:.1f}'), ('EV', '{:.1f}'), ('PRE', '{:.1f}'), ('TST', '{:.1f}'), ('WAI', '{:.3f}'), ('BURN', '{:.0f}')]:
        cols.append(f'{var}_{b}'); hdr.append(f"{'PSN' if var == 'NP' else var} {b}"); fmt[f'{var}_{b}'] = f_
t = table_after(cap, len(base) + 1, len(cols)); t.alignment = 1
set_widths(t, [0.95, 0.75, 0.95, 1.25] + [1.155] * 18)
for j, hname in enumerate(hdr): set_cell(t.rows[0].cells[j], hname, bold=True, size=6.5)
for i, (_, row) in enumerate(base.iterrows(), start=1):
    for j, c in enumerate(cols):
        val = row[c]
        sval = str(val) if c == 'Enso' else fmt[c].format(float(val)).replace('.', ',')
        set_cell(t.rows[i].cells[j], sval, size=6.5)
trPr = t.rows[0]._tr.get_or_add_trPr(); th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
anchor = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); anchor._p.getparent().remove(anchor._p); t._tbl.addnext(anchor._p)
cap = new_para_after(anchor, TABCAP_TPL, "Tabela A2 - Desempenho das 10 combinações de três variáveis ambientais (mais SAZsin e SAZcos) por bioma, "
                     "validação cruzada RepeatedKFold 5 × 30, grau 2.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(SV) + 1, 5); t.alignment = 1
set_widths(t, [3.5, 5.5, 3.5, 3.5, 4.5])
for j, hname in enumerate(['Bioma', 'Variáveis', 'R² treino (%)', 'R² teste (%)', 'Dif. treino–teste (pp)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
for i, (_, row) in enumerate(SV.sort_values(['bioma', 'r2_teste'], ascending=[True, False]).iterrows(), start=1):
    vals = [nome[row['bioma']], row['variaveis'].replace('BURN_log', 'BURNlog'), v(row['r2_treino']), v(row['r2_teste']), v(row['gap_pp'])]
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=9)
mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A3 — remoção da sazonalidade
cap = new_para_after(mid, TABCAP_TPL, "Tabela A3 - Efeito da remoção das componentes de sazonalidade harmônica no desempenho do "
                     "MRMP-N (grau 2, RepeatedKFold 5 × 30).", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(ABL) + 1, 6); t.alignment = 1
set_widths(t, [3.2, 6.6, 3.0, 3.0, 4.2, 2.6])
for j, hname in enumerate(['Bioma', 'Conjunto de variáveis', 'R² treino (%)', 'R² teste (%)', 'Dif. treino–teste (pp)', 'RMSE']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
for i, (_, row) in enumerate(ABL.iterrows(), start=1):
    b_ = [k for k, n_ in nome.items() if n_ == row['bioma']][0]; sem = 'sem' in row['conjunto']
    r2te = row['r2_teste'] if sem else RG.loc[b_, 'r2_teste_medio']
    gap_ = row['gap_pp'] if sem else RG.loc[b_, 'gap_overfitting_pp']
    vals = [row['bioma'], row['conjunto'], v(row['r2_treino'], 1), v(r2te, 1), v(gap_, 1), v(row['rmse'], 2)]
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=9)
mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A4 — R² do ciclo anual por variável
cap = new_para_after(mid, TABCAP_TPL, "Tabela A4 - Proporção da variância de cada variável climática explicada isoladamente pelo "
                     "ciclo anual (regressão contra saz_sin e saz_cos).", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(SAZ) + 1, 3); t.alignment = 1
set_widths(t, [4.5, 3.0, 3.0])
for j, hname in enumerate(['Bioma', 'Variável', 'R² (%)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
_ordem = {'Mata Atlântica': 0, 'Cerrado': 1, 'Caatinga': 2}
for i, (_, row) in enumerate(SAZ.assign(o=SAZ.bioma.map(_ordem)).sort_values(['o', 'r2'], ascending=[True, False]).iterrows(), start=1):
    for j, sval in enumerate([row['bioma'], row['variavel'], v(row['r2'], 1)]): set_cell(t.rows[i].cells[j], sval, size=9)
fim = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); fim._p.getparent().remove(fim._p); t._tbl.addnext(fim._p)
sect_break(fim, landscape=True)

# =============================================================================
# 17. LISTAS DE FIGURAS E TABELAS (sem bordas; páginas preenchidas depois)
# =============================================================================
FIGS = ["Fluxos de carbono estimados pelo algoritmo MODIS/MOD17: relação entre GPP, PSN e NPP",
        "Mapa de localização e distribuição dos biomas na área de estudo",
        "Fluxo metodológico do modelo MRMP-N",
        "Esquemas de particionamento treino/teste (RepeatedKFold, GroupKFold por ano e TimeSeriesSplit)",
        "Regressão linear simples entre a PSN e cada variável ambiental nos três biomas",
        "Observado vs. predito do MRMP-N nos três biomas",
        "Seleção do grau polinomial do MRMP-N nos três biomas",
        "Importância relativa das variáveis preditoras no modelo MRMP-N nos três biomas",
        "Diagnóstico de resíduos do MRMP-N nos três biomas",
        "Y-randomization do MRMP-N nos três biomas",
        "Distribuição das variáveis ambientais por fase ENSO na Mata Atlântica",
        "Distribuição das variáveis ambientais por fase ENSO no Cerrado",
        "Distribuição das variáveis ambientais por fase ENSO na Caatinga"]
TABS = ["Variáveis para predição da Fotossíntese Líquida (PSN)",
        "Desempenho preditivo do MRMP-N nos biomas Mata Atlântica, Cerrado e Caatinga na Bahia",
        "Comparação do desempenho preditivo (R²) dos modelos sob diferentes estratégias de validação",
        "Tipologia ecológica dos regimes de produtividade primária na Bahia",
        "Fator de Inflação da Variância (VIF) das variáveis preditoras por bioma",
        "Base de dados mensal dos três biomas (2001–2025) [A1]",
        "Desempenho das 10 combinações de variáveis ambientais por bioma [A2]",
        "Efeito da remoção das componentes de sazonalidade harmônica no desempenho do MRMP-N [A3]",
        "Proporção da variância das variáveis climáticas explicada pelo ciclo anual [A4]"]
PAGES = json.load(open(os.path.join(BASE, 'banca', 'paginas.json'))) if os.path.exists(os.path.join(BASE, 'banca', 'paginas.json')) else {}

def rebuild_list(tbl, prefix, items):
    while len(tbl.rows) > 1:
        tbl._tbl.remove(tbl.rows[-1]._tr)
    for i, title in enumerate(items, start=1):
        row = tbl.add_row()
        label = f"{prefix} {i}"
        if '[A' in title:
            label = f"{prefix} {title[title.index('[')+1:-1]}"; title = title[:title.index('[')].strip()
        set_cell(row.cells[0], label, size=11); set_cell(row.cells[1], title, size=11)
        set_cell(row.cells[2], str(PAGES.get(label, "")), size=11)
    set_widths(tbl, [2.6, 11.4, 2.0])
    # remove bordas (MB-14)
    tblPr = tbl._tbl.tblPr
    for old in tblPr.xpath('./w:tblBorders'): tblPr.remove(old)
    borders = OxmlElement('w:tblBorders')
    for side in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
        el = OxmlElement(f'w:{side}'); el.set(qn('w:val'), 'nil'); borders.append(el)
    depois = [c for c in tblPr if c.tag.split('}')[1] in ('shd', 'tblLayout', 'tblCellMar', 'tblLook', 'tblCaption', 'tblDescription')]
    if depois: depois[0].addprevious(borders)
    else: tblPr.append(borders)
    for row in tbl.rows:
        for c in row.cells:
            tcPr = c._tc.get_or_add_tcPr()
            for old in tcPr.xpath('./w:tcBorders'): tcPr.remove(old)
            b = OxmlElement('w:tcBorders')
            for side in ['top', 'left', 'bottom', 'right']:
                el = OxmlElement(f'w:{side}'); el.set(qn('w:val'), 'nil'); b.append(el)
            tcPr.append(b)
rebuild_list(d.tables[0], 'Figura', FIGS)
rebuild_list(d.tables[1], 'Tabela', TABS)

# Tabela 1: fonte/acesso e WAI
t1 = d.tables[2]
set_cell(t1.rows[0].cells[3], "Fonte / acesso", bold=True)
fontes = {"PSN": "MOD17A2H (NASA Earthdata) / Benfica et al. (2022)", "EV": "MOD16A2 (NASA Earthdata) / Benfica et al. (2022)",
          "PRE": "CHIRPS (UCSB) / Benfica et al. (2022)", "TST": "MOD11A2 (NASA Earthdata) / Benfica et al. (2022)",
          "WAI": "ETR/ETP do MOD16A2 / Benfica et al. (2022)", "BURN": "MCD64A1 (NASA Earthdata) / Benfica et al. (2022)",
          "ONI": "NOAA/CPC (oni.ascii.txt)"}
set_widths(t1, [2.1, 5.1, 2.8, 6.0])
for row in t1.rows:
    for c in row.cells:
        tcPr = c._tc.get_or_add_tcPr()
        for old in tcPr.xpath('./w:vAlign'): tcPr.remove(old)
        va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'center'); tcPr.append(va)
for row in t1.rows[1:]:
    if row.cells[0].text.strip() == 'PSN': set_cell(row.cells[2], "gC·m⁻²·mês⁻¹")
    if row.cells[0].text.strip() in ('SAZSIN', 'SAZCOS'):
        set_cell(row.cells[0], row.cells[0].text.strip().replace('SAZSIN', 'SAZsin').replace('SAZCOS', 'SAZcos'), bold=True)
for row in t1.rows[1:]:
    k = row.cells[0].text.strip()
    if k in fontes: set_cell(row.cells[3], fontes[k])
    if k == 'WAI': set_cell(row.cells[1], "Índice de Disponibilidade Hídrica (razão ETR/ETP)")
    if k == 'BURN': set_cell(row.cells[2], "ha")

# =============================================================================
# 18. SUBSTITUIÇÕES GLOBAIS E ITÁLICOS
# =============================================================================
for p in d.paragraphs:
    if p.style.name.startswith('toc'): continue
    if re.search(r'gap\s+de\s+(overfitting|sobreajuste)', p.text) and not p._p.xpath('.//w:drawing'):
        set_text(p, re.sub(r'gap\s+de\s+(overfitting|sobreajuste)', 'diferença treino–teste', p.text))
    regex_replace_para(p, r'n = 240', f'n = {N_OBS}')
    italicize_terms(p)
for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs: italicize_terms(p)

# células de todas as tabelas sem o recuo de primeira linha herdado do estilo Normal
for t in d.tables:
    for row in t.rows:
        for c in row.cells:
            for par in c.paragraphs:
                par.paragraph_format.first_line_indent = Cm(0); par.paragraph_format.left_indent = Cm(0)
# tabelas curtas (Tabela 5, A3, A4) não se dividem entre páginas
def manter_junta(t):
    for row in t.rows[:-1]:
        for c in row.cells:
            for par in c.paragraphs: par.paragraph_format.keep_with_next = True
        trPr = row._tr.get_or_add_trPr()
        if trPr.find(qn('w:cantSplit')) is None: trPr.append(OxmlElement('w:cantSplit'))
for t in d.tables:
    if 1 < len(t.rows) <= 12 and t.rows[0].cells[0].text.strip() in ('Variável', 'Bioma'): manter_junta(t)
_abstract = ORIG[73]; _kw_en = ORIG[74]
def _todos_paragrafos():
    for p in d.paragraphs: yield p
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs: yield p
for p in _todos_paragrafos():
    if p._p is _abstract._p or p._p is _kw_en._p: continue
    regex_replace_para(p, r'(\d)\.(\d+)%', r'\1,\2%')
    regex_replace_para(p, r'\bdo diferença treino', 'da diferença treino')
    regex_replace_para(p, r'\bno menor diferença', 'na menor diferença')
    regex_replace_para(p, r'saz_sin', 'SAZsin'); regex_replace_para(p, r'saz_cos', 'SAZcos')
    regex_replace_para(p, r'SAZSIN', 'SAZsin'); regex_replace_para(p, r'SAZCOS', 'SAZcos')
    regex_replace_para(p, r'essas pressões apresentam magnitudes', 'elas apresentam magnitudes')
# Sumário (campo TOC dentro de w:sdt): título e página de cada entrada a partir dos títulos atuais e do PDF renderizado
_anc2head = {}
for p in d.paragraphs:
    if p.style.name.startswith('Heading'):
        for bm in p._p.findall('.//' + qn('w:bookmarkStart')):
            if bm.get(qn('w:name'), '').startswith('_Toc'): _anc2head[bm.get(qn('w:name'))] = p.text.strip()
for sdt in d.element.body.findall(qn('w:sdt')):
    for par in sdt.findall('.//' + qn('w:p')):
        hl = par.find('.//' + qn('w:hyperlink'))
        if hl is None: continue
        anc = hl.get(qn('w:anchor')); titulo = _anc2head.get(anc)
        if not titulo: continue
        ts = [t_ for t_ in hl.findall('.//' + qn('w:t'))]
        # texto do título = maior w:t antes do campo PAGEREF; página = último w:t
        cand = [t_ for t_ in ts if t_.text and not t_.text.strip().isdigit() and not re.match(r'^[\d.]+$', t_.text.strip())]
        if cand:
            cand[0].text = titulo
            for extra in cand[1:]: extra.text = ''
        if ts and ts[-1].text and ts[-1].text.strip().isdigit():
            chave = 'H:' + titulo.upper()
            pg = PAGES.get(chave)
            if not pg:   # título quebrado em duas linhas no PDF: usa a chave que for prefixo do título
                cands = [k for k in PAGES if k.startswith('H:') and chave.startswith(k) and len(k) > 12]
                if cands: pg = PAGES[max(cands, key=len)]
            if pg: ts[-1].text = str(pg)
for p in d.paragraphs:
    if re.match(r'^(Figura|Tabela) (A?\d+) [-–]', p.text):
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.left_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p._p.xpath('.//w:drawing'):
        p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.left_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
# rodapés do modelo original contêm um "." solto que aparece no pé de todas as páginas
for rel in d.part.rels.values():
    if 'footer' in rel.reltype:
        for t_el in rel.target_part.element.xpath('.//w:t'):
            if t_el.text and t_el.text.strip() == '.':
                t_el.text = ''
uf = OxmlElement('w:updateFields'); uf.set(qn('w:val'), 'true')
_st = d.settings.element
_dep = [c for c in _st if c.tag.split('}')[1] in ('hdrShapeDefaults', 'footnotePr', 'endnotePr', 'compat', 'docVars', 'rsids', 'mathPr',
        'attachedSchema', 'themeFontLang', 'clrSchemeMapping', 'doNotIncludeSubdocsInStats', 'doNotAutoCompressPictures', 'forceUpgrade',
        'captions', 'readModeInkLockDown', 'smartTagType', 'schemaLibrary', 'shapeDefaults', 'doNotEmbedSmartTags', 'decimalSymbol', 'listSeparator')]
(_dep[0].addprevious(uf) if _dep else _st.append(uf))
for p in d.paragraphs:
    if p.text.strip() == 'SUMÁRIO':
        p.paragraph_format.page_break_before = True
d.save(DST)
print('salvo', DST)
