#!/usr/bin/env python3
"""trip/* -> the guide you carry: half-letter pages, two to a sheet, cut and clipped.

    ArtifactData action=list url=<artifact url> collection=trip out_dir=/tmp/fg
    python3 tools/fieldguide_pdf.py --data /tmp/fg/trip --out /tmp/fg
    node tools/render_packing_pdf.mjs /tmp/fg/print-fieldguide.html /tmp/fg/guide.pdf \\
         --landscape --margins 0,0,0,0 --footer ""

It covers what no other printed piece does. The packing list, the pocket reference
card and the point-at-this deck are already on paper and are NOT repeated here;
`ALREADY_PRINTED` says so, and the coverage guard below makes that a decision rather
than an oversight.

Shape, and why:

  HALF-LETTER, LOOSE, SINGLE-SIDED. Two 5.5 x 8.5in pages side by side on a landscape
  Letter sheet, one cut down the middle, bulldog-clipped. Loose leaves get dropped and
  reshuffled, so every page carries a number out of the total, the leg it belongs to
  and that leg's dates -- a page found on its own still says what it is. The backs are
  blank on purpose: that is the notepaper.

  A THUMB TAB steps down the outer edge, one position per section. Fan the clipped
  stack and you are at the right leg before reading a word -- the same idea as the
  band rules on the phrase cards.

  PAGINATION IS DONE IN THE BROWSER, not by CSS page breaks, because two pages share
  a sheet and CSS can only break sheets. A small script fills each page to its exact
  height and starts the next. Long prose splits between pages sentence by sentence and
  the continuation is marked; a heading is never left stranded at the foot of a page.

  DAY ROWS PRINT WHOLE. The longest is 4,722 characters and it stays 4,722 characters.
"""
import argparse, html, json, os, re, sys
from datetime import date

# ---------------------------------------------------------------- placement

LEGS = [
    ("out",      "Outbound", "27 – 29 Sep"),
    ("xian",     "Xi’an", "29 Sep – 2 Oct"),
    ("z165",     "Z165",     "2 – 3 Oct"),
    ("tibet",    "Tibet",    "3 – 10 Oct"),
    ("shanghai", "Shanghai", "10 – 12 Oct"),
    ("disney",   "Disney",   "12 – 15 Oct"),
    ("home",     "Home",     "15 – 16 Oct"),
]
LEG_BLURB = {
    "out":      "Los Angeles to Seoul to Xi’an, and a date line that eats the 28th.",
    "xian":     "Three nights at 400 m: the wall, the warriors, and the shopping run.",
    "z165":     "Thirty hours and 2,781 km, Xi’an to Lhasa over Tanggula.",
    "tibet":    "Eight days with Jeff and Kamana, and a tent night at 5,200 m.",
    "shanghai": "Land at 21:50, a night downtown, then Sunday on foot.",
    "disney":   "Three weekdays in the emptiest fortnight of the autumn.",
    "home":     "Pudong, not Hongqiao — and two separate tickets at LAX.",
}

# The order a leg lays its sources out in: how you got there, what the days hold,
# where you sleep, what to eat, what to know, and what it is like outside.
LEG_SRC = ["segments", "days", "tour", "disney", "stays", "food", "tips", "weather"]

# Sections that are not a leg, in the order they come after them.
TAIL = [
    ("kit",    "Bags and repacks",  ["kit", "repack"]),
    ("people", "People",            ["people"]),
    ("ref",    "Reference",         ["sleep", "money", "apps", "tasks"]),
]

# On paper already, by their own scripts. Not repeated here.
ALREADY_PRINTED = {
    "packing":   "tools/packing_pdf.py",
    "reference": "tools/reference_pdf.py",
    "phrases":   "tools/phrase_cards_pdf.py",
}
# Not rows at all -- the title block on page one is built out of this one.
NOT_ROWS = {"meta"}

# Deliberately not printed, keyed (document, row id, field). A string strips just
# that text out of the field; None drops the field whole. THE APP KEEPS ALL OF IT
# -- this is a print decision, and nothing here is written back to trip/*.
#
# Both of these were pages of their own: a scrap that would not fit on the page
# before it, opening a 3%-full page to hold one sentence. Cut on 21 September.
SKIP = {
    ("tips",   "tp05", "detail"): "The layover is an airport layover.",
    ("repack", "rp8",  "detail"): None,
}
_skipped = set()

