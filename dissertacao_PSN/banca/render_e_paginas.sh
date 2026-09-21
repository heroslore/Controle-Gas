#!/bin/bash
# Renderiza o docx em PDF (LibreOffice), extrai a página de cada legenda para paginas.json
set -e
cd "$(dirname "$0")"
R=/tmp/claude-0/-home-user-Controle-Gas/b644115f-efef-5303-8a82-3af14e08b70e/scratchpad/docx/render
mkdir -p $R && cp Trabalho_revisado_2001_2025.docx $R/rev.docx
export HOME=/root
(cd $R && timeout 500 soffice --headless --norestore -env:UserInstallation=file:///tmp/claude-0/lo_profile --convert-to pdf rev.docx > /dev/null 2>&1)
python3 - <<'PY'
import pdfplumber, re, json
R='/tmp/claude-0/-home-user-Controle-Gas/b644115f-efef-5303-8a82-3af14e08b70e/scratchpad/docx/render'
pl=pdfplumber.open(f'{R}/rev.pdf'); pages={}
texts=[(p.extract_text() or '') for p in pl.pages]
ini=next((i for i,t in enumerate(texts, start=1) if re.search(r'^1\s+APRESENTAÇÃO E JUSTIFICATIVA\s*$', t, flags=re.M)), 9)
for i,t in enumerate(texts, start=1):
    if i < ini: continue
    for ln in t.split('\n'):
        ln=ln.strip()
        if '....' in ln: continue                       # linha do Sumário
        m=re.match(r'^(Figura|Tabela) (A?\d+) [-–] ', ln)
        if m:
            k=f'{m.group(1)} {m.group(2)}'; pages.setdefault(k, i)
        h=re.match(r'^(\d+(?:\.\d+)*)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{3,})$', ln)
        if h: pages.setdefault('H:' + h.group(2).strip().upper(), i)
        if ln == 'REFERÊNCIAS' or ln.startswith('APÊNDICE '): pages.setdefault('H:' + ln.upper(), i)
json.dump(pages, open('paginas.json','w'), indent=1, ensure_ascii=False)
print('páginas', len(pl.pages), pages)
PY
