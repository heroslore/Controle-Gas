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
ROB = os.path.join(RES, 'robustez'); RJ = json.load(open(os.path.join(ROB, 'robustez.json'), encoding='utf-8'))
GT = pd.read_csv(os.path.join(ROB, 'grau_temporal.csv')); CT = pd.read_csv(os.path.join(ROB, 'combos_temporal.csv'))
ES = pd.read_csv(os.path.join(ROB, 'estabilidade_selecao.csv')); PI = pd.read_csv(os.path.join(ROB, 'permutation_importance.csv'))
NT = pd.read_csv(os.path.join(ROB, 'nulos_temporais.csv'))
def _ord(n): return f"{n}º"
_ORDF = {1: 'primeira', 2: 'segunda', 3: 'terceira', 4: 'quarta', 5: 'quinta', 6: 'sexta', 7: 'sétima', 8: 'oitava', 9: 'nona', 10: 'décima'}
def _vm(x, nd=1): return v(x, nd).replace('-', '−')
ENSO = json.load(open(os.path.join(RES, 'enso_resumo.json'), encoding='utf-8'))
ABL = pd.read_csv(os.path.join(RES, 'ablacao_sazonalidade.csv'))
SAZ = pd.read_csv(os.path.join(RES, 'sazonalidade_variaveis.csv'))

def v(x, nd=1):
    return f'{x:.{nd}f}'.replace('.', ',')

def r2(b, nd=1):  return v(RG.loc[b, 'r2_teste_medio'], nd)
def r2dp(b, nd=1):return v(RG.loc[b, 'r2_teste_dp'], nd)
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
# ---- análise do ENSO em anomalias mensais (Analise_ENSO_Anomalias_PSN.py; fase oficial NOAA da base)
JA  = json.load(open(os.path.join(RES, 'enso_anomalias.json'), encoding='utf-8'))
T6  = pd.read_csv(os.path.join(RES, 'enso_anomalias', 'tabela6_anomalias_por_fase.csv'))
A5  = pd.read_csv(os.path.join(RES, 'enso_anomalias', 'tabelaA5_boxplots_por_fase.csv'))
A4X = pd.read_csv(os.path.join(RES, 'enso_anomalias', 'tabelaA4_sazonalidade_importancia.csv'))
def pj(p):  return 'p < 0,001' if p < 0.001 else f'p = {v(p, 3)}'
def pv3(p): return '< 0,001' if p < 0.001 else v(p, 3)
def sgn(x, nd=1): return ('+' if x >= 0 else '−') + v(abs(x), nd)
def vm(x, nd=2): return ('−' if x < 0 else '') + v(abs(x), nd)
def faixa(a, b): return a if a == b else f'{a}% a {b}'
def t6(b, var): return JA['tabela6'][f'{nome[b]}|{var}']
def a5(b, var, f): return JA['a5'][f'{nome[b]}|{var}|{f}']
def cmp_(b, f, L): return JA['comp'][f'{nome[b]}|{f}|{L}']
def med(b, f, pred='TODOS'): return JA['mediacao'][f'{nome[b]}|{f}|{pred}']
def a4x(b, var): return JA['a4'][f'{nome[b]}|{var}']
NF = JA['n_fase']
JI = json.load(open(os.path.join(RES, 'interanual.json'), encoding='utf-8'))
T7 = pd.read_csv(os.path.join(RES, 'interanual', 'tabela7_interanual.csv'))
def ji(b): return JI['biomas'][b]
def _lagdesc(b):
    L = JA['lag'][nome[b]]; sig = [x['lag'] for x in L if x['p'] < 0.05]
    imax = max(L, key=lambda x: abs(x['rho'])); ult = max(sig) if sig else -1
    prim_ns = next((x['lag'] for x in L if x['p'] >= 0.05), 13)
    return dict(rho0=L[0]['rho'], p0=L[0]['p'], lagmax=imax['lag'], rhomax=imax['rho'], ult_sig=ult, prim_ns=prim_ns)
LN_CE = t6('CE', 'PSN')['delta_LN']; LN_CA = t6('CA', 'PSN')['delta_LN']
LN_LO, LN_HI = sorted([LN_CE, LN_CA])
P10_MA = (t6('MA', 'PSN')['pct_abaixo_P10_EN'], t6('MA', 'PSN')['pct_abaixo_P10_N'], t6('MA', 'PSN')['pct_abaixo_P10_LN'])
def _ult_lag_sig(b, f):
    ls = [L for L in (0, 1, 2, 3, 4, 6, 9, 12) if cmp_(b, f, L)['p'] < 0.05]; return max(ls) if ls else None
EXTENSO = {0: 'zero', 1: 'um', 2: 'dois', 3: 'três', 4: 'quatro', 5: 'cinco', 6: 'seis', 7: 'sete', 8: 'oito', 9: 'nove', 10: 'dez', 11: 'onze', 12: 'doze'}

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
    f"{r2('CE')}% (± {r2dp('CE')}) da variância da PSN no Cerrado, {r2('CA')}% (± {r2dp('CA')}) na Caatinga e "
    f"{r2('MA')}% (± {r2dp('MA')}) na Mata Atlântica. Em escala mensal e com agregação espacial por bioma, o RMSE de "
    f"teste variou de {rmse('CA')} a {rmse('MA')} gC·m⁻²·mês⁻¹ e o MAE de {mae('CA')} a {mae('MA')} gC·m⁻²·mês⁻¹; a "
    "instabilidade dos coeficientes associada à multicolinearidade (VIF elevado entre evapotranspiração e "
    "disponibilidade hídrica no Cerrado) foi contida pela regularização Ridge. Os "
    "resultados evidenciaram regimes ecológicos distintos de controle da PSN: limitação hídrica "
    "sazonal no Cerrado, resposta pulsada à precipitação na Caatinga e controle multifatorial na Mata Atlântica. A "
    "análise do El Niño–Oscilação Sul (ENSO), conduzida sobre anomalias mensais, indicou influência indireta e "
    f"defasada sobre a PSN: nos meses de La Niña a PSN ficou cerca de {v(LN_LO,0)}% a {v(LN_HI,0)}% acima do normal "
    "no Cerrado e na Caatinga, associada principalmente a anomalias positivas de evapotranspiração e com persistência "
    "de vários meses no Cerrado; na Mata Atlântica, as medianas brutas foram semelhantes entre as fases, mas, após a "
    f"remoção do ciclo sazonal, os meses de El Niño apresentaram redução média de {v(abs(t6('MA','PSN')['delta_EN']))}% "
    f"na PSN e aumento da frequência de meses extremamente baixos (de {v(P10_MA[1],0)}% para {v(P10_MA[0],0)}%), "
    "associados ao aquecimento da superfície. Os resultados indicam a viabilidade da regressão "
    "polinomial regularizada para representar relações ambientais complexas e reforçam a importância de abordagens "
    "diferenciadas para o monitoramento dos biomas baianos."
)
abstract = (
    "Conventional linear models may be insufficient to represent non-linear ecological relationships and "
    "interactions among environmental variables. This study developed and validated a Multiple Polynomial "
    "Regression Model of order N (MRMP-N), estimated by Ridge regression, to analyze Net Photosynthesis (PSN) in the "
    "Atlantic Forest, Cerrado and Caatinga biomes of Bahia, Brazil, between January 2001 and September 2025. Monthly "
    f"remote sensing data and climate variables were used, totaling {N_OBS} observations per biome. The polynomial "
    "degree and the set of predictor variables were determined empirically, and performance was assessed by repeated "
    "cross-validation, temporal validation and a Y-randomization test. The degree-2 model explained "
    f"{r2('CE').replace(',', '.')}% (± {r2dp('CE').replace(',', '.')}) of PSN variance in the Cerrado, "
    f"{r2('CA').replace(',', '.')}% (± {r2dp('CA').replace(',', '.')}) in the Caatinga and "
    f"{r2('MA').replace(',', '.')}% (± {r2dp('MA').replace(',', '.')}) in the Atlantic Forest. At a monthly scale "
    f"and with spatial aggregation by biome, test RMSE ranged from {rmse('CA').replace(',', '.')} to "
    f"{rmse('MA').replace(',', '.')} gC·m⁻²·month⁻¹ and MAE from {mae('CA').replace(',', '.')} to "
    f"{mae('MA').replace(',', '.')} gC·m⁻²·month⁻¹; the coefficient instability associated with "
    "multicollinearity (high VIF between evapotranspiration and water availability in the Cerrado) was contained by "
    "Ridge regularization. The results revealed distinct ecological regimes of "
    "climate–PSN association: seasonal water limitation in the Cerrado, pulsed response to rainfall in the "
    "Caatinga and multifactorial control in the Atlantic Forest. The analysis of the El Niño–Southern Oscillation "
    "(ENSO), performed on monthly anomalies, indicated an indirect and lagged influence on PSN: in La Niña months PSN "
    f"was about {v(LN_LO,0)}–{v(LN_HI,0)}% above normal in the Cerrado and Caatinga, associated mainly with positive "
    "evapotranspiration anomalies and persisting for several months in the Cerrado; in the Atlantic Forest, raw medians "
    "were similar across phases, but after removing the seasonal cycle El Niño months showed a mean PSN reduction of "
    f"{v(abs(t6('MA','PSN')['delta_EN'])).replace(',', '.')}% and a higher frequency of extremely low months (from "
    f"{v(P10_MA[1],0)}% to {v(P10_MA[0],0)}%), associated with surface warming. The results indicate the feasibility of regularized polynomial regression to represent "
    "complex environmental relationships and reinforce the importance of differentiated approaches for monitoring "
    "the biomes of Bahia."
)
# Ficha de referência (PT e EN): acrescenta a coorientadora, preservando o título em negrito
regex_replace_para(ORIG[58], r'Orientador: Fabrício Berton Zanchi\. ', 'Orientador: Fabrício Berton Zanchi. Coorientadora: Nayanne Silva Benfica. ')
regex_replace_para(ORIG[68], r'Advisor: Fabrício Berton Zanchi\. ', 'Advisor: Fabrício Berton Zanchi. Co-advisor: Nayanne Silva Benfica. ')
ORIG[121].paragraph_format.page_break_before = True   # APRESENTAÇÃO E JUSTIFICATIVA em página nova após o Sumário
set_text(ORIG[63], resumo)
set_text(ORIG[73], abstract)

# Lista de siglas: itálico nos termos estrangeiros + novas siglas
for i in range(87, 111):
    p = ORIG[i]
    if p.text.strip(): set_text(p, p.text)
set_text(ORIG[88], ORIG[88].text.replace("CHIRPS – Climate Hazards Group InfraRed Precipitation with Station data\n", "")
         + "\nGEE – Google Earth Engine\nIMERG – Integrated Multi-satellitE Retrievals for GPM (Global Precipitation Measurement)")
add_paras_after(ORIG[95], ORIG[95], ["NASA – Administração Nacional de Aeronáutica e Espaço dos Estados Unidos (National Aeronautics and Space Administration)"])
add_paras_after(ORIG[101], ORIG[101], ["NOAA – Administração Nacional Oceânica e Atmosférica dos Estados Unidos (National Oceanic and Atmospheric Administration)"])
add_paras_after(ORIG[88], ORIG[88], ["CPC – Centro de Previsão Climática da NOAA (Climate Prediction Center)"])
add_paras_after(ORIG[87], ORIG[87], ["ACF – Função de Autocorrelação (Autocorrelation Function)"])

# =============================================================================
# 3. APRESENTAÇÃO E FUNDAMENTAÇÃO
# =============================================================================
set_text(ORIG[122], ORIG[122].text
         .replace("respiração de manutenção de folhas e raízes finas.", "respiração de manutenção de folhas e raízes finas (Running et al., 2004; Running; Zhao, 2021).")
         .replace("decorrentes de fatores climáticos e antrópicos.", "decorrentes de fatores climáticos e antrópicos (Nemani et al., 2003; Benfica et al., 2022).")
         .replace("temperatura, precipitação e radiação solar.", "temperatura, precipitação e radiação solar (Nemani et al., 2003).")
         .replace("é imperativa para a ciência ambiental", "é relevante para a ciência ambiental"))
set_text(ORIG[123], ORIG[123].text
         .replace("A região da Bahia apresenta um sistema ambiental de notável complexidade", "O estado da Bahia apresenta um sistema ambiental heterogêneo")
         .replace("até os processos de degradação e desertificação na Caatinga.", "até os processos de degradação e desertificação na Caatinga (Ribeiro et al., 2009; Benfica et al., 2022; MapBiomas, 2025).")
         .replace("representações distorcidas que subestimam", "representações incompletas que subestimam")
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

set_text(ORIG[132], ORIG[132].text
         .replace("configurando respostas em platô ou em “U”.", "configurando respostas saturantes, com limiares ou mudanças de inclinação.")
         .replace("Hao et al. (2019), em revisão sobre modelagem ecológica, mostram que modelos capazes de representar formas de resposta não lineares superam consistentemente abordagens estritamente lineares.",
                  "Modelos capazes de representar formas de resposta não lineares tendem a descrever melhor essas relações do que abordagens estritamente lineares, como ilustram os estudos empíricos a seguir e o estudo de referência desta dissertação (Guimarães et al., 2024)."))
set_text(ORIG[133],
    "Além do controle climático, os ecossistemas estão submetidos a pressões antrópicas que atuam por mecanismos "
    "distintos das forçantes climáticas: enquanto o clima modula a produtividade por vias fisiológicas (disponibilidade "
    "hídrica, temperatura e radiação), as pressões humanas alteram diretamente a estrutura e a cobertura da vegetação, "
    "introduzindo variabilidade que não é capturável apenas por preditores climáticos. Essas pressões, que incluem "
    "desmatamento, expansão agropecuária, silvicultura, fragmentação da paisagem e degradação do solo, têm magnitudes "
    "expressivas nos três biomas. No Cerrado, foram desmatados cerca de 40,5 milhões de hectares de vegetação nativa "
    "entre 1985 e 2024 (redução de aproximadamente 28%), e em 2024 cerca de 47,9% do bioma correspondia a uso "
    "antrópico, com a fronteira agrícola MATOPIBA, que inclui o oeste da Bahia, concentrando a maior parte dessa "
    "conversão (MapBiomas, 2025).")
set_text(ORIG[134],
    "Na Mata Atlântica, a perda recente foi de cerca de 4,4 milhões de hectares entre 1985 e 2024 (MapBiomas, 2025), "
    "mas o quadro mais crítico é estrutural: restam apenas cerca de 12% a 16% da cobertura florestal original, com mais "
    "de 80% dos fragmentos menores que 50 ha e elevada distância média entre eles, o que intensifica os efeitos de "
    "borda e compromete a conectividade (Ribeiro et al., 2009); na Bahia, a expansão da silvicultura de eucalipto e o "
    "mosaico histórico com a cacauicultura-cabruca reconfiguram ainda mais a paisagem. Na Caatinga, a perda foi de cerca "
    "de 9,2 milhões de hectares no mesmo período, com 37% do bioma sob uso agropecuário em 2024 (MapBiomas, 2025), e "
    "parte do semiárido encontra-se em processo de degradação e desertificação, agravado pelas secas prolongadas "
    "(Marengo et al., 2018). Esse contraste entre biomas foi documentado regionalmente por Benfica et al. (2022), que "
    "mostraram, na Bahia, que a produtividade responde não apenas a variações de precipitação e temperatura, mas também "
    "a mudanças no uso e cobertura da terra e à ocorrência de queimadas.")
remove_para(ORIG[135])
set_text(ORIG[136], ORIG[136].text.replace(
    "(Dionizio et al., 2020).",
    "(Dionizio et al., 2020). A redução ocorre porque as gramíneas das pastagens têm sistema radicular raso e perdem "
    "grande parte da área foliar na estação seca, enquanto a vegetação nativa, com raízes profundas, continua "
    "acessando a água do subsolo e transpirando ao longo do ano; assim, embora o pasto possa ter índice de área "
    "foliar comparável no auge da estação chuvosa, sua evapotranspiração anual é menor, sobretudo nos meses secos "
    "(Oliveira et al., 2005; D'Acunha et al., 2024)."))

set_text(ORIG[138], ORIG[138].text.replace(
    "(ONI para temperatura/precipitação e destas para a PSN)",
    "(do Índice Oceânico Niño, ONI, para a temperatura e a precipitação regionais, e destas para a PSN). O ONI é a "
    "medida oficial da NOAA para o ENSO e corresponde à anomalia média de três meses da temperatura da superfície do "
    "mar no Pacífico equatorial central (região Niño 3.4)"))

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
                                            "a produtividade fotossintética, representada neste estudo pela Fotossíntese Líquida (PSN), dos biomas na Bahia."))
set_text(ORIG[149], "H1: A inclusão de termos polinomiais de ordem superior a 1 aumentará o desempenho preditivo em "
    "relação ao modelo linear de grau 1, sem aumento substancial do sobreajuste, avaliado pela diferença entre os "
    "desempenhos de treino e de teste e pela estabilidade sob validação cronológica; o grau adotado será determinado "
    "empiricamente pela comparação dos graus 1 a 5.")
set_text(ORIG[151], "H3: O Índice Oceânico Niño (ONI) não atuará como preditor direto da PSN, mas exercerá influência "
    "indireta por meio da modulação de variáveis climáticas e hídricas intermediárias (temperatura, precipitação, "
    "evapotranspiração e disponibilidade hídrica), configurando um mecanismo de influência indireta transmitido pelo "
    "clima regional.")
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
    "intermediárias (EV, PRE, TST e WAI) nos três biomas.")

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
    "eixos prioritários da conservação da biodiversidade no país (Brasil, 2006), e concentra iniciativas de restauração "
    "florestal, ainda em fase inicial na maior parte dos casos, alinhadas ao Plano Nacional de Recuperação da Vegetação "
    "Nativa (PLANAVEG; Brasil, 2017) e ao Zoneamento Ecológico-Econômico da Bahia (Bahia, 2020).",
    "O uso do solo difere entre os biomas: na Mata Atlântica predominam os mosaicos de fragmentos florestais "
    "intercalados por pastagens, cacauicultura, silvicultura de eucalipto e áreas urbanas; no oeste do estado, a "
    "fronteira agrícola do MATOPIBA converteu extensas áreas de Cerrado em lavouras de grãos e pastagens; e na "
    "Caatinga a pecuária extensiva, a agricultura de sequeiro e a extração de lenha respondem pela maior parte da "
    "conversão e da degradação da vegetação nativa (MapBiomas, 2025). O estado abriga ainda povos indígenas de "
    "diversas etnias (entre elas Pataxó, Pataxó Hã-Hã-Hãe, Tupinambá, Kiriri, Tuxá, Pankararé, Truká e Kaimbé; IBGE, 2025a), "
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
    "partir de produtos de sensoriamento remoto e de uma base de precipitação por satélite, todos de acesso público e "
    "gratuito, obtidos e processados na plataforma Google Earth Engine (GEE; Gorelick et al., 2017) por meio de sua "
    "interface em Python. A variável resposta, a Fotossíntese Líquida (PSN), provém do produto MOD17A2HGF, e a "
    "evapotranspiração real (EV) e a potencial (ETP) do produto MOD16A2GF, ambos da Coleção 6.1 do sensor MODIS a "
    "bordo do satélite Terra, da NASA, em suas versões com preenchimento de falhas consolidadas ao fim de cada ano "
    "(Running; Zhao, 2021; Running et al., 2021); a temperatura da superfície terrestre (TST) provém da banda diurna "
    "do produto MOD11A2 (Wan; Hook; Hulley, 2021) e a área queimada (BURN) do MCD64A1 (Giglio et al., 2018), ambos da "
    "mesma coleção. A precipitação (PRE) provém do produto GPM IMERG Final Run mensal, versão 07 (Huffman et al., "
    "2023), que combina estimativas de múltiplos satélites calibradas por estações pluviométricas, com resolução "
    "espacial de 0,1°; essa versão reprocessou integralmente a série desde 1998 e substituiu a versão 06 utilizada por "
    "Benfica et al. (2022). O Índice Oceânico Niño (ONI) foi obtido da tabela oficial do Centro de Previsão Climática "
    "(CPC) da NOAA. Os produtos MOD17A2HGF e MOD16A2GF são distribuídos em compostos de oito dias com resolução "
    "espacial de 500 m (1 km no MOD11A2), e a PSN corresponde à diferença entre a Produtividade Primária Bruta (GPP) e "
    "a respiração de manutenção de folhas e raízes finas. Para cada composto calculou-se a média espacial dos pixels "
    "válidos de cada bioma, delimitado pelo mapa de biomas do IBGE na escala 1:250.000 (IBGE, 2019) recortado pelo "
    "limite estadual da Bahia, na projeção nativa de cada produto e com os fatores de escala oficiais. Os compostos "
    "foram então agregados em períodos mensais de quatro compostos consecutivos, em janelas fixas de dia do ano, "
    "reproduzindo a agregação empregada por Benfica et al. (2022): a PSN, a EV e a ETP foram somadas, enquanto a TST foi "
    "agregada pela média em cada período; o WAI foi calculado como a razão EV/ETP e a área queimada como o número de pixels "
    "queimados no mês multiplicado pela área do pixel (25 ha). Cada janela abrange cerca de 32 dias e foi atribuída "
    "ao mês civil que contém a maior parte dos seus dias (janeiro, por exemplo, reúne os compostos iniciados em 27 de "
    "dezembro e em 1, 9 e 17 de janeiro), e é a esse mês de referência que se associam o ONI e as componentes de "
    "sazonalidade; os períodos aqui denominados mensais são, portanto, janelas fixas de compostos, e não meses civis "
    "estritos. Consideraram-se válidos os pixels dentro da faixa de valores válidos de cada produto; não se aplicou "
    "filtro adicional pela banda de controle de qualidade, uma vez que as versões com preenchimento de falhas (GF) já "
    "substituem as observações de baixa qualidade por valores interpolados (Running; Zhao, 2021), o que não elimina a "
    "incerteza inerente a esses produtos. Toda a série de 2001 a 2025 foi processada de forma "
    "homogênea com essas coleções, em vez de se emendar a base original de 2001 a 2020 aos anos recentes; a "
    "reprodução da base de Benfica et al. (2022) por esse procedimento apresentou correlação superior a 0,97 com a "
    "série original para todas as variáveis, com erro mediano inferior a 3,5%. A base mensal consolidada está "
    "reproduzida integralmente no Apêndice A e o código-fonte está disponível em repositório público, permitindo a "
    "reprodução de todos os resultados. As variáveis dependentes e preditoras que compõem o modelo estão detalhadas "
    "na Tabela 1.")