BLOCK_LABEL = {
    "segments": "Getting there", "days": "Day by day", "tour": "Tour days",
    "disney": "Tickets and park", "stays": "Where you sleep", "food": "What to eat",
    "tips": "What to know", "weather": "Outside",
    "kit": "The bags", "repack": "Repacks", "people": "People",
    "sleep": "Jet lag", "money": "Money", "apps": "Apps and wallet",
    "tasks": "Still open",
}

# How a row of each document becomes a printed entry. `kick` is the mono line above
# the title; `title` the name you scan for; `meta` the short facts on one line; and
# `prose` the paragraphs, each optionally under its own label.
SPEC = {
    "segments": dict(kick=["code"], title=("from", " → ", "to"),
                     meta=["depart", "arrive", "conf"], prose=[("detail", None)]),
    "days":     dict(kick=["date"], title="title", meta=[], prose=[("detail", None)]),
    "tour":     dict(kick=["day", "date"], title="title", meta=["alt"],
                     prose=[("detail", None)]),
    "stays":    dict(kick=[], title="name", meta=["place", "checkin", "checkout", "conf"],
                     prose=[("detail", None)]),
    "disney":   dict(kick=[], title="item", meta=["price"], prose=[("detail", None)]),
    "food":     dict(kick=["when"], title="dish", meta=["where"], cn="cn",
                     prose=[("detail", None)]),
    "tips":     dict(kick=["kind"], title="tip", meta=[], prose=[("detail", None)]),
    "weather":  dict(kick=["when"], title="place", meta=["temp", "alt"],
                     prose=[("detail", None)]),
    "kit":      dict(kick=["kind"], title="name", meta=["spec"], prose=[("detail", None)]),
    "repack":   dict(kick=["step", "when"], title="title", meta=[],
                     prose=[("moves", "Moves"), ("detail", "Watch out for")]),
    "people":   dict(kick=[], title="name", meta=["role", "contact"],
                     prose=[("detail", None)]),
    "sleep":    dict(kick=["when"], title="title", meta=["target", "light"],
                     prose=[("detail", None)]),
    "money":    dict(kick=[], title="item", meta=["amount", "status"],
                     prose=[("detail", None)]),
    "apps":     dict(kick=["group"], title="item", meta=[], prose=[("detail", None)]),
    "tasks":    dict(kick=["due"], title="title", meta=["owner"], prose=[("detail", None)]),
}
# A locator is only useful if it says what it is.
PREFIX = {"conf": "Ref ", "checkin": "In ", "checkout": "Out ", "owner": "For ",
          "depart": "Dep ", "arrive": "Arr ", "alt": "", "target": "Target "}

E = html.escape


def esc(v):
    return E(str(v or "").strip())


# ---------------------------------------------------------------- rows -> flow

def row_html(doc, r):
    """One entry, as a head node plus a list of prose paragraphs.

    Head and prose are separate flow items so a long entry can run over a page
    break without the browser being asked to break a table cell.
    """
    s = SPEC[doc]
    bits = []
    kick = [esc(r.get(k)) for k in s["kick"] if str(r.get(k) or "").strip()]
    if kick:
        bits.append('<div class="kick">%s</div>' % " &middot; ".join(kick))
    t = s["title"]
    if isinstance(t, tuple):
        title = esc(r.get(t[0])) + E(t[1]) + esc(r.get(t[2]))
    else:
        title = esc(r.get(t))
    if title.strip():
        bits.append('<div class="ttl">%s</div>' % title)
    meta = []
    for k in s["meta"]:
        v = str(r.get(k) or "").strip()
        if v:
            meta.append(E(PREFIX.get(k, "")) + esc(v))
    if meta:
        bits.append('<div class="meta">%s</div>' % " &middot; ".join(meta))
    if s.get("cn") and str(r.get(s["cn"]) or "").strip():
        bits.append('<div class="cn">%s</div>' % esc(r.get(s["cn"])))
    # data-doc/data-id are for the check downstream, which matches rendered
    # nodes back to rows rather than guessing from the text.
    head = ('<div class="ent" data-doc="%s" data-id="%s">%s</div>'
            % (E(doc), esc(r.get("id")), "".join(bits)))

    prose = []
    for k, label in s["prose"]:
        v = str(r.get(k) or "").strip()
        key = (doc, str(r.get("id") or ""), k)
        if key in SKIP:
            cut_text = SKIP[key]
            if cut_text is None:
                _skipped.add(key)
                continue
            if cut_text not in v:
                sys.exit("fieldguide: SKIP wants %s/%s/%s to lose %r, and that text is\n"
                         "not in the data any more. The rule is stale -- drop it or fix it,\n"
                         "rather than leaving one in the file that does nothing."
                         % (key[0], key[1], key[2], cut_text))
            v = v.replace(cut_text, "").strip()
            _skipped.add(key)
        if not v:
            continue
        prose.append(('<p class="pr" data-doc="%s" data-id="%s" data-f="%s">%s%s</p>'
                      % (E(doc), esc(r.get("id")), E(k),
                         ('<span class="lb">%s</span>' % E(label)) if label else "", esc(v)),
                     v))
    return head, prose


