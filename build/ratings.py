r'''Write ratings.json from MyHockeyRankings' USA 11U list, plus the few
tournament teams MHR rates only on its 12U list.

MHR rates 11U and 12U as one Peewee pool: the 12U list is pinned at 99.99 and
the 11U list tops out near 95, and a 2015 team that plays a 12U schedule shows
up on the 12U list. So both lists are on one scale and are used as they are,
with no offset.

There is no projection here, unlike the girls' site. Every team starts from
MHR's own number with a band of sqrt(8 / games played) -- the same width the
girls' site gives a team rated on MHR alone -- and the page adjusts it for
games entered since the list was captured.

**Every week is kept.** Each capture is a `mhr_11u_<date>.tsv` plus that
week's entries in `TWELVE_U`, and each becomes one entry in `snapshots` and in
every team's `snaps[date] = [rating, band, games]`, exactly the shape the
girls' live.py writes. The page reads the week in force on the day it is
asking about, so a tournament's seeds and Analysis tab keep the numbers that
were current when it was played -- and MHR's later number, which already
counts that tournament's games, is never added to them a second time.

`proj` and `band` are the first week a team appears in. A team that first
appears in a later week carries `since`, and no earlier day sees it.

    python build/ratings.py
'''
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NOISE = 8.0

# Rated on MHR's 12U list only, by capture date. Read off the USA 12U list
# (v=124) each week; Twin Bridges is under MHR's five-game minimum, so on no
# list, and is read off its team page (t=17560), which shows a provisional
# rating.
TWELVE_U = {
    '2026-11-04': [
        ('Allegheny Badgers (#2) 11U A (PA)', '10-3-2', 83.34),
        ('Omaha Jr Mavericks (Red) 12U A (NE)', '2-3-0', 79.16),
        # Named by the Jets on 5 November as the 2015 rosters these clubs bring.
        ('Chicago Stallions 12U A2 (IL)', '5-2-0', 77.89),
        ('San Francisco Sabercats 12U BB (CA)', '4-4-0', 72.41),
        ('Naperville Sabres 12U A2 (IL)', '4-6-0', 78.08),
        ('Twin Bridges Lightning (#1) 12U A3 (IL)', '2-2-0', 78.01),
        # Geneva Silver Stick Regional, 27-29 November: 12U teams in a 12U A
        # division, read off MHR's Illinois 12U list on 10 November.
        ('West Dundee Leafs 12U A1 (IL)', '7-5-1', 81.20),
        ('Geneva Cyclones 12U A1 (IL)', '2-11-2', 80.68),
    ],
    '2026-11-11': [
        ('Allegheny Badgers (#2) 11U A (PA)', '12-5-2', 82.83),
        ('Omaha Jr Mavericks (Red) 12U A (NE)', '2-7-0', 78.04),
        ('Chicago Stallions 12U A2 (IL)', '5-2-0', 77.29),
        ('San Francisco Sabercats 12U BB (CA)', '5-5-0', 74.15),
        ('Naperville Sabres 12U A2 (IL)', '5-6-0', 78.24),
        ('Twin Bridges Lightning (#1) 12U A3 (IL)', '2-2-0', 78.86),
        ('West Dundee Leafs 12U A1 (IL)', '7-5-1', 80.85),
        ('Geneva Cyclones 12U A1 (IL)', '2-12-2', 80.21),
    ],
}


def gp(record):
    return sum(int(x) for x in record.split('-'))


def band_for(n):
    return round(math.sqrt(NOISE / max(n, 1)), 2)


def week(date):
    '''One capture: {name: (rating, band, games, rank or None)}.'''
    out = {}
    path = HERE / ('mhr_11u_%s.tsv' % date)
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        rank, name, record, rating = line.split('\t')
        n = gp(record)
        out[name] = (float(rating), band_for(n), n, int(rank))
    for name, record, rating in TWELVE_U.get(date, []):
        n = gp(record)
        out[name] = (rating, band_for(n), n, None)
    return out


dates = sorted(p.stem.split('_')[-1] for p in HERE.glob('mhr_11u_*.tsv'))
weeks = {d: week(d) for d in dates}
newest = dates[-1]

teams, order = {}, []
for d in dates:
    for name, (rating, band, n, rank) in weeks[d].items():
        t = teams.get(name)
        if t is None:
            t = teams[name] = {'n': name, 'proj': rating, 'band': band,
                               'usa': rank is not None, 'na': rank is not None,
                               'rank': None, 'snaps': {}}
            if d != dates[0]:
                t['since'] = d
            order.append(name)
        t['snaps'][d] = [rating, band, n]

for name in order:
    t = teams[name]
    cur = weeks[newest].get(name)
    if cur:
        t['live'], t['liveBand'], t['mgp'] = cur[0], cur[1], cur[2]
        t['rank'] = cur[3]
        if cur[3] is not None:
            t['usa'] = t['na'] = True

out = {'live': {'asOf': newest, 'source': 'MyHockeyRankings USA 11U and 12U'},
       'snapshots': [{'asOf': d, 'teams': len(weeks[d])} for d in dates],
       'teams': [teams[n] for n in order]}
(ROOT / 'ratings.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(len(order), 'teams over', len(dates), 'weeks ->', ROOT / 'ratings.json')
for d in dates:
    print(' ', d, len(weeks[d]), 'teams')