set_text(ORIG[182],
    "A variável resposta é a Fotossíntese Líquida (PSN), e as variáveis preditoras candidatas são a "
    "evapotranspiração (EV), a precipitação acumulada (PRE), a temperatura da superfície terrestre (TST), o índice "
    "de disponibilidade hídrica (WAI), definido como a razão entre a evapotranspiração real e a potencial (ETR/ETP) "
    "e que expressa o grau em que a demanda atmosférica por água é atendida pela água disponível no sistema, e a "
    f"área queimada (BURN), acrescidas das duas componentes harmônicas de sazonalidade derivadas do indexador mensal. "
    f"O conjunto abrange o período de janeiro de 2001 a setembro de 2025, em escala mensal (n = {N_OBS} meses por "
    "bioma); os três últimos meses de 2025 foram excluídos porque a NASA encerrou a versão 07 do IMERG Final Run em "
    "setembro de 2025, e os meses seguintes só serão publicados na versão 08, prevista para o fim de 2026 (NASA, 2026). O "
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
P_ABL = [
    "A remoção das componentes harmônicas (Tabela A3, Apêndice A) reduziu o R² "
    f"de teste em {v(_com['MA'] - _sem['MA'])} pontos percentuais na Mata Atlântica (de {v(_com['MA'])}% para "
    f"{v(_sem['MA'])}%), {v(_com['CE'] - _sem['CE'])} pontos no Cerrado e {v(_com['CA'] - _sem['CA'])} pontos na "
    "Caatinga, uma queda muito mais acentuada do que se esperaria de um termo redundante, que a penalização L2 "
    "tenderia a anular. Essa diferença entre biomas é coerente com o grau em que as próprias variáveis climáticas já "
    f"estão ligadas ao calendário (Tabela A4, Apêndice A): no Cerrado, entre {v(_saz('CE','WAI'),0)}% e "
    f"{v(_saz('CE','EV'),0)}% da variância da evapotranspiração e do WAI é explicada isoladamente pelo ciclo anual, "
    f"contra apenas {v(_saz('MA','EV'),0)}% na Mata Atlântica, onde a variabilidade climática reflete "
    "predominantemente as condições meteorológicas de cada ano específico. A acentuada perda de desempenho ao remover "
    "a sazonalidade explícita nesse bioma sugere que a Fotossíntese Líquida responde a um componente do ciclo anual, "
    "possivelmente fotoperíodo ou fenologia foliar, não inteiramente mediado pelas variáveis climáticas medidas.",
    "A comparação entre os ajustes com e sem as componentes harmônicas também esclarece por que a importância relativa "
    "das variáveis climáticas se reordena quando a sazonalidade é representada explicitamente (Tabela A4, Apêndice A). "
    "Sem os harmônicos, a precipitação e a temperatura recebem parte do crédito que pertence ao próprio calendário, pois "
    "oscilam com a estação juntamente com a PSN; na presença deles, cada preditor passa a ser avaliado pela informação "
    "que acrescenta além do ciclo anual, isto é, pelas anomalias. Nessa condição a importância da precipitação cai para "
    f"cerca de 10% (de {v(a4x('CE','PRE')['imp_sem'],0)}% para {v(a4x('CE','PRE')['imp_com'],0)}% no Cerrado e de "
    f"{v(a4x('CA','PRE')['imp_sem'],0)}% para {v(a4x('CA','PRE')['imp_com'],0)}% na Caatinga) e a da temperatura recua "
    f"na Mata Atlântica (de {v(a4x('MA','TST')['imp_sem'],0)}% para {v(a4x('MA','TST')['imp_com'],0)}%), porque, removida "
    f"a estação, a chuva do próprio mês quase não se correlaciona com a anomalia de PSN (r = {v(a4x('CE','PRE')['r_anom'],2)} "
    f"no Cerrado e {v(a4x('CA','PRE')['r_anom'],2)} na Caatinga): a chuva é um fluxo de entrada ruidoso e defasado, e a "
    "vegetação responde à água que permaneceu disponível no solo nas semanas seguintes, não ao total precipitado no mês. "
    f"A evapotranspiração, ao contrário, mantém ou amplia sua importância (de {v(a4x('CE','EV')['imp_sem'],0)}% para "
    f"{v(a4x('CE','EV')['imp_com'],0)}% no Cerrado) porque mede a água efetivamente utilizada pela vegetação, e sua "
    f"anomalia acompanha de perto a anomalia de PSN (r entre {v(min(a4x(b,'EV')['r_anom'] for b in ('MA','CE','CA')),2)} e "
    f"{v(max(a4x(b,'EV')['r_anom'] for b in ('MA','CE','CA')),2)}): transpiração e assimilação de carbono ocorrem pelos "
    "mesmos estômatos, de modo que um mês em que a vegetação transpira mais que o normal para a época é um mês em que "
    "fotossintetiza mais que o normal. A temperatura permanece relevante na Mata Atlântica e na Caatinga como modulador "
    f"negativo (correlação das anomalias de {vm(a4x('MA','TST')['r_anom'],2)} e {vm(a4x('CA','TST')['r_anom'],2)}), "
    "expressão do estresse térmico e hídrico dos meses mais quentes que o usual. Em síntese, os harmônicos absorvem o "
    "ciclo anual determinístico da produtividade (fotoperíodo, radiação e fenologia foliar) e deixam às variáveis "
    "climáticas o papel de explicar os desvios em relação ao ano típico, que é justamente a informação relevante para a "
    "análise interanual e para o ENSO, tratada adiante."]
add_paras_after(ORIG[185], BODY_TPL, [
    "Para avaliar a contribuição das componentes harmônicas, realizou-se uma análise de ablação na qual o modelo foi "
    "reajustado sem SAZsin e SAZcos, mantendo inalterados o conjunto de variáveis ambientais e os procedimentos de "
    "treinamento e validação; complementarmente, calculou-se a proporção da variância de cada variável climática "
    "explicada isoladamente pelo ciclo anual, a correlação de cada variável com a PSN nos valores brutos e nas "
    "anomalias mensais, e o índice de contribuição relativa das variáveis com e sem os harmônicos. Os resultados são "
    "apresentados na seção 6.2.1 e nas Tabelas A3 e A4 do Apêndice A."])
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
    "realizada sobre observações não modificadas e evitando vazamento de informação entre treino e teste. O percentil "
    "3 foi adotado como compromisso entre proteger a estimação dos coeficientes dos poucos meses de produtividade "
    "anormalmente baixa e preservar a distribuição da resposta; a sensibilidade do desempenho a essa escolha foi "
    "verificada reajustando o modelo com winsorização em 0%, 1%, 3% e 5% (Tabela A6, Apêndice A).")
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
    "aplicação de validação cruzada RepeatedKFold, validação agrupada por ano (GroupKFold) e validação cronológica "
    "(TimeSeriesSplit com janela expansível) e teste de Y-randomization. Em cada partição, o pipeline foi aplicado "
    "nesta ordem: winsorização da resposta do treino, padronização das variáveis (StandardScaler ajustado no treino), "
    "expansão polinomial (PolynomialFeatures, grau 2, sem termo de viés) e regressão Ridge, cujo parâmetro α foi "
    "escolhido por GridSearchCV entre os valores 0,1; 1; 10; 50 e 100, com validação cruzada interna de cinco "
    "partições e o R² como métrica; a busca de α foi repetida para cada conjunto avaliado, formado por três variáveis "
    "ambientais e as duas componentes harmônicas.")
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

set_text(ORIG[211], ORIG[211].text.replace("calculado a partir das variáveis preditoras originais, antes da expansão polinomial.",
    "calculado a partir das cinco variáveis preditoras originais (três ambientais e duas harmônicas), antes da expansão polinomial, e não sobre os 20 termos gerados por ela."))
set_text(ORIG[212], ORIG[212].text
    .replace("Foram considerados como referência os limiares usuais: VIF < 5 (aceitável), 5 ≤ VIF < 10 (atenção) e VIF ≥ 10 (multicolinearidade elevada).",
             "Foram considerados como referência os limiares usuais: VIF < 5 (aceitável), 5 ≤ VIF < 10 (atenção) e VIF ≥ 10 (multicolinearidade elevada), lembrando que tais limiares são regras práticas, e não critérios absolutos (O'Brien, 2007).")
    .replace("Embora a Regressão Ridge ofereça robustez à multicolinearidade por meio da penalização L2,",
             "Embora a regressão Ridge reduza a instabilidade dos coeficientes causada pela multicolinearidade por meio da penalização L2 (o VIF em si não se altera),"))
from docx.shared import RGBColor
def h3(anchor, texto):
    h = new_para_after(anchor, HEAD2_TPL, texto); h.style = d.styles['Heading 3']
    h.alignment = WD_ALIGN_PARAGRAPH.LEFT; h.paragraph_format.first_line_indent = Cm(0); h.paragraph_format.left_indent = Cm(0)
    h.paragraph_format.space_before = Pt(12); h.paragraph_format.space_after = Pt(6); h.paragraph_format.keep_with_next = True
    for r_ in h.runs:
        r_.font.bold = True; r_.font.italic = False; r_.font.size = Pt(12); r_.font.color.rgb = RGBColor(0, 0, 0); r_.font.name = 'Times New Roman'
        rpr = r_._r.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); rpr.insert(0, rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): rf.set(qn(a), 'Times New Roman')
    return h
_h541 = h3(ORIG[212], "5.4.1 Análise da influência do ENSO")
_p541 = add_paras_after(_h541, BODY_TPL, [
    "A fase ENSO de cada mês foi classificada pelo critério oficial da NOAA: ONI igual ou superior a +0,5 °C (El Niño) "
    "ou igual ou inferior a −0,5 °C (La Niña) por pelo menos cinco trimestres móveis consecutivos, avaliados sobre a "
    "série completa do índice desde 1950, de modo que episódios iniciados antes de 2001 fossem reconhecidos. Como os "
    "episódios se concentram entre o fim e o início do ano, a comparação de valores brutos entre fases confundiria o "
    "efeito do ENSO com o da estação; por isso a análise foi conduzida sobre anomalias mensais, definidas como o desvio "
    "de cada valor em relação à média do respectivo mês do calendário em toda a série, expressas nas unidades originais "
    "e, para as médias por fase, em porcentagem dessa média.",
    "Para a PSN e para as variáveis climáticas de cada bioma, três propriedades da distribuição das anomalias foram "
    "comparadas entre fases: a posição central (teste de Kruskal-Wallis entre as três fases e teste de Mann-Whitney de "
    "cada fase ativa contra a neutra), a dispersão (teste de Fligner-Killeen) e a frequência de meses extremos, definida "
    "como a proporção de meses abaixo do décimo percentil ou acima do nonagésimo percentil da série de anomalias (teste "
    "de qui-quadrado). O tamanho de efeito das fases foi expresso pelo ε² de Kruskal-Wallis. Como esse conjunto envolve "
    "muitos testes, os valores-p foram submetidos à correção de Benjamini-Hochberg para taxa de falsas descobertas de "
    "5%, aplicada separadamente a cada família de testes, e os resultados que permanecem significativos após a "
    "correção são identificados na Tabela 6.",
    "Para estimar quanto da resposta da PSN pode ser reproduzido pelas variáveis intermediárias, realizou-se um "
    "experimento de perturbação baseado no modelo, sem pretensão de inferência causal: o MRMP-N ajustado à série "
    "completa foi usado para prever a PSN com os preditores em sua climatologia mensal e, alternativamente, com cada "
    "preditor (ou todos) deslocado pela anomalia média observada em cada fase; a diferença entre as duas predições, em "
    "porcentagem da PSN climatológica, é a parcela da resposta atribuível a cada canal no modelo. A persistência da "
    "resposta foi examinada de forma exploratória pela correlação de Spearman entre o ONI de um mês e a anomalia de "
    "PSN dos 0 a 12 meses seguintes, e por compósitos da anomalia média de PSN nas mesmas defasagens após meses de El "
    "Niño e de La Niña, com intervalos de confiança de 95% por bootstrap (2.000 reamostragens) e teste de Mann-Whitney "
    "contra os meses neutros; por serem fortemente correlacionadas entre si, as defasagens não foram submetidas a "
    "correção para múltiplas comparações e devem ser lidas como descrição do padrão temporal, não como testes "
    "independentes. Por fim, para os episódios com pelo menos cinco meses consecutivos na mesma fase, calculou-se a "
    "anomalia média de PSN durante o episódio e nos três meses seguintes."])
_h542 = h3(_p541, "5.4.2 Variabilidade interanual")
add_paras_after(_h542, BODY_TPL, [
    "Para examinar a produtividade na escala anual, a PSN mensal de cada bioma foi somada por ano nos 24 anos completos "
    "(2001 a 2024); como os meses da base são janelas fixas de compostos, a soma anual aproxima o ano civil com "
    "diferença de um composto nas bordas. O ano de 2025, com dados apenas até setembro, foi excluído da tendência e "
    "apresentado como valor parcial. A variabilidade entre anos foi medida pelo coeficiente de variação (CV) e a "
    "tendência monotônica pelo estimador de inclinação de Sen, com significância pelo teste de Mann-Kendall. A soma "
    "anual foi comparada, por correlação de Pearson, com o NPP anual do produto MOD17A3HGF (Coleção 6.1) para as mesmas "
    "máscaras de bioma, como verificação de consistência entre dois produtos da mesma família MOD17. A fase ENSO "
    "dominante de cada ano foi definida como a fase com pelo menos seis meses no ano, apenas como referência gráfica."])

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
    "estrutura sazonal e autocorrelação; por isso o desempenho foi adicionalmente examinado por um esquema agrupado "
    "por ano e por um esquema cronológico, descritos adiante. Adicionalmente, foi reportado o intervalo "
    "empírico de 95% da distribuição dos escores de R² obtidos nas partições, definido pelos percentis 2,5 e 97,5 "
    "dos valores observados. Ressalta-se que, por decorrerem de partições parcialmente sobrepostas do RepeatedKFold, "
    "esses escores não constituem observações independentes, motivo pelo qual se adota a expressão \"intervalo "
    "empírico\" em vez de \"intervalo de confiança\" no sentido estatístico estrito.")
set_text(ORIG[217], ORIG[217].text
    .replace("Complementarmente à validação cruzada repetida, o desempenho do modelo foi submetido a dois esquemas de validação que respeitam a estrutura cronológica da série, com o objetivo de verificar se as estimativas obtidas pelo RepeatedKFold se mantêm quando a separação entre treino e teste preserva a ordem temporal dos dados.",
             "Complementarmente à validação cruzada repetida, o desempenho do modelo foi examinado por dois esquemas que consideram a estrutura temporal da série: uma validação agrupada por ano (GroupKFold) e uma validação estritamente cronológica (TimeSeriesSplit com janela expansível). O objetivo foi verificar se as estimativas obtidas pelo RepeatedKFold se mantêm quando meses de um mesmo ano não são repartidos entre treino e teste e, no segundo esquema, quando o teste ocorre sempre depois do treino.")
    .replace("O primeiro, denominado GroupKFold por ano, agrupa as observações de um mesmo ano, de modo que anos inteiros sejam mantidos fora do conjunto de treino em cada partição; esse procedimento avalia a capacidade de generalização do modelo para períodos anuais não utilizados no ajuste e elimina a possibilidade de que meses consecutivos e autocorrelacionados sejam distribuídos simultaneamente entre treino e teste.",
             "O primeiro, denominado GroupKFold por ano, agrupa as observações de um mesmo ano em cinco grupos de cinco anos, de modo que anos inteiros sejam mantidos fora do conjunto de treino em cada partição (Figura 4b); esse procedimento não preserva a ordem cronológica, pois anos posteriores podem compor o treino usado para prever anos anteriores, mas avalia a generalização para anos inteiros não utilizados no ajuste e impede que meses consecutivos e autocorrelacionados de um mesmo ano sejam repartidos entre treino e teste.")
    .replace("O segundo, o TimeSeriesSplit com janela expansível, ajusta o modelo em períodos anteriores e avalia seu desempenho em períodos subsequentes,",
             "O segundo, o TimeSeriesSplit com janela expansível, é o único que preserva estritamente a ordem cronológica: ajusta o modelo em períodos anteriores e avalia seu desempenho no bloco de 49 meses seguinte, em cinco blocos sucessivos (Figura 4c),")
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
    "Adotaram-se dois indicadores complementares. O primeiro, seguindo a lógica de Guimarães et al. (2024), é a "
    "distância entre o R² de validação cruzada do modelo original e a média dos R² dos 100 modelos permutados, que "
    "expressa quanto o desempenho excede o que se obteria por associações arbitrárias; essa distância é reportada de "
    "forma descritiva, sem limiar fixo. O segundo é um p-valor empírico unilateral, definido como a proporção de "
    "permutações cujo R² iguala ou supera o do modelo original, adotando-se como significativo p inferior a 0,05.")
