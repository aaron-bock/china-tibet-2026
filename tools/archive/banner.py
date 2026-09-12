#!/usr/bin/env python3
"""Add an 'archived' banner to a published artifact's HTML and write a publishable file.

Usage: banner.py <infile> <outfile>
Reads a full document or a bare artifact fragment; writes the fragment with the
banner first, ready for the Artifact tool (which supplies its own skeleton).
"""
import re, sys

NEW = "https://claude.ai/code/artifact/eccc0f6c-dc3a-4c08-8381-905dee78f9ff"
BANNER = (
'<div role="note" style="background:#6E2A12;color:#FFF0E6;'
'font:400 14px/1.55 -apple-system,BlinkMacSystemFont,\'Segoe UI\',Roboto,sans-serif;'
'padding:14px 18px;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:baseline;'
'border-bottom:3px solid #C2571F">'
'<strong style="font:600 11px/1.5 ui-monospace,Menlo,monospace;letter-spacing:.14em;'
'text-transform:uppercase;color:#FFC7A0;white-space:nowrap">Archived &middot; 12 Sep 2026</strong>'
'<span style="flex:1 1 320px;min-width:0">Not maintained. Everything here now lives in the '
f'<a href="{NEW}" style="color:#FFF0E6;font-weight:600;'
'text-decoration:underline;text-underline-offset:2px">China &amp; Tibet 2026 dossier</a>, '
'which is the single source of truth for this trip.</span>'
'</div>\n'
)

def fragment(html: str) -> str:
    m = re.search(r'<body[^>]*>(.*)</body>', html, re.S | re.I)
    inner = m.group(1) if m else html
    # a full-document read leaves the platform's own reset <head> behind; drop the
    # doctype/html remnants if the page had no <body> to slice on
    inner = re.sub(r'(?is)^\s*<!doctype[^>]*>', '', inner)
    return inner.strip()

def main():
    src, dst = sys.argv[1], sys.argv[2]
    html = open(src, encoding='utf-8').read()
    inner = fragment(html)
    if 'Archived &middot; 12 Sep 2026' in inner or 'artifact/eccc0f6c' in inner:
        print(f'{dst}: banner already present, nothing to do')
        return
    # the banner has to land at the top of the RENDERED page, so it must sit inside
    # the body. Some of these pages carry their own <head>/<body> inside the
    # fragment; where they do, go after that body tag, otherwise after the page's
    # own </style>.
    inner_body = list(re.finditer(r'(?is)<body[^>]*>', inner))
    if inner_body:
        cut = inner_body[-1].end()
        out = inner[:cut] + '\n' + BANNER + inner[cut:]
    else:
        m = re.search(r'(?is)(.*?</style>\s*)(?=<)', inner)
        out = (m.group(1) + BANNER + inner[m.end():]) if m else (BANNER + inner)
    open(dst, 'w', encoding='utf-8').write(out)
    print(f'{dst}: banner added ({len(out)} bytes, was {len(html)})')

main()
