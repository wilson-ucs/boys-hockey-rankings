/* Capture the GameSheet schedule from your own browser.
 *
 * gamesheetstats is behind Cloudflare, which refuses an automated browser --
 * clearing the checkbox by hand just puts it back, in a loop. But an ordinary
 * browser session loads the site fine, so this reads the rows already on the
 * screen instead of pretending to be a scraper.
 *
 * The list is virtualised: only about twenty rows exist at any moment. So this
 * keeps harvesting while you scroll and accumulates the union, then copies the
 * lot as JSON.
 *
 * No "#" or "%" anywhere in here: this ends up inside a javascript: URL, and a
 * "#" would truncate it at the fragment.
 */
(function () {
  if (window.__gsGrab) { window.__gsGrab.open(); return; }

  var MONTHS = { Jan: 1, Feb: 2, Mar: 3, Apr: 4, May: 5, Jun: 6,
                 Jul: 7, Aug: 8, Sep: 9, Oct: 10, Nov: 11, Dec: 12 };
  var TIME = /^\d{1,2}:\d{2}\s*(AM|PM)$/i;
  var SCORE = /^(\d+)\s*[-–—:]\s*(\d+)$/;
  var DECISION = /^(?:F[/])?(OT|SO)$/i;
  var SKIP = /^(tournament|playoff|exhibition|now|final|live)$/i;
  var LIVE = /^live$/i;
  var ROUND = /(final|semi|quarter|qtr|consol|championship|bracket|place|medal)|^(?:qf|sf|cf)[- ]?[0-9]+$/i;

  /* Capture has to outlive the page. The schedule is best taken a day at a
   * time, and switching day is a full navigation that would otherwise throw
   * away everything gathered so far. Kept on gamesheetstats' own origin, so
   * three days can be collected in three passes and copied once at the end. */
  var STORE = 'gsGrab.v2';
  var epoch = 0;
  var games = {};

  /* Three day tabs are usually open at once, each running its own timer. If a
   * tab simply wrote its own copy the last writer would win and the other two
   * days would vanish -- and Reset in one tab would be undone a moment later by
   * the next tick of another. So the store is the accumulator: every write
   * merges into whatever is there, and an epoch lets a Reset tell the other
   * tabs to drop what they are holding. */
  function raw() {
    try {
      var v = JSON.parse(localStorage.getItem(STORE) || 'null');
      if (v && typeof v === 'object' && v.g) return v;
    } catch (e) {}
    return { e: 0, g: {} };
  }

  function save() {
    try {
      var cur = raw();
      if (cur.e !== epoch) { games = {}; epoch = cur.e; }
      for (var k in games) { if (games.hasOwnProperty(k)) cur.g[k] = games[k]; }
      /* A merge cannot express a deletion, so the eviction of a filled-in
       * bracket slot is re-applied to the merged set rather than carried. */
      evict(cur.g);
      cur.e = epoch;
      localStorage.setItem(STORE, JSON.stringify(cur));
      games = cur.g;
    } catch (e) {}
  }

  function reset() {
    epoch = Date.now();
    games = {};
    try { localStorage.setItem(STORE, JSON.stringify({ e: epoch, g: {} })); } catch (e) {}
  }

  (function () { var cur = raw(); epoch = cur.e; games = cur.g; })();

  function pad(v) { return ('0' + v).slice(-2); }

  function lines(cell) {
    return (cell.innerText || '').split('\n')
      .map(function (s) { return s.trim(); })
      .filter(function (s) { return s.length > 0; });
  }

  /* The table publishes its own column headers -- Date, Visitor, (blank), Home,
   * Location, #, Type -- so read them once and index by name. Guessing which
   * cell was the game number cost us every bracket row: those are numbered
   * "QF-1" and "SF-1", not "144", and a digits-only rule threw them away. */
  function columns(body) {
    var table = (body && body.closest)
              ? (body.closest('[data-slot=virtual-table]') || body.closest('[role=table]'))
              : null;
    if (!table) {
      table = document.querySelector('[data-slot=virtual-table]')
           || document.querySelector('[role=table]');
    }
    if (!table) return null;
    var heads = table.querySelectorAll('[role=columnheader]');
    if (!heads.length) return null;
    var out = [];
    for (var i = 0; i < heads.length; i++) {
      out.push((heads[i].innerText || '').trim().toLowerCase());
    }
    return out;
  }

  function byColumn(cells, cols) {
    var iVis = cols.indexOf('visitor'), iHome = cols.indexOf('home');
    var iNum = cols.indexOf(String.fromCharCode(35));
    if (iNum < 0) iNum = cols.indexOf('number');
    if (iNum < 0) iNum = cols.indexOf('game');
    if (iNum < 0) iNum = cols.indexOf('gm');
    if (iNum < 0) {
      for (var k = 0; k < cols.length; k++) {
        if (cols[k] === '' && k > iHome) { iNum = k; break; }
      }
    }
    if (iNum < 0) iNum = cols.indexOf('*');
    var iLoc = cols.indexOf('location'), iDate = cols.indexOf('date');
    if (iVis < 0 || iHome < 0) return null;

    var text = function (i) {
      return (i >= 0 && cells[i] && cells[i].length) ? cells[i] : [];
    };
    var roundName = null;
    var team = function (i) {
      var c = text(i);
      if (!c.length) return { name: null, div: null };
      var name = c[0];
      if (/^(tbd|to be determined|--|-|\?)$/i.test(name)) name = null;
      else if (!c[1] && ROUND.test(name)) {
        roundName = name;
        name = null;
      }
      return { name: name, div: c[1] || null };
    };

    var vis = team(iVis), home = team(iHome);
    var mid = (iHome - iVis === 2) ? text(iVis + 1) : [];
    var numCell = text(iNum);
    var raw = numCell.length ? numCell[0] : null;
    if (!raw) {
      /* Fall back to any short standalone token that is not something else. */
      for (var q = 0; q < cells.length; q++) {
        if (q === iVis || q === iHome || q === iLoc || q === iDate) continue;
        if (cells[q].length === 1 && cells[q][0].length <= 18
            && !TIME.test(cells[q][0]) && !SKIP.test(cells[q][0])
            && !SCORE.test(cells[q][0])) { raw = cells[q][0]; }
      }
    }
    if (!raw) return null;

    var num = raw, label = roundName;
    var split = raw.match(/^(\d+)\s+(.*)$/);
    if (split) { num = split[1]; label = split[2]; }

    var g = { n: num, label: label, date: null, time: null,
              rink: text(iLoc)[0] || null, division: vis.div || home.div || null,
              visitor: vis.name, home: home.name,
              visitorScore: null, homeScore: null, decision: null };

    var d = text(iDate);
    for (var a = 0; a < d.length; a++) {
      var dm = d[a].match(/^([A-Za-z]{3})[a-z]*\s+(\d{1,2}),\s*(\d{4})$/);
      if (dm && MONTHS[dm[1]]) {
        g.date = dm[3] + '-' + pad(MONTHS[dm[1]]) + '-' + pad(dm[2]);
      }
    }
    for (var b = 0; b < mid.length; b++) {
      var v = mid[b], sm = v.match(SCORE);
      if (sm) { g.visitorScore = +sm[1]; g.homeScore = +sm[2]; continue; }
      if (DECISION.test(v)) { g.decision = v.replace(/^F[/]/i, '').toUpperCase(); continue; }
      if (TIME.test(v)) g.time = v;
    }
    if (g.visitorScore !== null && !g.decision) g.decision = 'REG';
    if (anyLive(cells)) undecided(g);
    if (!g.label) {
      for (var z = 0; z < cells.length; z++) {
        for (var y = 0; y < cells[z].length; y++) {
          if (ROUND.test(cells[z][y])) {
            g.label = cells[z][y];
            z = cells.length;
            break;
          }
        }
      }
    }
    return g;
  }

  function parseRow(cells, cols) {
    if (cols) {
      var byCol = byColumn(cells, cols);
      if (byCol) return byCol;
    }
    var teams = [], i, j, c, v, m;
    for (i = 0; i < cells.length; i++) {
      // Divisions read "14U Group D" on our season and "U11 HL/LL" on others.
      if (cells[i].length >= 2 && /^(?:\d+U|U\d+)\b/i.test(cells[i][1])) teams.push(i);
    }

    var num = null, label = null, date = null, rink = null;
    for (i = 0; i < cells.length; i++) {
      c = cells[i];
      if (c.length !== 1) continue;
      v = c[0];
      m = v.match(/^([A-Za-z]{3})[a-z]*\s+(\d{1,2}),\s*(\d{4})$/);
      if (m && MONTHS[m[1]]) { date = m[3] + '-' + pad(MONTHS[m[1]]) + '-' + pad(m[2]); continue; }
      if (TIME.test(v) || SKIP.test(v)) continue;
      /* "144", or "142 S-Fnl 1 3v2" on a bracket row. */
      m = v.match(/^(\d+)(?:\s+(.*))?$/);
      if (m) { num = m[1]; label = m[2] || null; continue; }
      /* Before the teams are known the number column holds the round instead:
       * "14U QTR / CONSOL", "14U Semifinal". Reading it as the venue would
       * throw the row away, since a row with no number is not kept. */
      if (!num && ROUND.test(v)) { num = v; label = v; continue; }
      if (!rink || v.length > rink.length) rink = v;
    }
    if (!num) return null;

    var g = { n: num, label: label, date: date, time: null, rink: rink,
              division: null, visitor: null, home: null,
              visitorScore: null, homeScore: null, decision: null };

    if (teams.length >= 2) {
      var vi = teams[0], hi = teams[1];
      g.visitor = cells[vi][0];
      g.home = cells[hi][0];
      g.division = cells[vi][1];
      // The cell between the two teams: the faceoff time, or the score with
      // OT or SO on a second line once the game has been played.
      var mid = (hi - vi === 2) ? cells[vi + 1] : [];
      for (j = 0; j < mid.length; j++) {
        v = mid[j];
        m = v.match(SCORE);
        if (m) { g.visitorScore = +m[1]; g.homeScore = +m[2]; continue; }
        /* [/] rather than \/ so the source never contains two slashes in a row. */
        if (DECISION.test(v)) { g.decision = v.replace(/^F[/]/i, '').toUpperCase(); continue; }
        if (TIME.test(v)) g.time = v;
      }
      if (g.visitorScore !== null && !g.decision) g.decision = 'REG';
      if (anyLive(cells)) undecided(g);
    } else {
      // A bracket slot with nobody in it yet still has a time and a round name.
      for (i = 0; i < cells.length; i++) {
        for (j = 0; j < cells[i].length; j++) {
          v = cells[i][j];
          if (TIME.test(v)) g.time = v;
          if (!g.label && ROUND.test(v)) g.label = v;
        }
      }
    }
    return g;
  }

  /* A game being played carries a running score and a LIVE badge under it.
   * Taking that as the result would enter 1-3 for a game that finishes 4-3, so
   * the row is kept for its teams and time and the score is left off until the
   * badge goes. */
  function anyLive(cells) {
    for (var i = 0; i < cells.length; i++) {
      for (var j = 0; j < cells[i].length; j++) {
        if (LIVE.test(cells[i][j])) return true;
      }
    }
    return false;
  }

  function undecided(g) {
    g.visitorScore = null;
    g.homeScore = null;
    g.decision = null;
    g.live = true;
  }

  var misses = 0;

  function harvest() {
    /* Once a game starts, the site puts a LIVE GAMES table above ALL GAMES.
     * Reading only the first one would have captured four games and called it
     * the tournament. Both are read; the duplicates land on the same key. */
    var bodies = document.querySelectorAll('[data-slot=virtual-table-body]');
    if (!bodies.length) {
      /* Say why nothing is happening rather than sitting at zero in silence. */
      misses++;
      if (misses === 4) {
        if (/just a moment|verify you are human/i.test(document.title + ' ' + document.body.innerText)) {
          flash('Cloudflare is asking you to verify. Clear it, then the count starts.');
        } else {
          flash('No games here. This belongs on a GameSheet schedule tab -- open a day link and click the bookmark there.');
        }
      }
      return;
    }
    misses = 0;
    for (var b = 0; b < bodies.length; b++) {
      var cols = columns(bodies[b]);
      var rows = bodies[b].querySelectorAll('[role=row]');
      for (var i = 0; i < rows.length; i++) {
        var cells = [];
        var raw = rows[i].querySelectorAll('[role=cell]');
        for (var j = 0; j < raw.length; j++) cells.push(lines(raw[j]));
        if (!cells.length) continue;
        var g = parseRow(cells, cols);
        if (g) keep(g);
      }
    }
    save();
    paint();
  }

  /* Identity is the game number when there is one: that is exactly what a
   * number is for, and it survives a game being moved to another sheet or time.
   * Bracket rows have no number yet -- twelve of them all read "14U QTR /
   * CONSOL" -- so those are identified by when and where instead, which is
   * unique among the handful of rows in that state. When the teams are settled
   * the placeholder becomes a real three-digit number, so a numbered row also
   * evicts whatever slot it is standing in; otherwise the tournament would show
   * both the empty bracket and the game that filled it. */
  function evict(g) {
    for (var k in g) {
      if (!g.hasOwnProperty(k) || k.charAt(0) === 's') continue;
      var s = slotKey(g[k]);
      if (g.hasOwnProperty(s)) delete g[s];
    }
  }

  function slotKey(g) { return 's:' + [g.date || '', g.time || '', g.rink || ''].join('|'); }

  /* What makes a row itself, in the order the site gives us something to go on.
   *
   * A game number is best: it is exactly an identity, and it survives a game
   * moving sheet or time. A bracket game has none until the teams are settled,
   * so those fall back to when and where -- unique among the empty slots,
   * because an empty slot always shows a faceoff time.
   *
   * The teams are the middle case, and the one that was missing. Once a game
   * starts, the site puts the score where the time was, so a played bracket
   * game has no number AND no time: four of them on the same sheet all keyed
   * as "that rink, no time" and collapsed into one. Two teams and a date are
   * enough to tell them apart. */
  function idKey(g) {
    if (/^[0-9]+$/.test(String(g.n))) return 'n:' + g.n;
    if (g.visitor || g.home) {
      return 't:' + [g.date || '', g.visitor || '', g.home || ''].join('|');
    }
    return slotKey(g);
  }

  function keep(g) {
    var k = idKey(g);
    if (k.charAt(0) !== 's') {
      /* A game with an identity of its own is not also the empty slot it
       * grew out of. */
      delete games[slotKey(g)];
      games[k] = g;
    } else if (!games.hasOwnProperty(k) || !games[k].visitor) {
      games[k] = g;
    }
  }

  function list() {
    var out = [];
    for (var k in games) { if (games.hasOwnProperty(k)) out.push(games[k]); }
    return out.sort(function (a, b) {
      return (String(a.date) + ' ' + String(a.time)).localeCompare(
             (String(b.date) + ' ' + String(b.time)))
        || String(a.n).localeCompare(String(b.n));
    });
  }

  function payload() {
    var all = list();
    var withScores = all.filter(function (g) { return g.homeScore !== null; }).length;
    return { source: location.href, capturedAt: new Date().toISOString(),
             games: all.length, scored: withScores, rows: all };
  }

  var box, count, note, days;

  function paint() {
    if (!count) return;
    var all = list();
    var scored = all.filter(function (g) { return g.homeScore !== null; }).length;
    var slots = all.filter(function (g) { return !g.visitor && !g.home; }).length;
    var live = all.filter(function (g) { return g.live; }).length;
    count.textContent = all.length + ' games, ' + scored + ' with scores'
      + (live ? ', ' + live + ' still being played' : '')
      + (slots ? ', ' + slots + ' TBD' : '');
    if (!days) return;
    var byDay = {}, i;
    for (i = 0; i < all.length; i++) {
      var d = all[i].date || 'no date';
      byDay[d] = (byDay[d] || 0) + 1;
    }
    days.textContent = Object.keys(byDay).sort().map(function (d) {
      return d.slice(5) + ': ' + byDay[d];
    }).join('   ') || 'nothing captured yet';
  }

  function flash(msg) { if (note) note.textContent = msg; }

  function copy() {
    var p = payload();
    if (!p.games) {
      flash('Nothing captured yet. Scroll the list and watch the count.');
      return;
    }
    var text = JSON.stringify(p, null, 1);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(
        function () {
          flash('Copied ' + p.games + ' games (' + p.scored
              + ' with scores). Paste into the tournament page.');
        },
        function () { manual(text); });
    } else { manual(text); }
  }

  function manual(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('style', 'position:fixed;left:8px;right:8px;bottom:8px;height:38vh;' +
      'z-index:2147483647;font:12px monospace;padding:8px');
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    flash('Clipboard blocked. Select all in the box below and copy it.');
  }

  function button(labelText, fn) {
    var b = document.createElement('button');
    b.textContent = labelText;
    b.setAttribute('style', 'font:600 12px system-ui,sans-serif;padding:10px 12px;' +
      'min-height:42px;margin-right:6px;border-radius:6px;border:1px solid rgb(90,90,90);' +
      'background:rgb(40,40,40);color:rgb(255,255,255)');
    b.onclick = fn;
    return b;
  }

  function build() {
    box = document.createElement('div');
    box.setAttribute('style', 'position:fixed;top:10px;right:10px;z-index:2147483647;' +
      'background:rgb(17,17,17);color:rgb(255,255,255);border-radius:10px;padding:12px 14px;' +
      'font:13px/1.45 system-ui,sans-serif;box-shadow:0 8px 30px rgba(0,0,0,.45);' +
      'max-width:280px');
    count = document.createElement('div');
    count.setAttribute('style', 'font-weight:700;margin-bottom:4px');
    note = document.createElement('div');
    note.setAttribute('style', 'color:rgb(170,170,170);margin-bottom:9px;font-size:12px');
    note.textContent = 'Scroll the list; this keeps counting. Kept across days.';
    days = document.createElement('div');
    days.setAttribute('style', 'color:rgb(140,190,255);margin-bottom:9px;font-size:12px;'
      + 'font-family:ui-monospace,monospace');
    var bar = document.createElement('div');
    bar.appendChild(button('Copy', copy));
    bar.appendChild(button('Reset', function () {
      reset(); paint();
      flash('Cleared here and in the other day tabs. Reload them before scrolling again.');
    }));
    bar.appendChild(button('Close', function () { box.remove(); window.__gsGrab = null; }));
    box.appendChild(count);
    box.appendChild(note);
    box.appendChild(days);
    box.appendChild(bar);
    document.body.appendChild(box);
  }

  build();
  harvest();
  setInterval(harvest, 700);
  window.__gsGrab = { open: function () { if (box) box.style.display = 'block'; } };
})();
