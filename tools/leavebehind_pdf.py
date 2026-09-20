# -*- coding: utf-8 -*-
"""Build the one-page sheet to leave with family at home.

Writes print-leavebehind.html; tools/render_packing_pdf.mjs turns it into a PDF.

    ArtifactData action=list url=<artifact> collection=trip out_dir=<dir>
    python3 tools/leavebehind_pdf.py --data <dir>/trip --out <dir>
    node tools/render_packing_pdf.mjs <dir>/print-leavebehind.html <dir>/sheet.pdf

This is the only artifact here written for somebody else to read, which changes
what belongs on it. The traveller's own documents carry booking locators,
confirmation numbers and two companions' email addresses; a page that leaves his
hands carries none of them. A locator plus a surname is often enough to view or
change a booking, and nobody needs one to report a person missing.

REDACT below is that rule made mechanical. It is not a reminder to be careful --
it is checked against the finished HTML, and the script exits without writing
anything if a single forbidden string got through. Add to it whenever the data
grows a new reference number.
"""
import argparse, io, json, os, re, sys, html, datetime

e = lambda s: html.escape(str(s or ""))

# Strings that must never reach this page. Locators and confirmations first,
# then the people who did not consent to being on a sheet handed to strangers.
REDACT = [
    "FAFD77", "GBDPCB", "JP5E6A", "G3LX5Q",            # airline locators
    "84579041", "84582237",                             # Westin
    "1658114869461628", "1658114869392408",             # Trip.com
    "109750832349", "W107837385-1HMC",                  # hotel confirmations
    "UAY706135", "FUW045023",                           # Klook
    "0062450696002",                                    # ticket number
    "Margolin", "Mathur", "Rothbard",                   # companions, and Sandra
    "jamenv3d", "kamana2016", "sandra.rothbard",
    "PZC6M0", "Z322",                                   # a companion's own travel
    "step.state.gov",                                   # someone else's login lives there
]

def load(d, name):
    p = os.path.join(d, name + ".json")
    if not os.path.exists(p):
        sys.exit("missing %s — point --data at the trip/ directory of an ArtifactData dump" % p)
    return json.load(io.open(p, encoding="utf-8"))

def rows(doc):
    return doc.get("items", [])

def one(items, **kw):
    for r in items:
        if all(str(r.get(k, "")) == v for k, v in kw.items()):
            return r
    return {}

# The itinerary as a family reads it: one line per stretch, not per day.
LEGS = [
    ("Sun 27 – Tue 29 Sep", "In the air",
     "Los Angeles \u2192 Seoul \u2192 Xi'an. The 28th does not happen \u2014 it is lost crossing the date line."),
    ("Tue 29 Sep – Fri 2 Oct", "Xi'an, China", "Three days. Reachable normally."),
    ("Fri 2 – Sat 3 Oct", "On the train to Tibet",
     "Thirty hours up the Qinghai\u2013Tibet railway. Little or no signal."),
    ("Sat 3 – Sat 10 Oct", "Tibet, with a guided group",
     "Lhasa, Shigatse and Everest Base Camp with Asia Odyssey Travel. One night camped at 5,200 m."),
    ("Sat 10 – Sun 11 Oct", "Shanghai, downtown", "Reachable normally again from here."),
    ("Sun 11 – Thu 15 Oct", "Shanghai Disney Resort", ""),
    ("Thu 15 – Fri 16 Oct", "Flying home", "Landing in Atlanta early on the 16th."),
]

CONTACTS = [
    ("US State Department", "+1 202 501 4444",
     "Overseas Citizens Services. 24 hours, dialled from the US. <b>Start here</b> — lost passports, arrests, medical emergencies, welfare checks."),
    ("Asia Odyssey Travel — James Guo", "+86 177 2640 4023",
     "Runs the Tibet week and knows where the group is. WhatsApp; james@asiaodysseytravel.com. Quote AOT-BJ-James-50674."),
    ("US Consulate, Chengdu", "+86 28 8558 3992",
     "The post that covers Tibet, and the one that matters 3–10 October. 08:00–17:00 China time."),
    ("US Consulate, Shanghai", "+86 21 6433 6880", "Covers Shanghai, 10–15 October."),
    ("US Embassy, Beijing", "+86 10 8531 3000", "The national embassy, if the posts above cannot help."),
]

