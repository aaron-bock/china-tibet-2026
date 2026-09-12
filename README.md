# China & Tibet 2026

An editable trip dossier for Aaron Bock's **27 September – 16 October 2026** trip: Los Angeles →
Seoul → Xi'an → Lhasa by rail → Everest Base Camp → Shanghai → Atlanta. The Tibet leg is Asia
Odyssey Travel's eight-day EBC tour, party of five, customer ID `AOT-BJ-James-50674`.

Published as a Claude Artifact:
<https://claude.ai/code/artifact/eccc0f6c-dc3a-4c08-8381-905dee78f9ff>

## What this is

`index.html` is the whole application — a single page, no build step. Every field is editable in
place and saves server-side, so the page can be worked on right up to departure.

Thirteen sections: Itinerary, Flights & rail, Tibet tour, Stays, Disneyland, Open items, Money,
Apps & wallet, Packing, People, Reference, Point at this (Chinese names to show a driver), and
Notes. Each row carries a status — `confirmed` / `pending` / `action` / `done` — which drives the
colour stripe, the summary tiles and the "Needs you" banner.

Two inline altitude profiles, because altitude is the real risk on this trip: the Qinghai–Tibet
railway from Xi'an at 400 m to Lhasa at 3,650 m, and the tour's day-by-day high point through the
5,200 m tent night at base camp and 5,248 m at Gyatso La.

The **Download** button exports the current state four ways via the artifact `downloads`
capability:

| File | What it is |
| --- | --- |
| `china-tibet-2026-dossier.html` | Every section on one printable page, self-contained, works offline |
| `china-tibet-2026.md` | Plain Markdown |
| `china-tibet-2026-costs.csv` | The money table as a spreadsheet |
| `china-tibet-2026.json` | Raw records as stored |

## How the data is stored

The page declares the `db` and `downloads` capabilities. Records live in the artifact's document
store under the `trip` collection — one document per section, each holding an `items` array:

```
trip/meta       trip/days     trip/segments  trip/tour    trip/stays
trip/disney     trip/tasks    trip/money     trip/apps    trip/packing
trip/people     trip/reference  trip/phrases  trip/notes
```

The page holds no trip data of its own: it renders whatever the store returns, and shows a plain
message if the store is unavailable. `seed/` is the starting state of those documents — a record,
not something the page reads. Re-seeding overwrites later edits.

```
# read one document
Artifact(action="read_db", url=<artifact url>, db_op="get",
         collection="trip", doc_id="segments")

# re-seed (destructive — pin if_version from a read first)
Artifact(action="write_db", url=<artifact url>, db_op="batch", writes=[...])
```

## Sources

`sources/` vendors the Trip Kit documents this was built from, as supplied:

- **`Itinerary.html`** — the master document, assembled 10 September 2026. Flights, hotels, day by
  day, the Xi'an map, the full Shanghai Disneyland ticketing analysis, bookings and contacts. This
  is the authority; everything in `seed/` derives from it.
- `xian_shanghai_decisions.md` — what's booked, what's open, Golden Week constraints, the
  annual-pass verdict.
- `apps_and_services.md` — eSIM / VPN / Alipay setup, what breaks behind the firewall, museum
  booking channels, the pre-departure deadlines.
- `sandra_blog_2017.md` — index and access notes for Sandra Rothbard's private 2017 blog.
- `MEMORY.md` — the project's own memory notes, which name the rest of the Trip Kit.

Not vendored here because they weren't supplied, and they remain the authority for their own
subjects: `Prep-Checklist.html`, `Packing-List.html`, `Apps-and-Services.html`, `Sandra-2017.html`
and the Trip Kit `index.html`. The Packing section in this app therefore carries only the
train-and-altitude essentials the master itinerary calls out, and says so.

### A note on the first version

The first build of this app (commits `75fa691`, `0a58393`) was assembled from Gmail and Drive
before the Trip Kit was supplied, and got several things wrong: it dated the trip from 22
September (that's the separate Trybal SoCal trip), treated the Xi'an–Lhasa train as unticketed
(Z165 was confirmed with James on 16 August), read the Westin award night as a scheduling conflict
(it's needed — the train leaves at 09:27 on the 2nd), and missed the Disneyland ticket window
entirely. As the project memory puts it: *the real plan lives in WhatsApp, not email.*
