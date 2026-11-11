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

    python build/ratings.py
'''
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
AS_OF = '2026-11-04'          # MHR's "last update" on the captured lists
NOISE = 8.0

# Rated on MHR's 12U list only, read off it on 5 November.
TWELVE_U = [
    ('Allegheny Badgers (#2) 11U A (PA)', '10-3-2', 83.34),
    ('Omaha Jr Mavericks (Red) 12U A (NE)', '2-3-0', 79.16),
    # Named by the Jets on 5 November as the 2015 rosters these clubs bring.
    ('Chicago Stallions 12U A2 (IL)', '5-2-0', 77.89),
    ('San Francisco Sabercats 12U BB (CA)', '4-4-0', 72.41),
    ('Naperville Sabres 12U A2 (IL)', '4-6-0', 78.08),
    # Under MHR's five-game minimum, so on no list; read off its team page
    # (t=17560), which shows a provisional rating.
    ('Twin Bridges Lightning (#1) 12U A3 (IL)', '2-2-0', 78.01),
    # Geneva Silver Stick Regional, 27-29 November: 12U teams in a 12U A
    # division, read off MHR's Illinois 12U list on 10 November.
    ('West Dundee Leafs 12U A1 (IL)', '7-5-1', 81.20),
    ('Geneva Cyclones 12U A1 (IL)', '2-11-2', 80.68),
]


def gp(record):
    return sum(int(x) for x in record.split('-'))


def row(name, record, rating, ranked):
    n = gp(record)
    band = round(math.sqrt(NOISE / max(n, 1)), 2)
    return {'n': name, 'proj': rating, 'band': band, 'live': rating,
            'liveBand': band, 'mgp': n, 'usa': ranked, 'na': ranked,
            'rank': None}


teams = []
for line in (HERE / ('mhr_11u_%s.tsv' % AS_OF)).read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'):
        continue
    rank, name, record, rating = line.split('\t')
    t = row(name, record, float(rating), True)
    t['rank'] = int(rank)
    teams.append(t)
for name, record, rating in TWELVE_U:
    teams.append(row(name, record, rating, False))

out = {'live': {'asOf': AS_OF, 'source': 'MyHockeyRankings USA 11U and 12U'},
       'teams': teams}
(ROOT / 'ratings.json').write_text(json.dumps(out, indent=1) + '\n', encoding='utf-8')
print(len(teams), 'teams ->', ROOT / 'ratings.json')
