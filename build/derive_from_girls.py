r'''Turn a copy of girls-hockey-rankings/build/build_page.py into this site's
generator: the tournament page alone, published as index.html, with the
Chicago Jets 11U AA as the highlighted team.

Run once, on a fresh copy:

    cp ../girls-hockey-rankings/build/build_page.py build/
    python build/derive_from_girls.py

Every replacement must match exactly once (or the stated number of times), so
a change upstream fails loudly here instead of shipping a page half about the
Storm.'''
from pathlib import Path

P = Path(__file__).resolve().parent / 'build_page.py'
s = P.read_text(encoding='utf-8')


def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, 'expected %d of %r, found %d' % (count, old[:70], n)
    s = s.replace(old, new)


# ---------------------------------------------------------------- the build
sub(r'''data = json.loads((HERE / 'page_data.json').read_text(encoding='utf-8'))''',
    r'''# The rankings page's table data. This site has no rankings page.
data = {}''')

sub(r'''NAV = [('index.html', 'Rankings'),
       ('tournaments.html', 'Tournaments'),
       ('games.html', 'Games'),
       ('methodology.html', 'Methodology')]''',
    r'''NAV = [('index.html', 'Boys Hockey Rankings')]''')

sub(r'''PAGES = [
    ('index.html', '14U Girls Preseason Projections', RANKINGS_MAIN,
     with_adjust(SCRIPT)),
    ('tournaments.html', 'Tournaments &mdash; 14U Girls Preseason Projections',
     TOURNAMENTS_MAIN, with_adjust(TOURNAMENTS_SCRIPT)),
    ('games.html', 'Games &mdash; 14U Girls Preseason Projections',
     GAMES_MAIN, with_adjust(GAMES_SCRIPT)),
    ('methodology.html', 'Methodology &mdash; 14U Girls Preseason Projections',
     METHODOLOGY_MAIN, ''),
]''', r'''PAGES = [
    ('index.html', 'Boys Hockey Rankings',
     TOURNAMENTS_MAIN, with_adjust(TOURNAMENTS_SCRIPT)),
]''')

sub(r'''# /girls-hockey-rankings/, so a leading slash''',
    r'''# /boys-hockey-rankings/, so a leading slash''')

sub(r'''Ratings and team listings from <a href="https://myhockeyrankings.com" target="_blank" rel="noopener noreferrer">myhockeyrankings.com</a>, seasons 2023&ndash;24 through 2025&ndash;26, retrieved 1 September 2026. Projections are independent estimates and are not produced or endorsed by MyHockeyRankings.''',
    r'''Ratings from <a href="https://myhockeyrankings.com" target="_blank" rel="noopener noreferrer">myhockeyrankings.com</a>, USA 11U and 12U lists. Predictions are independent estimates and are not produced or endorsed by MyHockeyRankings.''')

# ---------------------------------------------------------------- the page
sub(r''' <a href="methodology.html">How this works &rarr;</a></p>''', '</p>', 2)
sub(r'''Predictions are rating differences, not measured results &mdash; &plusmn;1.4 rating points.''',
    r'''Predictions are rating differences, not measured results &mdash; a typical miss is about 2.5 goals.''')
sub(r'''aria-selected="true">Storm</button>''', r'''aria-selected="true">Jets</button>''')
sub(r'''<h3 id="t-storm-name">Windy City Storm 14U</h3>''',
    r'''<h3 id="t-storm-name">Chicago Jets 11U AA</h3>''')
sub(r'''<h2>Full 14U schedule</h2>''', r'''<h2>Full schedule</h2>''')
sub(r'''const STORM_PREFIX = 'Windy City';''', r'''const STORM_PREFIX = 'Chicago Jets';''')
sub(r'''/^Windy City/.test(names[g.home] || '') || /^Windy City/.test(names[g.away] || '')''',
    r'''/^Chicago Jets/.test(names[g.home] || '') || /^Chicago Jets/.test(names[g.away] || '')''')
sub(r'''const EDIT_KEY = 'storm2026';''', r'''const EDIT_KEY = 'jets2026';''', 2)
sub(r'''(EVENT && EVENT.file) || 'events/labor-day-girls-fest.json';''',
    r'''(EVENT && EVENT.file) || 'events/ccm-world-invite-chicago.json';''')
sub(r'''/\b(we|us|our|ours|storm|wcs)\b/''', r'''/\b(we|us|our|ours|jets)\b/''')

sub(r"""' The Storm take '""", r"""' The Jets take '""")
sub(r"""simulations of the rest of the group stage, the Storm '""",
    r"""simulations of the rest of the group stage, the Jets '""")
sub(r"""'; the Storm win about <b>'""", r"""'; the Jets win about <b>'""")
sub(r"""'</b>; the Storm&rsquo;s averaged <b>'""", r"""'</b>; the Jets&rsquo; averaged <b>'""")
sub(r"""'The Storm have faced the stronger field, by '""", r"""'The Jets have faced the stronger field, by '""")
sub(r"""'What are the Storm&rsquo;s chances?'""", r"""'What are the Jets&rsquo; chances?'""")
sub(r"""'Who do the Storm play next?'""", r"""'Who do the Jets play next?'""")

sub(r"""'</b> have climbed the North American list, <b>'""",
    r"""'</b> have climbed the USA 11U list, <b>'""")
sub(r"""' on the published North American list, so '""",
    r"""' on the USA 11U list, so '""")
sub(r"""    + 'list with these results in. Ranks are on the North American list, the one pool that '
    + 'holds all of these teams, counted over every team it rates &mdash; the same '
    + 'order the rankings page&rsquo;s North America tab shows the top 60 of, so a '
    + 'team&rsquo;s After here is its rank there. Below the top few that list is dense enough '
    + 'that a place or two is noise &mdash; read the rating change alongside '
    + 'the move. <a href="methodology.html">How this works &rarr;</a>';""",
    r"""    + 'list with these results in. Ranks are on MyHockeyRankings&rsquo; USA 11U list, '
    + 'counted over every team on it; a team MHR lists only at 12U has no rank there. '
    + 'That list is dense, so a place or two is noise &mdash; read the rating change '
    + 'alongside the move.';""")

# ---------------------------------------------------------------- crossover
# The 2015 Ribcor round of 16 pairs pool A with D and B with C, 1st v 4th and
# 2nd v 3rd, and the 5th and 6th places with the like finisher across.
sub(r"""    const cross = rules.crossover && placed.length === 2;
    function partner(i){
      if(cross){""", r"""    const cross = rules.crossover && placed.length === 2;
    function partner(i){
      // rules.crossPairs: [["A","D"],["B","C"]] names the pools that meet, and
      // rules.crossPlaces maps a finishing place (from 0) to the place it meets
      // across: [3, 2, 1, 0, 4, 5] is 1v4, 2v3 and like against like.
      if(rules.crossPairs){
        for(let gi = 0; gi < placed.length; gi++){
          const p = placed[gi].indexOf(i);
          if(p < 0) continue;
          let other = null;
          rules.crossPairs.forEach(function(pr){
            if(pr[0] === groups[gi]) other = pr[1];
            else if(pr[1] === groups[gi]) other = pr[0];
          });
          const oi = groups.indexOf(other);
          const q = rules.crossPlaces ? rules.crossPlaces[p] : p;
          return oi >= 0 && q != null ? placed[oi][q] : undefined;
        }
        return undefined;
      }
      if(cross){""")

P.write_text(s, encoding='utf-8')
print('ok')
