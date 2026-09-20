# Tooling

## The printable packing sheet

`packing_pdf.py` + `render_packing_pdf.mjs` make the Letter-size sheet you actually carry:
one checkbox per item, grouped by the bag it rides in, `!` on the ones you can't forget,
dashed checkboxes for the two sections you buy or rent in China, and the "Not taking" list
at the end so a decision already made doesn't get made twice.

The app is the source of truth. Fetch live data first — **do not build from `seed/`**, which
is a mirror and lags:

```
# 1. pull trip/packing out of the live artifact
ArtifactData action=get url=<artifact url> collection=trip doc_id=packing out_dir=/tmp/pk

# 2. build the HTML (aborts if the bag list has drifted — see below)
python3 tools/packing_pdf.py --data /tmp/pk/trip/packing.json --out /tmp/pk

# 3. render it, from a directory that has playwright installed
node tools/render_packing_pdf.mjs /tmp/pk/print-packing.html /tmp/pk/China-Tibet-2026-packing-list.pdf
```

The PDF is a build output and is not committed.

### Why `--data` has no default

The first version of this pipeline lived outside the repo and read a snapshot path baked into
line 4 of the script. By the time anyone looked at the printed sheet again it was six rows and
eleven bag moves behind the app, with nothing anywhere saying so. Requiring the path means the
question "is this data current?" gets asked every time.

### The bag guard

`packing_pdf.py` holds its own short print notes for each bag — shorter than the app's on
purpose, because a sheet is scanned and a page is read. Those are print copy. The bag *names*,
though, are checked against `var BAGS=[…]` in `index.html` and against the bags present in the
data, in all three directions. A bag added to the app, renamed, or retired stops the build with
a message naming it, rather than silently dropping those items off the sheet.

## The leave-behind sheet

`leavebehind_pdf.py` makes the one-page sheet you hand to family before you go: where you are,
which flights, which hotels, and who to call. It leads with the fact that matters most to someone
at home — that 2–10 October is a week with almost no contact, and that silence then is expected.

```
ArtifactData action=list url=<artifact url> collection=trip out_dir=/tmp/lb
python3 tools/leavebehind_pdf.py --data /tmp/lb/trip --out /tmp/lb
node tools/render_packing_pdf.mjs /tmp/lb/print-leavebehind.html /tmp/lb/sheet.pdf \
     --max-pages 1 --margins 11mm,12mm,9mm,12mm --footer ""
```

### It is redacted, and the redaction is enforced

This is the only output here written for someone else to read, and it leaves the traveller's
hands. No booking locators, no confirmation numbers, no companions' contact details. A locator
plus a surname is often enough to view or change a booking, and nobody needs one to report a
person missing.

`REDACT` at the top of the script is that rule made mechanical: the finished HTML is searched for
every forbidden string and **nothing is written if one got through**. Add to the list whenever the
data grows a new reference number. "I was careful" is not a mechanism.

### One page is a build constraint

`--max-pages 1` deletes the output and fails rather than shipping two pages. Chromium paginates a
little tighter than a viewport measurement suggests, so the boundary is easy to cross while
editing copy — this catches it. `--margins` must match the `@page` rule in the generating script,
or Chromium's own margins silently win.

## Everything else

`render_packing_pdf.mjs` renders both sheets; its name predates the second one.

`rebuild_packing.py`, `extract.mjs` and `build_seeds.mjs` are one-shot migrations, kept for the
record of how the data got its current shape. They are not part of any current pipeline.
`archive/` has its own README.