def flow_for(doc, rows, want_label=True):
    out = []
    if want_label:
        out.append({"k": "sub", "h": '<h3 class="sub">%s</h3>' % E(BLOCK_LABEL[doc])})
    for r in rows:
        head, prose = row_html(doc, r)
        out.append({"k": "head", "h": head, "doc": doc, "id": r.get("id")})
        for h, raw in prose:
            out.append({"k": "prose", "h": h, "doc": doc, "id": r.get("id")})
    return out


# ---------------------------------------------------------------- page one

def page_one(meta, sections):
    p = ['<div class="t-eyebrow">Field guide &middot; carry this</div>',
         '<h1 class="t-title">%s<br><span class="t-yr">%s</span></h1>'
         % (esc(meta.get("title", "China & Tibet")), esc(meta.get("year", ""))),
         '<div class="t-by">%s &middot; %s &middot; %s</div>'
         % (esc(meta.get("traveler")), esc(meta.get("dateRange")), esc(meta.get("length"))),
         '<p class="t-sum">%s</p>' % esc(meta.get("summary"))]

    p.append('<div class="t-warn"><b>2 &ndash; 10 October</b>'
             'Eight days on the plateau with almost no contact. Silence in that window '
             'is what is supposed to happen.</div>')

    p.append('<h3 class="sub">The shape of it</h3>')
    for lid, label, dates in LEGS:
        p.append('<div class="t-leg"><span class="t-ln">%s</span>'
                 '<span class="t-ld">%s</span><span class="t-lb">%s</span></div>'
                 % (E(label), E(dates), E(LEG_BLURB[lid])))

    p.append('<h3 class="sub">Where things are</h3>')
    # One flow item: the contents list is short and must never split, or half of
    # it ends up on a page you have to find by reading the contents list.
    p.append('<div class="toc">' + "".join(
        '<div class="toc-r"><span>%s</span><b data-toc="%s">&nbsp;</b></div>'
        % (E(label), E(key)) for key, label in sections) + '</div>')

    p.append('<div class="t-else"><b>Also in the clip</b>'
             'The packing list, the pocket reference card with every locator and phone '
             'number, and the point-at-this deck. None of it is repeated here. '
             '<b>The backs of these pages are blank</b> &mdash; that is your notepaper.</div>')
    # A sub-heading is tagged as one so it is carried forward rather than left
    # at the foot of a page with its list on the next.
    return [{"k": "sub" if x.startswith('<h3 class="sub"') else "raw", "h": x} for x in p]


# ---------------------------------------------------------------- the page

