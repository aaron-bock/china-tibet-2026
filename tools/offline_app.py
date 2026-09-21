#!/usr/bin/env python3
"""index.html + a live trip/* dump -> one self-contained file that works with the radio off.

    ArtifactData action=list url=<artifact url> collection=trip out_dir=/tmp/off
    python3 tools/offline_app.py --data /tmp/off/trip --out /tmp/off

index.html IS NOT MODIFIED. The artifact stays the source of truth and this copy is
regenerated from it; there is no second version of the app to keep in step by hand.

Two things tie the app to the network and both are replaced here:

  1. The three Google Fonts <link>s at the top. Faces are fetched and written back
     inline as base64 woff2. A FETCH FAILURE FAILS THE BUILD -- a half-embedded file
     looks right on this machine and falls back to Times on the phone, which is the
     one outcome nobody would notice until it mattered. --no-fonts is the explicit
     way to take the system stack instead.

  2. The boot block, which asks window.claude for a database. The replacement bakes
     the data in and keeps edits in localStorage. It hands `db` an object with the
     same .doc().set() shape the app already calls, so queue()/flush() and every
     call site above them are untouched.

Both regions are found by exact text. If either anchor has moved, THE BUILD STOPS and
names it -- a silently unpatched output would be an offline copy that is not offline.
"""
import argparse, base64, json, os, re, sys, urllib.request
from datetime import date

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Only the subsets the app's own text uses. Cyrillic, Greek and the maths block
# would triple the file to render characters that appear nowhere in the trip.
SUBSETS = ("latin", "latin-ext")

FONT_LINKS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:opsz,wght@6..96,400;6..96,600&family=Public+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">"""

FONT_CSS_URL = re.search(r'href="([^"]+css2[^"]+)"', FONT_LINKS).group(1)

BOOT = '''if(window.claude && typeof window.claude.use==="function"){
  window.claude.use("downloads").then(function(d){ dl=d; }).catch(function(){});
  window.claude.use("db").then(function(d){
    if(!d){ noData(); return; }
    db=d;
    d.collection("trip").onSnapshot(function(snap){
      snap.docs.forEach(function(doc){ store[doc.id]=doc.data()||{}; });
      if(snap.empty && !booted){
        $("#main").innerHTML='<div class="boot"><b>Nothing stored yet</b>'+
          'The trip records have not been written to this page.</div>';
        return;
      }
      render();
    },function(e){
      saver("error",(e&&e.code==="revoked")?"Read only":"Sync lost");
    });
  }).catch(function(){ noData(); });
} else { noData(); }'''

STYLE_END = "</style>\n\n<header class=\"mast\">"
SHEET_FOOT = '''    <div class="sheet-foot">
      <span class="sheet-msg" id="sheetMsg"></span>
      <button class="btn" id="closeExport">Close</button>'''
FOOT_COPY = "Edits save for everyone who opens this page."


# ---------------------------------------------------------------- fonts

def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": UA}), timeout=45).read()