def build(d):
    meta = load(d, "meta")
    segs = rows(load(d, "segments"))
    stays = rows(load(d, "stays"))

    out = []
    out.append('<div class="band"><h3>If you do not hear from him between 2 and 10 October, that is expected</h3>'
               '<p>He boards a thirty-hour train on the 2nd and spends the following week on the Tibetan plateau, '
               'including a night camped at 5,200 m with no signal at all. Silence through that stretch is not a '
               'cause for concern on its own. He is with a guided group throughout and the operator below can reach '
               'them. Normal phone and internet resume when he lands in Shanghai on the evening of the 10th.</p>'
               '<p class="tz"><b>China is 12 hours ahead of Atlanta.</b> Their morning is your previous evening.</p>'
               '</div>')

    out.append('<section><h2>Where he is</h2><table class="itin">')
    for when, where, note in LEGS:
        nt = '<span class="nt">%s</span>' % e(note) if note else ''
        out.append('<tr><td class="dt">%s</td><td><b>%s</b>%s</td></tr>' % (e(when), e(where), nt))
    out.append('</table></section>')

    out.append('<div class="cols"><section><h2>Flights and trains</h2><table class="fl">')
    for s in segs:
        out.append('<tr><td class="cd">%s</td><td>%s<span class="nt">%s &rarr; %s</span></td>'
                   '<td class="ar">arrives<br><b>%s</b></td></tr>'
                   % (e(s.get("code")), e(s.get("depart")), e(s.get("from")), e(s.get("to")), e(s.get("arrive"))))
    out.append('</table></section>')

    ADDR = {
        "The Westin Xi'an": ("66 Ci En Road, Qujiang New District, Xi'an", "+86 29 6568 6568"),
        "Metropolo Nanjing Road Nanjing Hotel": ("200 Shanxi South Road, Huangpu, Shanghai", "+86 21 6322 2888"),
        "Toy Story Hotel": ("360 Shendi West Road, Pudong, Shanghai", "+86 21 2099 8003"),
    }
    out.append('<section><h2>Where he is sleeping</h2><table class="fl">')
    seen = set()
    for s in stays:
        n = s.get("name", "")
        base = n.replace(" · award night", "")
        if base in seen:
            continue
        seen.add(base)
        if base in ADDR:
            addr, tel = ADDR[base]
            out.append('<tr><td colspan="2"><b>%s</b><span class="nt">%s</span></td><td class="ar">%s</td></tr>'
                       % (e(base), e(addr), e(tel)))
        else:
            out.append('<tr><td colspan="3"><b>%s</b><span class="nt">%s — booked through Asia Odyssey Travel; '
                       'the operator below holds the hotel list.</span></td></tr>'
                       % (e(base), e(s.get("place"))))
    out.append('</table></section></div>')

    out.append('<section><h2>Reaching him</h2><p class="reach">'
               '<b>WhatsApp is the one that works.</b> His phone runs a foreign eSIM, so messages and calls go '
               'through on cellular data — but <b>not on Chinese hotel Wi-Fi</b>, which sits inside the national '
               'firewall and blocks it. If a message will not send, that is usually why. Email reaches him too: '
               'bock.aaron@gmail.com.</p>'
               '<p class="reach">WhatsApp number: <span class="rule"></span></p></section>')

    out.append('<section><h2>If something is wrong</h2><table class="ct">')
    for name, num, note in CONTACTS:
        out.append('<tr><td><b>%s</b><span class="nt">%s</span></td><td class="ph">%s</td></tr>'
                   % (e(name), note, e(num)))
    out.append('</table></section>')

    # str.replace rather than %-formatting: the stylesheet is full of literal
    # percent signs (width:100%) and doubling every one of them is a trap that
    # only shows up the next time someone edits the CSS.
    return (TPL.replace("{{WHO}}",   e(meta.get("traveler")))
               .replace("{{DATES}}", e(meta.get("dateRange")))
               .replace("{{BODY}}",  "\n".join(out))
               .replace("{{PRINTED}}", datetime.date.today().strftime("%d %B %Y")))

