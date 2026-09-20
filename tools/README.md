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

## The pocket reference card

`reference_pdf.py` makes the one-page card from `trip/reference` — consulates, card lines,
booking locators, the channels that actually sell tickets, and the three things that are a problem
at a Tibetan checkpoint. The app's own note for that document calls it "the page to print and fold
into a passport", which is exactly what this is.

```
ArtifactData action=get url=<artifact url> collection=trip doc_id=reference out_dir=/tmp/ref
python3 tools/reference_pdf.py --data /tmp/ref/trip/reference.json --out /tmp/ref
node tools/render_packing_pdf.mjs /tmp/ref/print-reference.html /tmp/ref/card.pdf \
     --max-pages 1 --margins 12mm,12mm,10mm,12mm --footer ""
```

### It is the opposite of the leave-behind sheet

The two scripts sit next to each other and are easy to confuse. **The leave-behind sheet goes to
other people and is redacted; this card goes in the traveller's own pocket and exists to carry the
locators.** Do not copy `REDACT` into this one, and do not drop the locators from it — they are
the reason it exists.

Still absent here, because they are not in the data: the Trip.com booking PINs (the rows say where
they live instead) and the STEP login on the shared Drive sheet, which belongs to someone else.

Two columns, split by how you reach for it: people and places you contact on the left, strings you
read out on the right. Add a new `group` to the data and the build stops until you place it in
`LEFT`, `RIGHT` or `FULL` — silently dropping a group off a card you are carrying instead of your
phone would be the worst kind of failure here.

## Point-at-this cards

`phrase_cards_pdf.py` turns `trip/phrases` into bilingual cards to print and cut out, six to a
Letter sheet — 48 cards on 8 sheets, 3.75in × 3.33in each. Signed off 20 September after a mock;
**black and white throughout**, for a mono laser.

```
ArtifactData action=get url=<artifact url> collection=trip doc_id=phrases out_dir=/tmp/cards
python3 tools/phrase_cards_pdf.py --data /tmp/cards/trip/phrases.json --out /tmp/cards
node tools/render_packing_pdf.mjs /tmp/cards/print-cards.html /tmp/cards/cards.pdf \
     --margins 12.7mm,12.7mm,12.7mm,12.7mm --footer ""
```

`--ids p11,p38,p02` builds a mock sheet **through the same code as the full deck**, so what gets
approved is what gets printed. Pick the awkward rows, not the first few: the shortest Chinese, the
longest, a slash, a long note.

### The design decisions worth not undoing

- **The Chinese is the card.** A stranger reads it at arm's length; the English exists so you can
  find the right card in a stack. Size flexes with length — 54px for two characters, 20px for the
  thirty-character Metropolo address — because one fixed size suits neither end.
- **Cards butt together and the hairline border is the cut line.** Two cuts across, one down.
- **Nothing depends on colour.** The sheet is black, white and two greys, and a check over the
  rendered page asserts no non-grey value is painted anywhere. Legs are told apart by RULE STYLE
  AND WEIGHT — solid, dashed, dotted, double, thin, thick — because eight greys would band and
  drift on a laser and two adjacent ones would be indistinguishable. The leg NAME is printed in the
  band regardless: the rule is what you see fanning the deck, the name is what you read holding the
  card.
- **`DANGER` marks cards that must never be held up.** Right now that is `p20`, the wrong Xi'an
  station, carried only so the name can be recognised when a driver proposes it. In mono the
  loudest thing available is inversion, so it gets a 2px border, a solid band, the Chinese struck
  through, and the warning white out of solid black. A destination card that loses you the Z165 if
  shown by mistake is the one thing on this sheet that must not look like every other card — and it
  prints next to the correct station, so the pair reads together.

## Everything else

`render_packing_pdf.mjs` renders both sheets; its name predates the second one.

`rebuild_packing.py`, `extract.mjs` and `build_seeds.mjs` are one-shot migrations, kept for the
record of how the data got its current shape. They are not part of any current pipeline.
`archive/` has its own README.