set_text(ORIG[223], ORIG[223].text.replace("Shapiro-Wilk e Kruskal-Wallis", "Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney, Fligner-Killeen e qui-quadrado, e para a correlação de Spearman"))
set_text(ORIG[224],
    "A semente aleatória foi fixada em random_state = 42 em todos os procedimentos que envolvem aleatoriedade "
    "(partições, permutações e reamostragens), o que permite reproduzir exatamente os resultados. A robustez do "
    "desempenho não decorre do valor específico da semente, mas do uso de validação repetida (150 partições) e dos "
    "esquemas complementares de validação. Uma única execução do script do modelo (Modelo_PSN.py) reproduz o ajuste e "
    "todas as validações da seção 5.5, inclusive as Tabelas A7 a A10. As análises foram "
    "executadas em Python 3.11, com numpy 2.4, pandas 3.0, scikit-learn 1.9, scipy 1.17 e statsmodels 0.15; o código, "
    "a base de dados e os scripts de extração estão disponíveis em repositório público "
    "(https://github.com/heroslore/Controle-Gas, pastas dissertacao_PSN e npp_modis).")

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
    "A comparação sistemática entre os graus polinomiais 1 a 5 (Figura 7) levou à seleção do grau 2 nos três "
    "biomas, por oferecer o melhor compromisso entre desempenho preditivo (R² de teste), estabilidade (diferença "
    "treino–teste) e parcimônia (número de termos), critério composto adotado neste estudo. O ganho do grau 2 em relação "
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
set_text(ORIG[253], "Figura 8 - Índice de contribuição relativa das variáveis preditoras no modelo MRMP-N nos três biomas "
         "(soma dos valores absolutos dos coeficientes dos termos que envolvem cada variável, normalizada a 100% por bioma).", bold=True)
replace_image(ORIG[254], os.path.join(FIG, 'fig05_importancia.png'))
ce_wai_vs_tst = sv['CE'].iloc[0]['r2_teste'] - sv['CE'][sv['CE'].variaveis == 'EV + PRE + TST']['r2_teste'].iloc[0]
set_text(ORIG[255], ORIG[255].text.replace(
    "(da ordem de 0,3 ponto percentual no R² de teste)", f"(de {v(ce_wai_vs_tst)} ponto percentual no R² de teste)"))
set_text(ORIG[250],
    "A escolha do grau 2 deve ser lida de forma restrita: dentro do conjunto de variáveis e do intervalo de graus "
    "avaliados, os termos de segunda ordem (quadráticos e de interação entre pares de variáveis) foram suficientes para "
    "obter o melhor compromisso entre desempenho de teste e complexidade do modelo, e graus superiores não "
    "acrescentaram estrutura preditiva que compensasse o aumento do número de termos e do sobreajuste.")
set_text(ORIG[257],
    "A presença das componentes harmônicas de sazonalidade em todos os modelos (mantidas fixas por construção) e o "
    "peso que elas recebem nos três biomas reforçam que a PSN na Bahia possui padrão sazonal marcado e regular, "
    "associado ao ciclo anual de precipitação e radiação. A evapotranspiração (EV) aparece como preditor central em "
    "todos os biomas, e as variáveis hídricas (PRE ou WAI) integram o conjunto ótimo de cada um, confirmando que o "
    "balanço hídrico é o principal controle preditivo da PSN na região. Cabe lembrar que a importância mostrada na "
    "Figura 8 é um índice de contribuição relativa baseado nos coeficientes do modelo ajustado sobre variáveis padronizadas (soma dos valores "
    "absolutos dos coeficientes dos termos que envolvem cada variável), e não uma medida causal. Como a padronização é "
    "aplicada antes da expansão polinomial, os termos quadráticos e de interação não têm exatamente a mesma escala dos "
    "termos lineares, e a regularização Ridge reparte o peso entre termos correlacionados; o índice deve, portanto, ser "
    "lido como uma síntese descritiva da estrutura do modelo ajustado, útil para comparar os biomas entre si, e não como "
    "uma quantificação estrita da importância de cada variável. No Cerrado, em que EV e WAI apresentam VIF elevado "
    "(Tabela 5), a contribuição individual desses dois preditores deve ser interpretada com cautela adicional, pois parte "
    "da informação é compartilhada entre eles.")
set_text(ORIG[258],
    "A ausência da área queimada (BURNlog) no conjunto selecionado de qualquer bioma, apesar de sua inclusão como "
    "candidata, indica que, na escala mensal e espacial adotada, essa variável não acrescentou poder preditivo "
    "suficiente em relação aos demais preditores. Esse resultado não implica ausência de efeito ecológico do fogo, "
    "documentado na Bahia por Benfica et al. (2022) e em savanas tropicais por Navarro-Rosales et al. (2025), e pode "
    "refletir, entre outros fatores, a heterogeneidade espacial das queimadas dentro de cada bioma, respostas defasadas "
    "da produtividade e informação compartilhada com os preditores hídricos.")
# 6.2.1 — contribuição das componentes harmônicas (resultados que estavam em Métodos)
P_ABL = [t_.replace("possivelmente fotoperíodo ou fenologia foliar, não inteiramente mediado pelas variáveis climáticas medidas.",
                    "possivelmente fotoperíodo ou fenologia foliar (Borchert; Rivera, 2001; Wu et al., 2016), não inteiramente representado pelas variáveis climáticas medidas.")
          .replace("transpiração e assimilação de carbono ocorrem pelos "
    "mesmos estômatos", "transpiração e assimilação de carbono ocorrem pelos mesmos estômatos")
          for t_ in P_ABL]
P_ABL = [t_.replace("transpiração e assimilação de carbono ocorrem pelos mesmos estômatos, de modo que",
                    "transpiração e assimilação de carbono ocorrem pelos mesmos estômatos (Lawson; Vialet-Chabrand, 2019), de modo que")
          .replace("Em síntese, os harmônicos absorvem o ciclo anual determinístico da produtividade (fotoperíodo, radiação e fenologia foliar)",
                   "Em síntese, os harmônicos absorvem o ciclo anual determinístico da produtividade, associado ao fotoperíodo, à radiação e à fenologia foliar (Alberton et al., 2019; Wu et al., 2016),")
          .replace("A comparação entre os ajustes com e sem as componentes harmônicas também esclarece", "A comparação entre os ajustes com e sem as componentes harmônicas esclarece")
          for t_ in P_ABL]
_h621 = h3(ORIG[258], "6.2.1 Contribuição da representação harmônica da sazonalidade")
add_paras_after(_h621, BODY_TPL, P_ABL)
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
    "é ampla, e nenhuma das 100 permutações igualou o modelo real (p empírico = "
    "0,0099 nos três biomas). Isso indica que o desempenho observado dificilmente decorre de associações arbitrárias "
    "que também seriam obtidas após permutação da variável resposta, e não "
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
_nf_lo = min(min(JA['fase_nov_fev'][f]) for f in ('El Niño', 'La Niña')); _nf_hi = max(max(JA['fase_nov_fev'][f]) for f in ('El Niño', 'La Niña'))
_mj_lo = min(min(JA['fase_mai_jul'][f]) for f in ('El Niño', 'La Niña')); _mj_hi = max(max(JA['fase_mai_jul'][f]) for f in ('El Niño', 'La Niña'))
_pre_ce = JA['bruto']['Cerrado|PRE']
set_text(ORIG[289],
    f"A classificação oficial da NOAA (seção 5.4.1) resultou em {NF['Neutro']} meses neutros, {NF['El Niño']} de El "
    f"Niño e {NF['La Niña']} de La Niña. As fases ativas concentram-se entre novembro e fevereiro (de {v(_nf_lo,0)}% a "
    f"{v(_nf_hi,0)}% dos seus meses em cada um desses meses, contra {v(_mj_lo,0)}% a {v(_mj_hi,0)}% em maio, junho e "
    "julho), e é isso que torna enganosa a comparação de valores brutos: a precipitação média do Cerrado, por exemplo, "
    f"é de {v(_pre_ce['media_LN'],0)} mm nos meses de La Niña e de {v(_pre_ce['media_N'],0)} mm nos neutros, mas a "
    f"diferença cai para {v(t6('CE','PRE')['media_abs_LN'],0)} mm quando se retira o ciclo anual. A Tabela 6 resume, "
    "por bioma e variável, as anomalias médias em cada fase e os testes de posição, dispersão e extremos; as Figuras 11 "
    "a 13 mostram as distribuições brutas, cujos valores exatos estão na Tabela A5 do Apêndice A.")
# ---- Tabela 6
cap6 = new_para_after(ORIG[289], TABCAP_TPL,
    "Tabela 6 - Anomalias médias (%) das variáveis nos meses de El Niño e de La Niña em relação aos meses neutros "
    "e valores-p dos testes de posição central (Kruskal-Wallis), dispersão (Fligner-Killeen) e frequência de meses "
    "extremos (qui-quadrado), com a proporção de meses abaixo do décimo percentil por fase, 2001–2025.", bold=True)
cap6.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap6, len(T6) + 1, 8); t.alignment = 1
set_widths(t, [2.1, 1.4, 2.1, 2.1, 1.5, 1.7, 1.7, 3.4])
for j, hname in enumerate(['Bioma', 'Variável', 'Δ El Niño\n(%)', 'Δ La Niña\n(%)', 'p\nposição', 'p\ndispersão', 'p\nextremos', '% de meses abaixo do P10\n(EN / N / LN)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8); t.rows[0].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
def _mk(pval, bh_):
    return ('*' if pval < 0.05 else '') + ('‡' if bh_ else '')
_prev = None
for i, r in enumerate(T6.itertuples(), start=1):
    vals = [r.bioma if r.bioma != _prev else '', r.variavel,
            sgn(r.delta_EN, 1) + _mk(r.p_mw_EN, r.bh_mw_EN), sgn(r.delta_LN, 1) + _mk(r.p_mw_LN, r.bh_mw_LN),
            pv3(r.p_kw) + ('‡' if r.bh_kw else ''), pv3(r.p_fligner) + ('‡' if r.bh_fligner else ''), pv3(r.p_chi2) + ('‡' if r.bh_chi2 else ''),
            f"{r.pct_abaixo_P10_EN:.0f} / {r.pct_abaixo_P10_N:.0f} / {r.pct_abaixo_P10_LN:.0f}"]
    _prev = r.bioma
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=8)
nota6 = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL,
    "EN = El Niño; N = Neutro; LN = La Niña. Anomalia = desvio em relação à média do mês do calendário em toda a série; "
    "as colunas Δ expressam a anomalia média em porcentagem dessa média (* p < 0,05 no teste de Mann-Whitney contra os "
    "meses neutros), e os testes foram aplicados às anomalias nas unidades originais de cada variável (P10 = décimo "
    "percentil da série de anomalias). ‡ = permanece significativo a 5% após a correção de Benjamini-Hochberg aplicada "
    "a cada família de testes. Sob ausência de efeito, esperam-se 10% dos meses abaixo do P10 em cada fase.")
nota6._p.getparent().remove(nota6._p); t._tbl.addnext(nota6._p)
nota6.paragraph_format.first_line_indent = Cm(0); nota6.paragraph_format.space_before = Pt(2)
for r_ in nota6.runs: r_.font.size = Pt(9)
# ---- Mata Atlântica
_ma = {var: t6('MA', var) for var in ('PSN', 'EV', 'PRE', 'TST', 'WAI')}
_m5 = {f: a5('MA', 'PSN', f) for f in ('El Niño', 'Neutro', 'La Niña')}
set_text(ORIG[290],
    "Na Mata Atlântica, a temperatura da superfície foi a variável mais sensível às fases do ENSO: nos meses de El "
    f"Niño ela ficou, em média, {v(_ma['TST']['delta_EN'])}% (cerca de {v(JA['tst_MA_EN_graus'])} °C) acima do normal "
    f"da época ({pj(_ma['TST']['p_mw_EN'])}), e {v(_ma['TST']['pct_acima_P90_EN'],0)}% desses meses situaram-se no decil "
    f"mais quente da série, contra {v(_ma['TST']['pct_acima_P90_N'],0)}% dos meses neutros (Figura 11). A "
    f"evapotranspiração e a precipitação não diferiram na posição central ({pj(_ma['EV']['p_kw'])} e "
    f"{pj(_ma['PRE']['p_kw'])}), mas apresentaram maior dispersão nas fases ativas (Fligner-Killeen, "
    f"{pj(_ma['EV']['p_fligner'])} e {pj(_ma['PRE']['p_fligner'])}).",
)
add_paras_after(ORIG[290], BODY_TPL, [
    "Na PSN da Mata Atlântica, as medianas brutas foram semelhantes entre as fases "
    f"({v(_m5['El Niño']['mediana'])}, {v(_m5['Neutro']['mediana'])} e {v(_m5['La Niña']['mediana'])} gC·m⁻²·mês⁻¹ em "
    "El Niño, neutro e La Niña; Tabela A5). Após a remoção do ciclo sazonal, porém, os meses de El Niño apresentaram um "
    f"deslocamento negativo modesto, com anomalia média de {sgn(_ma['PSN']['delta_EN'])}% ({pj(_ma['PSN']['p_mw_EN'])}), "
    f"maior dispersão ({pj(_ma['PSN']['p_fligner'])}) e um aumento forte dos extremos baixos: {v(P10_MA[0],0)}% desses "
    f"meses ficaram abaixo do décimo percentil, contra {v(P10_MA[1],0)}% dos meses neutros e {v(P10_MA[2],0)}% dos de La "
    f"Niña ({pj(_ma['PSN']['p_chi2'])}); o mínimo observado sob El Niño ({v(_m5['El Niño']['minimo'])} gC·m⁻²·mês⁻¹) é "
    f"{v(_m5['Neutro']['minimo'] - _m5['El Niño']['minimo'],0)} unidades inferior ao mínimo dos meses neutros "
    f"({v(_m5['Neutro']['minimo'])}). O El Niño age, portanto, mais sobre a cauda inferior da distribuição do que sobre "
    "o seu centro, o que explica por que o teste de posição central aplicado aos valores brutos não detectava efeito. "
    "A La Niña não produziu resposta na Mata Atlântica em nenhuma das três propriedades."])
replace_image(ORIG[291], os.path.join(FIG, 'fig08_enso_MA.png'))
set_caption_after_image(ORIG[291], "Figura 11 - Distribuição das variáveis ambientais por fase ENSO na Mata Atlântica.")
# ---- Cerrado
_ce = {var: t6('CE', var) for var in ('PSN', 'EV', 'PRE', 'TST', 'WAI')}
_c5 = {f: a5('CE', 'PSN', f) for f in ('El Niño', 'Neutro', 'La Niña')}
set_text(ORIG[293],
    f"No Cerrado, retirado o ciclo anual, a precipitação mensal não diferiu entre fases na posição central "
    f"({pj(_ce['PRE']['p_kw'])}), embora sua dispersão tenha aumentado ({pj(_ce['PRE']['p_fligner'])}). O sinal do ENSO "
    "apareceu nas variáveis que integram o balanço hídrico: nos meses de La Niña a evapotranspiração ficou "
    f"{v(_ce['EV']['delta_LN'])}% acima do normal da época e o WAI {v(_ce['WAI']['delta_LN'])}% (ambos "
    f"{pj(max(_ce['EV']['p_mw_LN'], _ce['WAI']['p_mw_LN']))}), enquanto nos meses de El Niño as anomalias de EV "
    f"({v(_ce['EV']['delta_EN'])}%) e de WAI ({v(_ce['WAI']['delta_EN'])}%) não foram significativas (Figura 12). A PSN "
    f"respondeu no mesmo sentido: anomalia média de {sgn(_ce['PSN']['delta_LN'])}% nos meses de La Niña "
    f"({pj(_ce['PSN']['p_mw_LN'])}; mediana de {v(_c5['La Niña']['mediana'])} contra {v(_c5['Neutro']['mediana'])} "
    f"gC·m⁻²·mês⁻¹ nos meses neutros) e de {sgn(_ce['PSN']['delta_EN'])}% nos de El Niño ({pj(_ce['PSN']['p_mw_EN'])}). "
    f"O efeito da La Niña desloca a distribuição inteira: o primeiro quartil sobe de {v(_c5['Neutro']['Q1'])} para "
    f"{v(_c5['La Niña']['Q1'])} gC·m⁻²·mês⁻¹ e a proporção de meses no decil mais baixo cai de "
    f"{v(_ce['PSN']['pct_abaixo_P10_N'],0)}% para {v(_ce['PSN']['pct_abaixo_P10_LN'],0)}%. O resultado é consistente "
    "com as chuvas acima do normal no Brasil Central durante a La Niña (Cai et al., 2020) e sugere que, no Cerrado, o "
    "que transmite o sinal do ENSO à produtividade não é a chuva do próprio mês, e sim a água efetivamente disponível e "
    "utilizada pela vegetação, integrada ao longo de semanas.")
replace_image(ORIG[294], os.path.join(FIG, 'fig09_enso_CE.png'))
set_caption_after_image(ORIG[294], "Figura 12 - Distribuição das variáveis ambientais por fase ENSO no Cerrado.")
# ---- Caatinga
_ca = {var: t6('CA', var) for var in ('PSN', 'EV', 'PRE', 'TST', 'WAI')}
_a5c = {f: a5('CA', 'PSN', f) for f in ('El Niño', 'Neutro', 'La Niña')}
set_text(ORIG[296],
    f"Na Caatinga o padrão foi semelhante: nos meses de La Niña a evapotranspiração ficou {v(_ca['EV']['delta_LN'])}% "
    f"acima do normal ({pj(_ca['EV']['p_mw_LN'])}), a temperatura {v(abs(_ca['TST']['delta_LN']))}% abaixo "
    f"({pj(_ca['TST']['p_mw_LN'])}) e a PSN {v(_ca['PSN']['delta_LN'])}% acima ({pj(_ca['PSN']['p_mw_LN'])}; mediana de "
    f"{v(_a5c['La Niña']['mediana'])} contra {v(_a5c['Neutro']['mediana'])} gC·m⁻²·mês⁻¹), sem diferença de posição "
    f"central na precipitação ({pj(_ca['PRE']['p_kw'])}), cuja dispersão aumentou nas fases ativas "
    f"({pj(_ca['PRE']['p_fligner'])}) (Figura 13). Nos meses de El Niño a PSN ficou {v(abs(_ca['PSN']['delta_EN']))}% "
    f"abaixo do normal, diferença não significativa ({pj(_ca['PSN']['p_mw_EN'])}), ainda que "
    f"{v(_ca['PSN']['pct_abaixo_P10_EN'],0)}% desses meses tenham caído no decil mais baixo, contra "
    f"{v(_ca['PSN']['pct_abaixo_P10_N'],0)}% dos neutros e {v(_ca['PSN']['pct_abaixo_P10_LN'],0)}% dos de La Niña. Esse "
    "comportamento é compatível com a dinâmica de pulsos de recursos dos ecossistemas semiáridos, em que a atividade "
    "biológica responde rapidamente aos eventos de disponibilidade de água (Schwinning; Sala, 2004), com as medições de "
    "fluxo de CO₂ na Caatinga, que acompanham a magnitude e a distribuição da chuva (Mendes et al., 2020, 2025), e com "
    "os achados de Silva et al. (2026), que associam anos de El Niño a reduções da produtividade no bioma.")
replace_image(ORIG[297], os.path.join(FIG, 'fig10_enso_CA.png'))
set_caption_after_image(ORIG[297], "Figura 13 - Distribuição das variáveis ambientais por fase ENSO na Caatinga.")
# ---- experimento de perturbação (sensibilidade) e defasagem
_fr = {b: 100 * med(b, f)['efeito'] / med(b, f)['observado'] for b, f in (('CE', 'La Niña'), ('CA', 'La Niña'), ('MA', 'El Niño'))}
_fr_lo, _fr_hi = sorted([_fr['CE'], _fr['CA']])
P_SENS = ("O experimento de perturbação baseado no modelo (seção 5.4.1) indica quanto dessas respostas pode ser reproduzido "
    "pelas variáveis intermediárias. Nos meses de La Niña, deslocar os preditores pelas suas anomalias médias faz o "
    f"modelo prever PSN {sgn(med('CE','La Niña')['efeito'])}% no Cerrado (observado {sgn(med('CE','La Niña')['observado'])}%) "
    f"e {sgn(med('CA','La Niña')['efeito'])}% na Caatinga (observado {sgn(med('CA','La Niña')['observado'])}%); deslocar "
    f"apenas a evapotranspiração já produz {sgn(med('CE','La Niña','EV')['efeito'])}% no Cerrado e "
    f"{sgn(med('CA','La Niña','EV')['efeito'])}% na Caatinga. Nos meses de El Niño na Mata Atlântica, o modelo prevê "
    f"{sgn(med('MA','El Niño')['efeito'])}% (observado {sgn(med('MA','El Niño')['observado'])}%), e a temperatura sozinha "
    f"responde por {sgn(med('MA','El Niño','TST')['efeito'])}%. Assim, o experimento reproduziu de {v(_fr_lo,0)}% a "
    f"{v(_fr_hi,0)}% da magnitude observada nos biomas sazonais, quase inteiramente pela via da evapotranspiração, e cerca "
    f"de {v(_fr['MA'],0)}% no bioma úmido, sobretudo pela via da temperatura; a parcela restante não é explicada pelos "
    "preditores do mesmo mês e pode envolver radiação e defasagem da resposta. Trata-se de uma decomposição baseada no "
    "modelo, e não de uma análise causal.")
