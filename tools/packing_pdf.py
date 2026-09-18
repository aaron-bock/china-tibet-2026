# -*- coding: utf-8 -*-
"""Build the printable packing sheet from trip/packing.

Writes print-packing.html; tools/render_packing_pdf.mjs turns that into the PDF.
(reportlab is not installed anywhere this runs. Chromium is.)

Get live data in front of it first — the app is the source of truth, not seed/:

    ArtifactData action=get url=<artifact> collection=trip doc_id=packing \\
                 out_dir=<dir>
    python3 tools/packing_pdf.py --data <dir>/trip/packing.json --out <dir>

--data has no default on purpose. The first version of this script read a
snapshot path baked into line 4, and by the time anyone looked the sheet was six
rows and eleven bag moves behind the app with nothing on it saying so. A path
you have to type is a path you have to think about.

The bag guard is the other half of that lesson: the short notes below are print
copy, hand-written and deliberately shorter than the app's, so they cannot be
generated from index.html. But the NAMES can be checked against it, and are.
Add a bag to the app and this aborts until it is described here.
"""
import argparse, collections, datetime, html, io, json, os, re, sys

# Print copy, not a mirror of the app's notes. On screen the Sling note spends a
# clause each on the Z165 toilet and the Disney coasters; that is right for a
# page you read and wrong for a sheet you scan at 6am with a bag open.
NOTES = {
    "Worn":          "On your body through security. None of it counts as a bag.",
    "Sling":         "Never leaves you. Documents, money, phone.",
    "Talon 22":      "Under the seat for the thirteen hours to Incheon, then the day bag.",
    "Talon 44":      "Overhead and shut. The thirty-hour kit on the train, the only bag at base camp.",
    "Away":          "Checked to Xi'an, then shut under the bunk from 2 October until Lhasa.",
    "Buy in Xi'an":  "Not packed. Picked up 29-30 September, before the Z165.",
    "Rent in Lhasa": "Not packed. Sorted around Barkhor, handed back on the 10th.",
}
# The two that are shopping runs rather than bags: dashed checkbox, amber heading.
SHOP = ("Buy in Xi'an", "Rent in Lhasa")

e = lambda s: html.escape(str(s or ""))


def app_bags(index_html):
    """The bag names the app itself ships, in packing order."""
    src = io.open(index_html, encoding="utf-8").read()
    m = re.search(r"var BAGS=\[(.*?)\n\];", src, re.S)
    if not m:
        sys.exit("could not find `var BAGS=[...]` in %s" % index_html)
    return [n.encode().decode("unicode_escape")
            for n in re.findall(r'\{n:"((?:[^"\\]|\\.)*)"', m.group(1))]


def check_bags(order, rows):
    """Abort loudly rather than print a sheet that is quietly missing a bag."""
    described, used = set(NOTES), {r.get("bag") for r in rows if r.get("bag")}
    problems = []
    for n in order:
        if n not in described:
            problems.append("bag %r is in the app but has no note in tools/packing_pdf.py" % n)
    for n in described - set(order):
        problems.append("bag %r has a note here but no longer exists in the app" % n)
    for n in used - set(order):
        problems.append("bag %r appears in the data but is not one of the app's bags" % n)
    if problems:
        sys.exit("packing_pdf: the bag list has drifted —\n  " + "\n  ".join(problems))


def build(rows, order):
    live    = [r for r in rows if r.get("own") != "skip"]
    skipped = [r for r in rows if r.get("own") == "skip"]
    buys    = [r for r in live if r.get("own") == "buy"]
    musts   = [r for r in live if r.get("prio") == "must"]

    body = []
    for bag in order:
        rs = [r for r in live if r.get("bag") == bag]
        if not rs:
            continue
        shop = bag in SHOP
        body.append('<section class="bag%s">' % (" shop" if shop else ""))
        body.append('<div class="bh"><h2>%s</h2><span class="ct">%d %s</span></div>'
                    % (e(bag), len(rs), "item" if len(rs) == 1 else "items"))
        body.append('<p class="bn">%s</p>' % e(NOTES[bag]))
        body.append("<ul>")
        for r in rs:
            must = r.get("prio") == "must"
            # In the two shopping sections every row is a buy, so the tag would
            # be on every line and mean nothing.
            buy = r.get("own") == "buy" and not shop
            body.append('<li%s>' % (' class="must"' if must else ""))
            body.append('<span class="bx"></span>')
            body.append('<div class="tx">')
            body.append('<div class="ln"><span class="it">%s</span>%s%s<span class="zn">%s</span></div>'
                        % (e(r.get("item")),
                           '<span class="tag must">!</span>' if must else "",
                           '<span class="tag buy">buy</span>' if buy else "",
                           e(r.get("zone", ""))))
            if r.get("detail"):
                body.append('<div class="wy">%s</div>' % e(r["detail"]))
            body.append("</div></li>")
        body.append("</ul></section>")

    if skipped:
        body.append('<section class="bag gone"><div class="bh"><h2>Not taking</h2>'
                    '<span class="ct">%d decided against</span></div>' % len(skipped))
        body.append('<p class="bn">Here so a decision you already made does not get made again.</p>')
        body.append('<ul class="flat">')
        for r in skipped:
            body.append('<li><span class="it">%s</span></li>' % e(r.get("item")))
        body.append("</ul></section>")

    return DOC % (len(live), len(musts), len(buys), len(skipped),
                  "\n".join(body),
                  datetime.date.today().strftime("%d %B %Y")), \
           (len(live), len(musts), len(buys), len(skipped))


