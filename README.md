# China & Tibet 2026

Trip dossier for Aaron Bock's 22 September – 16 October 2026 trip: Atlanta → Los Angeles →
Seoul → Xi'an → Lhasa (by rail) → Shanghai → Atlanta. The Tibet leg is run by Asia Odyssey
Travel under customer ID `AOT-BJ-James-50674`, with five travellers.

Published as a Claude Artifact:
<https://claude.ai/code/artifact/eccc0f6c-dc3a-4c08-8381-905dee78f9ff>

## What this is

`index.html` is the whole application — a single page with no build step. Everything on it is
editable in place, and edits persist server-side for anyone who opens the page.

Nine sections: Itinerary, Flights & rail, Stays, Open items, People, Money, Packing,
Reference, Recommendations. Each row carries a status (`confirmed` / `pending` / `action` /
`done`) that drives the colour stripe, the summary tiles and the "Needs you" banner.

The **Download** button exports the current state four ways, via the artifact `downloads`
capability:

| File | What it is |
| --- | --- |
| `china-tibet-2026-dossier.html` | Every section on one printable page, self-contained, works offline |
| `china-tibet-2026.md` | Plain Markdown |
| `china-tibet-2026-costs.csv` | The money table as a spreadsheet |
| `china-tibet-2026.json` | Raw records as stored |

## How the data is stored

The page declares the `db` and `downloads` capabilities. Trip records live in the artifact's
document store under the `trip` collection — one document per section, each holding an
`items` array:

```
trip/meta        trip/days       trip/segments   trip/stays    trip/tasks
trip/people      trip/money      trip/packing    trip/reference  trip/notes
```

The page holds no trip data of its own: it renders whatever the store returns, and shows a
plain message if the store is unavailable. `seed/` holds the initial contents of those
documents, assembled from the `Travel/Everest` Gmail label and the shared "Important Info In
China" sheet in Drive. It is a record of the starting state, not something the page reads —
re-seeding would overwrite later edits.

To inspect or re-seed from Claude Code:

```
# read one document
Artifact(action="read_db", url=<artifact url>, db_op="get",
         collection="trip", doc_id="segments")

# re-seed every document (destructive — overwrites in-page edits)
Artifact(action="write_db", url=<artifact url>, db_op="batch", writes=[
  {"op":"set","collection":"trip","doc_id":"segments","file_path":"seed/segments.json"},
  ...
])
```

## Sources

Built from Aaron's own records, not from anything invented:

- Gmail label `Travel/Everest` — 14 threads: the Asia Odyssey correspondence, Delta and
  Korean Air receipts, the China Eastern award, both Westin Xi'an confirmations, the visa
  submission to the Chinese consulate in Atlanta, Kamana's group flight details, and Sandra
  Rothbard's recommendations.
- Google Drive — "Important Info In China", shared by Sandra Rothbard: US consulate and
  embassy contacts, international card numbers. That sheet also carries someone else's State
  Department STEP login; it is deliberately **not** reproduced here, and the dossier instead
  carries an open item to enrol under Aaron's own account.

Figures that only ever arrived as image attachments — the Tibet tour price and the day-by-day
Tibet plan — are recorded as open items rather than guessed at.