ld = {b: _lagdesc(b) for b in ('MA', 'CE', 'CA')}
def _c(b, f, L, nd=0): return sgn(cmp_(b, f, L)['media'], nd)
def _prim_ns_comp(b, f):
    for L in (0, 1, 2, 3, 4, 6, 9, 12):
        if cmp_(b, f, L)['p'] >= 0.05: return L
    return None
_sigCE = [x['lag'] for x in JA['lag']['Cerrado'] if x['p'] < 0.05]
_ma_en = [abs(cmp_('MA', 'El Niño', L)['media']) for L in (0, 1, 2, 3, 4, 6)]
_ma_ln_sig = _ult_lag_sig('MA', 'La Niña')
P_LAG0 = ("A resposta da PSN não se restringe ao mês em fase ENSO. A correlação de Spearman entre o ONI de um mês e a "
    "anomalia de PSN dos meses seguintes é negativa nos três biomas (El Niño reduz e La Niña eleva a PSN), mas com "
    "persistência diferente em cada um, como mostram os compósitos por fase da Figura 14. Como descrito na seção 5.4.1, "
    "essa análise é exploratória, e as defasagens não são testes independentes.")
P_LAG_CA = (f"Na Caatinga a resposta é imediata e curta: a correlação é máxima no próprio mês (ρ = {vm(ld['CA']['rhomax'],2)}) "
    f"e deixa de ser significativa após {EXTENSO[ld['CA']['prim_ns'] - 1]} meses. Após meses de La Niña, a anomalia média "
    f"de PSN é de cerca de {_c('CA','La Niña',0)}% no mês da fase e nos dois meses seguintes, cai para "
    f"{faixa(_c('CA','La Niña',4), _c('CA','La Niña',3))}% no terceiro e no quarto mês após a fase e deixa de ser "
    f"significativa aos {EXTENSO[_prim_ns_comp('CA','La Niña')]} meses, padrão compatível com a resposta pulsada da "
    "vegetação caducifólia do semiárido (Schwinning; Sala, 2004; Mendes et al., 2020).")
P_LAG_CE = (f"No Cerrado a resposta é mais lenta e persistente: a correlação é fraca no mês corrente (ρ = {vm(ld['CE']['rho0'],2)}, "
    f"{'não significativa' if ld['CE']['p0'] >= 0.05 else 'significativa'}), mas significativa de {EXTENSO[min(_sigCE)]} a "
    f"{EXTENSO[max(_sigCE)]} meses depois, com máximo aos {EXTENSO[ld['CE']['lagmax']]} meses (ρ = {vm(ld['CE']['rhomax'],2)}). "
    f"Após meses de La Niña, o ganho de {faixa(_c('CE','La Niña',2), _c('CE','La Niña',1))}% dos primeiros meses não decai, "
    f"mantendo-se em {_c('CE','La Niña',6)}% aos seis e {_c('CE','La Niña',9)}% aos nove meses (p < 0,05 em todas as "
    f"defasagens até {EXTENSO[_ult_lag_sig('CE','La Niña')]} meses); o El Niño quase não aparece no mês corrente "
    f"({_c('CE','El Niño',0)}%) e só se manifesta tardiamente ({_c('CE','El Niño',3)}% aos três, {_c('CE','El Niño',4)}% "
    f"aos quatro e {_c('CE','El Niño',12)}% aos doze meses), sem atingir significância. Esse padrão é compatível com o "
    "armazenamento de água em solos profundos, explorado por sistemas radiculares extensos, que sustenta a vegetação do "
    "Cerrado na estação seca (Oliveira et al., 2005; Fan et al., 2017): um excedente hídrico na estação chuvosa de La "
    "Niña seria consumido ao longo dos meses seguintes, e um déficit de El Niño seria cobrado na estação seguinte.")
P_LAG_MA = (f"Na Mata Atlântica a resposta é intermediária e assimétrica: a correlação é máxima com {EXTENSO[ld['MA']['lagmax']]} "
    f"meses de atraso (ρ = {vm(ld['MA']['rhomax'],2)}) e persiste por cerca de {EXTENSO[ld['MA']['ult_sig']]} meses. O El "
    f"Niño reduz a PSN em {v(min(_ma_en),0)}% a {v(max(_ma_en),0)}% de forma significativa do mês corrente até o sexto "
    f"mês, com resíduo significativo até {EXTENSO[_ult_lag_sig('MA','El Niño')]} meses, enquanto a La Niña não produz "
    f"ganho significativo em {'nenhuma defasagem' if _ma_ln_sig is None else 'quase nenhuma defasagem'}. A assimetria é "
    "coerente com o canal térmico identificado acima: o bioma úmido não é limitado por água em condições médias, de modo "
    "que água adicional não o beneficia, mas calor adicional o prejudica.")
_last = add_paras_after(ORIG[297], BODY_TPL, [P_SENS, P_LAG0, P_LAG_CA, P_LAG_CE, P_LAG_MA])
_pic14 = add_figure_after(_last, "Figura 14 - Anomalia média da PSN (%) durante e após meses de El Niño e de La Niña, por defasagem de 0 a "
                 "12 meses, com intervalo de confiança de 95% (bootstrap), nos três biomas; símbolos cheios indicam diferença "
                 "significativa em relação aos meses neutros (Mann-Whitney, p < 0,05).", os.path.join(FIG, 'fig14_compositos_enso.png'), width_cm=11.5)
# ---- Tabela 7: episódios mais intensos
_evs = sorted(JA['eventos'], key=lambda e: -e['oni_pico'])
_sel = [e for e in JA['eventos'] if e['inicio'] in ('2014-10', '2010-06', '2021-09', '2023-06', '2015-10')]
_sel = sorted([e for e in JA['eventos'] if e['fase'] == 'El Niño'], key=lambda e: -e['oni_pico'])[:2] + sorted([e for e in JA['eventos'] if e['fase'] == 'La Niña'], key=lambda e: -e['meses'])[:2]
_p7 = new_para_after(_pic14, BODY_TPL,
    "Os episódios mais intensos e mais longos ilustram o padrão (Tabela 7): durante os El Niños de 2014–2016, o mais "
    "forte da série, e de 2023–2024, a PSN ficou abaixo do normal nos três biomas, e no primeiro caso a redução se "
    "aprofundou nos três meses seguintes, sobretudo no Cerrado; durante as La Niñas prolongadas de 2010–2011 e 2021–2023, "
    "a PSN ficou acima do normal no Cerrado e na Caatinga, mas não na Mata Atlântica. Os anos de 2015 e 2016 coincidem com o período de seca extrema documentado no "
    "Nordeste e no Sudeste do Brasil (Marengo et al., 2018; Cunha et al., 2019). Cabe lembrar, porém, que a relação entre a fase "
    "do ENSO e a chuva no Nordeste não é unívoca: a La Niña de 2011–2012, por exemplo, coincidiu com o início de uma seca severa "
    "na região, atribuída à configuração das temperaturas do Pacífico central e do Atlântico tropical (Rodrigues; McPhaden, 2014), "
    "o que reforça a leitura das fases como modulação probabilística, e não determinística, das condições regionais.")
cap7 = new_para_after(_p7, TABCAP_TPL, "Tabela 7 - Anomalia média da PSN (%) durante os dois episódios de El Niño mais intensos e "
                      "as duas La Niñas mais longas da série (2001–2025) e nos três meses seguintes, por bioma.", bold=True)
cap7.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap7, len(_sel) + 1, 8); t.alignment = 1
set_widths(t, [1.6, 2.7, 1.2, 1.4, 2.1, 2.1, 2.1, 2.8])
for j, hname in enumerate(['Fase', 'Período', 'Meses', 'ONI máx.\n(°C)', 'Mata Atlântica\ndurante / após', 'Cerrado\ndurante / após', 'Caatinga\ndurante / após', 'Contexto']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8); t.rows[0].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
_ctx = {'2014-10': 'El Niño forte; seca no Nordeste e no Sudeste (Marengo et al., 2018)',
        '2023-06': 'El Niño de 2023–2024', '2010-06': 'La Niña de 2010–2011', '2021-09': 'La Niña prolongada de 2021–2023'}
for i, e in enumerate(_sel, start=1):
    def _s0(x): return '0' if abs(round(x)) < 0.5 else sgn(x, 0)
    def _da(b): return f"{_s0(e[f'durante_{b}'])}% / {_s0(e[f'depois3m_{b}'])}%"
    vals = [e['fase'], f"{e['inicio'].replace('-', '/')} a {e['fim'].replace('-', '/')}", str(e['meses']), v(e['oni_pico'], 1), _da('MA'), _da('CE'), _da('CA'), _ctx.get(e['inicio'], '')]
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=8)
_fim7 = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); _fim7._p.getparent().remove(_fim7._p); t._tbl.addnext(_fim7._p)
_d_lo = min(abs(t6(b, 'PSN')[k]) for b, k in (('MA', 'delta_EN'), ('CE', 'delta_LN'), ('CA', 'delta_LN')))
_d_hi = max(abs(t6(b, 'PSN')[k]) for b, k in (('MA', 'delta_EN'), ('CE', 'delta_LN'), ('CA', 'delta_LN')))
set_text(ORIG[299],
    "Quando a intensidade do ONI é usada como preditor contínuo, o poder explicativo permanece baixo: a regressão "
    f"linear simples do ONI sobre cada variável climática explicou no máximo {v(ENSO['ols_max'])}% de sua variância "
    "(temperatura da Mata Atlântica), e os tamanhos de efeito das fases sobre as anomalias (ε² de Kruskal-Wallis) "
    f"ficaram entre {v(JA['eps2_range'][0],2)} e {v(JA['eps2_range'][1],2)}. Esses valores indicam que o ENSO responde "
    "por uma fração pequena da variabilidade mensal, dominada pelo ciclo anual e pela variabilidade meteorológica "
    f"local; não indicam, contudo, ausência de efeito, pois os desvios médios associados às fases (de {v(_d_lo,0)}% a "
    f"{v(_d_hi,0)}% da PSN) são sistemáticos, coerentes entre variáveis e biomas e, no caso da Mata Atlântica, "
    "concentrados nos extremos. A influência do ENSO sobre o sistema regional não se manifesta, portanto, de forma "
    "linear e direta, mas por relações indiretas, defasadas e, em parte, assimétricas entre as fases, mais "
    "adequadamente representadas pela classificação em fases e pela análise de anomalias.")
set_text(ORIG[300],
    "A interpretação conjunta desses resultados sustenta um padrão de influência indireta, na qual o ENSO atua como "
    "forçante de larga escala que modula variáveis intermediárias, com canais distintos por bioma: a evapotranspiração "
    "e o WAI, expressões da água efetivamente disponível, no Cerrado e na Caatinga, onde a PSN dos meses de La Niña fica "
    f"cerca de {v(LN_LO,0)}% a {v(LN_HI,0)}% acima do normal; e a temperatura da superfície na Mata Atlântica, onde os "
    "meses de El Niño apresentam redução modesta da PSN típica e aumento acentuado da frequência de meses de "
    "produtividade muito baixa.")
set_text(ORIG[301],
    "O deslocamento apenas modesto da produtividade típica da Mata Atlântica, apesar da resposta significativa da "
    "temperatura, sugere que esse ecossistema apresenta capacidade parcial de amortecimento frente às oscilações "
    "climáticas de larga escala, decorrente de sua maior reserva hídrica e da menor amplitude de seu ciclo anual; esse "
    "amortecimento, contudo, falha nos meses mais quentes, quando a produtividade cai de forma abrupta. No Cerrado e na "
    "Caatinga, onde a produtividade é governada pelo balanço hídrico, o amortecimento é menor e o sinal do ENSO chega à "
    "PSN de forma sistemática, com persistência de vários meses no Cerrado.")

set_text(ORIG[302], ORIG[302].text
    .replace("Sob cenários de intensificação dos eventos ENSO particularmente episódios de El Niño mais frequentes e severos, projetados para o século XXI a magnitude",
             "Sob cenários de intensificação dos eventos ENSO, com episódios de El Niño mais frequentes e severos projetados para o século XXI (Cai et al., 2021), a magnitude")
    .replace("mostrou-se metodologicamente adequada para capturar os efeitos indiretos do ENSO", "mostrou-se adequada, neste conjunto de dados, para representar os efeitos indiretos do ENSO"))

# =============================================================================
# 13b. 6.6 VARIABILIDADE INTERANUAL (nova subseção; "Implicações" passa a 6.7)
# =============================================================================
_h66 = new_para_after(ORIG[302], ORIG[303], "Variabilidade interanual da produtividade")
_cv = {b: ji(b)['cv'] for b in ('MA', 'CE', 'CA')}; _ma = ji('MA'); _ce = ji('CE'); _ca = ji('CA')
_mes25 = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'][_ma['meses_2025'] - 1]
def _tend(b):
    i = ji(b); return f"{sgn(i['sen_pct_periodo'], 1)}%; {pj(i['p_mk'])}"
def _anos(lst): return ', '.join(str(a) for a in lst)
def _p2025(b):
    x = ji(b)['dif_2025_pct']; return f"{v(abs(x), 0)}% {'acima' if x > 0 else 'abaixo'}"
_p66 = add_paras_after(_h66, BODY_TPL, [
    "A extensão da série para 25 anos permite examinar a produtividade também na escala anual, dimensão que a análise "
    "mensal não cobre (métodos na seção 5.4.2). A Figura 15 mostra a soma anual da PSN de cada bioma nos 24 anos "
    f"completos (2001 a 2024), com o valor parcial de 2025 (janeiro a {_mes25}) e a fase ENSO dominante de cada ano, "
    "indicada apenas como referência, já que a mistura de meses de fases distintas dentro do ano torna a comparação "
    "anual menos nítida do que a análise mensal em anomalias da seção 6.5, que permanece a base da conclusão sobre o "
    "ENSO; a Tabela 8 resume as estatísticas.",
    f"A soma anual da PSN correlacionou-se em {v(min(ji(b)['r_npp'] for b in ('MA','CE','CA')), 2)} a "
    f"{v(max(ji(b)['r_npp'] for b in ('MA','CE','CA')), 2)} com o NPP anual do MOD17A3HGF nos três biomas, o que mostra "
    "elevada consistência entre os dois produtos da família MOD17 (o NPP é sistematicamente menor porque desconta ainda "
    f"a respiração de manutenção do lenho e a de crescimento). A produtividade anual média foi de {v(_ma['media'], 0)} g C·m⁻²·ano⁻¹ na "
    f"Mata Atlântica, {v(_ce['media'], 0)} no Cerrado e {v(_ca['media'], 0)} na Caatinga, mas a variabilidade entre anos "
    f"foi cerca de três vezes maior nos biomas sazonais (CV de {v(_cv['CE'])}% no Cerrado e {v(_cv['CA'])}% na Caatinga) "
    f"do que na Mata Atlântica ({v(_cv['MA'])}%), o que quantifica, na escala anual, a tipologia da Tabela 4: onde a "
    "produtividade é governada pelo balanço hídrico, os anos secos e chuvosos deixam marca proporcionalmente maior. "
    f"Os piores anos coincidem com secas conhecidas: {_anos(_ca['piores'])} na Caatinga, período da grande seca do "
    f"Nordeste e do El Niño de 2015–2016; {_anos(_ma['piores'])} na Mata Atlântica, com o mínimo da série em "
    f"{_ma['min_ano']} ({v(_ma['min_val'], 0)} g C·m⁻²·ano⁻¹) durante o El Niño forte; e {_anos(_ce['piores'])} no Cerrado, "
    f"cujo mínimo ({_ce['min_ano']}, {v(_ce['min_val'], 0)} g C·m⁻²·ano⁻¹) reflete a produtividade mais baixa do início da "
    "série.",
    f"A Mata Atlântica foi o único bioma com tendência negativa ao longo do período ({_tend('MA')}), de cerca de "
    f"{v(abs(_ma['sen_pct_periodo']), 0)}% em 24 anos: não significativa ao nível de 5%, embora com sinal sugestivo de "
    "declínio, e com valores particularmente baixos em 2015 e 2016; no Cerrado "
    f"({_tend('CE')}) e na Caatinga ({_tend('CA')}) não houve tendência significativa. Esse "
    "resultado é compatível com a hipótese, discutida na seção 6.3, de que fatores de paisagem, como a fragmentação e a "
    "expansão da silvicultura, reduzam a produtividade do bioma mais alterado do estado, mas não a comprova: sem "
    "variáveis de uso do solo no modelo, a queda não pode ser separada do aquecimento da superfície, que a seção 6.5 "
    "mostra ser o canal pelo qual o El Niño deprime a PSN da Mata Atlântica. Em 2025, o período de janeiro a "
    f"{_mes25} esteve {_p2025('MA')} da média do mesmo período na Mata Atlântica, {_p2025('CE')} no Cerrado e "
    f"{_p2025('CA')} na Caatinga, valores que só poderão ser interpretados quando o ano estiver completo."])
_pic15 = add_figure_after(_p66, "Figura 15 - Soma anual da PSN por bioma (2001–2024), tendência de Sen, ano parcial de 2025 e "
                          "anos com fase ENSO dominante (pelo menos seis meses na fase); os três piores anos de cada bioma "
                          "estão identificados.", os.path.join(FIG, 'fig15_interanual.png'), width_cm=12.5)
cap8 = new_para_after(_pic15, TABCAP_TPL, "Tabela 8 - Variabilidade interanual da PSN por bioma nos anos completos (2001–2024): média e "
                      "coeficiente de variação da soma anual, tendência de Sen (variação percentual acumulada no período e valor-p "
                      "de Mann-Kendall), piores e melhores anos e correlação com o NPP anual do MOD17A3HGF.", bold=True)
cap8.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap8, len(T7) + 1, 7); t.alignment = 1
set_widths(t, [2.6, 2.3, 1.6, 3.0, 2.3, 2.3, 1.9])
for j, hname in enumerate(['Bioma', 'PSN anual média\n(g C·m⁻²·ano⁻¹)', 'CV (%)', 'Tendência de Sen\n2001–2024', 'Piores anos', 'Melhores anos', 'r com NPP anual']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8); t.rows[0].cells[j].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
for i, r in enumerate(T7.itertuples(), start=1):
    vals = [r.bioma, f"{v(r.media, 0)} ± {v(r.dp, 0)}", v(r.cv, 1), f"{sgn(r.sen_pct_periodo, 1)}% ({pj(r.p_mk)})", r.piores, r.melhores, v(r.r_npp, 2)]
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=8)
_fim7 = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); _fim7._p.getparent().remove(_fim7._p); t._tbl.addnext(_fim7._p)
ORIG[303].paragraph_format.page_break_before = False

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
    "modelo, o que se recomenda para trabalhos futuros. A literatura sobre fragmentação e degradação de borda (Lima et "
    "al., 2020; Broggio et al., 2024) sugere que políticas de restauração florestal e de controle do desmatamento podem "
    "contribuir para reduzir a variabilidade da PSN e elevar a produtividade ecossistêmica, implicação que este estudo "
    "apoia, mas não demonstra por si só.")
set_text(ORIG[306], ORIG[306].text
    .replace("um dos eixos prioritários da conservação no país.", "um dos eixos prioritários da conservação no país (Brasil, 2006).")
    .replace("reforçam a urgência de estratégias de conectividade entre fragmentos florestais como condição para a resiliência ecossistêmica",
             "reforçam, em conjunto com a literatura sobre fragmentação (Ribeiro et al., 2009; Lima et al., 2020), a relevância de estratégias de conectividade entre fragmentos florestais para a resiliência ecossistêmica"))
