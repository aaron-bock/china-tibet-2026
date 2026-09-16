# Project memory — China-Tibet Trip 2026

**Read this first, and read all of it, before touching anything about this trip.**

Everything below changed on 2026-09-12. If you are Claude on a new machine and
you find an older copy of this file in the iCloud folder, this one wins.

## There is now one document, and it is the only one

**The China & Tibet 2026 dossier** — <https://claude.ai/code/artifact/eccc0f6c-dc3a-4c08-8381-905dee78f9ff>

That page is the single source of truth for this trip. Aaron's instruction, verbatim:
*"This will be the true source of info going forward."* It is editable in place, it
saves as you type, and it exports itself (HTML, Markdown, costs CSV, shopping CSV,
JSON) for taking offline before departure.

Eighteen sections, reached through four groups rather than one long row of tabs:

- **Itinerary** — Overview, then one tab per leg: Outbound, Xi'an, Z165, Tibet,
  Shanghai, Disney, Home
- **Packing** — Packing, Own or buy, Repacks, Bags
- **Open items** — on its own, because it is the list of things still owed
- **Reference** — Jet lag, Money, Apps & wallet, People, Reference, Point at this, Notes

### The legs are a view, not a new shape for the data

Flights, beds, day-by-day, tour days, tickets and weather are still six separate
documents with six different field layouts. Each row carries a `leg` field, and a
leg tab gathers whichever rows are tagged for it, rendering each source in that
source's own layout under its own sub-heading. Nothing was flattened to fit, and
`trip/days`, `trip/segments`, `trip/tour`, `trip/stays`, `trip/disney` and
`trip/weather` still exist exactly as before.

A `leg` may hold more than one token, space-separated — the Shanghai weather row
is tagged `shanghai disney` because those days share a forecast. The sections
that own those layouts are still in SCHEMA but are in no group, so they have no
tab and no panel; they are there for their fields and their labels.

Packing is grouped by the bag each item rides in, with a picker on every row that
moves it between bags. Its bags are Worn, Sling, Talon 22, Talon 44, Away,
Buy in Xi'an and Rent in Lhasa; the last two are acquired there, not packed.
Own / Buy / Skip triage lives on the same records, under Own or buy, and the Buy
marks become the shopping-list export.

The Why column on Packing is deliberately one line, and absent on rows where it
would only restate the item — that is a standing editorial rule, not an oversight.
Don't reintroduce paragraphs there.

The source lives in the GitHub repo **aaron-bock/china-tibet-2026** on branch
`claude/china-trip-planner-3dq17s`: `index.html` is the page, `seed/*.json` is the
first-run data, `tools/` holds the extractors that built the seeds from the old pages.

### The app's data does not live in the repo

The live, edited state lives in the artifact's runtime `db` (`trip/*` documents), not
in `seed/*.json`. The seeds only populate an empty database on first run. So:

- **Never** "restore" the app by re-seeding — that would overwrite Aaron's edits.
- Editing `seed/*.json` changes nothing for a database that already exists.
- The repo copy will not work as a static page anywhere (GitHub Pages included),
  because there is no `db` outside the artifact runtime. Don't offer it as a mirror.
- To change the app, edit the page and republish it to the same artifact URL.

## All six old Trip Kit pages are archived

Archived 2026-09-12, each with a banner at the top pointing at the dossier. They are a
record of what changed, not something to plan from — and nothing in them should be
copied forward without checking it against the app first.

| Page | Artifact |
|---|---|
| China-Tibet Trip Kit (front door) | `65e30345-b6b5-4438-aee4-f7034f64bb14` |
| Itinerary (was the master document) | `db0a3465-f329-47b2-a0d9-1300d2d79d90` |
| Packing List | `34674237-5194-4538-8249-c385789e9677` |
| Own It or Buy It (prep checklist) | `c6bf9cba-c0f1-470b-8ec6-3d69702ccae0` |
| China Trip Phone Kit (apps & services) | `ac2f1858-d9b6-456a-a881-d44ee391ec57` |
| Sandra's 2017 Notes | `84f80d00-6586-4783-92f6-c75ebdb9be46` |

Three earlier documents were archived on 2026-09-10 and their banners re-pointed at the
dossier on 2026-09-12, so every old page now links straight here:

| Page | Artifact |
|---|---|
| Xi'an to Everest Base Camp | `e30ce61e-259d-478d-83f8-de26123df0c2` |
| Xi'an, Wall to Warriors | `0e766031-5e51-432b-a7cb-cff77258d607` |
| Xi'an to Disneytown | `8b2e8b41-3c6d-4aaa-8b46-28ab3da22683` |

Nine archived pages in total. None of them is a plan.

**Not archivable from here, and still outstanding:** the files in the iCloud `Trip Kit`
folder and the docs in the "China-Tibet Trip 2026" Claude Project. Those need Aaron.
Until he does it, a future session can still stumble on a stale copy — hence the
"this one wins" line at the top.

## Notes kept for provenance only

`itinerary_sources.md`, `xian_shanghai_decisions.md`, `apps_and_services.md`,
`sandra_blog_2017.md`, `sandra_china_tips.md`, `sandra_2026_crossover.md`.

They explain *why* facts are what they are, and they are worth reading when a decision
needs re-litigating. They are **not** current: where a note and the app disagree, the
app is right. Do not hand these to Aaron as deliverables and do not plan from them.

## Standing cautions

- **The real plan lives in WhatsApp, not email.** This is the one that has already
  cost a rebuild: a version assembled from Gmail and Drive had the trip starting
  22 September (that's the separate Trybal SoCal trip), treated the Z165 as unticketed
  when James had confirmed it on 16 August for 2 Oct 09:27, read the Westin award
  night as a conflict, and missed the Disneyland ticket window entirely.
- **Sandra's blog is from 2017.** Her warnings held; her logistics largely didn't.
  Anything operational from it must be re-checked before it goes in a deliverable.
- **Do not copy the STEP credentials out of the shared Drive sheet
  ("Important Info In China").** They are someone else's login. Deliberately excluded
  from the app and from the repo; the app's Reference section instead says to enrol at
  step.state.gov under Aaron's own account.
- **The repo is public and carries live booking data** — airline record locators, a
  ticket number, Westin confirmations, an e-mail list, a phone number, a SkyMiles
  number, the permit delivery address. Flagged to Aaron on 2026-09-12; he has not yet
  said whether to make it private. Assume it is still public.

Last rewritten: 2026-09-12, when the app became authoritative.