CSS = r"""
@page { size: 11in 8.5in; margin: 0; }
*{box-sizing:border-box}
/* Mono laser: every value here is a true neutral, because nothing on this
   page is told apart by hue and a tinted grey only bands. */
html,body{margin:0;padding:0;background:#fff;color:#111111;
  font-family:"Liberation Sans",Arial,Helvetica,sans-serif;
  -webkit-print-color-adjust:exact; print-color-adjust:exact}

.sheet{width:11in;height:8.5in;display:flex;position:relative;
  page-break-after:always;break-after:page;overflow:hidden}
.sheet:last-child{page-break-after:auto;break-after:auto}
/* One cut per sheet, down the middle. The line runs the full height so there is
   something to follow rather than two ticks to line up by eye; under half a point
   it leaves nothing visible on either finished edge. */
.cut{position:absolute;left:5.5in;top:0;bottom:0;width:0;border-left:.4px solid #999999}

.page{width:5.5in;height:8.5in;position:relative;overflow:hidden;
  padding:.36in .52in .34in .40in}
.page.blank{}
.hd{display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:.8px solid #111111;padding-bottom:3.5px;margin-bottom:9px}
.hd .l{font:600 7.4pt "Liberation Mono",monospace;letter-spacing:.13em;text-transform:uppercase}
.hd .r{font:7pt "Liberation Mono",monospace;color:#6a6a6a}
.ft{position:absolute;left:.40in;right:.52in;bottom:.20in;
  display:flex;justify-content:space-between;align-items:baseline;
  font:7pt "Liberation Mono",monospace;color:#777777777}
.ft .n{font-weight:600;color:#111111}
/* The thumb index: one step per section, read by fanning the cut stack. */
.tab{position:absolute;right:.05in;width:.26in;background:#111111;color:#fff;
  writing-mode:vertical-rl;text-orientation:mixed;
  font:600 6.6pt "Liberation Mono",monospace;letter-spacing:.1em;text-transform:uppercase;
  display:flex;align-items:center;justify-content:center;padding:4px 0}
.flow{height:7.10in;overflow:hidden}
/* Content is measured on .inner, never on .flow: scrollHeight on a box that
   clips never reports LESS than the box, so a half-full page would measure
   as exactly full and every entry would start a new page. flow-root keeps
   the children's margins inside the measurement. */
.inner{display:flow-root}

h2.sec{font:600 15pt "Liberation Serif",Georgia,serif;margin:2px 0 1px;letter-spacing:-.01em}
.sec-d{font:7.2pt "Liberation Mono",monospace;letter-spacing:.12em;text-transform:uppercase;
  color:#6a6a6a;margin-bottom:5px}
.sec-n{font-size:8.1pt;line-height:1.36;color:#2e2e2e;margin:0 0 9px;
  border-left:2px solid #111111;padding-left:7px}
h3.sub{font:600 7.2pt "Liberation Mono",monospace;letter-spacing:.14em;text-transform:uppercase;
  color:#111111;margin:10px 0 4px;padding-bottom:2px;border-bottom:.5px solid #cccccc}
h3.sub:first-child{margin-top:0}

.ent{margin:6px 0 0}
.kick{font:600 7pt "Liberation Mono",monospace;letter-spacing:.08em;color:#6a6a6a}
.ttl{font:600 9.6pt "Liberation Serif",Georgia,serif;line-height:1.2;margin-top:.5px}
.meta{font:7.2pt "Liberation Mono",monospace;color:#585858;line-height:1.3;margin-top:1.5px}
.cn{font-family:"WenQuanYi Zen Hei","Noto Sans CJK SC",sans-serif;font-size:12pt;
  line-height:1.35;margin-top:2.5px;padding:2px 5px;border:.6px solid #111111;display:inline-block}
p.pr{font-size:8.1pt;line-height:1.4;margin:2.5px 0 0;color:#222222;
  text-align:left;hyphens:none}
p.pr .lb{font:600 6.6pt "Liberation Mono",monospace;letter-spacing:.11em;
  text-transform:uppercase;color:#6a6a6a;margin-right:5px}
p.pr.cont:before{content:"\2026 ";color:#999999}

/* page one */
.t-eyebrow{font:600 7pt "Liberation Mono",monospace;letter-spacing:.16em;text-transform:uppercase;color:#6a6a6a}
.t-title{font:600 27pt "Liberation Serif",Georgia,serif;line-height:1.02;margin:3px 0 0;letter-spacing:-.02em}
.t-yr{color:#6a6a6a}
.t-by{font:7.6pt "Liberation Mono",monospace;color:#585858;margin-top:5px}
.t-sum{font-size:8.3pt;line-height:1.42;margin:8px 0 0;color:#222222}
.t-warn{margin:9px 0 0;padding:6px 8px;background:#111111;color:#fff;font-size:7.9pt;line-height:1.38}
.t-warn b{display:block;font:600 7pt "Liberation Mono",monospace;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2px}
.t-leg{display:flex;gap:7px;align-items:baseline;flex-wrap:wrap;
  padding:3px 0;border-bottom:.4px solid #dddddd}
.t-ln{font:600 8.6pt "Liberation Serif",Georgia,serif;min-width:.82in}
.t-ld{font:7pt "Liberation Mono",monospace;color:#6a6a6a;min-width:1.05in}
.t-lb{font-size:7.6pt;color:#444444;flex:1 1 1.7in;line-height:1.3}
.toc-r{display:flex;justify-content:space-between;align-items:baseline;
  font-size:8.1pt;padding:1.6px 0;gap:6px}
.toc-r b{font:600 7.6pt "Liberation Mono",monospace}
.t-else{margin:9px 0 0;padding:6px 8px;border:.6px solid #111111;font-size:7.7pt;line-height:1.38}
.t-else b:first-child{display:block;font:600 7pt "Liberation Mono",monospace;letter-spacing:.14em;text-transform:uppercase;margin-bottom:2px}
"""