set_text(ORIG[307], ORIG[307].text
    .replace("aponta que a conservação da disponibilidade hídrica por meio da proteção de nascentes, manutenção da cobertura vegetal nativa e controle das queimadas constitui a intervenção de maior impacto para a manutenção da produtividade e dos serviços ecossistêmicos do bioma.",
             "reforça a relevância da disponibilidade hídrica como variável a ser considerada no monitoramento e no planejamento do bioma, o que dá sustentação a medidas como a proteção de nascentes, a manutenção da cobertura vegetal nativa e o controle das queimadas.")
    .replace("a proteção hídrica torna-se uma prioridade estratégica", "a proteção hídrica tende a ganhar prioridade"))
set_text(ORIG[308],
    f"Para a Caatinga, o alto desempenho preditivo do modelo (R² = {r2('CA')}%) indica que a PSN responde de forma "
    "previsível às condições climáticas do mês. O modelo pode, assim, fornecer uma base quantitativa para sistemas de "
    "monitoramento da produtividade por sensoriamento remoto e, quando acoplado a previsões meteorológicas ou "
    "climáticas das variáveis ambientais ou a dados quase em tempo real, para o desenvolvimento futuro de sistemas de "
    "alerta, com aplicação no acompanhamento da segurança alimentar e hídrica das populações rurais, especialmente em "
    "anos de El Niño.")
set_text(ORIG[309], ORIG[309].text
    .replace("alinhada aos objetivos do Zoneamento Ecológico-Econômico da Bahia e às metas de restauração florestal do Plano Nacional de Recuperação da Vegetação Nativa (PLANAVEG).",
             "alinhada aos objetivos do Zoneamento Ecológico-Econômico da Bahia (Bahia, 2020) e às metas de restauração florestal do Plano Nacional de Recuperação da Vegetação Nativa (PLANAVEG; Brasil, 2017).")
    .replace("ao demonstrar que os controles ecológicos", "ao indicar que os controles ecológicos"))
set_text(ORIG[312],
    "Os principais resultados confirmaram a viabilidade do modelo nos três biomas analisados. O MRMP-N de grau 2 "
    f"apresentou elevado desempenho preditivo no Cerrado (R² = {r2('CE')}%) e na Caatinga (R² = {r2('CA')}%), além "
    f"de desempenho moderado na Mata Atlântica (R² = {r2('MA')}%), refletindo regimes ecológicos distintos de "
    "controle da produtividade primária na região. A extensão da série para 2001–2025 (297 meses) elevou o R² da "
    f"Mata Atlântica em relação à série original de 2001–2020 (de 62,3% para {r2('MA')}%) e manteve os do Cerrado e "
    "da Caatinga, indicando estabilidade do modelo frente aos anos recentes, que incluíram o El Niño intenso de "
    "2023–2024. Na escala anual (2001–2024), a produtividade variou cerca de três vezes mais nos biomas sazonais "
    f"(CV de {v(ji('CE')['cv'])}% no Cerrado e {v(ji('CA')['cv'])}% na Caatinga) do que na Mata Atlântica "
    f"({v(ji('MA')['cv'])}%), único bioma com tendência negativa, de aproximadamente "
    f"{v(abs(ji('MA')['sen_pct_periodo']), 0)}% em 24 anos, não significativa ao nível de 5% ({pj(ji('MA')['p_mk'])}), embora "
    "com sinal sugestivo de declínio, e os piores anos coincidiram com as secas de 2012–2013 e com o El Niño de "
    "2015–2016.")
set_text(ORIG[313],
    "Retomando as hipóteses formuladas: a H1 confirmou-se. O grau 2 superou o modelo linear nos "
    f"três biomas ({v(g['MA'][2]-g['MA'][1])}, {v(g['CE'][2]-g['CE'][1])} e {v(g['CA'][2]-g['CA'][1])} pontos "
    "percentuais de R² de teste na Mata Atlântica, no Cerrado e na Caatinga), sem aumento substancial do sobreajuste: a "
    f"diferença treino–teste ficou em no máximo {v(max(gp[b][2] for b in ('MA','CE','CA')))} pp e a queda no "
    f"TimeSeriesSplit em no máximo {v(max(RG.loc[b, 'queda_timeseries_pp'] for b in ('MA','CE','CA')))} pp, enquanto os "
    "graus 4 e 5 degradaram o desempenho de teste. Na Mata Atlântica o grau 3 alcançou R² de teste "
    f"{v(g3['MA']-g['MA'][2])} ponto acima do grau 2, com diferença treino–teste {v(gp['MA'][3]-gp['MA'][2])} pp maior; "
    "optou-se pelo grau 2 como grau comum aos três biomas por parcimônia (20 termos contra 55) e por ser superior ao "
    "grau 3 no Cerrado e na Caatinga. A H2 confirmou-se: o conjunto de variáveis "
    f"climáticas associado às componentes de sazonalidade explicou entre {r2('MA')}% e {r2('CE')}% da variância da "
    "PSN, acima do limiar de 60% estabelecido, e a composição do conjunto selecionado diferiu entre os biomas: "
    f"{conj('CA').replace(' + SAZsin + SAZcos','')} na Caatinga, {conj('CE').replace(' + SAZsin + SAZcos','')} no "
    f"Cerrado e {conj('MA').replace(' + SAZsin + SAZcos','')} na Mata Atlântica, o que aponta a maior relevância do "
    "Índice de Disponibilidade Hídrica (WAI) em sistemas com forte sazonalidade hídrica e, na Mata Atlântica, a "
    "importância das interações entre variáveis.")
set_text(ORIG[314],
    "A H3 confirmou-se em sua essência: o ONI explicou no máximo 3% da variância das variáveis climáticas e não atua "
    "de forma linear e direta sobre a PSN. A análise em anomalias mensais, porém, revelou um efeito sistemático e "
    f"consistente: nos meses de La Niña a PSN ficou cerca de {v(LN_LO,0)}% a {v(LN_HI,0)}% acima do normal no Cerrado e "
    "na Caatinga, em associação com anomalias de evapotranspiração e de WAI, com resposta imediata e curta na Caatinga "
    "e persistente por vários meses no "
    f"Cerrado; na Mata Atlântica, os meses de El Niño apresentaram redução modesta da PSN típica "
    f"({sgn(t6('MA','PSN')['delta_EN'])}%) e aumento da frequência de meses de produtividade extremamente baixa (de "
    f"{v(P10_MA[1],0)}% para {v(P10_MA[0],0)}%), associados ao aquecimento da superfície. O padrão é, portanto, o de uma "
    "influência indireta, defasada e assimétrica entre fases, associada à água efetivamente utilizada pela vegetação "
    "nos biomas sazonais e à temperatura no bioma úmido.")
set_text(ORIG[316], ORIG[316].text.replace(
    "sem efeito linear direto significativo sobre a PSN.",
    "transmitida pela evapotranspiração no Cerrado e na Caatinga e pela temperatura na Mata Atlântica, com respostas da "
    "PSN de sinais opostos entre as fases e defasadas em vários meses."))
set_text(ORIG[317], ORIG[317].text.rstrip() +
    " Cabe ainda registrar que o MRMP-N é um modelo explicativo-preditivo contemporâneo: ele estima a PSN de um mês "
    "a partir das variáveis ambientais desse mesmo mês e, portanto, não gera previsões autônomas do futuro; para "
    "projetar a PSN de meses vindouros, seria necessário alimentá-lo com valores observados ou previstos de EV, "
    "PRE, TST e WAI. A autocorrelação residual detectada nos três biomas indica que parte da memória "
    "temporal do sistema não é capturada por preditores do mesmo mês. Por fim, a seleção do conjunto de variáveis "
    "ambientais foi feita sobre as mesmas partições de validação usadas para reportar o desempenho, e não em um "
    "esquema totalmente aninhado; isso pode introduzir algum otimismo de seleção, atenuado pelas validações agrupada "
    "por ano e cronológica, de modo que o desempenho deve ser lido como consistente nos esquemas avaliados, e não como "
    "definitivamente validado.")
set_text(ORIG[320],
    "Como perspectivas para trabalhos futuros, sugere-se a incorporação explícita da dependência temporal, por "
    "meio de preditores defasados ou termos autorregressivos, para absorver a autocorrelação residual identificada; "
    "a extensão da análise do ENSO a compósitos por estação do ano, a classes de intensidade do ONI e a outros modos "
    "de variabilidade, como o dipolo do Atlântico tropical; a "
    "incorporação de variáveis estruturais da paisagem em estudos voltados à Mata Atlântica; a utilização de escalas "
    "temporais mais finas para investigação de eventos extremos; e a aplicação do modelo MRMP-N em outras regiões "
    "com gradientes ambientais semelhantes, visando avaliar sua capacidade de generalização. Adicionalmente, a "
    "integração entre abordagens estatísticas e modelos ecofisiológicos baseados em processos pode contribuir para "
    "aprofundar a compreensão dos mecanismos ambientais que regulam a Fotossíntese Líquida (PSN) nos ecossistemas "
    "tropicais.")

# =============================================================================
# 15b. ROBUSTEZ DA SELEÇÃO, IMPORTÂNCIA POR PERMUTAÇÃO E NULOS TEMPORAIS (revisão JSAES)
# =============================================================================
def _par(prefix):
    for p in d.paragraphs:
        if p.text.startswith(prefix): return p
    raise KeyError(prefix)
def _r2g(b, g, e): return GT[(GT.bioma == nome[b]) & (GT.grau == g) & (GT.esquema == e)]['r2_teste'].iloc[0]
def _mg(b, e): return RJ[b]['melhor_grau'][e]
def _rk(b, e): return RJ[b]['rank_selecionado'][e]
def _dif(b): return RJ[b]['dif']
def _pi(b, e): return {r[0]: r for r in RJ[b]['perm'][e]}
def _nul(b, i): return RJ[b]['nulos'][i]
# --- 5.5 métodos: três parágrafos após os indicadores do Y-randomization (ORIG[220])
add_paras_after(ORIG[220], BODY_TPL, [
    "Robustez da seleção sob os esquemas temporais de validação. Como o grau polinomial e o conjunto de variáveis foram escolhidos com base "
    "no RepeatedKFold, verificou-se se as mesmas escolhas seriam feitas quando a própria seleção emprega esquemas que "
    "consideram a estrutura temporal da série: os graus 1 a 5 e as 10 combinações de três variáveis ambientais foram "
    "reavaliados, com o mesmo pipeline, sob GroupKFold por ano e sob TimeSeriesSplit, registrando-se o grau de maior R² de "
    "teste e a posição da combinação selecionada em cada esquema (Tabelas A7 e A8). A estabilidade da seleção foi ainda "
    "medida partição a partição no RepeatedKFold: a frequência com que cada combinação foi a melhor entre as 150 partições "
    "e a diferença pareada de R² de teste entre a primeira e a segunda combinações de cada bioma, com intervalo de confiança "
    "de 95% por bootstrap das partições (5.000 reamostragens) e teste de Wilcoxon pareado.",
    "Importância por permutação fora da amostra. Como complemento ao índice baseado nos coeficientes (seção 6.2), cuja "
    "comparabilidade entre termos de ordens diferentes é limitada, calculou-se a importância por permutação (Breiman, 2001) "
    "de forma compatível com a dependência temporal: em cada bloco de teste do GroupKFold por ano e do TimeSeriesSplit, o "
    "modelo ajustado no treino foi avaliado no teste com cada preditor original (as três variáveis ambientais e as duas "
    "componentes harmônicas) embaralhado 20 vezes. A queda média do R² de teste e a razão entre o RMSE com e sem "
    "embaralhamento medem quanto o desempenho fora da amostra depende de cada variável; reportam-se a média e o desvio-padrão "
    "entre blocos e a parcela de cada variável na queda total (Tabela A9). Como o embaralhamento de um preditor rompe também "
    "suas correlações com os demais, variáveis colineares, como EV e WAI no Cerrado, partilham importância, e a medida deve ser "
    "lida como preditiva, não causal.",
    "Nulos que preservam a estrutura temporal. A permutação completa da PSN no Y-randomization destrói toda a dependência "
    "temporal da resposta, o que torna o teste pouco exigente em séries autocorrelacionadas. Por isso, o mesmo procedimento "
    "(R² de validação cruzada RepeatedKFold com α fixo) foi repetido sob dois nulos que mantêm a autocorrelação e o ciclo "
    "sazonal da PSN: (i) o deslocamento circular da série da PSN em relação aos preditores, para todos os 296 deslocamentos "
    "possíveis, entre os quais os 24 múltiplos de 12 meses preservam integralmente o calendário; e (ii) a permutação de anos "
    "inteiros (100 permutações dos 24 anos completos, mantidos no lugar os nove meses de 2025), que também preserva o "
    "calendário. Nesses nulos o modelo continua a dispor da sazonalidade e da memória temporal da série; o que se perde é o "
    "alinhamento entre a PSN e as condições climáticas do mesmo período. O p-valor empírico foi definido como (número de "
    "nulos com R² igual ou superior ao original + 1)/(n + 1) (Tabela A10)."])
# --- 6.2 resultados: grau sob esquemas temporais (após ORIG[250])
def _frase_grau(b):
    g1, g2 = _mg(b, 'GroupKFold'), _mg(b, 'TimeSeriesSplit')
    if g1 == 2 and g2 == 2:
        return f"{nome[b]}: grau 2 nos dois esquemas ({v(_r2g(b, 2, 'GroupKFold'), 1)}% e {v(_r2g(b, 2, 'TimeSeriesSplit'), 1)}%)"
    def _um(g, e, rot):
        return (f"grau 2 no {rot} ({v(_r2g(b, 2, e), 1)}%)" if g == 2 else
                f"grau {g} no {rot} ({v(_r2g(b, g, e), 1)}% contra {v(_r2g(b, 2, e), 1)}% do grau 2)")
    return f"{nome[b]}: {_um(g1, 'GroupKFold', 'GroupKFold')} e {_um(g2, 'TimeSeriesSplit', 'TimeSeriesSplit')}"
def _frase_excecoes_grau():
    exc = [(b, e, _mg(b, e), _r2g(b, _mg(b, e), e) - _r2g(b, 2, e)) for b in ('MA', 'CE', 'CA') for e in ('GroupKFold', 'TimeSeriesSplit') if _mg(b, e) != 2]
    if not exc: return "O grau 2 foi o de maior R² de teste em todos os biomas e esquemas."
    partes = [f"grau {g} {'na' if b != 'CE' else 'no'} {nome[b]} sob {e} (+{v(m, 1)} pp)" for b, e, g, m in exc]
    return ("Nos casos em que outro grau superou o grau 2 (" + "; ".join(partes) + "), a vantagem não ultrapassou "
            f"{v(max(m for *_, m in exc), 1)} ponto percentual, dentro da variação entre partições; o grau 3 traz o quase triplo de "
            "termos e maior diferença treino–teste, e o grau 1 na Caatinga reflete a resposta quase linear desse bioma já observada.")
add_paras_after(ORIG[250], BODY_TPL, [
    "A seleção do grau não dependeu do esquema de validação (Tabela A7). Quando a comparação dos graus 1 a 5 é refeita sob os "
    "esquemas que consideram a estrutura temporal, o maior R² de teste é obtido por: " + "; ".join(_frase_grau(b) for b in ('MA', 'CE', 'CA')) +
    ". " + _frase_excecoes_grau() + " Os graus 4 e 5 degradam o desempenho de teste em todos os esquemas, e o grau 2 permanece "
    "o de melhor compromisso entre desempenho, estabilidade e parcimônia também sob os esquemas agrupado por ano e cronológico."])
# --- 6.2 resultados: WAI x TST reescrito + estabilidade da seleção (ORIG[255])
_dce = _dif('CE')
set_text(ORIG[255],
    "O resultado mais relevante dessa etapa é a ausência da Temperatura de Superfície Terrestre (TST) no conjunto selecionado "
    "do Cerrado: o WAI foi selecionado em lugar da TST na combinação de melhor desempenho. Isso indica que, na presença do WAI, "
    "a TST não agrega poder preditivo independente sobre a PSN do Cerrado, tendo sua informação já representada pelo WAI. "
    f"A vantagem do conjunto com WAI sobre a melhor combinação com TST é pequena ({v(ce_wai_vs_tst)} ponto percentual no R² de "
    "teste), ainda que consistente também na menor diferença treino–teste. Partição a partição (Tabela A8), a combinação "
    f"{_dce['primeira']} foi a melhor em {v(RJ['CE']['freq_melhor'], 0)}% das 150 partições do RepeatedKFold, e sua diferença "
    f"pareada de R² de teste em relação a {_dce['segunda']} foi de {v(_dce['dif_media_pp'], 2)} pp (IC 95% por bootstrap: "
    f"{v(_dce['ic95_inf'], 2)} a {v(_dce['ic95_sup'], 2)} pp; Wilcoxon, {pj(_dce['p_wilcoxon'])}), positiva em "
    f"{v(_dce['prop_particoes_primeira_maior'], 0)}% das partições; sob os esquemas temporais, EV + PRE + WAI ficou em "
    f"{_ord(_rk('CE', 'GroupKFold'))} lugar no GroupKFold por ano e em {_ord(_rk('CE', 'TimeSeriesSplit'))} no TimeSeriesSplit. A preferência "
    "pelo WAI é, portanto, estatisticamente consistente, mas de magnitude pequena, e aponta redundância da TST na presença do "
    "WAI, e não sua irrelevância ecológica. Para a Mata Atlântica e a Caatinga, as combinações selecionadas foram as melhores em "
    f"{v(RJ['MA']['freq_melhor'], 0)}% e {v(RJ['CA']['freq_melhor'], 0)}% das partições e ocuparam, respectivamente, a "
    f"{_ORDF[_rk('MA', 'GroupKFold')]} e a {_ORDF[_rk('CA', 'GroupKFold')]} posições no GroupKFold por ano e a "
    f"{_ORDF[_rk('MA', 'TimeSeriesSplit')]} e a {_ORDF[_rk('CA', 'TimeSeriesSplit')]} no TimeSeriesSplit (Tabela A8); na Caatinga, as três "
    "melhores combinações distam menos de 0,3 ponto percentual entre si, e a escolha entre elas é a menos estável dos três biomas.")
# --- 6.2 resultados: importância por permutação (após ORIG[257])
def _frase_perm(b):
    pg = _pi(b, 'GroupKFold'); ordem = sorted(pg, key=lambda k: -pg[k][5])
    return (f"{'na' if b != 'CE' else 'no'} {nome[b]}, {ordem[0]} concentra {v(pg[ordem[0]][5], 0)}% da queda total do R² (razão de RMSE "
            f"{v(pg[ordem[0]][3], 1)}), seguida de {ordem[1]} ({v(pg[ordem[1]][5], 0)}%) e {ordem[2]} ({v(pg[ordem[2]][5], 0)}%)")
add_paras_after(ORIG[257], BODY_TPL, [
    "A importância por permutação fora da amostra (Tabela A9), que não depende da escala dos coeficientes, coincide com o índice "
    "da Figura 8 no preditor dominante, a evapotranspiração, mas lhe atribui parcela muito maior: " + "; ".join(_frase_perm(b) for b in ('MA', 'CE', 'CA')) +
    ". Os valores absolutos das quedas são grandes porque o embaralhamento de um preditor central leva os termos quadráticos e de "
    "interação a extrapolar, mas as parcelas são semelhantes entre GroupKFold e TimeSeriesSplit. As duas medidas divergem na "
    "posição das variáveis secundárias, o que é esperado: o índice de coeficientes reparte o peso entre termos correlacionados, ao "
    "passo que a permutação atribui a cada variável apenas a informação que ela carrega além das demais; por isso, no Cerrado, o WAI "
    f"recebe {v(_pi('CE', 'GroupKFold')['WAI'][5], 0)}% da queda total sob permutação, apesar dos {v(imp['CE']['WAI'] if isinstance(imp.get('CE'), dict) and 'WAI' in imp['CE'] else 0, 0)}% do índice de "
    "coeficientes, porque grande parte de sua informação é partilhada com a EV (VIF elevado, Tabela 5). Esse contraste reforça a "
    "leitura do índice da Figura 8 como descrição da estrutura do modelo ajustado, e não como medida de importância no sentido estrito."])
