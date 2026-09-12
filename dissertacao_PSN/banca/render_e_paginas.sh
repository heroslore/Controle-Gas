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
for i,p in enumerate(pl.pages, start=1):
    if i < 9: continue
    for ln in (p.extract_text() or '').split('\n'):
        m=re.match(r'^(Figura|Tabela) (A?\d+) [-–] ', ln.strip())
        if m:
            k=f'{m.group(1)} {m.group(2)}'; pages.setdefault(k, i)
        h=re.match(r'^(\d+(?:\.\d+)*)\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\n]{3,})$', ln.strip())
        if h and i > 8:
            pages.setdefault('H:' + h.group(2).strip().upper(), i)
json.dump(pages, open('paginas.json','w'), indent=1, ensure_ascii=False)
print('páginas', len(pl.pages), pages)
PY