# The paginator. It runs before load fires, so the renderer needs no extra wait;
# nothing here uses a webfont, so measurement is not racing a download.
JS = r"""
(function(){
var ITEMS = window.__FLOW, SECS = window.__SECS, TABS = window.__TABS;
var host = document.getElementById("out");

function newPage(sec){
  var pg = document.createElement("div"); pg.className="page"; pg.dataset.sec=sec.key;
  var hd = document.createElement("div"); hd.className="hd";
  hd.innerHTML = '<span class="l"></span><span class="r"></span>';
  hd.querySelector(".l").textContent = sec.tab;
  hd.querySelector(".r").textContent = sec.dates || "";
  pg.appendChild(hd);
  var tab = document.createElement("div"); tab.className="tab";
  tab.textContent = sec.tab;
  var i = TABS.indexOf(sec.key);
  tab.style.top = (0.80 + i*0.66) + "in";
  tab.style.height = "0.58in";
  pg.appendChild(tab);
  var fl = document.createElement("div"); fl.className="flow";
  var inner = document.createElement("div"); inner.className="inner";
  fl.appendChild(inner);
  pg.appendChild(fl);
  var ft = document.createElement("div"); ft.className="ft";
  ft.innerHTML = '<span class="g">China &amp; Tibet 2026</span><span class="n"></span>';
  pg.appendChild(ft);
  host.appendChild(pg);
  return {pg:pg, box:fl, flow:inner};
}
function room(p){ return p.box.clientHeight - p.flow.getBoundingClientRect().height; }
function fits(p){ return room(p) >= -0.5; }

/* Sentence-level splitting, used only when a paragraph will not fit a page.
   Built by scanning rather than by a regex, because a regex that skips what it
   does not match loses characters, and this text is meant to arrive whole. The
   join check is the proof: if anything went missing, the paragraph is carried
   as one piece instead. */
function sentences(t){
  var out = [], buf = "";
  for (var i = 0; i < t.length; i++) {
    buf += t[i];
    if (".!?\u2014".indexOf(t[i]) < 0) continue;
    var j = i + 1;
    while (j < t.length && ".!?\u2014\"')]\u201d\u2019".indexOf(t[j]) >= 0) { buf += t[j]; j++; }
    if (j < t.length && /\s/.test(t[j])) {
      while (j < t.length && /\s/.test(t[j])) { buf += t[j]; j++; }
      out.push(buf); buf = "";
    }
    i = j - 1;
  }
  if (buf) out.push(buf);
  if (!out.length || out.join("") !== t) return [t];
  return out;
}

var pages = [], cur = null, curSec = null;

/* A heading, or an entry's head, left at the foot of a page is a lie about
   where the next thing starts. When something breaks to a new page, the
   headings immediately above it come too -- unless that would empty the page
   they are on, which would mean the heading does not fit anywhere. */
function carry(from, to){
  var move = [];
  while (from.flow.children.length > 1) {
    var last = from.flow.lastElementChild;
    if (last.dataset.k !== "sub" && last.dataset.k !== "head") break;
    move.unshift(last); from.flow.removeChild(last);
  }
  move.forEach(function(n){ to.flow.appendChild(n); });
}

ITEMS.forEach(function(it){
  if (it.k === "sec") {
    curSec = it.sec;
    cur = newPage(curSec); pages.push(cur);
    var h = document.createElement("div");
    h.innerHTML = it.h;
    while (h.firstChild) cur.flow.appendChild(h.firstChild);
    return;
  }
  if (!cur) { cur = newPage(curSec); pages.push(cur); }

  var node = document.createElement("div");
  node.innerHTML = it.h;
  if (node.children.length !== 1) {
    /* Every flow item must be exactly one element, or a page break could land
       inside one and lose the rest. Say so rather than paginate nonsense. */
    throw new Error("flow item is not a single element: " + it.h.slice(0, 80));
  }
  node = node.firstElementChild;
  node.dataset.k = it.k;
  cur.flow.appendChild(node);

  if (fits(cur)) return;

  cur.flow.removeChild(node);

  if (it.k === "prose") {
    /* Prose is the only thing allowed to straddle a page. Fill what is left of
       this one sentence by sentence, mark the carry-over, and go on. */
    var lb = node.querySelector(".lb");
    var label = lb ? lb.textContent : null;
    var body = lb ? node.textContent.slice(lb.textContent.length) : node.textContent;
    var parts = sentences(body), i = 0, first = true;

    while (i < parts.length) {
      var p = document.createElement("p");
      p.className = "pr" + (first ? "" : " cont");
      p.dataset.doc = node.dataset.doc; p.dataset.id = node.dataset.id;
      p.dataset.f = node.dataset.f; p.dataset.k = "prose";
      if (first && label) {
        var sp = document.createElement("span");
        sp.className = "lb"; sp.textContent = label; p.appendChild(sp);
      }
      var tn = document.createTextNode(""); p.appendChild(tn);
      cur.flow.appendChild(p);

      var taken = 0, txt = "";
      while (i + taken < parts.length) {
        var next = txt + parts[i + taken];
        tn.data = next;
        if (!fits(cur)) break;
        txt = next; taken++;
      }
      if (taken === 0) {
        if (cur.flow.children.length > 1) {
          /* Nothing of it fits here, but the page has other content: move on
             and try the whole paragraph again on a fresh one. */
          cur.flow.removeChild(p);
          var prev = cur; cur = newPage(curSec); pages.push(cur);
          carry(prev, cur);
          continue;
        }
        /* One sentence taller than an empty page. Print it rather than lose
           it -- the overflow check downstream is what reports this. */
        tn.data = parts[i]; taken = 1;
      } else {
        tn.data = txt;
      }
      i += taken; first = false;
      if (i < parts.length) { cur = newPage(curSec); pages.push(cur); }
    }
    return;
  }

  var was = cur; cur = newPage(curSec); pages.push(cur);
  carry(was, cur);
  cur.flow.appendChild(node);
});

/* Numbers, then the contents list, then two pages to a sheet. */
var total = pages.length;
pages.forEach(function(p, i){
  p.pg.querySelector(".ft .n").textContent = (i + 1) + " / " + total;
  p.pg.dataset.page = i + 1;
});
var firstOf = {};
pages.forEach(function(p, i){ if (!(p.pg.dataset.sec in firstOf)) firstOf[p.pg.dataset.sec] = i + 1; });
Array.prototype.forEach.call(document.querySelectorAll("[data-toc]"), function(b){
  b.textContent = firstOf[b.dataset.toc] != null ? String(firstOf[b.dataset.toc]) : "—";
});

var all = Array.prototype.slice.call(host.children);
host.innerHTML = "";
for (var i = 0; i < all.length; i += 2) {
  var sh = document.createElement("div"); sh.className = "sheet";
  sh.innerHTML = '<div class="cut"></div>';
  sh.appendChild(all[i]);
  if (all[i + 1]) sh.appendChild(all[i + 1]);
  else { var bl = document.createElement("div"); bl.className = "page blank"; sh.appendChild(bl); }
  host.appendChild(sh);
}
window.__pages = total;
window.__sheets = host.children.length;
})();
"""