# --- 6.3 discussão: dependência algorítmica PSN–EV (após ORIG[280]: "Nesse contexto, o WAI ...")
_p_wai = _par("Nesse contexto, o WAI")
add_paras_after(_p_wai, BODY_TPL, [
    "Uma ressalva sobre a origem dos dados aplica-se à associação entre a PSN e a evapotranspiração. A PSN (MOD17A2HGF) e a "
    "EV (MOD16A2GF) são estimadas por algoritmos da mesma família, que partilham entradas: ambos utilizam a fração da radiação "
    "fotossinteticamente ativa absorvida e o índice de área foliar do produto MOD15A2H, a classificação de cobertura do solo do "
    "MCD12Q1 e os mesmos campos meteorológicos de reanálise (temperatura, déficit de pressão de vapor e radiação do GMAO/MERRA-2) "
    "(Running et al., 2004; Running; Zhao, 2021; Running et al., 2021). Parte da forte associação entre EV e PSN observada nos "
    "três biomas pode, portanto, refletir dependência algorítmica entre os produtos, e não apenas o acoplamento ecofisiológico "
    "entre transpiração e assimilação de carbono pelos estômatos (Lawson; Vialet-Chabrand, 2019). Essa dependência não "
    "invalida o uso do modelo para o fim proposto, que é representar e prever a PSN estimada pelo MOD17 a partir de variáveis "
    "disponíveis na mesma escala; e a associação da PSN com a precipitação (IMERG) e com a temperatura da superfície (MOD11A2), "
    "produtos independentes do MOD17, aponta na mesma direção. Ela recomenda, contudo, cautela ao interpretar a magnitude da "
    "contribuição da EV como evidência ecológica autônoma. A validação das relações com dados independentes, como as medições "
    "de fluxo por covariância de vórtices disponíveis para a Caatinga (Mendes et al., 2020, 2025) e para o Cerrado (Vourlitis et "
    "al., 2022), é indicada como etapa futura."])
# --- 6.4 resultados: nulos temporais (após "O teste de Y-randomization responde ...")
_p_yr = _par("O teste de Y-randomization responde")
def _frase_nulo(b):
    n0, n1, n2 = _nul(b, 0), _nul(b, 1), _nul(b, 2)
    return (f"{'na' if b != 'CE' else 'no'} {nome[b]}, o R² médio dos modelos nulos foi de {_vm(n0['r2_nulo_media'])}% com o deslocamento circular "
            f"(máximo {_vm(n0['r2_nulo_max'])}%) e de {_vm(n1['r2_nulo_media'])}% e {_vm(n2['r2_nulo_media'])}% nos nulos que "
            f"preservam o calendário (deslocamentos múltiplos de 12 meses e permutação de anos), contra {v(n0['r2_original'], 1)}% do modelo original")
add_paras_after(_p_yr, BODY_TPL, [
    "Os nulos que preservam a estrutura temporal da PSN (Tabela A10) são mais exigentes, como esperado, porque mantêm a "
    "autocorrelação e, no caso dos deslocamentos múltiplos de 12 meses e da permutação de anos inteiros, também o ciclo sazonal: "
    + "; ".join(_frase_nulo(b) for b in ('MA', 'CE', 'CA')) + ". Nenhum dos nulos alcançou o modelo original em nenhum bioma "
    f"(p empírico entre {pv3(min(_nul(b, i)['p_empirico'] for b in ('MA', 'CE', 'CA') for i in range(3)))} e "
    f"{pv3(max(_nul(b, i)['p_empirico'] for b in ('MA', 'CE', 'CA') for i in range(3)))}). A diferença entre o R² original e o dos "
    "nulos com calendário preservado quantifica o ganho que decorre do alinhamento entre a PSN e as condições climáticas do "
    "próprio período, além do que a sazonalidade e a memória temporal da série já explicam; esse ganho é maior nos biomas "
    "sazonais e menor na Mata Atlântica, coerente com a menor previsibilidade climática desse bioma."])
# --- Tabela 4: cabeçalho causal
for _t in d.tables:
    for _c in _t.rows[0].cells:
        if _c.text.strip() == 'Controlador dominante': set_cell(_c, 'Preditor dominante', bold=True)
# --- 7: limitações e perspectivas
set_text(ORIG[317], ORIG[317].text.rstrip() +
    " Três limitações de origem dos dados devem ainda ser explicitadas: (i) a PSN e a EV provêm de algoritmos MODIS que "
    "compartilham entradas (seção 6.3), de modo que parte da associação entre elas pode ser algorítmica; (ii) a temperatura da "
    "superfície (MOD11A2) não passou por filtro pela banda de qualidade QC_Day, e a sensibilidade da série de TST a esse filtro "
    "não foi avaliada; e (iii) os períodos aqui chamados mensais são janelas fixas de 32 dias, associadas a um mês civil de "
    "referência, e não meses civis estritos.")