DOC = """<!doctype html><html><head><meta charset="utf-8"><title>Packing list</title><style>
@page { size: Letter; margin: 14mm 13mm 16mm; }
*{box-sizing:border-box}
body{margin:0;font:10.5pt/1.4 "Liberation Sans",Helvetica,Arial,sans-serif;color:#15191f}
h1{font:600 21pt/1.05 "Liberation Serif",Georgia,serif;margin:0;letter-spacing:-.01em}
header{border-bottom:2px solid #15191f;padding-bottom:7px;margin-bottom:13px}
.sub{font:8.5pt/1.4 "Liberation Mono",monospace;letter-spacing:.09em;text-transform:uppercase;color:#5d6773;margin-top:5px}
.tiles{display:flex;gap:16px;margin:9px 0 0;font:8.5pt/1.3 "Liberation Mono",monospace;color:#5d6773}
.tiles b{display:block;font:600 14pt/1.1 "Liberation Mono",monospace;color:#15191f}
section.bag{break-inside:auto;margin-bottom:15px}
.bh{display:flex;align-items:baseline;justify-content:space-between;gap:10px;
    border-bottom:1px solid #9aa4b0;padding-bottom:3px;break-after:avoid}
.bh h2{font:600 9.5pt/1.2 "Liberation Mono",monospace;letter-spacing:.15em;text-transform:uppercase;margin:0}
.ct{font:8pt "Liberation Mono",monospace;color:#7b8694}
.bn{font-size:8.5pt;color:#5d6773;margin:3px 0 6px;break-after:avoid}
ul{list-style:none;margin:0;padding:0}
li{display:flex;gap:8px;align-items:flex-start;padding:3px 0 3px;border-bottom:.5px solid #e3e7ec;break-inside:avoid}
.bx{flex:0 0 11px;height:11px;margin-top:2px;border:1.1px solid #626c7a;border-radius:1.5px}
.tx{flex:1;min-width:0}
.ln{display:flex;align-items:baseline;gap:6px}
.it{font-weight:600;font-size:10.5pt}
li.must .it{font-weight:700}
.zn{margin-left:auto;padding-left:10px;font:7.5pt "Liberation Mono",monospace;color:#7b8694;
    white-space:nowrap;flex:0 0 auto}
.wy{font-size:8.5pt;color:#5d6773;margin-top:.5px;max-width:72ch}
.tag{font:700 6.5pt/1 "Liberation Mono",monospace;letter-spacing:.08em;text-transform:uppercase;
     padding:1.5px 3.5px;border-radius:2px;flex:0 0 auto}
.tag.must{background:#f3ded9;color:#a33526}
.tag.buy{background:#f6ead1;color:#96640a}
section.shop .bx{border-style:dashed}
section.shop .bh h2{color:#96640a}
section.gone{margin-top:6px}
section.gone .bh h2{color:#7b8694}
ul.flat{display:flex;flex-wrap:wrap;gap:0 18px}
ul.flat li{border:0;padding:1px 0;width:calc(33.333%% - 12px)}
ul.flat .it{font-weight:400;font-size:9pt;color:#7b8694;text-decoration:line-through}
footer{margin-top:12px;border-top:.5px solid #c9d0d8;padding-top:5px;
       font:7.5pt "Liberation Mono",monospace;color:#8b95a2}
</style></head><body>
<header>
<h1>Packing list</h1>
<div class="sub">China &amp; Tibet 2026 &middot; Aaron Bock &middot; 27 Sep &ndash; 16 Oct</div>
<div class="tiles">
<div><b>%d</b>to pack</div>
<div><b>%d</b>can't forget</div>
<div><b>%d</b>still to buy</div>
<div><b>%d</b>not taking</div>
</div>
</header>
%s
<footer>Printed %s &middot; ! = can't forget &middot; dashed box = bought or rented in China, not packed at home</footer>
</body></html>"""


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Build the printable packing sheet.")
    ap.add_argument("--data", required=True,
                    help="path to a trip/packing.json — fetch it live, do not reach for seed/")
    ap.add_argument("--out", default=".", help="directory for print-packing.html")
    ap.add_argument("--index", default=os.path.join(here, "index.html"),
                    help="the app, read only to check the bag list still matches")
    a = ap.parse_args()

    rows = json.load(io.open(a.data, encoding="utf-8"))["items"]
    order = app_bags(a.index)
    check_bags(order, rows)

    doc, (live, musts, buys, skipped) = build(rows, order)
    path = os.path.join(a.out, "print-packing.html")
    io.open(path, "w", encoding="utf-8").write(doc)

    filed = collections.Counter(r.get("bag") for r in rows if r.get("own") != "skip")
    print("read %s — %d rows" % (a.data, len(rows)))
    print("wrote %s — %d bytes" % (path, len(doc)))
    print("  %d to pack · %d can't forget · %d still to buy · %d not taking"
          % (live, musts, buys, skipped))
    print("  " + " · ".join("%s %d" % (b, filed[b]) for b in order if filed[b]))


if __name__ == "__main__":
    main()
