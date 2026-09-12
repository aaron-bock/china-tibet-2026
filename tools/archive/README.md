# Archive banner

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

The script is idempotent: it bails if the banner text or the dossier artifact id is already
present, so re-running it on an already-archived page is a no-op rather than a double banner.
