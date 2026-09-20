# -*- coding: utf-8 -*-
"""Build the pocket reference card — the numbers you cannot look up.

Writes print-reference.html; tools/render_packing_pdf.mjs turns it into a PDF.

    ArtifactData action=get url=<artifact> collection=trip doc_id=reference \\
                 out_dir=<dir>
    python3 tools/reference_pdf.py --data <dir>/trip/reference.json --out <dir>
    node tools/render_packing_pdf.mjs <dir>/print-reference.html <dir>/card.pdf \\
         --max-pages 1 --margins 12mm,12mm,10mm,12mm --footer ""

THIS ONE IS THE OPPOSITE OF leavebehind_pdf.py, and the two sit next to each
other, so be clear which you are editing. The leave-behind sheet goes to other
people and is redacted: no locators, no confirmations, no companions. THIS card
goes in the traveller's own pocket and exists precisely to carry the locators,
the card lines and the consulate numbers -- the things you cannot look up once
the phone is dead or inside the firewall. The app's own note for this document
calls it "the page to print and fold into a passport".

What still does not appear, because it is not in the data and must not be:
the Trip.com booking PINs (the rows say where they live instead), and the STEP
login on the shared Drive sheet, which belongs to someone else.
"""
import argparse, datetime, html, io, json, os, sys

e = lambda s: html.escape(str(s or ""))

# Column assignment, and it is the split a person actually makes when they reach
# for this: the left column is people and places you contact, the right is
# strings you read out. It also happens to balance the two columns, which the
# obvious grouping did not -- Booking refs alone is nine of the twenty-two rows.
LEFT  = ["Consular", "Cards", "Booking channels", "Dates that bind"]
RIGHT = ["Booking refs", "Loyalty"]
FULL  = ["Rules"]                     # long prose, boxed across the foot

def col(rows, groups):
    out = []
    for g in groups:
        rs = [r for r in rows if r.get("group") == g]
        if not rs:
            continue
        out.append('<h2>%s</h2>' % e(g))
        for r in rs:
            val = r.get("value") or ""
            out.append('<div class="r"><div class="hd"><span class="nm">%s</span>%s</div>%s</div>'
                       % (e(r.get("name")),
                          ('<span class="vl">%s</span>' % e(val)) if val and val != "—" else "",
                          ('<div class="dt">%s</div>' % e(r.get("detail"))) if r.get("detail") else ""))
    return "\n".join(out)

def build(rows):
    full = []
    for g in FULL:
        for r in [x for x in rows if x.get("group") == g]:
            paras = [p.strip() for p in (r.get("detail") or "").split("\n") if p.strip()]
            full.append('<div class="warn"><div class="wh">%s</div>%s</div>'
                        % (e(r.get("name")),
                           "".join('<p>%s</p>' % e(p) for p in paras)))
    placed = set(LEFT) | set(RIGHT) | set(FULL)
    stray = sorted({r.get("group") for r in rows if r.get("group") not in placed})
    if stray:
        sys.exit("reference_pdf: these groups have nowhere to go -- add them to "
                 "LEFT, RIGHT or FULL:\n  " + "\n  ".join(stray))
    return (TPL.replace("{{LEFT}}",  col(rows, LEFT))
               .replace("{{RIGHT}}", col(rows, RIGHT))
               .replace("{{FULL}}",  "\n".join(full))
               .replace("{{PRINTED}}", datetime.date.today().strftime("%d %B %Y")))

TPL = """<!doctype html><html><head><meta charset="utf-8"><title>Reference card</title><style>
@page { size: Letter; margin: 12mm 12mm 10mm; }
*{box-sizing:border-box}
body{margin:0;font:8.6pt/1.3 "Liberation Sans",Helvetica,Arial,sans-serif;color:#15191f}
header{border-bottom:2px solid #15191f;padding-bottom:5px;margin-bottom:9px;
       display:flex;align-items:baseline;justify-content:space-between;gap:12px}
h1{font:600 18pt/1 "Liberation Serif",Georgia,serif;margin:0;letter-spacing:-.01em}
.sub{font:8pt "Liberation Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#5d6773;text-align:right}
.cols{display:flex;gap:16px;align-items:flex-start}
.cols>div{flex:1;min-width:0}
h2{font:600 8pt/1.2 "Liberation Mono",monospace;letter-spacing:.15em;text-transform:uppercase;
   margin:9px 0 3px;padding-bottom:2px;border-bottom:1px solid #9aa4b0;color:#15191f}
h2:first-child{margin-top:0}
.r{padding:3px 0;border-bottom:.5px solid #e3e7ec}
.hd{display:flex;gap:8px;align-items:baseline;justify-content:space-between}
.nm{font-weight:700;font-size:8.8pt;line-height:1.25}
.vl{flex-shrink:0;font:600 9pt "Liberation Mono",monospace;white-space:nowrap;color:#15191f}
.dt{font-size:7.6pt;color:#5d6773;line-height:1.28;margin-top:.5px}
.warn{margin-top:10px;border:1.2px solid #a33526;border-left-width:4px;border-radius:3px;
      background:#fbf2f0;padding:7px 10px}
.wh{font:700 10pt/1.2 "Liberation Sans",Helvetica,sans-serif;color:#8d2d20;margin-bottom:3px}
.warn p{margin:0 0 3px;font-size:8.2pt;line-height:1.32;color:#2b313b}
.warn p:last-child{margin-bottom:0}
footer{margin-top:9px;border-top:.5px solid #c9d0d8;padding-top:4px;
       font:7.2pt "Liberation Mono",monospace;color:#6b7280;display:flex;justify-content:space-between}
</style></head><body>
<header>
  <h1>Reference card</h1>
  <div class="sub">Aaron Bock &middot; China &amp; Tibet<br>27 Sep &ndash; 16 Oct 2026</div>
</header>
<div class="cols">
  <div>{{LEFT}}</div>
  <div>{{RIGHT}}</div>
</div>
{{FULL}}
<footer><span>Printed {{PRINTED}}</span><span>Fold into the passport</span></footer>
</body></html>"""

def main():
    ap = argparse.ArgumentParser(description="Build the pocket reference card.")
    ap.add_argument("--data", required=True,
                    help="path to a live trip/reference.json — fetch it, do not reach for seed/")
    ap.add_argument("--out", default=".", help="directory for print-reference.html")
    a = ap.parse_args()

    rows = json.load(io.open(a.data, encoding="utf-8"))["items"]
    doc = build(rows)
    path = os.path.join(a.out, "print-reference.html")
    io.open(path, "w", encoding="utf-8").write(doc)
    print("read %s — %d rows" % (a.data, len(rows)))
    print("wrote %s — %d bytes" % (path, len(doc)))

if __name__ == "__main__":
    main()
