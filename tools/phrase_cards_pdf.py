# -*- coding: utf-8 -*-
"""Bilingual point-at-this cards, six to a Letter sheet, to print and cut out.

    ArtifactData action=get url=<artifact> collection=trip doc_id=phrases \\
                 out_dir=<dir>
    python3 tools/phrase_cards_pdf.py --data <dir>/trip/phrases.json --out <dir>
    node tools/render_packing_pdf.mjs <dir>/print-cards.html <dir>/cards.pdf \\
         --margins 12.7mm,12.7mm,12.7mm,12.7mm --footer ""

`--ids` builds a subset (a mock sheet) through exactly the same code as the
full deck, so what gets approved is what gets printed.

THE CHINESE IS THE CARD. Everything else is your index for finding it in a
stack: a stranger reads the big line at arm's length across a taxi seat, and
the English exists so you can pull the right card without reading Chinese.
Type size therefore flexes with length -- two characters get 54px, the
thirty-character Metropolo address gets 20px over two lines -- rather than
every card sharing one size that suits neither.

Cards butt against each other with a hairline border: that border IS the cut
line, so a sheet is two cuts across and one down, not twelve.

Colour bands by leg, with the leg NAME in the band as well: colour alone is
no use photocopied, printed mono, or to anyone colour-blind.
"""
import argparse, datetime, html, io, json, os, re, sys

e = lambda s: html.escape(str(s or ""))

# Legs in trip order. BLACK AND WHITE ONLY -- these print on a mono laser, so
# the band is distinguished by RULE STYLE AND WEIGHT, never by colour. Eight
# combinations of solid/dashed/dotted/double and thin/thick survive a laser and
# a photocopier, where eight greys would not: mid greys band and drift, and two
# of them next to each other are indistinguishable.
#
# The leg NAME is printed in the band regardless, and that is the real index --
# the rule is what you see when the deck is fanned, the name is what you read
# when you have the card.
LEGS = [
    ("All legs", "4px solid"),  ("Outbound", "2px dotted"),
    ("Xi'an",    "1.5px solid"), ("Z165",     "3px dashed"),
    ("Tibet",    "4px double"),  ("Shanghai", "3px dotted"),
    ("Disney",   "2px dashed"),  ("Home",     "3px solid"),
]
LEGC = dict(LEGS)
ORDER = [n for n, _ in LEGS]

# The one card that must never be held up by mistake: it is the WRONG station,
# carried only so the name can be recognised when a driver proposes it.
DANGER = {"p20"}

def leg_of(when):
    w = str(when or "").strip()
    if "·" in w:
        return w.split("·")[-1].strip()
    return w or "All legs"

def date_of(when):
    w = str(when or "").strip()
    return w.split("·")[0].strip() if "·" in w else ""

def cn_size(cn):
    """The whole design in one function: length decides the type size."""
    n = len(re.sub(r"\s", "", str(cn or "")))
    for lim, px in ((3, 54), (6, 46), (9, 38), (14, 31), (22, 25)):
        if n <= lim:
            return px
    return 20

def card(r, i):
    leg = leg_of(r.get("when"))
    rule = LEGC.get(leg, "3px solid")
    bad = r.get("id") in DANGER
    return """<div class="c%s">
  <div class="band" style="border-top:%s #000">
    <span class="lg">%s</span><span class="dt">%s</span>
  </div>
  <div class="en">%s</div>
  <div class="cn" style="font-size:%dpx">%s</div>
  %s
  <div class="ft">%s<span class="no">%d</span></div>
</div>""" % (
        " danger" if bad else "",
        "6px solid" if bad else rule,
        e(leg.upper()), e(date_of(r.get("when"))),
        e(r.get("en")),
        cn_size(r.get("cn")), e(r.get("cn")),
        '<div class="x">DO NOT SHOW THIS &mdash; it is the wrong station</div>' if bad else "",
        ('<span class="nt">%s</span>' % e(r.get("detail"))) if r.get("detail") else "<span></span>",
        i)

def build(rows):
    pages, per = [], 6
    for p in range(0, len(rows), per):
        chunk = rows[p:p + per]
        cells = "\n".join(card(r, p + n + 1) for n, r in enumerate(chunk))
        # Pad the last sheet so the grid keeps its shape and the cut lines run
        # the full width of the page.
        cells += '\n<div class="c blank"></div>' * (per - len(chunk))
        pages.append('<section class="sheet">%s</section>' % cells)
    return (TPL.replace("{{PAGES}}", "\n".join(pages))
               .replace("{{N}}", str(len(rows)))
               .replace("{{SHEETS}}", str(len(pages)))
               .replace("{{PRINTED}}", datetime.date.today().strftime("%d %B %Y")))

