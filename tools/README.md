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

## Everything else

`rebuild_packing.py`, `extract.mjs` and `build_seeds.mjs` are one-shot migrations, kept for the
record of how the data got its current shape. They are not part of any current pipeline.
`archive/` has its own README.
