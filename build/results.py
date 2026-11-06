"""Write results.json: every finished game, as evidence for the rankings.

The rankings adjust a team's projection towards what its games imply, and this
is the ledger they read. It is build output -- regenerated from the event files
each time, never edited -- so a score corrected a week later simply produces a
corrected ranking, with nothing accumulated to unwind.

    python build/results.py

An event file lives in events/ and is listed in events/index.json, which is
also what the tournament page reads. All this needs from one is `teams` carrying
an `mhrName` for every side and `games` -- so a season log of one-off games,
which has no groups and no bracket, is read by exactly the same code as a
64-team showcase.

Games are keyed by MyHockeyRankings name, because that is what ratings.json is
keyed by and what the two lists have in common. A team with no `mhrName`, or a
name absent from ratings.json, is dropped from the ledger with a line saying so
-- a game against a team we cannot rate carries no information.

It is dropped from the ledger, not from the record. `storm` carries every game
the Storm play, rated opponent or not, played or not, across every file, which
is what the games page renders. Whether the ledger could use it is the `rated`
flag on the row.

Add a tournament by dropping its file in events/ and adding a row to
events/index.json. Nothing here needs editing.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The Storm row is picked out everywhere on this site; here it is what the
# season log is a log of.
STORM = 'Chicago Jets'


def events():
    """Every event of the season, read from the index the page reads."""
    doc = json.loads((ROOT / 'events' / 'index.json').read_text(encoding='utf-8'))
    return [(e['id'], e['file'], e.get('kind', 'tournament'))
            for e in doc.get('events', [])]


def main():
    rated = {t['n'] for t in json.loads(
        (ROOT / 'ratings.json').read_text(encoding='utf-8'))['teams']}

    games, meta, storm, dropped = [], [], [], {}
    storm_name, storm_mhr = [None], [None]
    for event_id, filename, kind in events():
        path = ROOT / filename
        if not path.exists():
            print('%-24s missing, skipped' % filename)
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        team = {t['id']: t for t in doc.get('teams', [])}
        mhr = {tid: t.get('mhrName') for tid, t in team.items()}
        # A log names its metadata block for what it is; a tournament calls it
        # `tournament`. Same three fields either way.
        info = doc.get('tournament') or doc.get('log') or {}
        meta.append({'id': event_id, 'kind': kind, 'name': info.get('name'),
                     'dates': info.get('dates'), 'file': filename})

        kept = 0
        for g in doc.get('games', []):
            h, a = mhr.get(g.get('home')), mhr.get(g.get('away'))
            us = next((s for s in ('home', 'away')
                       if (team.get(g.get(s)) or {}).get('name', '').startswith(STORM)),
                      None)
            if us:
                storm_mhr[0] = mhr.get(g.get(us)) or storm_mhr[0]
                storm_name[0] = team[g[us]].get('name') or storm_name[0]
                them = 'away' if us == 'home' else 'home'
                foe = team.get(g.get(them)) or {}
                foeMhr = mhr.get(g.get(them))
                oppRating = foe.get('ratingForPrediction')
                # A game entered into the ledger after it was played shows as it
                # did then: an unrated opponent with the estimate we had, so a
                # row already on the page does not change under anyone.
                if g.get('recorded') and g['recorded'] > g['start'][:10]:
                    foeMhr = None
                    oppRating = foe.get('estimateBefore', oppRating)
                storm.append({
                    'event': event_id, 'eventName': info.get('name'), 'kind': kind,
                    'date': g['start'][:10], 'start': g['start'],
                    'home': us == 'home',
                    'opp': foe.get('name'), 'oppMhr': foeMhr,
                    # An unrated opponent may still carry a supplied estimate,
                    # which is worth showing even though the ledger cannot use it.
                    'oppRating': oppRating,
                    'rated': bool(foeMhr and foeMhr in rated),
                    'gf': g.get(us + 'Score'), 'ga': g.get(them + 'Score'),
                    'decision': g.get('decision'),
                    'rink': g.get('rink'), 'round': g.get('round'),
                })

            if g.get('homeScore') is None or g.get('awayScore') is None:
                continue
            for side, name in ((g.get('home'), h), (g.get('away'), a)):
                if side and (not name or name not in rated):
                    dropped[name or side] = dropped.get(name or side, 0) + 1
            if not h or not a or h not in rated or a not in rated:
                continue
            # The day is what the adjustment ages a game by; the faceoff is
            # what lets a page ask for a rating between two games on one day.
            row = {'event': event_id, 'date': g['start'][:10],
                   'start': g['start'],
                   'home': h, 'away': a,
                   'homeScore': g['homeScore'], 'awayScore': g['awayScore']}
            # A game that entered the ledger after the fact says when. A seed
            # frozen before then was made without it and must stay that way.
            if g.get('recorded'):
                row['recorded'] = g['recorded']
            # Played before the MHR snapshot of this date but not yet in its
            # number, so the page keeps it in the ledger for that snapshot.
            if g.get('mhrMissing'):
                row['mhrMissing'] = g['mhrMissing']
            games.append(row)
            kept += 1
        print('%-24s %3d games' % (event_id, kept))

    for name, n in sorted(dropped.items()):
        print('  no rating for %-40s %d game(s) dropped' % (name, n))

    games.sort(key=lambda g: (g['date'], g['home']))
    storm.sort(key=lambda g: (g['start'], g['opp'] or ''))
    out = {'events': meta, 'games': games,
           'stormName': storm_name[0], 'stormMhr': storm_mhr[0],
           'storm': storm}
    (ROOT / 'results.json').write_text(
        json.dumps(out, indent=1, ensure_ascii=False) + '\n',
        encoding='utf-8', newline='\n')

    teams = {g['home'] for g in games} | {g['away'] for g in games}
    print('\nresults.json: %d games, %d teams, %s'
          % (len(games), len(teams),
             (games[0]['date'] + ' to ' + games[-1]['date']) if games else 'empty'))
    played = [g for g in storm if g['gf'] is not None]
    unrated = [g for g in played if not g['rated']]
    print('Storm season: %d games on the schedule, %d played%s'
          % (len(storm), len(played),
             (', %d against a team MHR does not rate' % len(unrated)) if unrated else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