def font_css():
    """The css2 stylesheet, with every woff2 inlined as a data: URI.

    Bodoni Moda and Public Sans are variable fonts: Google serves ONE file for all
    the weights asked for. Emitting it once per weight would write the same 46 KB
    three times, so faces sharing a URL are merged into a single rule with a weight
    RANGE, which is what a variable font wants anyway. IBM Plex Mono is static and
    genuinely has a file per weight; it is not merged.
    """
    try:
        css = fetch(FONT_CSS_URL).decode("utf-8")
    except Exception as e:
        sys.exit("offline: could not reach Google Fonts (%s).\n"
                 "Fix the network or pass --no-fonts to take the system stack." % e)

    blocks = re.findall(r"/\* (\S+) \*/\s*(@font-face \{.*?\})", css, re.S)
    if not blocks:
        sys.exit("offline: the Google Fonts stylesheet had no @font-face rules in it.")

    faces, order = {}, []
    for subset, block in blocks:
        if subset not in SUBSETS:
            continue
        fam = re.search(r"font-family: '([^']+)'", block).group(1)
        weight = int(re.search(r"font-weight: (\d+);", block).group(1))
        style = re.search(r"font-style: (\S+);", block).group(1)
        url = re.search(r"url\((\S+?)\)", block).group(1)
        rng = re.search(r"unicode-range: ([^;]+);", block)
        key = (fam, style, url)
        if key not in faces:
            faces[key] = {"weights": [], "range": rng.group(1) if rng else None}
            order.append(key)
        faces[key]["weights"].append(weight)

    if not faces:
        sys.exit("offline: no %s faces in the stylesheet -- the subset names changed."
                 % " or ".join(SUBSETS))

    out, total = [], 0
    for key in order:
        fam, style, url = key
        f = faces[key]
        try:
            raw = fetch(url)
        except Exception as e:
            sys.exit("offline: %s %s failed to download (%s). Nothing written."
                     % (fam, f["weights"], e))
        if raw[:4] != b"wOF2":
            sys.exit("offline: %s came back as something other than woff2." % fam)
        total += len(raw)
        lo, hi = min(f["weights"]), max(f["weights"])
        out.append(
            "@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:swap;\n"
            "src:url(data:font/woff2;base64,%s) format('woff2');%s}"
            % (fam, style, ("%d %d" % (lo, hi)) if lo != hi else str(lo),
               base64.b64encode(raw).decode("ascii"),
               ("unicode-range:%s;" % f["range"]) if f["range"] else ""))

    sys.stderr.write("offline: embedded %d faces, %d KB of woff2\n"
                     % (len(out), total // 1024))
    return ("<style>\n/* Google Fonts, fetched and embedded at build time. No network\n"
            "   request is made for these -- see tools/offline_app.py. */\n"
            + "\n".join(out) + "\n</style>")


# --no-fonts needs no substitute stack: --f-disp, --f-body and --f-mono in the
# app's own :root already fall back to Georgia, -apple-system and ui-monospace.
# Overriding them here would only be wrong, since this lands ABOVE that rule.
NO_FONTS = ("<!-- Built with --no-fonts: Bodoni Moda, Public Sans and IBM Plex Mono are\n"
            "     not embedded. The stacks in :root below fall back on their own. -->")


# ---------------------------------------------------------------- the shim

def shim(seed, pulled):
    return '''/* ---------- offline boot ----------
   Written by tools/offline_app.py. The artifact asked window.claude for a
   database; this file carries one, pulled %(pulled)s, and keeps whatever you
   change in this browser's own storage. Nothing here reaches the shared page.

   `db` below has the same .doc(path).set(body) shape the app already calls, so
   queue(), flush() and every edit above them are exactly as they are online. */
var SEED = %(seed)s;
var PULLED = "%(pulled)s";
var LKEY = "ct26-offline";

function localAll(){
  try{ var raw=localStorage.getItem(LKEY); return raw?(JSON.parse(raw)||{}):{}; }
  catch(_){ return {}; }
}
function localWrite(id,body){
  var all=localAll(); all[id]=body;
  try{ localStorage.setItem(LKEY,JSON.stringify(all)); return true; }catch(_){ return false; }
}

db = { doc: function(path){
  var id=String(path).replace(/^trip\\//,"");
  return { set: function(body){
    /* A full storage quota is the one way this can fail, and it must not fail
       silently -- the chip has to stop saying Saved. */
    return localWrite(id,body) ? Promise.resolve()
         : Promise.reject({code:"quota"});
  } };
} };

/* Downloads offline: a Blob and a synthetic click. doExport() is untouched --
   it only needs something with .save({filename,data}) that returns a promise. */
dl = { save: function(o){
  try{
    var b=new Blob([o.data],{type:"text/plain;charset=utf-8"});
    var a=document.createElement("a");
    a.href=URL.createObjectURL(b); a.download=o.filename;
    document.body.appendChild(a); a.click();
    setTimeout(function(){ URL.revokeObjectURL(a.href); a.remove(); },0);
    return Promise.resolve();
  }catch(e){ return Promise.reject(e); }
} };

/* "Saved" online means saved for everyone. Here it means saved on this phone,
   and the difference is the whole point of the file. */
saver = (function(orig){
  return function(s,msg){
    if(msg==null && s==="saved") msg="Saved on this device";
    if(msg==null && s==="error") msg="Not saved \\u2014 storage full";
    orig(s,msg);
  };
})(saver);

Object.keys(SEED).forEach(function(k){ store[k]=SEED[k]; });
var over=localAll();
Object.keys(over).forEach(function(k){ store[k]=over[k]; });
render();

(function(){
  var note=document.getElementById("offlineNote"), hide=document.getElementById("offlineHide");
  var NKEY="ct26-offline-note";
  try{ if(localStorage.getItem(NKEY)==="hidden" && note) note.hidden=true; }catch(_){}
  if(hide) hide.addEventListener("click",function(){
    if(note) note.hidden=true;
    try{ localStorage.setItem(NKEY,"hidden"); }catch(_){}
  });
  var reset=document.getElementById("resetLocal");
  if(reset) reset.addEventListener("click",function(){
    var n=Object.keys(localAll()).length;
    if(!n){ document.getElementById("sheetMsg").textContent="Nothing to forget \\u2014 this is the copy as pulled."; return; }
    if(!window.confirm("Throw away every change made on this device and go back to the copy pulled "
       +PULLED+"?\\n\\nThis cannot be undone. Download the data backup first if you want to keep them."))
      return;
    try{ localStorage.removeItem(LKEY); }catch(_){}
    location.reload();
  });
})();''' % {"seed": seed, "pulled": pulled}


BANNER = '''<div class="wrap">
  <div class="offline-note" id="offlineNote">
    <b>Offline copy &middot; pulled {PULLED}</b>
    <span>This works with the radio off, and it is yours alone: ticks and edits save to this
    device and never reach the shared page. To bring them home, use Download &rarr; Data backup.</span>
    <button type="button" class="off-x" id="offlineHide" aria-label="Hide this note">&times;</button>
  </div>
</div>
'''

BANNER_CSS = '''
/* ---------- offline copy ---------- */
.offline-note{
  display:flex; flex-wrap:wrap; align-items:baseline; gap:4px 10px; position:relative;
  margin:14px 0 0; padding:11px 40px 11px 13px; border-radius:7px;
  background:var(--saffron-wash); border:1px solid var(--line);
  font-size:12.5px; line-height:1.5; color:var(--soft);
}
.offline-note b{
  font-family:var(--f-mono); font-size:10px; letter-spacing:.13em; text-transform:uppercase;
  color:var(--saffron); white-space:nowrap;
}
.offline-note .off-x{
  position:absolute; top:6px; right:8px; border:0; background:transparent;
  font-size:17px; line-height:1; color:var(--faint); padding:4px 6px; cursor:pointer;
}
.offline-note[hidden]{display:none}
@media print{ .offline-note{display:none!important} }
'''


# ---------------------------------------------------------------- build

def cut(src, anchor, what, replacement):
    n = src.count(anchor)
    if n != 1:
        sys.exit("offline: the %s anchor appears %d times in index.html, expected once.\n"
                 "It has been edited since this script was written -- update the anchor\n"
                 "rather than shipping a copy that is not actually offline." % (what, n))
    return src.replace(anchor, replacement)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="directory of trip/*.json from a live pull")
    ap.add_argument("--app", default="index.html")
    ap.add_argument("--out", default=".")
    ap.add_argument("--no-fonts", action="store_true",
                    help="skip font embedding and use the system stack")
    a = ap.parse_args()

    src = open(a.app, encoding="utf-8").read()

    files = sorted(f for f in os.listdir(a.data) if f.endswith(".json"))
    if not files:
        sys.exit("offline: no JSON in %s. Pull trip/* live first." % a.data)
    seed = {}
    for f in files:
        seed[f[:-5]] = json.load(open(os.path.join(a.data, f), encoding="utf-8"))
    sys.stderr.write("offline: baking in %d documents, %d rows\n"
                     % (len(seed), sum(len(d.get("items", [])) for d in seed.values())))

    pulled = date.today().strftime("%-d %B %Y")

    # Check every anchor first. Finding out the boot block moved AFTER a minute
    # of font downloads is a worse way to learn it.
    for anchor, what in ((FONT_LINKS, "font <link>"), (BOOT, "boot block"),
                         (STYLE_END, "stylesheet end"), ("</header>\n", "header close"),
                         ("<style>\n:root{", "stylesheet start"),
                         (SHEET_FOOT, "download sheet footer"), (FOOT_COPY, "footer copy")):
        cut(src, anchor, what, anchor)

    src = cut(src, FONT_LINKS, "font <link>",
              NO_FONTS if a.no_fonts else font_css())
    src = cut(src, BOOT, "boot block",
              shim(json.dumps(seed, ensure_ascii=False, separators=(",", ":")), pulled))
    src = cut(src, STYLE_END, "stylesheet end", BANNER_CSS + STYLE_END)
    src = cut(src, "</header>\n", "header close",
              "</header>\n" + BANNER.replace("{PULLED}", pulled))
    src = cut(src, SHEET_FOOT, "download sheet footer",
              SHEET_FOOT.replace(
                  '<button class="btn" id="closeExport">Close</button>',
                  '<button class="btn" id="resetLocal" title="Go back to the copy as pulled">'
                  'Forget my offline edits</button>\n'
                  '      <button class="btn" id="closeExport">Close</button>'))
    src = cut(src, FOOT_COPY, "footer copy",
              "This is an offline copy pulled " + pulled +
              ". Edits save to this device only — the shared page is still the one "
              "everyone else sees.")

    # The artifact runtime supplies the document wrapper; a file opened from disk
    # has none, and without the charset the em dashes and the Chinese come out wrong.
    head = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<meta name="color-scheme" content="light dark">\n'
            '<meta name="apple-mobile-web-app-capable" content="yes">\n'
            '<meta name="mobile-web-app-capable" content="yes">\n')
    src = cut(src, "<style>\n:root{", "stylesheet start", "</head>\n<body>\n<style>\n:root{")
    src = head + src + "\n</body>\n</html>\n"

    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "China-Tibet-2026-offline.html")
    open(dest, "w", encoding="utf-8").write(src)
    print("wrote %s -- %d KB" % (dest, len(src.encode("utf-8")) // 1024))


if __name__ == "__main__":
    main()
