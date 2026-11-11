# Boys Hockey Rankings

A static tournament tracker for the Chicago Jets (CSDHL) 11U AA, the boys'
counterpart of `../girls-hockey-rankings`. One page, `index.html`, with the
same tabs and features as that site's tournament page: Jets, Brackets,
Schedule, Analysis, Ask and the keyed score entry (`?edit=jets2026`).

**Most of what is true of the girls' tournament page is true here**, because
the generator is a copy of that one. Read `../girls-hockey-rankings/CLAUDE.md`
before changing page behaviour. The same rules apply: `index.html` is build
output, `events/*.json` are hand-maintained data, patch scripts go in a file
with `r'''` strings, and `grep -c $'\b' index.html` must be 0.

The repo is meant to be public, like the girls' one: teams and ratings only,
no personal information about children or families.

## Layout

| Path | What it is |
|---|---|
| `index.html` | **Generated.** The tournament page. |
| `build/build_page.py` | Copy of the girls' generator, derived by `derive_from_girls.py`. |
| `build/derive_from_girls.py` | Turns a fresh copy into this site's generator. Every replacement asserts its count. |
| `build/ratings.py` | Writes `ratings.json` from the captured MHR list. |
| `build/mhr_11u_<date>.tsv` | MHR's USA 11U list, all teams, as captured. |
| `build/results.py` | Builds `results.json` from `events/index.json`. `STORM` is `'Chicago Jets'`. |
| `events/` | One file per tournament plus `index.json`. |

## Taking a fix from the girls' site

    cp ../girls-hockey-rankings/build/build_page.py build/
    python build/derive_from_girls.py
    python build/build_page.py

If an assertion fails, the girls' page changed under a replacement; update
the replacement rather than editing the derived file by hand.

## Ratings

MHR rates 11U and 12U as **one Peewee pool on one scale**: the 12U list is
pinned at 99.99, the 11U list tops out near 95, and a 2015 team playing a 12U
schedule appears on the 12U list (Allegheny Badgers (#2) 11U A). So both are
used as published, with no offset. There is no projection: every team starts
from MHR's number with a band of sqrt(8 / games played), and the page adjusts
for games entered since `live.asOf`. Only teams on the 11U list carry a rank
(`na`), so the Analysis tab's ranks are MHR's USA 11U ranks.

Refresh: copy the 11U list into a new `mhr_11u_<date>.tsv` (the built-in
browser gets past Cloudflare; read every row of the table, all pages), add a
`TWELVE_U[<date>]` entry for every 12U-only team from the USA 12U list
(`v=124`), and run `python build/ratings.py`. Never edit or delete an older
tsv: **every week is kept**, as on the girls' site. `ratings.json` carries
`snapshots` and each team's `snaps[date]`, and the page reads the week in
force on the day it is asking about. With only the newest week, a refresh
would put a past tournament's seeds and Analysis on MHR's later number, which
already holds that tournament's games -- counting them twice.

**Then compare each team's ledger games with what MHR counted**, exactly as
the girls' CLAUDE.md describes. MHR is slow to receive tournament scores: on
11 November it had 13 of CCM Chicago's 59 games on neither team's page (most
of Sunday's), and those carry `"mhrMissing": "2026-11-11"`. A game on one
side's MHR page only is MHR filing it under a different team (see below) and
is left unmarked, or that side would count it twice.

**MHR disagrees with two of our 12U identities.** The Hawks' and Northwest
Chargers' CCM games are filed against Twin Bridges Lightning **(#2)** 12U A3,
and the Hawks' game against Naperville Sabres **12U A1**, where our file has
(#1) A3 and 12U A2 (named by the Jets). Chicago Stallions 12U A2 has no CCM
game on MHR at all. Unresolved: ask the owner before changing them.

**A club with several 12U teams and no 11U team cannot be identified from MHR
alone**, because nothing on the list marks the 2015 roster. Those teams carry
`mhrName: null`, `basis: "unranked"` and the division's average as
`ratingForPrediction` with a 2.5 band, and their `note` lists the candidates.
When the owner says which team it is, set `mhrName`, `rating`, `band` and
`ratingForPrediction` from `ratings.json` (adding the team to `TWELVE_U`).

**A capped blowout lowers the favourite, and that is deliberate.** A margin
counts at most 7 goals (`ADJ_CAP`), so a team 12 goals better that wins 17-0
is credited with 7 and drops -- the Jets went 84.20 to 83.99 on 6 November.
MHR does the same, and the owner's decision is to match MHR: do not add an
exemption for maxed-out wins. Enter the score the tournament posts (it caps
at 7 too), not the true one.

## Crossover playoffs

200x85's pooled formats pair pools rather than mirroring a seeding:
`rules.crossPairs` names the pools that meet (`[["A","D"],["B","C"]]`) and
`rules.crossPlaces` maps a finishing place, from 0, to the place it meets
across (`[3, 2, 1, 0, 4, 5]` is 1v4, 2v3, and 5th and 6th against the like
finisher). `simulate()`'s `partner()` reads them for the next-opponent guess.
This exists only in this copy; `derive_from_girls.py` adds it.

## Where each tournament's data came from

| Event | Source | How |
|---|---|---|
| CCM World Invite Chicago (2015 Ribcor) | my.200x85.com (Regystra), division 990 | built-in browser, page text |
| Geneva Silver Stick Regional (12U A) | silverstick.org, tournament 33085, division 33094 | built-in browser, page text |

The 200x85 schedule prints `HOME` then `VISITOR`, and the file keeps that
order. Playoff slots are named for places (`B1st` v `C4th`) and game winners,
and the file carries them as labels with no teams until they fill.

silverstick.org is the same platform as scgha.com: it prints `Away @ Home`, so
the second team is the file's home, and the game ids are the site's numbers.
Its rinks are printed only as `North` and `South`, and the file keeps that.
The Silver Stick round robin is win 2, tie 1, loss 0 with no overtime, so the
file sets `rules.tiesStand` (see the girls' CLAUDE.md). Geneva Cyclones "12U
A" is read as MHR's 12U A1, not the A2; the team's `note` says so.