TPL = """<!doctype html><html><head><meta charset="utf-8"><title>While I am away</title><style>
@page { size: Letter; margin: 11mm 12mm 9mm; }
*{box-sizing:border-box}
body{margin:0;font:8.7pt/1.27 "Liberation Sans",Helvetica,Arial,sans-serif;color:#15191f}
header{border-bottom:2px solid #15191f;padding-bottom:5px;margin-bottom:8px;
       display:flex;align-items:baseline;justify-content:space-between;gap:12px}
h1{font:600 19pt/1 "Liberation Serif",Georgia,serif;margin:0;letter-spacing:-.01em}
.who{font:8pt "Liberation Mono",monospace;letter-spacing:.08em;text-transform:uppercase;color:#5d6773;text-align:right}
h2{font:600 8.5pt/1.2 "Liberation Mono",monospace;letter-spacing:.15em;text-transform:uppercase;
   margin:0 0 4px;padding-bottom:2px;border-bottom:1px solid #9aa4b0}
section{margin-bottom:7px}
.band{border:1.4px solid #a33526;border-left-width:4px;border-radius:3px;padding:6px 9px;margin-bottom:8px;background:#fbf2f0}
.band h3{font:700 10pt/1.22 "Liberation Sans",Helvetica,sans-serif;margin:0 0 3px;color:#8d2d20}
.band p{margin:0;font-size:8.3pt;line-height:1.3}
.band .tz{margin-top:4px;font-size:8.5pt;color:#5d6773}
table{width:100%;border-collapse:collapse}
td{vertical-align:top;padding:2.1px 0;border-bottom:.5px solid #e3e7ec}
tr:last-child td{border-bottom:0}
.nt{display:block;font-size:7.6pt;color:#5d6773;line-height:1.26}
.itin .dt{width:126px;font:7.7pt "Liberation Mono",monospace;color:#15191f;padding-right:8px;white-space:nowrap}
.cols{display:flex;gap:16px;margin-bottom:7px}
.cols>section{flex:1;min-width:0;margin-bottom:0}
.fl .cd{width:52px;font:600 8.5pt "Liberation Mono",monospace;white-space:nowrap}
.fl .ar{width:104px;text-align:right;font-size:7.6pt;color:#5d6773;line-height:1.25;white-space:nowrap}
.fl .ar b{font:600 8pt "Liberation Mono",monospace;color:#15191f}
.ct .ph{width:130px;text-align:right;font:600 9.5pt "Liberation Mono",monospace;white-space:nowrap}
.reach{margin:0 0 3px;font-size:8.3pt}
.rule{display:inline-block;width:150px;border-bottom:1px solid #626c7a;height:.9em}
footer{margin-top:8px;border-top:.5px solid #c9d0d8;padding-top:4px;
       font:7.2pt "Liberation Mono",monospace;color:#8b95a2;display:flex;justify-content:space-between}
</style></head><body>
<header>
  <div><h1>While I am away</h1></div>
  <div class="who">{{WHO}}<br>China &amp; Tibet &middot; {{DATES}}</div>
</header>
{{BODY}}
<footer><span>Printed {{PRINTED}}</span><span>No booking references on this page, by design</span></footer>
</body></html>"""

def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Build the one-page leave-behind sheet.")
    ap.add_argument("--data", required=True,
                    help="the trip/ directory of a live ArtifactData dump — not seed/")
    ap.add_argument("--out", default=".", help="directory for print-leavebehind.html")
    a = ap.parse_args()

    doc = build(a.data)

    # The redaction list is enforced, not trusted. Nothing is written on a hit.
    hits = sorted({s for s in REDACT if s.lower() in doc.lower()})
    if hits:
        sys.exit("leavebehind_pdf: REFUSING TO WRITE — these must never appear on a page that "
                 "leaves his hands:\n  " + "\n  ".join(hits))

    path = os.path.join(a.out, "print-leavebehind.html")
    io.open(path, "w", encoding="utf-8").write(doc)
    print("read %s" % a.data)
    print("wrote %s — %d bytes" % (path, len(doc)))
    print("  redaction check clean: %d forbidden strings, none present" % len(REDACT))

if __name__ == "__main__":
    main()
