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

### Printing on coloured card stock

`--all-stocks` writes **one file per colour**, because "print pages 2–3 on blue" is the instruction
that goes wrong at a printer. Load a stock, print its file, done — no sheet can mix colours because
no file contains two.

| Stock | What's on it | Legs | Cards | Sheets |
|---|---|---|---|---|
| White | Everyday | All legs + Outbound | 6 | 1 |
| Blue | Xi'an | Xi'an | 12 | 2 |
| Green | Train & Tibet | Z165 + Tibet | 18 | 3 |
| Yellow | Shanghai | Shanghai | 8 | 2 |
| Pink | Disney & home | Disney + Home | 4 | 1 |

Eight legs merged to five so that three groups land exactly on a six-card sheet boundary; splitting
Tibet off the train or Disney off the flight home costs two extra sheets for nothing. **White takes
the everyday cards** — highest-contrast stock to the most-handled cards, not the most important
ones. Legs stay distinguishable inside a colour by their band rule, so green tells Z165 from Tibet.

Two invariants the build enforces rather than trusts:

- **Card numbers are assigned once, globally, before the split** — 1–48 in trip order. They are how
  a shuffled deck is sorted again, so they must mean the same thing on every colour. Restarting at
  1 per stock would quietly destroy that.
- **`--all-stocks` fails if `STOCK` does not cover every card.** A leg renamed in the data would
  otherwise drop part of the deck on the floor silently.

Spare slots print as **write-your-own cards** — band, cut border, ruled lines — rather than empty
rectangles. Six of them, on yellow and pink.

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

## The field guide

`fieldguide_pdf.py` makes the thing you actually carry: everything in the app that no
other printed piece covers, on half-letter pages, two to a sheet, cut and clipped.
Seventeen Letter sheets, thirty-four pages.

```
ArtifactData action=list url=<artifact url> collection=trip out_dir=/tmp/fg
python3 tools/fieldguide_pdf.py --data /tmp/fg/trip --out /tmp/fg
node tools/render_packing_pdf.mjs /tmp/fg/print-fieldguide.html /tmp/fg/guide.pdf \
     --landscape --margins 0,0,0,0 --footer ""
```

Print single-sided, cut each sheet once down the hairline at the middle, clip. **The backs stay blank on
purpose** — that is the notepaper, and page one says so.

### It carries the locators

Like the pocket reference card and unlike the leave-behind sheet: this goes in the
traveller's own bag, so flight refs and hotel confirmations are printed. Do not copy
`REDACT` into it.

### Loose leaves decide the design

There is no fold and no facing spread, so every page has to survive being dropped on its
own. Each carries **`n / N`**, the section it belongs to, and that leg's dates; a **thumb
tab** steps down the outer edge, one position per section, so a fanned stack lands on the
right leg before you read anything. The tab is inset 0.05in from the page edge — a cut
that wanders should not shave it.

### Pagination is done in the browser, not by CSS

Two pages share a sheet and CSS page breaks can only break *sheets*, so a script fills each
page to its measured height and starts the next. Three things that were learned the hard
way and should not be undone:

- **Height is measured on `.inner`, never on `.flow`.** `scrollHeight` on a box that clips
  never reports less than the box itself, so a half-empty page measures as exactly full.
  The first build of this made 203 pages instead of 36.
- **Prose is the only thing allowed to straddle a break**, sentence by sentence, and the
  carry-over is marked with a leading `…`. The splitter is a scanner with a join check
  rather than a regex: a regex skips what it does not match, and the first one silently
  dropped sixteen characters out of a day row. Day rows print **whole** — the longest is
  4,629 characters and stays that way.
- **A heading never ends a page.** When anything breaks, the headings immediately above it
  are carried along.

### `SKIP`, and why it is enforced

Two paragraphs are deliberately not printed: the last sentence of `tips/tp05` and the whole
"Watch out for" on `repack/rp8`. Each was a **page of its own** — a scrap that would not fit
on the page before it, so the paginator opened a 3%-full page to hold one sentence. Cut on
21 September, on the traveller's call. **The app keeps both**; this is a print decision and
nothing here writes to `trip/*`.

`SKIP` is keyed `(document, row id, field)`: a string strips just that text, `None` drops the
field. The build fails if a skip's text is no longer in the data, and fails if a skip never
fires at all — a rule sitting in the file doing nothing is worse than no rule, because it
reads as though the text is still being removed.

### The coverage guard

Every document in `trip/*` must be placed: on a leg (`LEG_SRC`), in `TAIL`, in
`ALREADY_PRINTED`, or in `NOT_ROWS`. **A stray one stops the build**, and so does a leg
source with a row that carries no `leg` tag — which would otherwise print nowhere at all.
Dropping a section off a guide you are carrying *instead of* your phone is the failure
nobody would notice until it mattered.

`ALREADY_PRINTED` is the list of what the other scripts here cover — packing, reference,
phrases — and the check asserts none of it leaks back in.

### Mono, and neutral

Every value in the stylesheet is a true grey. Nothing here is told apart by hue, and a
tinted grey only bands on a laser; the check asserts no channel spread anywhere on the
rendered page.

## The offline copy of the app

`offline_app.py` turns `index.html` plus a live dump into one file that works on a phone
with the radio off. **`index.html` is not modified** — the artifact stays the source of
truth and this is regenerated from it, so there is no second copy of the app to keep in
step by hand.

```
ArtifactData action=list url=<artifact url> collection=trip out_dir=/tmp/off
python3 tools/offline_app.py --data /tmp/off/trip --out /tmp/off
```

Two things tie the app to the network and both are replaced:

- **The Google Fonts `<link>`.** The faces are fetched and written back as base64 woff2,
  latin and latin-ext only. Bodoni Moda and Public Sans are variable — Google serves one
  file for every weight asked for — so faces sharing a URL are merged into a single rule
  with a weight *range* rather than embedding the same 46 KB three times. 448 KB all in.
- **The boot block.** `db` is replaced with an object of the same `.doc(path).set(body)`
  shape, writing `localStorage["ct26-offline"]`, so `queue()`, `flush()` and every edit
  above them are exactly what they are online. `dl` becomes a Blob and a synthetic click,
  which keeps the whole Download sheet working — and the JSON export is how edits made on
  the road come home.

### A failed font fetch fails the build

`--no-fonts` is the explicit way to take the system stack. What must never happen is a
half-embedded file: it looks right on the machine that built it and falls back to Times on
the phone, which is exactly the kind of thing nobody notices until they are somewhere
without a network.

### The anchor guard

Six regions are found by exact text and rewritten. **Every anchor is checked before a
single font is downloaded**, and a miss stops the build naming the region. An
unpatched output would be an offline copy that is not offline.

### It says what it is, three times

The banner, the saver chip ("Saved on this device", never "Saved") and the page footer all
say the same thing: edits live on this phone and never reach the shared page. The two will
drift, and the file should not pretend otherwise. **"Forget my offline edits"** in the
Download sheet is the only way back to the baked-in copy, so it has to be discoverable.

## Everything else

`render_packing_pdf.mjs` renders every sheet here; its name predates all but the first.
`--margins` must match the generating script's `@page` rule, or Chromium's own win
silently; `--landscape` is for the field guide's two-up sheets; `--max-pages` turns a
one-page promise into a build constraint.

`rebuild_packing.py`, `extract.mjs` and `build_seeds.mjs` are one-shot migrations, kept for the
record of how the data got its current shape. They are not part of any current pipeline.
`archive/` has its own README.