set_text(ORIG[320], ORIG[320].text.replace(
    "a extensão da análise do ENSO a compósitos",
    "a validação das relações entre PSN e variáveis climáticas com medições independentes de fluxo por covariância de "
    "vórtices e a reextração da TST com filtro pela banda QC_Day; a extensão da análise do ENSO a compósitos"))

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
    "a proporção da variância de cada variável climática explicada pelo ciclo anual; as Tabelas A7 a A10 reúnem a robustez "
    "da seleção sob validação temporal, a importância por permutação e os nulos que preservam a estrutura temporal (seção 5.5).")
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
# Tabela A4 — ciclo anual, correlações e importância com/sem harmônicos
cap = new_para_after(mid, TABCAP_TPL, "Tabela A4 - Ligação de cada variável climática com o calendário e com a PSN: proporção da "
                     "variância explicada isoladamente pelo ciclo anual (regressão contra SAZsin e SAZcos), correlação de Pearson "
                     "com a PSN nos valores brutos e nas anomalias mensais, e importância relativa no MRMP-N ajustado à série "
                     "completa sem e com as componentes harmônicas.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(A4X) + 1, 7); t.alignment = 1
set_widths(t, [3.2, 2.0, 3.2, 2.2, 2.6, 5.0, 5.0])
for j, hname in enumerate(['Bioma', 'Variável', 'R² ciclo anual (%)', 'r bruto', 'r anomalias', 'Importância sem harmônicos (%)', 'Importância com harmônicos (%)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8)
_dash = lambda x, nd=1: '—' if pd.isna(x) else v(x, nd)
_prev = None
for i, r in enumerate(A4X.itertuples(), start=1):
    for j, sval in enumerate([r.bioma if r.bioma != _prev else '', r.variavel, _dash(r.r2_ciclo), _dash(r.r_bruto, 2), _dash(r.r_anom, 2), _dash(r.imp_sem), _dash(r.imp_com)]):
        set_cell(t.rows[i].cells[j], sval, size=9)
    _prev = r.bioma
mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A5 — valores dos boxplots por fase ENSO
cap = new_para_after(mid, TABCAP_TPL, "Tabela A5 - Valores dos diagramas de caixa das Figuras 11 a 13: estatísticas descritivas das "
                     "variáveis por fase ENSO (critério oficial da NOAA), valores brutos mensais, 2001–2025. PSN em gC·m⁻²·mês⁻¹, "
                     "EV e PRE em mm·mês⁻¹, TST em °C, WAI adimensional; outliers = valores além de 1,5 vez o intervalo interquartil.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(A5) + 1, 11); t.alignment = 1
set_widths(t, [3.0, 1.8, 1.8, 1.2, 1.9, 1.9, 2.1, 1.9, 1.9, 1.9, 1.8])
for j, hname in enumerate(['Bioma', 'Variável', 'Fase', 'n', 'Mín.', 'Q1', 'Mediana', 'Média', 'Q3', 'Máx.', 'Outliers']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8)
_pb = _pv = None
for i, r in enumerate(A5.itertuples(), start=1):
    nd = 3 if r.variavel == 'WAI' else 1
    vals = [r.bioma if r.bioma != _pb else '', r.variavel if (r.variavel != _pv or r.bioma != _pb) else '', r.fase, str(int(r.n)),
            v(r.minimo, nd), v(r.Q1, nd), v(r.mediana, nd), v(r.media, nd), v(r.Q3, nd), v(r.maximo, nd), str(int(r.outliers))]
    _pb, _pv = r.bioma, r.variavel
    for j, sval in enumerate(vals): set_cell(t.rows[i].cells[j], sval, size=8)
mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A6 — sensibilidade ao percentil de winsorização
SW = pd.read_csv(os.path.join(RES, 'sensibilidade_winsor.csv'))
cap = new_para_after(mid, TABCAP_TPL, "Tabela A6 - Sensibilidade do desempenho do MRMP-N (grau 2, RepeatedKFold 5 × 30) ao percentil de "
                     "winsorização inferior da PSN no conjunto de treino (0% = sem winsorização; 3% = valor adotado).", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(SW) + 1, 6); t.alignment = 1
set_widths(t, [3.4, 2.6, 3.0, 3.0, 4.2, 2.6])
for j, hname in enumerate(['Bioma', 'Percentil (%)', 'R² treino (%)', 'R² teste (%)', 'Dif. treino–teste (pp)', 'RMSE']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
_prev = None
for i, r in enumerate(SW.itertuples(), start=1):
    for j, sval in enumerate([r.bioma if r.bioma != _prev else '', str(int(r.percentil)), v(r.r2_treino, 1), v(r.r2_teste, 1), v(r.gap_pp, 1), v(r.rmse, 2)]):
        set_cell(t.rows[i].cells[j], sval, size=9)
    _prev = r.bioma
mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
def _left(t):
    for row in t.rows:
        for c in row.cells:
            for par in c.paragraphs: par.alignment = WD_ALIGN_PARAGRAPH.LEFT
# Tabela A7 — grau x esquema de validação
cap = new_para_after(mid, TABCAP_TPL, "Tabela A7 - R² de teste (%) do MRMP-N por grau polinomial (1 a 5) sob os três esquemas de validação: "
                     "RepeatedKFold 5 × 30 (critério usado na seleção), GroupKFold por ano e TimeSeriesSplit com janela expansível. "
                     "Conjunto de variáveis selecionado de cada bioma.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, 16, 5); t.alignment = 1
set_widths(t, [3.4, 2.0, 4.0, 4.0, 4.0]); _left_pending = t
for j, hname in enumerate(['Bioma', 'Grau', 'RepeatedKFold\n(%)', 'GroupKFold por ano\n(%)', 'TimeSeriesSplit\n(%)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
_i = 1
for b in ('MA', 'CE', 'CA'):
    for g_ in range(1, 6):
        _gk = GT[(GT.bioma == nome[b]) & (GT.grau == g_) & (GT.esquema == 'GroupKFold')]['r2_teste'].iloc[0]
        _ts = GT[(GT.bioma == nome[b]) & (GT.grau == g_) & (GT.esquema == 'TimeSeriesSplit')]['r2_teste'].iloc[0]
        for j, sval in enumerate([nome[b] if g_ == 1 else '', str(g_), v(sg(b, g_, 'r2_teste'), 1), v(_gk, 1), v(_ts, 1)]):
            set_cell(t.rows[_i].cells[j], sval, size=9)
        _i += 1
_left(t); mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A8 — combinações sob esquemas temporais + estabilidade
cap = new_para_after(mid, TABCAP_TPL, "Tabela A8 - As 10 combinações de três variáveis ambientais (mais SAZsin e SAZcos) por bioma, grau 2: R² de teste "
                     "sob RepeatedKFold 5 × 30, frequência com que cada combinação foi a melhor entre as 150 partições, e R² de teste "
                     "(posição entre parênteses) sob GroupKFold por ano e TimeSeriesSplit. Em negrito, a combinação selecionada.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, 31, 6); t.alignment = 1
set_widths(t, [3.0, 4.4, 3.0, 3.2, 3.6, 3.6]); _left_pending = t
for j, hname in enumerate(['Bioma', 'Variáveis', 'RepeatedKFold\n(%)', 'Melhor em\n(% das partições)', 'GroupKFold\n(%) (posição)', 'TimeSeriesSplit\n(%) (posição)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=9)
_i = 1
for b in ('MA', 'CE', 'CA'):
    _e = ES[ES.bioma == nome[b]]
    for k_, r in enumerate(_e.itertuples()):
        _g = CT[(CT.bioma == nome[b]) & (CT.esquema == 'GroupKFold') & (CT.variaveis == r.variaveis)].iloc[0]
        _t = CT[(CT.bioma == nome[b]) & (CT.esquema == 'TimeSeriesSplit') & (CT.variaveis == r.variaveis)].iloc[0]
        _sel = (r.variaveis == RJ[b]['selecionado'])
        for j, sval in enumerate([nome[b] if k_ == 0 else '', r.variaveis, v(r.r2_teste, 1), v(r.freq_melhor_pct, 1),
                                  f"{v(_g.r2_teste, 1)} ({_ord(int(_g['rank']))})", f"{v(_t.r2_teste, 1)} ({_ord(int(_t['rank']))})"]):
            set_cell(t.rows[_i].cells[j], sval, size=9, bold=(True if _sel and j == 1 else None))
        _i += 1
_left(t); mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A9 — importância por permutação
cap = new_para_after(mid, TABCAP_TPL, "Tabela A9 - Importância por permutação fora da amostra, por bloco temporal: queda do R² de teste (pontos "
                     "percentuais, média ± desvio-padrão entre os cinco blocos; 20 embaralhamentos por bloco), razão entre o RMSE com e sem "
                     "embaralhamento e parcela de cada variável na queda total (%), sob GroupKFold por ano e TimeSeriesSplit.", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, 16, 8); t.alignment = 1
set_widths(t, [2.8, 2.0, 3.4, 2.4, 2.4, 3.4, 2.4, 2.4]); _left_pending = t
for j, hname in enumerate(['Bioma', 'Variável', 'GroupKFold\nqueda R² (pp)', 'GroupKFold\nrazão RMSE', 'GroupKFold\nparcela (%)',
                           'TimeSeriesSplit\nqueda R² (pp)', 'TimeSeriesSplit\nrazão RMSE', 'TimeSeriesSplit\nparcela (%)']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8)
_i = 1
for b in ('MA', 'CE', 'CA'):
    _pg = PI[(PI.bioma == nome[b]) & (PI.esquema == 'GroupKFold')].set_index('variavel'); _pt = PI[(PI.bioma == nome[b]) & (PI.esquema == 'TimeSeriesSplit')].set_index('variavel')
    for k_, var_ in enumerate(_pg.sort_values('parcela_media_pct', ascending=False).index):
        rg, rt = _pg.loc[var_], _pt.loc[var_]
        for j, sval in enumerate([nome[b] if k_ == 0 else '', var_, f"{v(rg.queda_media_pp, 1)} ± {v(rg.queda_dp_pp, 1)}", v(rg.razao_rmse_media, 2),
                                  f"{v(rg.parcela_media_pct, 1)} ± {v(rg.parcela_dp_pct, 1)}", f"{v(rt.queda_media_pp, 1)} ± {v(rt.queda_dp_pp, 1)}",
                                  v(rt.razao_rmse_media, 2), f"{v(rt.parcela_media_pct, 1)} ± {v(rt.parcela_dp_pct, 1)}"]):
            set_cell(t.rows[_i].cells[j], sval, size=8)
        _i += 1
_left(t); mid = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); mid._p.getparent().remove(mid._p); t._tbl.addnext(mid._p)
# Tabela A10 — nulos temporais
cap = new_para_after(mid, TABCAP_TPL, "Tabela A10 - Nulos que preservam a estrutura temporal da PSN: R² de validação cruzada (RepeatedKFold 5 × 30, "
                     "α fixo) do modelo original e dos modelos nulos obtidos por deslocamento circular da PSN (todos os 296 deslocamentos; "
                     "subconjunto dos múltiplos de 12 meses, que preservam o calendário) e por permutação de anos inteiros (100 permutações). "
                     "p empírico = (nº de nulos com R² ≥ original + 1)/(n + 1).", bold=True)
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
t = table_after(cap, len(NT) + 1, 7); t.alignment = 1
set_widths(t, [2.8, 7.0, 1.4, 2.4, 3.0, 2.4, 2.0]); _left_pending = t
for j, hname in enumerate(['Bioma', 'Nulo', 'n', 'R² original (%)', 'R² nulo média ± dp (%)', 'R² nulo máx. (%)', 'p empírico']):
    set_cell(t.rows[0].cells[j], hname, bold=True, size=8)
_prev = None
for i, r in enumerate(NT.itertuples(), start=1):
    for j, sval in enumerate([r.bioma if r.bioma != _prev else '', r.teste, str(int(r.n)), v(r.r2_original, 1), f"{v(r.r2_nulo_media, 1)} ± {v(r.r2_nulo_dp, 1)}",
                              v(r.r2_nulo_max, 1), pv3(r.p_empirico)]):
        set_cell(t.rows[i].cells[j], sval, size=8)
    _prev = r.bioma
_left(t); fim = new_para_after(t.rows[-1].cells[0].paragraphs[0], BODY_TPL, ""); fim._p.getparent().remove(fim._p); t._tbl.addnext(fim._p)
sect_break(fim, landscape=True)

# =============================================================================
# 16b. REFERÊNCIAS novas (fontes de dados citadas em 5.2)
REF_TPL = ORIG[338]
def add_ref_after(anchor, texto):
    return new_para_after(anchor, REF_TPL, texto)
add_ref_after(ORIG[337], "ALBERTON, B.; ALMEIDA, J.; HENRIQUES, R.; TORRES, R. S.; MENGHINI, R.; MORELLATO, L. P. C. Leafing patterns and "
              "drivers across seasonally dry tropical communities. Remote Sensing, v. 11, n. 19, 2267, 2019. DOI: 10.3390/rs11192267.")
_bo = add_ref_after(ORIG[341], "BORCHERT, R.; RIVERA, G. Photoperiodic control of seasonal development and dormancy in tropical stem-succulent "
              "trees. Tree Physiology, v. 21, n. 4, p. 213-221, 2001. DOI: 10.1093/treephys/21.4.213.")
_br = add_ref_after(_bo, "BRASIL. Ministério do Meio Ambiente. O Corredor Central da Mata Atlântica: uma nova escala de conservação da "
              "biodiversidade. Brasília: MMA; Conservação Internacional; Fundação SOS Mata Atlântica, 2006. 46 p.")
_br = add_ref_after(_br, "BRASIL. Ministério do Meio Ambiente. Plano Nacional de Recuperação da Vegetação Nativa (Planaveg). Brasília: "
              "MMA, 2017. Instituído pela Portaria Interministerial nº 230, de 14 de novembro de 2017. Disponível em: "
              "https://www.gov.br/mma/pt-br/composicao/sbio/dflo/plano-nacional-de-recuperacao-da-vegetacao-nativa-planaveg. "
              "Acesso em: 21 set. 2026.")
add_ref_after(_br, "BREIMAN, L. Random forests. Machine Learning, v. 45, n. 1, p. 5-32, 2001. DOI: 10.1023/A:1010933404324.")
_ba = add_ref_after(ORIG[339], "BAHIA. Secretaria do Meio Ambiente. A zona costeira no Estado da Bahia. Salvador: SEMA, 2024. Disponível em: "
              "https://www.ba.gov.br/meioambiente/16479/1-zona-costeira-no-estado-da-bahia. Acesso em: 21 set. 2026.")
add_ref_after(_ba, "BAHIA. Secretaria do Meio Ambiente; Secretaria do Planejamento. Zoneamento Ecológico-Econômico do Estado da Bahia: "
              "Relatório da Comissão Técnica do ZEE-BA. Salvador: SEMA; SEPLAN, 2020. Disponível em: "
              "http://www.zee.ba.gov.br/wp-content/uploads/2020/07/Relatorio.pdf. Acesso em: 21 set. 2026.")
_ca = add_ref_after(ORIG[343], "CAI, W.; MCPHADEN, M. J.; GRIMM, A. M.; RODRIGUES, R. R.; TASCHETTO, A. S.; GARREAUD, R. D. et al. Climate "
              "impacts of the El Niño–Southern Oscillation on South America. Nature Reviews Earth & Environment, v. 1, p. 215-231, "
              "2020. DOI: 10.1038/s43017-020-0040-3.")
_ca = add_ref_after(_ca, "CAI, W.; SANTOSO, A.; COLLINS, M.; DEWITTE, B.; KARAMPERIDOU, C.; KUG, J.-S. et al. Changing El Niño–Southern "
              "Oscillation in a warming climate. Nature Reviews Earth & Environment, v. 2, p. 628-644, 2021. DOI: 10.1038/s43017-021-00199-z.")
_ca = add_ref_after(_ca, "CUNHA, A. P. M. A.; ZERI, M.; DEUSDARÁ LEAL, K.; COSTA, L.; CUARTAS, L. A.; MARENGO, J. A. et al. Extreme drought "
              "events over Brazil from 2011 to 2019. Atmosphere, v. 10, n. 11, 642, 2019. DOI: 10.3390/atmos10110642.")
add_ref_after(_ca, "D'ACUNHA, B.; DALMAGRO, H. J.; ARRUDA, P. H. Z. de; BIUDES, M. S.; LATHUILLIÈRE, M. J.; URIBE, M.; COUTO, E. G.; "
              "BRANDO, P. M.; VOURLITIS, G.; JOHNSON, M. S. Changes in evapotranspiration, transpiration and evaporation across natural "
              "and managed landscapes in the Amazon, Cerrado and Pantanal biomes. Agricultural and Forest Meteorology, v. 346, 109875, "
              "2024. DOI: 10.1016/j.agrformet.2023.109875.")
add_ref_after(ORIG[344], "FAN, Y.; MIGUEZ-MACHO, G.; JOBBÁGY, E. G.; JACKSON, R. B.; OTERO-CASAL, C. Hydrologic regulation of plant rooting "
              "depth. Proceedings of the National Academy of Sciences, v. 114, n. 40, p. 10572-10577, 2017. DOI: 10.1073/pnas.1712381114.")
add_ref_after(ORIG[351], "LAWSON, T.; VIALET-CHABRAND, S. Speedy stomata, photosynthesis and plant water use efficiency. New Phytologist, "
              "v. 221, n. 1, p. 93-98, 2019. DOI: 10.1111/nph.15330.")
_ma = add_ref_after(ORIG[355], "MARENGO, J. A.; ALVES, L. M.; ALVALA, R. C. S.; CUNHA, A. P.; BRITO, S.; MORAES, O. L. L. Climatic characteristics "
              "of the 2010-2016 drought in the semiarid Northeast Brazil region. Anais da Academia Brasileira de Ciências, v. 90, n. 2, "
              "p. 1973-1985, 2018. DOI: 10.1590/0001-3765201720170206.")
_ma = add_ref_after(_ma, "MENDES, K. R.; CAMPOS, S.; SILVA, L. L.; MUTTI, P. R.; FERREIRA, R. R.; MEDEIROS, S. S. et al. Seasonal variation in "
              "net ecosystem CO2 exchange of a Brazilian seasonally dry tropical forest. Scientific Reports, v. 10, 9454, 2020. "
              "DOI: 10.1038/s41598-020-66415-w.")
add_ref_after(_ma, "MENDES, K. R.; MENEZES, R. S. C.; OLIVEIRA, P. E. S.; LIMA, J. R. S.; MOURA, M. S. B.; SOUZA, E. S. et al. The caatinga "
              "dry tropical forest: a highly efficient carbon sink in South America. Agricultural and Forest Meteorology, v. 369, 110573, "
              "2025. DOI: 10.1016/j.agrformet.2025.110573.")
_ob = add_ref_after(ORIG[359], "O'BRIEN, R. M. A caution regarding rules of thumb for variance inflation factors. Quality & Quantity, v. 41, "
              "p. 673-690, 2007. DOI: 10.1007/s11135-006-9018-6.")
_ol = add_ref_after(_ob, "OLDEN, J. D.; LAWLER, J. J.; POFF, N. L. Machine learning methods without tears: a primer for ecologists. "
              "The Quarterly Review of Biology, v. 83, n. 2, p. 171-193, 2008. DOI: 10.1086/587826.")
_ol = add_ref_after(_ol, "OLIVEIRA, R. S.; BEZERRA, L.; DAVIDSON, E. A.; PINTO, F.; KLINK, C. A.; NEPSTAD, D. C.; MOREIRA, A. Deep root function "
              "in soil water dynamics in cerrado savannas of central Brazil. Functional Ecology, v. 19, n. 4, p. 574-581, 2005. "
              "DOI: 10.1111/j.1365-2435.2005.01003.x.")
add_ref_after(_ol, "PICHLER, M.; HARTIG, F. Machine learning and deep learning: a review for ecologists. Methods in Ecology and "
              "Evolution, v. 14, n. 4, p. 994-1016, 2023. DOI: 10.1111/2041-210X.14061.")
add_ref_after(ORIG[360], "RODRIGUES, R. R.; MCPHADEN, M. J. Why did the 2011-2012 La Niña cause a severe drought in the Brazilian Northeast? "
              "Geophysical Research Letters, v. 41, n. 3, p. 1012-1018, 2014. DOI: 10.1002/2013GL058703.")
add_ref_after(ORIG[362], "SCHWINNING, S.; SALA, O. E. Hierarchy of responses to resource pulses in arid and semi-arid ecosystems. Oecologia, "
              "v. 141, n. 2, p. 211-220, 2004. DOI: 10.1007/s00442-004-1520-8.")
remove_para(ORIG[347])   # HAO et al. (2019) não é mais citado
_g = add_ref_after(ORIG[345], "GIGLIO, L.; BOSCHETTI, L.; ROY, D. P.; HUMBER, M. L.; JUSTICE, C. O. The Collection 6 MODIS burned area mapping "
                   "algorithm and product. Remote Sensing of Environment, v. 217, p. 72-85, 2018. DOI: 10.1016/j.rse.2018.08.005.")
add_ref_after(_g, "GORELICK, N.; HANCHER, M.; DIXON, M.; ILYUSHCHENKO, S.; THAU, D.; MOORE, R. Google Earth Engine: planetary-scale "
              "geospatial analysis for everyone. Remote Sensing of Environment, v. 202, p. 18-27, 2017. DOI: 10.1016/j.rse.2017.06.031.")
add_ref_after(ORIG[347], "HUFFMAN, G. J.; STOCKER, E. F.; BOLVIN, D. T.; NELKIN, E. J.; TAN, J. GPM IMERG Final Precipitation L3 1 month "
              "0.1 degree x 0.1 degree V07. Greenbelt: Goddard Earth Sciences Data and Information Services Center (GES DISC), 2023. "
              "DOI: 10.5067/GPM/IMERG/3B-MONTH/07.")
_ib = add_ref_after(ORIG[348], "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Biomas e sistema costeiro-marinho do Brasil: compatível "
              "com a escala 1:250 000. Rio de Janeiro: IBGE, 2019. (Relatórios Metodológicos, v. 45).")
_ib = add_ref_after(_ib, "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Censo Demográfico 2022: etnias e línguas indígenas: "
              "principais características sociodemográficas: resultados do universo. Rio de Janeiro: IBGE, 2025a. Disponível em: "
              "https://biblioteca.ibge.gov.br/index.php/biblioteca-catalogo?view=detalhes&id=2102223. Acesso em: 21 set. 2026.")
add_ref_after(_ib, "INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). Cidades e Estados: Bahia. Rio de Janeiro: IBGE, 2025b. "
              "Disponível em: https://www.ibge.gov.br/cidades-e-estados/ba.html. Acesso em: 21 set. 2026.")
remove_para(ORIG[349])   # INPE (Monitoramento do El Niño e La Niña) não é citado no texto; as fases ENSO vêm do ONI/NOAA
_nasa = add_ref_after(ORIG[356], "NATIONAL AERONAUTICS AND SPACE ADMINISTRATION (NASA). IMERG V08 transition schedule. Greenbelt: NASA Global "
              "Precipitation Measurement, 2026. Disponível em: https://gpm.nasa.gov/data/news/imerg-v08-transition-schedule. Acesso em: 17 set. 2026.")
add_ref_after(_nasa, ORIG[359].text.strip())   # NOAA (ONI) reposicionada em ordem alfabética
remove_para(ORIG[359])
add_ref_after(ORIG[361], "RUNNING, S. W.; MU, Q.; ZHAO, M.; MORENO, A. User's guide: MODIS global terrestrial evapotranspiration (ET) product "
              "(MOD16A2/A3 and year-end gap-filled MOD16A2GF/A3GF), Collection 6.1. Missoula: Numerical Terradynamic Simulation Group, "
              "University of Montana, 2021.")
_wan = add_ref_after(ORIG[364], "WAN, Z.; HOOK, S.; HULLEY, G. MODIS/Terra Land Surface Temperature/Emissivity 8-Day L3 Global 1 km SIN Grid V061 "
              "(MOD11A2). Sioux Falls: NASA EOSDIS Land Processes DAAC, 2021. DOI: 10.5067/MODIS/MOD11A2.061.")
add_ref_after(_wan, "WU, J.; ALBERT, L. P.; LOPES, A. P.; RESTREPO-COUPE, N.; HAYEK, M.; WIEDEMANN, K. T. et al. Leaf development and "
              "demography explain photosynthetic seasonality in Amazon evergreen forests. Science, v. 351, n. 6276, p. 972-976, 2016. "
              "DOI: 10.1126/science.aad5068.")

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
        "Índice de contribuição relativa das variáveis preditoras no modelo MRMP-N nos três biomas",
        "Diagnóstico de resíduos do MRMP-N nos três biomas",
        "Y-randomization do MRMP-N nos três biomas",
        "Distribuição das variáveis ambientais por fase ENSO na Mata Atlântica",
        "Distribuição das variáveis ambientais por fase ENSO no Cerrado",
        "Distribuição das variáveis ambientais por fase ENSO na Caatinga",
        "Anomalia média da PSN durante e após meses de El Niño e de La Niña, por defasagem de 0 a 12 meses, nos três biomas",
        "Soma anual da PSN por bioma (2001–2024), tendência de Sen, ano parcial de 2025 e anos com fase ENSO dominante"]
TABS = ["Variáveis para predição da Fotossíntese Líquida (PSN)",
        "Desempenho preditivo do MRMP-N nos biomas Mata Atlântica, Cerrado e Caatinga na Bahia",
        "Comparação do desempenho preditivo (R²) dos modelos sob diferentes estratégias de validação",
        "Tipologia ecológica dos regimes de produtividade primária na Bahia",
        "Fator de Inflação da Variância (VIF) das variáveis preditoras por bioma",
        "Anomalias médias das variáveis por fase ENSO e testes de posição, dispersão e extremos",
        "Anomalia média da PSN durante e após os episódios de ENSO mais intensos e mais longos",
        "Variabilidade interanual da PSN por bioma (2001–2024): média, CV, tendência de Sen e consistência com o NPP anual",
        "Base de dados mensal dos três biomas (2001–2025) [A1]",
        "Desempenho das 10 combinações de variáveis ambientais por bioma [A2]",
        "Efeito da remoção das componentes de sazonalidade harmônica no desempenho do MRMP-N [A3]",
        "Ciclo anual, correlação com a PSN e importância das variáveis com e sem harmônicos [A4]",
        "Valores dos diagramas de caixa das Figuras 11 a 13 por fase ENSO [A5]",
        "Sensibilidade do desempenho ao percentil de winsorização da PSN [A6]",
        "R² de teste por grau polinomial sob os três esquemas de validação [A7]",
        "Combinações de variáveis sob validação temporal e estabilidade da seleção [A8]",
        "Importância por permutação fora da amostra por bloco temporal [A9]",
        "Nulos que preservam a estrutura temporal da PSN [A10]"]
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
fontes = {"PSN": "MOD17A2HGF, Coleção 6.1 (NASA), via GEE", "EV": "MOD16A2GF, Coleção 6.1 (NASA), via GEE",
          "PRE": "GPM IMERG Final mensal V07 (NASA GES DISC), via GEE", "TST": "MOD11A2, Coleção 6.1 (NASA), via GEE",
          "WAI": "ETR/ETP do MOD16A2GF", "BURN": "MCD64A1, Coleção 6.1 (NASA), via GEE",
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
    if 1 < len(t.rows) <= 20 and t.rows[0].cells[0].text.strip() in ('Variável', 'Bioma'): manter_junta(t)
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
_BM66 = '_Toc900000066'
_bs = OxmlElement('w:bookmarkStart'); _bs.set(qn('w:id'), '9066'); _bs.set(qn('w:name'), _BM66)
_be = OxmlElement('w:bookmarkEnd'); _be.set(qn('w:id'), '9066')
_h66._p.insert(1 if _h66._p.pPr is not None else 0, _bs); _h66._p.append(_be)
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
# entrada nova do Sumário para 6.6 (cópia da entrada de "Implicações", que passa a 6.7)
for sdt in d.element.body.findall(qn('w:sdt')):
    for par in sdt.findall('.//' + qn('w:p')):
        hl = par.find('.//' + qn('w:hyperlink'))
        if hl is None or not _anc2head.get(hl.get(qn('w:anchor')), '').startswith('Implicações ambientais'): continue
        novo = copy.deepcopy(par); par.addprevious(novo)
        nhl = novo.find('.//' + qn('w:hyperlink')); nhl.set(qn('w:anchor'), _BM66)
        for it in novo.findall('.//' + qn('w:instrText')):
            if it.text and 'PAGEREF' in it.text: it.text = re.sub(r'_Toc\d+', _BM66, it.text)
        nts = [t_ for t_ in nhl.findall('.//' + qn('w:t')) if t_.text]
        nums = [t_ for t_ in nts if re.match(r'^\d+(\.\d+)*$', t_.text.strip())]
        if nums: nums[0].text = '6.6'
        tit = [t_ for t_ in nts if not re.match(r'^[\d.]+$', t_.text.strip())]
        if tit:
            tit[0].text = 'Variabilidade interanual da produtividade'
            for extra in tit[1:]: extra.text = ''
        pg66 = PAGES.get('H:VARIABILIDADE INTERANUAL DA PRODUTIVIDADE')
        if nts and nts[-1].text.strip().isdigit() and pg66: nts[-1].text = str(pg66)
        ots = [t_ for t_ in hl.findall('.//' + qn('w:t')) if t_.text]
        onums = [t_ for t_ in ots if re.match(r'^\d+(\.\d+)*$', t_.text.strip())]
        if onums: onums[0].text = '6.7'
        break
for p in d.paragraphs:
    if re.match(r'^(Figura|Tabela) (A?\d+) [-–]', p.text):
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.left_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p._p.xpath('.//w:drawing'):
        p.paragraph_format.first_line_indent = Cm(0); p.paragraph_format.left_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
# ---- referências alinhadas à esquerda (ABNT NBR 6023: sem justificação, evita lacunas nas URLs)
_hr = [p for p in d.paragraphs if p.text.strip().upper().startswith('REFERÊNCIAS')][-1]
_after = False
for p in d.paragraphs:
    if p._p is _hr._p: _after = True; continue
    if _after and p.text.strip(): p.alignment = WD_ALIGN_PARAGRAPH.LEFT
# ---- ajustes pontuais de redação (pente-fino)
_SUBS = [
    (r"a previsibilidade estatística de um ecossistema é diretamente proporcional ao grau em que ele é governado por uma única forçante ambiental dominante\. Quanto mais multifatorial o controle ecológico, menos previsível o sistema, e maior a necessidade de abordagens analíticas integradas\.",
     "neste estudo, a maior predominância de controles climáticos coincidiu com maior previsibilidade estatística, e o controle mais multifatorial, com menor previsibilidade e maior necessidade de abordagens analíticas integradas."),
    (r"marcada pela intensa fragmentação da paisagem e pela forte pressão antrópica na Bahia, que introduzem componentes adicionais de variabilidade na PSN não integralmente representad[a-z]+ pelos preditores climáticos",
     "como discutido na seção 6.1, na qual fatores de paisagem introduzem variabilidade na PSN não representada pelos preditores climáticos"),
    (r"coerente com secas severas ou queimadas de grande escala, capazes de gerar reduções abruptas da produtividade primária não plenamente capturadas pelos preditores climáticos médios",
     "compatível com eventos ambientais extremos não plenamente representados pelos preditores mensais"),
    (r"com território de aproximadamente 564\.733 km², o que o torna o quinto maior estado do país e a unidade da federação que faz divisa com o maior número de estados\.",
     "com território de aproximadamente 564.764 km² (IBGE, 2025b), o que o torna o quinto maior estado do país e a unidade da federação que faz divisa com o maior número de estados."),
    (r"e a extensa faixa litorânea, de cerca de 1\.188 km,", "e a extensa faixa litorânea, a mais longa do país, com mais de 1.100 km (Bahia, 2024),"),
    (r"(Pataxó, Pataxó Hã-Hã-Hãe, Tupinambá, Kiriri, Tuxá, Pankararé, Truká e Kaimbé, entre outras)", r"\1; IBGE, 2025a"),
    (r"apresenta desempenho robusto e estatisticamente validado nos três biomas", "apresenta desempenho consistente nos esquemas de validação avaliados nos três biomas"),
    (r"Os resultados obtidos demonstram que o MRMP-N", "Os resultados obtidos indicam que o MRMP-N"),
    (r"garantindo\s+robustez estatística e capacidade de generalização", "o que favorece a robustez estatística e a capacidade de generalização"),
    (r"potencial para o desenvolvimento de sistemas de alerta precoce de declínio de produtividade",
     "potencial para o desenvolvimento futuro de sistemas de alerta de declínio de produtividade, quando o modelo for acoplado a previsões das variáveis ambientais"),
    (r"Zoneamento Ecológico-Econômico da Bahia e o Plano Nacional de Recuperação da Vegetação Nativa \(PLANAVEG\) ao identificar",
     "Zoneamento Ecológico-Econômico da Bahia (Bahia, 2020) e o Plano Nacional de Recuperação da Vegetação Nativa (PLANAVEG; Brasil, 2017) ao identificar"),
    (r"e a influência da fragmentação apontam a restauração florestal", "e a hipótese da influência da fragmentação apontam a restauração florestal"),
    (r"\s*\(Hao et al\., 2019\)", ""),
    (r";\s*Hao et al\., 2019", ""),
    (r"para as quais abordagens flexíveis superam consistentemente as estritamente lineares\.", "para as quais abordagens flexíveis tendem a superar as estritamente lineares (Olden; Lawler; Poff, 2008; Pichler; Hartig, 2023)."),
    (r"forçante climática indireta, mediada principalmente pelas variáveis de temperatura e precipitação, transmitida pela evapotranspiração no Cerrado e na Caatinga e pela temperatura na Mata Atlântica,",
     "forçante climática indireta, associada principalmente à evapotranspiração no Cerrado e na Caatinga e à temperatura na Mata Atlântica,"),
    (r"forçante climática indireta, mediada principalmente pelas variáveis de temperatura e precipitação,", "forçante climática indireta, associada principalmente à evapotranspiração no Cerrado e na Caatinga e à temperatura na Mata Atlântica,"),
    (r"não se aplicou filtro adicional pela banda de controle de qualidade, uma vez que as versões com preenchimento de falhas \(GF\) já substituem as observações de baixa qualidade por valores interpolados \(Running; Zhao, 2021\), o que não elimina a incerteza inerente a esses produtos\.",
     "para os produtos com preenchimento de falhas (MOD17A2HGF e MOD16A2GF) não se aplicou filtro adicional pela banda de controle de qualidade, uma vez que essas versões já substituem as observações de baixa qualidade por valores interpolados (Running; Zhao, 2021), o que não elimina a incerteza inerente a esses produtos. O MOD11A2 não possui versão com preenchimento de falhas: os pixels sem observação de céu claro não recebem valor de TST e ficam fora da média do composto, mas a banda de qualidade QC_Day, que classifica a incerteza dos pixels retidos, não foi usada como filtro; a sensibilidade da série de TST a esse filtro não foi avaliada e é registrada como limitação (Capítulo 7)."),
    (r"os períodos aqui denominados mensais são, portanto, janelas fixas de compostos, e não meses civis estritos\.",
     "os períodos aqui denominados mensais são, portanto, janelas fixas de 32 dias, e não meses civis estritos; as componentes harmônicas de sazonalidade (SAZsin e SAZcos) usam o índice do mês civil de referência de cada janela, e as janelas são as mesmas de Benfica et al. (2022), o que mantém a comparabilidade com a série original."),
    (r"regimes ecológicos distintos de controle da PSN", "regimes ecológicos distintos de associação entre o clima e a PSN"),
    (r"os regimes de controle da PSN identificados", "os regimes de associação entre o clima e a PSN identificados"),
    (r"no Cerrado, em substituição à Temperatura de Superfície Terrestre \(TST\), configura", "no Cerrado, selecionado em lugar da Temperatura de Superfície Terrestre (TST), configura"),
    (r"compreensão dos controles ecofisiológicos da produtividade", "compreensão dos fatores ecofisiológicos associados à produtividade"),
    (r"o WAI atua como integrador eficiente dos múltiplos controles climáticos sobre a PSN", "o WAI resume, em uma única variável, múltiplos fatores climáticos associados à PSN"),
    (r"a maior predominância de controles climáticos coincidiu com maior previsibilidade estatística, e o controle mais multifatorial,",
     "a maior predominância de preditores climáticos coincidiu com maior previsibilidade estatística, e a associação mais multifatorial,"),
    (r"os principais controles climáticos e hídricos da PSN", "os principais preditores climáticos e hídricos da PSN"),
    (r"onde a produtividade é governada pelo balanço hídrico", "onde a produtividade está associada predominantemente ao balanço hídrico"),
    (r"grau em que cada ecossistema é governado por forçantes climáticas", "grau em que a PSN de cada ecossistema é previsível a partir de forçantes climáticas"),
    (r"esquemas complementares de validação temporal \(GroupKFold por ano e TimeSeriesSplit com janela expansível\)", "validação agrupada por ano (GroupKFold) e cronológica (TimeSeriesSplit com janela expansível)"),
    (r"esquemas de validação temporal \(GroupKFold por ano e TimeSeriesSplit\)", "validação agrupada por ano (GroupKFold) e cronológica (TimeSeriesSplit)"),
    (r"esquemas de validação temporal \(GroupKFold por ano e", "validação agrupada por ano (GroupKFold) e cronológica ("),
    (r"determinação empírica do grau polinomial ótimo, em substituição à fixação prévia de um grau, garantindo que",
     "determinação empírica do grau polinomial, em substituição à fixação prévia de um grau, de modo que"),
    (r"A análise empírica indicou o grau 2 como ótimo para os três biomas analisados, resultado discutido",
     "A análise empírica indicou o grau 2 como o de melhor compromisso entre desempenho preditivo, estabilidade e parcimônia para os três biomas analisados, resultado discutido"),
    (r"O grau polinomial ótimo foi determinado empiricamente, identificando-se o grau 2 como aquele que melhor equilibra desempenho preditivo e controle de (?:sobreajuste|overfitting)",
     "O grau polinomial foi selecionado empiricamente, adotando-se o grau 2 como o de melhor compromisso entre desempenho preditivo, estabilidade e parcimônia"),
    (r"foi identificado um conjunto ótimo de variáveis preditoras para cada bioma", "foi identificado, para cada bioma, o conjunto de variáveis preditoras de melhor desempenho"),
    (r"que havia sido a ótima na série original", "que havia sido a de melhor desempenho na série original"),
    (r"conjuntos ótimos distintos", "conjuntos selecionados distintos"),
    (r"conjunto ótimo", "conjunto selecionado"),
    (r"o conjunto selecionado identificado foi", "o conjunto selecionado foi"),
    (r"A Figura 8 ilustra a importância relativa de cada variável preditora nos três biomas, calculada a partir dos coeficientes padronizados do modelo Ridge\. A importância relativa de cada variável foi calculada como a soma dos valores absolutos dos coeficientes padronizados de todos os termos",
     "A Figura 8 apresenta o índice de contribuição relativa de cada variável preditora nos três biomas, calculado a partir dos coeficientes do modelo Ridge ajustado sobre as variáveis padronizadas. O índice de cada variável foi calculado como a soma dos valores absolutos dos coeficientes de todos os termos"),
    (r"regimes ecológicos distintos de controle da produtividade primária, apesar de compartilharem", "regimes ecológicos distintos de controle da PSN, apesar de compartilharem"),
    (r"sintetiza os regimes de controle da produtividade primária identificados em cada bioma", "sintetiza os regimes de controle da PSN identificados em cada bioma"),
    (r"efeitos indiretos do ENSO sobre a produtividade primária sem a necessidade", "efeitos indiretos do ENSO sobre a PSN sem a necessidade"),
    (r"nos mecanismos de controle da produtividade primária\.", "nos mecanismos de controle da PSN."),
    (r"os principais controles climáticos e hídricos da produtividade primária e ao apontar", "os principais controles climáticos e hídricos da PSN e ao apontar"),
    (r"validação cruzada repetida, validação temporal e teste de Y-randomization", "validação cruzada repetida, validação agrupada por ano e cronológica, e teste de Y-randomization"),
    (r"repeated cross-validation, temporal validation and a Y-randomization test", "repeated cross-validation, year-grouped and chronological validation, and a Y-randomization test"),
    (r"validação temporal", "validação cronológica"),
    (r"\boverfitting\b", "sobreajuste"),
    (r"estimado por Regressão Ridge", "estimado por regressão Ridge"),
    (r"(?<!Polinomial; )(?<!; )\bRegressão Ridge\b(?! Polinomial)", "regressão Ridge"),
    (r"El Niño-Oscilação Sul", "El Niño–Oscilação Sul"),
    (r"controle da produtividade primária na região", "controle da PSN na região"),
    (r"gradiente regional de previsibilidade climática da produtividade primária", "gradiente regional de previsibilidade climática da PSN"),
]
for p in d.paragraphs:
    if p.style.name.startswith('toc') or p._p.xpath('.//w:drawing'): continue
    for pat, repl in _SUBS:
        if re.search(pat, p.text): regex_replace_para(p, pat, repl)
# rodapés do modelo original contêm um "." solto que aparece no pé de todas as páginas
for rel in d.part.rels.values():
    if 'footer' in rel.reltype:
        for t_el in rel.target_part.element.xpath('.//w:t'):
            if t_el.text and t_el.text.strip() == '.':
                t_el.text = ''

# =============================================================================
# 17. FORMATAÇÃO ABNT / ACABAMENTO VISUAL (não altera conteúdo)
# =============================================================================
def _txt(el):
    return ''.join(t.text or '' for t in el.iter(qn('w:t')))
_PPR_ORDER = ['pStyle', 'keepNext', 'keepLines', 'pageBreakBefore', 'framePr', 'widowControl', 'numPr', 'suppressLineNumbers', 'pBdr',
              'shd', 'tabs', 'suppressAutoHyphens', 'kinsoku', 'wordWrap', 'overflowPunct', 'topLinePunct', 'autoSpaceDE', 'autoSpaceDN',
              'bidi', 'adjustRightInd', 'snapToGrid', 'spacing', 'ind', 'contextualSpacing', 'mirrorIndents', 'suppressOverlap', 'jc',
              'textDirection', 'textAlignment', 'textboxTightWrap', 'outlineLvl', 'divId', 'cnfStyle', 'rPr', 'sectPr', 'pPrChange']
def _ppr_insert(ppr, el):
    """Insere el em w:pPr respeitando a ordem do esquema OOXML."""
    tag = el.tag.split('}')[1]; pos = _PPR_ORDER.index(tag)
    for child in ppr:
        ctag = child.tag.split('}')[1]
        if ctag in _PPR_ORDER and _PPR_ORDER.index(ctag) > pos:
            child.addprevious(el); return el
    ppr.append(el); return el
def _is_empty_par(el):
    if el.tag != qn('w:p'): return False
    if el.xpath('.//w:drawing') or el.xpath('.//w:sectPr') or el.xpath('.//w:br'): return False
    return not _txt(el).strip()
def _find_par(pred):
    for p in d.paragraphs:
        if pred(p.text): return p
    raise KeyError(pred)
# 17.1 seções primárias (capítulos) em página nova; REFERÊNCIAS sem numeração e centralizada (NBR 14724)
for p in d.paragraphs:
    if p.style.name != 'Heading 1': continue
    t = p.text.strip()
    if t.startswith('APÊNDICE') or t.startswith('REFERÊNCIAS'):
        continue                                   # já começam em página nova pela quebra de seção
    p.paragraph_format.page_break_before = True
_ref = _find_par(lambda t: t.strip().startswith('REFERÊNCIAS'))
_np = OxmlElement('w:numPr'); _il = OxmlElement('w:ilvl'); _il.set(qn('w:val'), '0'); _ni = OxmlElement('w:numId'); _ni.set(qn('w:val'), '0')
_np.append(_il); _np.append(_ni)
_ppr = _ref._p.get_or_add_pPr(); _ps = _ppr.find(qn('w:pStyle'))
(_ps.addnext(_np) if _ps is not None else _ppr.insert(0, _np))
_ref.alignment = WD_ALIGN_PARAGRAPH.CENTER
_ref.paragraph_format.left_indent = Cm(0); _ref.paragraph_format.first_line_indent = Cm(0)
# 17.2 listas pré-textuais e Sumário em página própria
for p in d.paragraphs:
    if p.text.strip() in ('LISTA DE FIGURAS', 'LISTA DE TABELAS'): p.paragraph_format.page_break_before = True
for el in d.element.body.iter(qn('w:p')):
    if _txt(el).strip() == 'SUMÁRIO':
        ppr = el.find(qn('w:pPr'))
        if ppr is None: ppr = OxmlElement('w:pPr'); el.insert(0, ppr)
        if ppr.find(qn('w:pageBreakBefore')) is None:
            _ppr_insert(ppr, OxmlElement('w:pageBreakBefore'))
# 17.3 controle de viúvas/órfãs no estilo base
d.styles['Normal'].paragraph_format.widow_control = True
# 17.4 Figura 3: estilo herdado de colagem → Normal
for p in d.paragraphs:
    if p.style.name == 'font-claude-response-body': p.style = d.styles['Normal']
# 17.5 reposicionamentos para evitar páginas quase vazias (o texto que cita cada elemento continua antes dele)
def _scale_img(par, width_cm):
    for ext in par._p.xpath('.//wp:extent') + par._p.xpath('.//a:ext'):
        if ext.get('cx') is None or ext.get('cy') is None: continue      # a:ext de extLst não tem dimensões
        cx, cy = int(ext.get('cx')), int(ext.get('cy'))
        if cx <= 0: continue
        ncx = int(width_cm * 360000); ext.set('cx', str(ncx)); ext.set('cy', str(int(cy * ncx / cx)))
for _fig, _w in (('Figura 2 - ', 14.0), ('Figura 3 - ', 14.0), ('Figura 4 - ', 13.5)):
    _c = _find_par(lambda t, f=_fig: t.startswith(f)); _i = [i for i, q in enumerate(d.paragraphs) if q._p is _c._p][0]
    _scale_img(d.paragraphs[_i + 1], _w)
for p in d.paragraphs:                                   # legendas: espaçamento simples (NBR 14724)
    if re.match(r'^(Figura|Tabela) (A?\d+) [-–]', p.text):
        p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(3)
for t in d.tables:                                       # células: espaçamento simples
    if t.rows[0].cells[0].text.strip() == 'N°': continue  # listas pré-textuais
    for row in t.rows:
        for c in row.cells:
            for par in c.paragraphs: par.paragraph_format.line_spacing = 1.0
_cap5 = _find_par(lambda t: t.startswith('Figura 5 - ')); _i5 = [i for i, q in enumerate(d.paragraphs) if q._p is _cap5._p][0]
_img5 = d.paragraphs[_i5 + 1]; _nxt5 = d.paragraphs[_i5 + 2]
assert _nxt5.text.startswith('Os resultados obtidos indicam'), _nxt5.text[:60]
_nxt5._p.addnext(_img5._p); _nxt5._p.addnext(_cap5._p); _nxt5.paragraph_format.space_before = Pt(0)
_cap15 = _find_par(lambda t: t.startswith('Figura 15 - ')); _i15 = [i for i, q in enumerate(d.paragraphs) if q._p is _cap15._p][0]
_img15 = d.paragraphs[_i15 + 1]
_tend_p = _find_par(lambda t: t.startswith('A Mata Atlântica foi o único bioma com tendência negativa'))
_tend_p._p.addprevious(_cap15._p); _tend_p._p.addprevious(_img15._p)   # Figura 15 antes do parágrafo que discute a tendência
# 17.5b ordem pós-textual (NBR 14724): referências, depois apêndice
_body = d.element.body
_hap = _find_par(lambda t: t.strip().startswith('APÊNDICE A'))
_els = list(_body); _iap = _els.index(_hap._p); _iref = _els.index(_ref._p)
_fim_ap = next(e for e in _els[_iap:_iref] if e.tag == qn('w:p') and e.find(qn('w:pPr')) is not None and e.find(qn('w:pPr')).find(qn('w:sectPr')) is not None)
_ifim = _els.index(_fim_ap)
_apx = _els[_iap:_ifim + 1]                      # bloco do apêndice (termina no parágrafo com sectPr paisagem)
_refs = [e for e in _els[_iref:] if e.tag != qn('w:sectPr')]
_sect_land = _fim_ap.find(qn('w:pPr')).find(qn('w:sectPr'))
_fim_ap.find(qn('w:pPr')).remove(_sect_land)        # o apêndice passa a ser a última seção: usa o sectPr do corpo
_final = _body.find(qn('w:sectPr'))
_final.getparent().replace(_final, _sect_land)
_last_ref = d.paragraphs[[i for i, q in enumerate(d.paragraphs) if q._p is _refs[-1]][0]] if _refs[-1].tag == qn('w:p') else None
for e in _refs: _hap._p.addprevious(e)            # referências vão para antes do apêndice
if _last_ref is not None: sect_break(_last_ref, landscape=False)   # fecha a seção retrato das referências
_ref.paragraph_format.page_break_before = False
for sdt in d.element.body.findall(qn('w:sdt')):
    for par in sdt.findall('.//' + qn('w:p')):
        hl = par.find('.//' + qn('w:hyperlink'))
        if hl is None or not _anc2head.get(hl.get(qn('w:anchor')), '').startswith('REFERÊNCIAS'): continue
        ts = [t_ for t_ in hl.findall('.//' + qn('w:t')) if t_.text]
        for t_ in ts:
            if re.match(r'^\d+$', t_.text.strip()) and t_ is not ts[-1]: t_.text = ''      # remove o "8"
        for tab in hl.findall('.//' + qn('w:tab')):                                          # tab entre número e título
            tab.getparent().remove(tab); break
        pgr = PAGES.get('H:REFERÊNCIAS')
        if pgr and ts[-1].text.strip().isdigit(): ts[-1].text = str(pgr)
        _BMAP = '_Toc900000077'
        _bs2 = OxmlElement('w:bookmarkStart'); _bs2.set(qn('w:id'), '9077'); _bs2.set(qn('w:name'), _BMAP)
        _be2 = OxmlElement('w:bookmarkEnd'); _be2.set(qn('w:id'), '9077')
        _hap._p.insert(1 if _hap._p.pPr is not None else 0, _bs2); _hap._p.append(_be2)
        novo = copy.deepcopy(par); par.addnext(novo)
        nhl = novo.find('.//' + qn('w:hyperlink')); nhl.set(qn('w:anchor'), _BMAP)
        for it in novo.findall('.//' + qn('w:instrText')):
            if it.text and 'PAGEREF' in it.text: it.text = re.sub(r'_Toc\d+', _BMAP, it.text)
        nts = [t_ for t_ in nhl.findall('.//' + qn('w:t')) if t_.text]
        tit = [t_ for t_ in nts if not re.match(r'^\d+$', t_.text.strip())]
        if tit:
            tit[0].text = 'APÊNDICE A – BASE DE DADOS MENSAL E RESULTADOS DA SELEÇÃO DE VARIÁVEIS'
            for extra in tit[1:]: extra.text = ''
        pga = PAGES.get('H:APÊNDICE A – BASE DE DADOS MENSAL E RESULTADOS DA SELEÇÃO DE VARIÁVEIS')
        if pga and nts[-1].text.strip().isdigit(): nts[-1].text = str(pga)
        break
for sdt in d.element.body.findall(qn('w:sdt')):          # Sumário em espaçamento simples (cabe em uma página)
    for par in sdt.findall('.//' + qn('w:p')):
        ppr = par.find(qn('w:pPr'))
        if ppr is None or ppr.find(qn('w:pStyle')) is None or not ppr.find(qn('w:pStyle')).get(qn('w:val')).startswith('Sumrio'): continue
        spc = ppr.find(qn('w:spacing'))
        if spc is None:
            spc = _ppr_insert(ppr, OxmlElement('w:spacing'))
        spc.set(qn('w:line'), '240'); spc.set(qn('w:lineRule'), 'auto'); spc.set(qn('w:before'), '0'); spc.set(qn('w:after'), '120')
# 17.6 "Fonte:" abaixo de todas as figuras e tabelas (NBR 14724), fonte 10, espaçamento simples
def _keep_next(pel):
    ppr = pel.find(qn('w:pPr'))
    if ppr is None: ppr = OxmlElement('w:pPr'); pel.insert(0, ppr)
    if ppr.find(qn('w:keepNext')) is None: _ppr_insert(ppr, OxmlElement('w:keepNext'))
def _fonte_apos(el, texto):
    q = new_para_after(d.paragraphs[0], CAPTION_TPL, texto)      # cria e depois move para depois de el
    el.addnext(q._p)
    if el.tag == qn('w:p'): _keep_next(el)                          # imagem fica com a sua fonte
    else:
        for pel in el.findall(qn('w:tr'))[-1].iter(qn('w:p')): _keep_next(pel)   # última linha da tabela fica com a fonte
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = q.paragraph_format; pf.first_line_indent = Cm(0); pf.left_indent = Cm(0); pf.right_indent = Cm(0)
    pf.space_before = Pt(0); pf.space_after = Pt(12); pf.line_spacing = 1.0; pf.keep_with_next = False
    for r in q.runs: r.font.bold = False; r.font.size = Pt(10)
    nx = q._p.getnext()
    if nx is not None and _is_empty_par(nx): nx.getparent().remove(nx)
    return q
_FONTE = "Fonte: elaborada pelo autor (2026)."
_FONTE_ESP = {'Figura 1': "Fonte: elaborada pelo autor (2026), com base em Running e Zhao (2021).",
              'Figura 2': "Fonte: elaborada pelo autor (2026), a partir da malha de biomas do IBGE (2019).",
              'Tabela A1': "Fonte: elaborada pelo autor (2026), a partir dos produtos descritos na seção 5.2."}
_body = d.element.body
_prev_cap = None
for el in list(_body):
    if el.tag == qn('w:p'):
        m = re.match(r'(Figura|Tabela) (A?\d+) [-–]', _txt(el))
        if m: _prev_cap = f"{m.group(1)} {m.group(2)}"
        if el.xpath('.//w:drawing') and _prev_cap and _prev_cap.startswith('Figura'):
            _fonte_apos(el, _FONTE_ESP.get(_prev_cap, _FONTE)); _prev_cap = None
    elif el.tag == qn('w:tbl') and _prev_cap and _prev_cap.startswith('Tabela'):
        _fonte_apos(el, _FONTE_ESP.get(_prev_cap, _FONTE)); _prev_cap = None
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
