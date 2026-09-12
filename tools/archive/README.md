# Archive tooling

## banner.py

`banner.py` stamps the "Archived" banner onto a saved copy of one of the six old Trip Kit
artifacts and writes a publishable fragment beside it.

Run on 2026-09-12 against all six. Each output was published back to its own artifact URL,
so the banner is live on every one of them:

| Page | Artifact | New version |
|---|---|---|
| China-Tibet Trip Kit (front door) | `65e30345-b6b5-4438-aee4-f7034f64bb14` | 4 |
| Itinerary | `db0a3465-f329-47b2-a0d9-1300d2d79d90` | 8 |
| Packing List | `34674237-5194-4538-8249-c385789e9677` | 13 |
| Own It or Buy It | `c6bf9cba-c0f1-470b-8ec6-3d69702ccae0` | 7 |
| China Trip Phone Kit | `ac2f1858-d9b6-456a-a881-d44ee391ec57` | 5 |
| Sandra's 2017 Notes | `84f80d00-6586-4783-92f6-c75ebdb9be46` | 2 |

Two details worth keeping, because both cost a round to find:

- **Publishing wraps the file in its own `<!doctype html><head>…</head><body>`,** so the
  fragment must be page content only. `fragment()` slices `<body>…</body>` out of the saved
  copy and drops the doctype remnants.
- **Some of these pages carry a second, inner `<body>`** (the Itinerary has one at line 493 of
  Aaron's original — pre-existing, not introduced here). Anchoring on the *first* `<body>` put
  the banner inside `<head>`, where it rendered as nothing. `main()` prefers the **last** inner
  `<body>`, and falls back to the end of the first `</style>` when there is none.

## repoint.py

The three documents archived back on 2026-09-10 already had a banner, but it named the
master document in bold text with no link — and that document ("Xi'an, Everest,
Disneytown", later renamed "Itinerary") is itself archived now. `repoint.py` rewrites
just the banner body to link the dossier, leaving the "Archived 10 September 2026"
heading alone: that date is the historical fact and shouldn't move.

| Page | Artifact | New version |
|---|---|---|
| Xi'an to Disneytown | `8b2e8b41-3c6d-4aaa-8b46-28ab3da22683` | 6 |
| Xi'an to Everest Base Camp | `e30ce61e-259d-478d-83f8-de26123df0c2` | 7 |
| Xi'an, Wall to Warriors | `0e766031-5e51-432b-a7cb-cff77258d607` | 4 |

A third detail, on top of the two above: prefer `action: "read_file"` on `index.html`
for the source. That returns the file exactly as uploaded, with no wrapper to strip, so
the republish is byte-identical apart from the banner swap. `action: "read"` is still
what satisfies the publish guard — `read_file` does not — so both calls are needed: read
to be allowed to publish, read_file to get clean bytes.

Both scripts are idempotent: it bails if the banner text or the dossier artifact id is already
present, so re-running it on an already-archived page is a no-op rather than a double banner.