# ---------------------------------------------------------------- build

def build(data):
    docs = {}
    for f in sorted(os.listdir(data)):
        if f.endswith(".json"):
            docs[f[:-5]] = json.load(open(os.path.join(data, f), encoding="utf-8"))

    # The coverage guard. A document added to the app later must land somewhere
    # on purpose; dropping it off a guide you are carrying instead of a phone is
    # the failure that would not be noticed until it mattered.
    placed = set(LEG_SRC) | {d for _, _, ds in TAIL for d in ds} | set(ALREADY_PRINTED) | NOT_ROWS
    stray = sorted(set(docs) - placed)
    if stray:
        sys.exit("fieldguide: %s in the data and nowhere in this script.\n"
                 "Add it to a leg (LEG_SRC), to TAIL, or to ALREADY_PRINTED -- "
                 "and give it a SPEC and a BLOCK_LABEL." % ", ".join(stray))
    missing = sorted(placed - set(docs) - set(ALREADY_PRINTED))
    if missing:
        sys.exit("fieldguide: this script places %s but the data has no such document."
                 % ", ".join(missing))
    for d in set(LEG_SRC) | {x for _, _, ds in TAIL for x in ds}:
        if d not in SPEC:
            sys.exit("fieldguide: no SPEC for %s." % d)

    # Every row of a leg source must be tagged for a leg, or it prints nowhere.
    for d in LEG_SRC:
        orphan = [r.get("id") for r in docs[d]["items"] if not str(r.get("leg") or "").strip()]
        if orphan:
            sys.exit("fieldguide: %s rows %s carry no leg and would print nowhere."
                     % (d, ", ".join(map(str, orphan))))

    meta = docs.get("meta", {})
    sections = [("trip", "The whole trip")]
    for lid, label, dates in LEGS:
        sections.append((lid, label))
    for key, label, _ in TAIL:
        sections.append((key, label))

    flow = []
    flow.append({"k": "sec", "sec": {"key": "trip", "tab": "Trip", "dates": esc(meta.get("dateRange"))},
                 "h": ""})
    flow += page_one(meta, sections)

    for lid, label, dates in LEGS:
        head = ('<h2 class="sec">%s</h2><div class="sec-d">%s</div>'
                '<p class="sec-n">%s</p>' % (E(label), E(dates), E(LEG_BLURB[lid])))
        flow.append({"k": "sec", "sec": {"key": lid, "tab": label, "dates": dates}, "h": head})
        for doc in LEG_SRC:
            rows = [r for r in docs[doc]["items"]
                    if lid in str(r.get("leg") or "").split()]
            if rows:
                flow += flow_for(doc, rows)

    for key, label, ds in TAIL:
        head = '<h2 class="sec">%s</h2><div class="sec-d">%s</div>' % (E(label), E("Reference"))
        flow.append({"k": "sec", "sec": {"key": key, "tab": label.split()[0], "dates": ""},
                     "h": head})
        for doc in ds:
            rows = docs[doc]["items"]
            if rows:
                flow += flow_for(doc, rows)

    unused = sorted(set(SKIP) - _skipped)
    if unused:
        sys.exit("fieldguide: SKIP names %s, which never came past this build.\n"
                 "The row is gone or renamed -- a rule that silently does nothing is\n"
                 "worse than no rule." % ", ".join("/".join(u) for u in unused))

    tabs = [s[0] for s in sections]
    page = ("<!doctype html>\n<html><head><meta charset=\"utf-8\">"
            "<title>China &amp; Tibet 2026 — field guide</title>\n<style>%s</style>"
            "</head><body><div id=\"out\"></div>\n<script>\n"
            "window.__FLOW=%s;\nwindow.__SECS=%s;\nwindow.__TABS=%s;\n</script>\n"
            "<script>%s</script></body></html>\n"
            % (CSS,
               json.dumps(flow, ensure_ascii=False),
               json.dumps(sections, ensure_ascii=False),
               json.dumps(tabs, ensure_ascii=False),
               JS))
    return page, flow, docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    page, flow, docs = build(a.data)
    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "print-fieldguide.html")
    open(dest, "w", encoding="utf-8").write(page)
    n = sum(1 for f in flow if f["k"] == "head")
    print("wrote %s -- %d entries, %d flow items" % (dest, n, len(flow)))


if __name__ == "__main__":
    main()