TPL = """<!doctype html><html><head><meta charset="utf-8"><title>Point at this — cards</title><style>
@page { size: Letter; margin: 12.7mm; }
*{box-sizing:border-box}
/* Black, white and two greys. Nothing on this sheet depends on colour. */
body{margin:0;font:10pt/1.35 "Liberation Sans",Helvetica,Arial,sans-serif;color:#000;
     -webkit-print-color-adjust:exact;print-color-adjust:exact}
.sheet{display:grid;grid-template-columns:repeat(2,360px);grid-auto-rows:320px;
       width:720px;break-after:page}
.sheet:last-child{break-after:auto}
.c{border:.5px solid #888;padding:14px 16px 11px;display:flex;flex-direction:column;
   overflow:hidden;background:#fff}
.c.blank{border-color:#ccc}
.band{padding-top:5px;margin-bottom:9px;display:flex;
      align-items:baseline;justify-content:space-between;gap:8px}
.lg{font:700 8pt "Liberation Mono",monospace;letter-spacing:.14em;color:#000}
.dt{font:8pt "Liberation Mono",monospace;color:#444;letter-spacing:.04em;white-space:nowrap}
.en{font-size:11.5pt;font-weight:700;line-height:1.2;margin-bottom:6px}
.cn{flex-grow:1;display:flex;align-items:center;justify-content:center;text-align:center;
    font-family:"Noto Sans CJK SC","Source Han Sans SC","WenQuanYi Zen Hei","Liberation Sans",sans-serif;
    font-weight:700;line-height:1.28;letter-spacing:.01em;word-break:break-word;padding:2px 0;color:#000}
.ft{border-top:.5px solid #bbb;padding-top:5px;margin-top:6px;display:flex;
    align-items:flex-end;justify-content:space-between;gap:8px}
.nt{font-size:7.6pt;line-height:1.3;color:#444;flex:1}
.no{font:600 7.5pt "Liberation Mono",monospace;color:#666;flex-shrink:0}
/* The one card that must never be held up. In mono the loudest thing available
   is inversion, so the warning is white out of solid black. */
.c.danger{border:2px solid #000}
.c.danger .cn{text-decoration:line-through;text-decoration-thickness:3px}
.x{font:700 8.5pt "Liberation Sans",Helvetica,sans-serif;background:#000;color:#fff;
   text-align:center;letter-spacing:.03em;padding:3px 4px;margin-top:4px}
</style></head><body>
{{PAGES}}
</body></html>"""

def main():
    ap = argparse.ArgumentParser(description="Build the point-at-this cards.")
    ap.add_argument("--data", required=True, help="a live trip/phrases.json — not seed/")
    ap.add_argument("--out", default=".", help="directory for print-cards.html")
    ap.add_argument("--ids", default="", help="comma-separated row ids for a mock sheet")
    ap.add_argument("--name", default="print-cards.html", help="output file name")
    a = ap.parse_args()

    rows = json.load(io.open(a.data, encoding="utf-8"))["items"]
    if a.ids:
        want = [x.strip() for x in a.ids.split(",") if x.strip()]
        by = {r["id"]: r for r in rows}
        missing = [w for w in want if w not in by]
        if missing:
            sys.exit("no such row id: " + ", ".join(missing))
        rows = [by[w] for w in want]
    else:
        rows.sort(key=lambda r: (ORDER.index(leg_of(r.get("when")))
                                 if leg_of(r.get("when")) in ORDER else 99))

    doc = build(rows)
    path = os.path.join(a.out, a.name)
    io.open(path, "w", encoding="utf-8").write(doc)
    print("read %s" % a.data)
    print("wrote %s — %d cards on %d sheet(s)" % (path, len(rows), (len(rows) + 5) // 6))
    seen = {}
    for r in rows:
        seen.setdefault(leg_of(r.get("when")), 0)
        seen[leg_of(r.get("when"))] += 1
    print("  " + " · ".join("%s %d" % (k, v) for k, v in seen.items()))

if __name__ == "__main__":
    main()
