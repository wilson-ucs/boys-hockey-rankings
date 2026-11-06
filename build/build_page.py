import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def _bookmarklet():
    """build/bookmarklet.js as a javascript: URL, comments and newlines removed."""
    import re as _re
    js = (HERE / 'bookmarklet.js').read_text(encoding='utf-8')
    js = _re.sub(r'/\*[\s\S]*?\*/', '', js)
    js = _re.sub(r'(?m)^\s*//.*$', '', js)
    js = _re.sub(r'\n\s*', ' ', js)
    js = _re.sub(r'\s{2,}', ' ', js).strip()
    # A trailing // comment is fatal once the newlines are gone: it swallows
    # the rest of the file. Comments in bookmarklet.js must be block comments
    # or sit on their own line, and this refuses to build if that slips.
    assert '//' not in js, 'bookmarklet.js must not use // comments'
    # A "#" would truncate the URL at the fragment and a "%" would be decoded.
    assert '#' not in js and '%' not in js, 'bookmarklet.js must avoid # and %'
    return 'javascript:' + js


# The rankings page's table data. This site has no rankings page.
data = {}

# build/bookmarklet.js, flattened into a javascript: URL for the score panel.
BOOKMARKLET_URL = _bookmarklet()

# Every page is this shell with four holes punched in it. The stylesheet and
# the theme tokens live here once, so the two pages cannot drift apart.
SHELL = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Roboto:wght@400;500;600;700&family=Roboto+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --paper:#eceff1; --card:#ffffff; --card-2:#f5f8f9;
  --ink:#0f1a20; --ink-2:#33454e; --muted:#64777f; --line:#d2dde1; --line-soft:#e3eaed;
  --accent:#4a308b; --accent-soft:rgba(74,48,139,.10);
  --up:#0a6b50; --up-bg:rgba(10,107,80,.10);
  --warn:#7a5200; --warn-bg:rgba(122,82,0,.10);
  --down:#9d4029; --down-bg:rgba(157,64,41,.10);
  --shadow:0 1px 2px rgba(15,26,32,.06), 0 8px 24px -16px rgba(15,26,32,.30);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#0a1013; --card:#121c21; --card-2:#16232a;
    --ink:#e6eef1; --ink-2:#bdcdd4; --muted:#8ba0a9; --line:#22323a; --line-soft:#1a272d;
    --accent:#a78be8; --accent-soft:rgba(167,139,232,.13);
    --up:#4bc79c; --up-bg:rgba(75,199,156,.13);
    --warn:#e0b45f; --warn-bg:rgba(224,180,95,.13);
    --down:#e08165; --down-bg:rgba(224,129,101,.13);
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -18px rgba(0,0,0,.9);
  }
}
:root[data-theme="dark"]{
  --paper:#0a1013; --card:#121c21; --card-2:#16232a;
  --ink:#e6eef1; --ink-2:#bdcdd4; --muted:#8ba0a9; --line:#22323a; --line-soft:#1a272d;
  --accent:#a78be8; --accent-soft:rgba(167,139,232,.13);
  --up:#4bc79c; --up-bg:rgba(75,199,156,.13);
  --warn:#e0b45f; --warn-bg:rgba(224,180,95,.13);
  --down:#e08165; --down-bg:rgba(224,129,101,.13);
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -18px rgba(0,0,0,.9);
}
*{box-sizing:border-box}
body{
  background:var(--paper); color:var(--ink);
  font:400 16px/1.6 Roboto,"Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px 72px}
h1,h2,h3{font-family:"Bebas Neue",Impact,"Arial Narrow",sans-serif;font-weight:400;
  text-transform:uppercase;letter-spacing:.03em;text-wrap:balance;margin:0}
.eyebrow{
  font:600 11px/1 "Roboto Mono",ui-monospace,monospace;
  letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
}

/* ---------- header nav ---------- */
.nav{display:flex;flex-wrap:wrap;gap:2px;padding-top:20px}
/* Three tabs are two characters too wide for a 320px phone, and a nav
   that will not wrap takes the whole page sideways with it. */
@media (max-width:360px){.nav a{padding-left:11px;padding-right:11px;letter-spacing:.09em}}
.nav a{
  font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);text-decoration:none;padding:9px 14px;border-radius:3px 3px 0 0;
}
.nav a:hover{color:var(--ink-2);background:var(--card-2)}
.nav a[aria-current="page"]{color:var(--ink);background:var(--card);box-shadow:inset 0 -2px 0 var(--accent)}
.nav a:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}

/* ---------- masthead ---------- */
.masthead{border-bottom:1px solid var(--line);padding:22px 0 26px;margin-bottom:30px}
.masthead h1{font-size:clamp(32px,5.4vw,50px);font-weight:400;letter-spacing:.045em;line-height:1.02;margin:12px 0 10px}
.masthead h1 .thin{font-size:.64em;letter-spacing:.07em;color:var(--ink-2)}
.dek{max-width:62ch;color:var(--ink-2);font-size:16.5px;margin:0}
.stamp{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:18px}
.stamp span{font:500 12.5px/1 "Roboto Mono",ui-monospace,monospace;color:var(--muted)}
.stamp b{color:var(--ink);font-weight:600}
.disclaimer{margin:14px 0 0;font-size:13.5px;color:var(--muted)}
.disclaimer a{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-soft);white-space:nowrap}
.disclaimer a:hover{border-bottom-color:var(--accent)}
.disclaimer a:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:2px}

/* ---------- validation strip ---------- */
.vstrip{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:1px;background:var(--line-soft);border:1px solid var(--line);border-radius:3px;overflow:hidden;margin:26px 0 34px}
.vcell{background:var(--card);padding:14px 16px}
.vcell .k{font:600 24px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.vcell .l{font-size:13px;color:var(--muted);margin-top:5px;line-height:1.35}

/* ---------- storm callout ---------- */
.storm{
  background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:2px;padding:20px 22px;margin-bottom:34px;box-shadow:var(--shadow);
  display:grid;grid-template-columns:minmax(0,1fr) auto;gap:22px;align-items:center;
}
.storm h3{font-size:22px;font-weight:400;letter-spacing:.045em;margin-bottom:6px}
.storm p{margin:0;font-size:14.5px;color:var(--ink-2);max-width:58ch}
.storm > *{min-width:0}
.storm .figs{display:flex;flex-wrap:wrap;gap:20px 26px}
.storm .fig .n{white-space:nowrap}
.storm p.scout-link{margin-top:12px;font-size:14px}
.storm .scout{margin-top:12px;padding-top:12px;border-top:1px solid var(--line);font-size:14px;max-width:62ch}
.storm .scout h4{font-size:15px;font-weight:600;margin:0 0 4px}
.storm .scout h5{font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin:14px 0 6px}
.storm .scout ol{margin:0;padding-left:20px}
.storm .scout li{margin:3px 0}
.storm .scout p{margin:0 0 4px}
.storm .fig{text-align:right}
.storm .fig .n{font:600 30px/1 "Roboto Mono",ui-monospace,monospace;color:var(--accent);font-variant-numeric:tabular-nums}
.storm .fig.sm .n{color:var(--muted)}
.storm .fig .c{font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin-top:7px}
@media (max-width:700px){.storm{grid-template-columns:1fr}.storm .figs{justify-content:flex-start;gap:18px 22px}.storm .fig{text-align:left}}
/* On a phone the row becomes a grid so the captions line up in columns
   instead of drifting with each number's width. */
@media (max-width:460px){
  .storm{padding:17px 16px}
  .storm .figs{display:grid;grid-template-columns:repeat(auto-fit,minmax(92px,1fr));gap:15px 14px}
  .storm .fig .n{font-size:26px}
  .storm .fig .c{letter-spacing:.08em;font-size:9.5px}
}

/* ---------- tabs + table ---------- */
/* Five tabs do not fit a 320px phone in one line, and a strip that will not
   wrap takes the page sideways with it. */
.tabs{display:flex;flex-wrap:wrap;gap:2px;margin-bottom:0}
.tab .sm{display:none}
.tab{
  font:600 13px/1 Roboto,"Helvetica Neue",Arial,sans-serif;letter-spacing:.01em;
  padding:11px 16px;border:1px solid var(--line);border-bottom:none;background:var(--card-2);
  color:var(--muted);cursor:pointer;border-radius:3px 3px 0 0;
}
.tab[aria-selected="true"]{background:var(--card);color:var(--ink);box-shadow:inset 0 2px 0 var(--accent)}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
/* Two tabs wrapping onto two rows on a phone wastes a line to say nothing. The
   long label is the one worth reading where there is room for it; below that
   the tab carries a short one instead of being cut in half. */
@media (max-width:560px){
  .tab{padding:11px 11px;font-size:12.5px}
  .tab .lg{display:none}
  .tab .sm{display:inline}
}
.tablewrap{border:1px solid var(--line);background:var(--card);border-radius:0 3px 3px 3px;overflow-x:auto;box-shadow:var(--shadow)}
/* A tournament panel holds whole sections rather than one table, so it gets
   air above it instead of the table frame's border. */
.tpanel{padding-top:26px}
.anwrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(280px,100%),1fr));gap:14px;margin:0 0 24px}
.anx{border:1px solid var(--line);background:var(--card);border-radius:3px;padding:16px 18px;box-shadow:var(--shadow)}
.anx h3{font-size:15px;letter-spacing:.05em;margin:0 0 12px}
.anlist{list-style:none;margin:0;padding:0;counter-reset:an}
.anlist li{display:flex;align-items:baseline;gap:9px;padding:7px 0;border-top:1px solid var(--line-soft);font-size:13.5px}
.anlist li:first-child{border-top:0}
.anlist li.hl{font-weight:600}
.ann{flex:1 1 auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.anm{font:600 12px/1 "Roboto Mono",ui-monospace,monospace;white-space:nowrap}
.anr{font:500 11.5px/1 "Roboto Mono",ui-monospace,monospace;color:var(--muted);white-space:nowrap}
/* Seventy teams is too many to scroll past, so the box narrows the list
   rather than the list being a dropdown you hunt through. Every team is a
   toggle; the search only decides which toggles are on screen. */
.sfil{margin:0 0 16px}
/* The season's other tournaments, next to the one on screen. */
.t-pick{display:flex;align-items:center;gap:9px;margin:14px 0 0;flex-wrap:wrap}
.t-pick label{font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.t-pick select{font:400 13.5px/1.2 Roboto,"Helvetica Neue",Arial,sans-serif;padding:8px 10px;max-width:100%;border:1px solid var(--line);border-radius:3px;background:var(--card);color:var(--ink)}
.t-pick select:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.sfil-bar{display:flex;flex-wrap:wrap;align-items:center;gap:9px;margin-bottom:10px}
.sfil-q{font:400 14px/1.2 Roboto,"Helvetica Neue",Arial,sans-serif;padding:9px 11px;min-width:190px;flex:1 1 190px;max-width:280px;border:1px solid var(--line);border-radius:3px;background:var(--card);color:var(--ink)}
.sfil-q:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.sfil-all{font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-2);background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 13px;cursor:pointer}
.sfil-all:hover{border-color:var(--accent);color:var(--accent)}
.sfil-all:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sfil-said{font:500 12px/1.4 "Roboto Mono",ui-monospace,monospace;color:var(--muted)}
.sfil-list{display:flex;flex-wrap:wrap;gap:6px;max-height:168px;overflow-y:auto;padding:2px;border:1px solid var(--line);border-radius:3px;background:var(--card);margin-top:2px}
/* Chosen teams stay in view with the list shut, or you could filter yourself
   into a short table with no way to see what caused it. */
.sfil-picked{display:flex;flex-wrap:wrap;gap:6px}
.sfil-picked:not(:empty){margin-bottom:4px}
.sfil-x{display:inline-block;margin:-8px -11px -8px 4px;padding:8px 11px 8px 7px;opacity:.75;font-size:14px;line-height:1}
.sfil-t{display:inline-flex;align-items:center;min-height:34px;font:500 12.5px/1 Roboto,"Helvetica Neue",Arial,sans-serif;padding:8px 11px;border:1px solid var(--line);border-radius:17px;background:var(--card);color:var(--ink-2);cursor:pointer;white-space:nowrap}
.sfil-t:hover{border-color:var(--accent)}
.sfil-t[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
.sfil-t:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sfil-none{font:500 12px/1.4 Roboto,sans-serif;color:var(--muted);padding:6px 2px}
.tpanel > :first-child{margin-top:0}
/* Three lines is enough to know whether you want the rest. The button is
   only added when the text actually overflows, measured after render. */
.clamp{display:-webkit-box;-webkit-box-orient:vertical;-webkit-line-clamp:3;overflow:hidden}
.clamp.open{display:block;-webkit-line-clamp:unset}
/* Doubled class only to outrank .t-sub's own bottom margin, which is
   defined later in this sheet. Without it the paragraph's margin sat
   between the last line and the link. */
.clamp.clamp{margin-bottom:0}
/* The paragraph's own bottom margin used to sit between the last line and
   the link, which read as a gap rather than as part of the text. The
   margin moves below the link instead. */
.clamp-more{background:none;border:0;padding:0;margin:0 0 15px;cursor:pointer;font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.clamp-more:hover{text-decoration:underline}
.clamp-more:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
table{border-collapse:collapse;width:100%;min-width:660px}
thead th{
  font:600 10.5px/1.2 "Roboto Mono",ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;
  color:var(--muted);text-align:left;padding:13px 12px;border-bottom:1px solid var(--line);white-space:nowrap;
}
th.num,td.num{text-align:right;font-variant-numeric:tabular-nums}
th.srt{cursor:pointer;user-select:none;white-space:nowrap}
th.srt:hover{color:var(--ink-2)}
th.srt .car{opacity:0;margin-left:4px}
th.srt[aria-sort] .car{opacity:1;color:var(--accent)}
th.srt:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
td.adj{font:600 15px/1 "Roboto Mono",ui-monospace,monospace;width:78px;color:var(--ink)}
td.gp{font:500 13px/1 "Roboto Mono",ui-monospace,monospace;color:var(--muted);width:38px}
td.shift{font:600 12.5px/1 "Roboto Mono",ui-monospace,monospace;width:62px}
td.shift.up{color:var(--up)}
td.shift.dn{color:var(--down)}
td.shift.flat{color:var(--muted)}
tbody td{padding:10px 12px;border-bottom:1px solid var(--line-soft);font-size:14.5px;vertical-align:middle}
tbody tr:last-child td{border-bottom:none}
tbody tr.hl{background:var(--accent-soft)}
td.rk{font:600 15px/1 "Roboto Mono",ui-monospace,monospace;color:var(--ink);width:46px;font-variant-numeric:tabular-nums}
td.team{font-weight:500;min-width:250px}
td.team .loc{color:var(--muted);font:500 12px/1 "Roboto Mono",ui-monospace,monospace;margin-left:8px}
td.proj{font:600 15px/1 "Roboto Mono",ui-monospace,monospace;width:78px}
td.inp{font:400 12.5px/1.35 "Roboto Mono",ui-monospace,monospace;color:var(--muted);white-space:nowrap}
.mv{display:inline-block;min-width:40px;text-align:center;padding:2.5px 6px;border-radius:2px;
  font:600 11.5px/1.25 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
.mv.up{color:var(--up);background:var(--up-bg)}
.mv.dn{color:var(--down);background:var(--down-bg)}
.mv.fl{color:var(--muted)}
.flag{font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.08em;
  border:1px solid var(--line);color:var(--muted);padding:3px 5px;border-radius:2px}
/* The browser hides `hidden` with [hidden]{display:none} in its own sheet, and
   any class selector here outranks that. Several elements toggled by `hidden`
   also carry a class that sets display -- .sfil-list, .storm, .figs, .t-pick --
   so without this the attribute is set, the element stays on screen, and every
   check of `el.hidden` says it worked. */
[hidden]{display:none!important}

table.mini{min-width:0;width:auto;margin:0 0 20px;border:1px solid var(--line);background:var(--card)}
table.mini th,table.mini td{padding:7px 16px;font-size:13.5px}
table.mini thead th{font:600 10px/1.2 "Roboto Mono",ui-monospace,monospace;letter-spacing:.1em}
.eq{font:500 15px/1.5 "Roboto Mono",ui-monospace,monospace;color:var(--ink);background:var(--card-2);border-left:2px solid var(--accent);padding:12px 16px;margin:0 0 18px;max-width:46ch;overflow-x:auto}

.legend{display:flex;flex-wrap:wrap;gap:6px 20px;margin:12px 2px 40px;font-size:12.5px;color:var(--muted)}
.muted{color:var(--muted)}

/* ---------- tournament ---------- */
.t-empty{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:38px 22px;margin:30px 0;text-align:center;color:var(--muted);font-size:14px;box-shadow:var(--shadow)}
.t-empty b{display:block;color:var(--ink);font-size:17px;margin-bottom:8px;font-weight:600}
.t-empty code{font:500 13px/1 "Roboto Mono",ui-monospace,monospace;color:var(--ink-2)}
.t-sec h2{font-size:27px;letter-spacing:.04em;margin:44px 0 6px;padding-top:26px;border-top:1px solid var(--line)}
.t-sub{max-width:68ch;color:var(--muted);font-size:13px;margin:0 0 14px}
.gwrap{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(430px,100%),1fr));gap:14px}
.gcard{background:var(--card);border:1px solid var(--line);border-radius:3px;box-shadow:var(--shadow);overflow-x:auto}
.gcard h4{font-size:19px;padding:13px 14px 9px;border-bottom:1px solid var(--line-soft)}
.gcard thead th{font:500 10.5px/1.2 "Roboto Mono",ui-monospace,monospace;letter-spacing:.11em;padding:12px 8px}
.gcard tbody td{padding:9px 8px;border-bottom:1px solid var(--line-soft);font-size:14px}
table.st{min-width:430px}
/* Seven columns will not fit a phone honestly, so the table scrolls inside
   its own card rather than taking the page with it. Trimming the gutters
   first keeps that scroll to a nudge instead of a journey. */
@media (max-width:460px){
  .gcard{overflow-x:auto}
  table.st{min-width:346px;font-size:12px}
  table.st td.tm{max-width:128px}
}
table.st td.tm{font-weight:500;white-space:nowrap;max-width:190px;overflow:hidden;text-overflow:ellipsis}
/* Pts, G% and S% were touching while Team hoarded the slack. A width hint
   sends spare space to the three numeric columns instead, and the extra left
   padding separates them from each other. */
.gcard table.st th:nth-last-child(-n+3),
.gcard table.st td:nth-last-child(-n+3){padding-left:18px}
@media (max-width:460px){
  .gcard table.st th:nth-last-child(-n+3),
  .gcard table.st td:nth-last-child(-n+3){padding-left:8px}
}
.gcard table.st th:nth-last-child(-n+3){width:14%}
td.pend{color:var(--muted)}
td.gold{font-weight:700;width:1%}
.tag{font:500 9.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase;border:1px solid var(--accent);color:var(--accent);border-radius:2px;padding:2px 4px;margin-left:5px;vertical-align:1px;white-space:nowrap}
.t-when{font:500 12px/1.4 "Roboto Mono",ui-monospace,monospace;color:var(--muted);white-space:nowrap}
tr.dayrow td{background:var(--card-2);font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-2);padding:11px 12px;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
tbody tr.dayrow:first-child td{border-top:none}
.t-gd{font:600 14px/1 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}
.t-wp{font:600 12px/1 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;color:var(--muted);margin-left:5px}
.t-seed{font:600 11.5px/1 "Roboto Mono",ui-monospace,monospace;color:var(--muted);font-variant-numeric:tabular-nums;margin-left:5px}
.t-bar{display:flex;align-items:center;gap:13px;flex-wrap:wrap;margin-top:16px}
.t-refresh{font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-2);background:var(--card);border:1px solid var(--line);border-radius:3px;padding:9px 14px;cursor:pointer}
.t-refresh:hover:not(:disabled){border-color:var(--accent);color:var(--accent)}
.t-refresh:disabled{opacity:.5;cursor:default}
.t-refresh:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.t-said{font:500 12px/1.4 "Roboto Mono",ui-monospace,monospace;color:var(--muted)}
.t-run{display:flex;align-items:center;gap:9px;flex-wrap:wrap;font:500 12px/1.5 "Roboto Mono",ui-monospace,monospace;color:var(--muted)}
.t-score{font:600 15px/1 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;color:var(--ink)}
.t-note{color:var(--muted);font-size:12.5px;margin:10px 2px 30px}
.unrk{display:inline-block;font:600 9.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.09em;text-transform:uppercase;border:1px dashed var(--down);color:var(--down);padding:2px 5px;border-radius:2px;margin-left:7px;white-space:nowrap;vertical-align:1px}
.ask-bar{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 18px;max-width:640px}
.ask-bar input{flex:1 1 260px;min-width:0;font:500 14px/1.2 Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:3px;padding:11px 12px}
.ask-bar input:focus{outline:2px solid var(--accent);outline-offset:-1px}
#t-ask-out p{max-width:68ch;font-size:14px;margin:0 0 12px}
#t-ask-out .t-mini{max-width:520px;margin-bottom:18px}
ul.ask-eg{list-style:none;margin:0 0 8px;padding:0;display:flex;flex-wrap:wrap;gap:8px}
ul.ask-eg li{margin:0}
.ask-q{display:inline-block;cursor:pointer;font:500 12.5px/1 Roboto,"Helvetica Neue",Arial,sans-serif;color:var(--ink-2);background:var(--card-2);border:1px solid var(--line);border-radius:14px;padding:8px 12px}
.ask-q:hover{border-color:var(--accent);color:var(--accent)}
.tl{cursor:pointer;border-bottom:1px dotted var(--line);}
.tl:hover{color:var(--accent);border-bottom-color:var(--accent)}
.tl:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.t-mini{width:100%;min-width:0;margin-top:12px}
.t-mini td{padding:6px 0;border-bottom:1px solid var(--line-soft);font-size:13.5px}
.t-mini tr:last-child td{border-bottom:none}
.t-mini td:last-child{text-align:right;font:600 13px/1 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums}

/* ---------- add a game (only drawn when unlocked) ---------- */
.ga-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px 14px;margin:0 0 16px;max-width:760px}
.ga-form label{display:flex;flex-direction:column;gap:6px;font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.11em;text-transform:uppercase;color:var(--muted);min-width:0}
.ga-form label.wide{grid-column:span 2}
@media (max-width:560px){.ga-form label.wide{grid-column:span 1}}
.ga-form input,.ga-form select{font:500 14px/1 "Roboto Mono",ui-monospace,monospace;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:3px;padding:10px;min-width:0;width:100%}
.ga-form input:focus,.ga-form select:focus{outline:2px solid var(--accent);outline-offset:-1px}

/* ---------- score entry (only drawn when unlocked) ---------- */
.sc-bar{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:0 0 16px}
.sc-toggle,.sc-act{font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.12em;
  text-transform:uppercase;color:var(--muted);background:var(--card-2);
  border:1px solid var(--line);border-radius:3px;padding:0 15px;min-height:46px;cursor:pointer}
.sc-toggle[aria-pressed="true"]{background:var(--card);color:var(--ink);
  box-shadow:inset 0 -2px 0 var(--accent)}
.sc-act:hover{border-color:var(--accent);color:var(--accent)}
.sc-note{font:500 12px/1.5 "Roboto Mono",ui-monospace,monospace;color:var(--muted);
  margin:0 0 14px}
.sc-note b{color:var(--warn)}
.sc-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:12px}
.sc-game{background:var(--card);border:1px solid var(--line);border-radius:3px;
  box-shadow:var(--shadow);padding:13px 14px}
.sc-game.hl{background:var(--accent-soft)}
.sc-game.mismatch{border-color:var(--warn)}
.sc-head{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin-bottom:10px;
  font:600 10.5px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.11em;
  text-transform:uppercase;color:var(--muted)}
.sc-num{color:var(--ink-2)}
.sc-src{border:1px solid var(--line);border-radius:2px;padding:3px 6px}
.sc-src.is-manual{color:var(--accent);border-color:var(--accent)}
.sc-src.is-scraped{color:var(--up);border-color:var(--up)}
.sc-row{display:flex;align-items:center;gap:12px;padding:8px 0}
.sc-row + .sc-row{border-top:1px solid var(--line-soft)}
.sc-name{flex:1;font-size:15px;font-weight:500;line-height:1.3}
/* 19px keeps iOS from zooming the page when the field takes focus. */
.sc-in{width:78px;min-height:50px;padding:0 6px;text-align:center;
  font:600 19px/1 "Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;
  color:var(--ink);background:var(--card-2);border:1px solid var(--line);border-radius:4px;
  -moz-appearance:textfield}
.sc-in:focus{outline:2px solid var(--accent);outline-offset:1px;background:var(--card)}
.sc-in::-webkit-outer-spin-button,.sc-in::-webkit-inner-spin-button{
  -webkit-appearance:none;margin:0}
.sc-dec{display:flex;gap:6px;margin-top:10px}
.sc-dec button{flex:1;font:600 10px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);background:var(--card-2);border:1px solid var(--line);border-radius:3px;min-height:44px;cursor:pointer}
.sc-dec button[aria-pressed="true"]{color:var(--ink);background:var(--card);border-color:var(--accent);box-shadow:inset 0 -2px 0 var(--accent)}
.sc-foot{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:10px}
.sc-clear{font:600 10px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.1em;
  text-transform:uppercase;color:var(--muted);background:none;border:1px solid var(--line);
  border-radius:3px;padding:0 13px;min-height:44px;cursor:pointer}
.sc-clear:hover{border-color:var(--down);color:var(--down)}
.sc-flag{font:500 11.5px/1.35 "Roboto Mono",ui-monospace,monospace;color:var(--warn)}
/* The panel sits directly above the Storm callout, which has no rule of its
   own to separate them. */
#t-edit{margin-bottom:44px}
.sc-bm{margin:0 0 24px;padding-bottom:20px;border-bottom:1px solid var(--line-soft)}
.sc-bm p{font:500 12px/1.6 "Roboto Mono",ui-monospace,monospace;color:var(--muted);max-width:70ch;margin:0 0 10px}
.sc-days{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px}
.sc-days a{flex:1 1 150px;text-align:center;font:600 11px/1.3 "Roboto Mono",ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);background:var(--card);border:1px solid var(--line);border-radius:3px;padding:14px 10px;text-decoration:none;min-height:46px}
.sc-days a:hover{border-color:var(--accent);color:var(--accent)}
.sc-days a b{display:block;color:var(--muted);font-weight:500;font-size:10px;letter-spacing:.06em;margin-top:3px}
.sc-bm a{display:inline-block;font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);border:1px solid var(--accent);border-radius:3px;padding:14px 16px;text-decoration:none;margin-right:8px}
.sc-paste{width:100%;min-height:90px;margin:12px 0 10px;padding:11px;font:500 12px/1.5 "Roboto Mono",ui-monospace,monospace;color:var(--ink);background:var(--card-2);border:1px solid var(--line);border-radius:3px}
.sc-paste:focus{outline:2px solid var(--accent);outline-offset:1px}
.sc-result{font:500 12px/1.7 "Roboto Mono",ui-monospace,monospace;color:var(--muted);margin-top:10px}
.sc-result b{color:var(--ink-2)}
.sc-result .bad{color:var(--down)}
.sc-result .warn{color:var(--warn)}
.sc-result .ok{color:var(--up)}
.sc-out{width:100%;min-height:130px;margin-top:14px;padding:11px;
  font:500 12px/1.55 "Roboto Mono",ui-monospace,monospace;color:var(--ink);
  background:var(--card-2);border:1px solid var(--line);border-radius:3px}

/* ---------- prose ---------- */
section.doc{margin-top:14px}
section.doc h2{font-size:27px;font-weight:400;letter-spacing:.04em;margin:44px 0 6px;padding-top:26px;border-top:1px solid var(--line)}
section.doc h3{font-size:18px;font-weight:400;margin:26px 0 6px;letter-spacing:.055em}
section.doc p{max-width:68ch;color:var(--ink-2);margin:9px 0}
section.doc ul{max-width:68ch;color:var(--ink-2);padding-left:19px;margin:9px 0}
section.doc li{margin:5px 0}
section.doc strong{color:var(--ink);font-weight:600}
.eq{
  background:var(--card);border:1px solid var(--line);border-radius:3px;
  padding:16px 18px;margin:16px 0;overflow-x:auto;
  font:500 13.5px/1.85 "Roboto Mono",ui-monospace,monospace;color:var(--ink);
}
.eq .cm{color:var(--muted)}
.eq .hi{color:var(--accent)}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin:18px 0}
.panel{background:var(--card);border:1px solid var(--line);border-radius:3px;padding:16px 18px}
.panel h4{font:600 11px/1 "Roboto Mono",ui-monospace,monospace;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
.panel table{min-width:0;width:100%}
.panel td{padding:6px 0;border-bottom:1px solid var(--line-soft);font-size:13.5px}
.panel td:last-child{text-align:right;font-family:"Roboto Mono",ui-monospace,monospace;font-variant-numeric:tabular-nums;font-weight:500}
.panel tr:last-child td{border-bottom:none}
footer{margin-top:46px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
footer a{color:var(--ink-2)}

/* ---------- phones ----------
   Every table here was about 900px wide in a 334px window, so two thirds of
   each row sat off the edge -- and the columns that say which row you are
   reading sat behind the ones that do not. The rank came before the team, the
   rink came between the teams and the score.

   Below 560px nothing is allowed to force a width: the long text wraps, the
   detail that belongs to a name moves underneath it, and the analytical
   columns go away. All of them are still there on a laptop. `.tsm` is a line
   that exists only on a phone, `.ism` the same inline, `.lgo` a label that
   gives way to a shorter one, and `.hide-sm` a column that goes. */
.tsm,.ism{display:none}
@media (max-width:900px){
  table,table.st{min-width:0}
  /* `table.st td.tm` outranks a bare `td.tm` whatever the source order, so
     the standings cell has to be named the same way or it keeps its nowrap
     and truncates a club to "Pittsburgh Penguins ..." instead of wrapping. */
  td.team,td.tm,table.st td.tm{min-width:0;white-space:normal;
    overflow:visible;text-overflow:clip}
  .hide-sm{display:none}
  .tsm{display:block;font:500 11.5px/1.35 "Roboto Mono",ui-monospace,monospace;
       color:var(--muted);letter-spacing:0;margin-top:4px;white-space:normal}
  .ism{display:inline}
  .lgo{display:none}
  td.team .loc{display:block;margin:4px 0 0}
  thead th{padding:11px 7px;letter-spacing:.06em}
  tbody td{padding:9px 7px;font-size:13.5px;vertical-align:top}
  td.rk{width:auto;padding-right:2px}
  td.adj,td.proj{width:auto}
  /* The badge is 40px wide so a column of them lines up. In a narrow cell
     that width is what pushes it onto its own line under the score. */
  .mv{min-width:0;padding:2px 5px;font-size:10.5px}
  /* The 18px gutter that separates the odds from the record is most of what
     is left over the edge once the seed and the goals have moved. */
  .gcard table.st th:nth-last-child(-n+3),
  .gcard table.st td:nth-last-child(-n+3){padding-left:7px}
  .t-when{font-size:11.5px}
  .t-score{font-size:14px}
  table.mini th,table.mini td{padding:7px 9px;font-size:13px}
  .sfil-t{min-height:42px;padding:10px 14px;font-size:13.5px}
  .sfil-x{margin:-10px -14px -10px 6px;padding:10px 14px 10px 8px;font-size:17px}
}

/* A standings card is a column of a grid, so at 320px it has 264px to work
   with rather than the page's 334. The team name is the only thing that can
   give, and the record, the points and the odds are why the card exists. */
@media (max-width:400px){
  /* The last thing that will not shrink is a team name with a badge stuck to
     it, so below 400 those are allowed to wrap and the cell is capped. */
  td.team{max-width:150px}
  .tag,.unrk{white-space:normal}
  .gcard table.st td.tm{max-width:116px}
  .gcard tbody td,.gcard thead th{padding-left:5px;padding-right:5px}
  .gcard table.st th:nth-last-child(-n+3),
  .gcard table.st td:nth-last-child(-n+3){padding-left:5px}
}
</style>
</head>
<body>

<div class="wrap">

<nav class="nav" aria-label="Pages">
__NAV__
</nav>

__MAIN__

<footer>
  Ratings from <a href="https://myhockeyrankings.com" target="_blank" rel="noopener noreferrer">myhockeyrankings.com</a>, USA 11U and 12U lists. Predictions are independent estimates and are not produced or endorsed by MyHockeyRankings.
</footer>
</div>
__SCRIPT__
</body>
</html>
'''

RANKINGS_MAIN = r'''<header class="masthead">
  <div class="eyebrow">Preseason model &middot; 2026&ndash;27 &middot; last updated __UPDATED__</div>
  <h1>Girls 14U / U15<br><span class="thin">projected preseason rankings</span></h1>
  <p class="dek">MyHockeyRankings publishes nothing for 2026&ndash;27 until 30 September. Until then this is a projection from last season&rsquo;s MHR ratings &mdash; the returning group and the birth&#8209;year class moving up behind them &mdash; moved by the games each team has actually played.</p>
  <div class="stamp">
    <span>Source <b>myhockeyrankings.com</b></span>
    <span>Fitted on <b>2 age&#8209;up transitions</b></span>
    <span>Sample <b>219 teams</b></span>
  </div>
  <p class="disclaimer">Projected, not measured &mdash; &plusmn;1.4 rating points.</p>
</header>

<div class="storm">
  <div>
    <h3>Windy City Storm 14U</h3>
    <p>The Storm ranked <strong>13th in the USA at both 14U and 12U</strong> last season, so the returning group and the incoming 2013s point to exactly the same place &mdash; the model has no internal argument to resolve. Only Boston Jr Eagles Maroon (4th and 4th) matches that agreement in the American top 20.</p>
  </div>
  <div class="figs">
    <div class="fig"><div class="n" id="st-usa">12</div><div class="c">USA 14U</div></div>
    <div class="fig"><div class="n" id="st-na">18</div><div class="c">N. America</div></div>
    <div class="fig"><div class="n" id="st-rating">96.54</div>
      <div class="c" id="st-rating-c">proj. rating</div></div>
  </div>
</div>

<div class="tabs" role="tablist">
  <button class="tab" role="tab" id="tab-usa" aria-controls="p-usa" aria-selected="true"><span class="lg">USA Girls 14U &mdash; Top 30</span><span class="sm">USA &middot; Top 30</span></button>
  <button class="tab" role="tab" id="tab-na" aria-controls="p-na" aria-selected="false"><span class="lg">North America 14U / U15 &mdash; Top 60</span><span class="sm">N. America &middot; Top 60</span></button>
</div>
<div class="tablewrap">
  <div id="p-usa" role="tabpanel" aria-labelledby="tab-usa"></div>
  <div id="p-na" role="tabpanel" aria-labelledby="tab-na" hidden></div>
</div>
<div class="legend">
  <span><b>#</b> = rank among every rated team on today&rsquo;s ratings; each tab shows the top of that order, so a team plays its way on and off it.</span>
  <span><b>Move</b> = places up or down since the weekly MyHockeyRankings refresh<span id="mv-since"></span>: the change from the order this list showed the day before.</span>
  <span><b>Inputs</b> = the org&rsquo;s 2025&ndash;26 rank at the older age, then at the younger age.</span>
  <span><b>n/r</b> = no ranked team at the younger age; projection uses the returning group only.</span>
  <span id="adj-note"></span>
</div>'''

METHODOLOGY_MAIN = r'''<div class="vstrip">
  <div class="vcell"><div class="k">0.74</div><div class="l">Rank correlation with actual finishing order, on a season the model never saw</div></div>
  <div class="vcell"><div class="k">0.67</div><div class="l">Same test, carrying last year&rsquo;s rating forward unchanged</div></div>
  <div class="vcell"><div class="k">&plusmn;1.4</div><div class="l">Typical error of a projected rating, in MHR points (&asymp; goals per game)</div></div>
  <div class="vcell"><div class="k">57 / 43</div><div class="l">Weight on the returning 14U team vs. the incoming 12U class</div></div>
</div>

<section class="doc">

<h2>How these were built</h2>

<p>MyHockeyRankings solves one equation for every team: <strong>rating = average goal differential + strength of schedule</strong>, where strength of schedule is the mean rating of the opponents faced, goal differential in any single game is capped at seven, and the whole system is solved iteratively until it settles. There is no human voting and no preseason seeding. Two consequences drive everything below.</p>

<p>First, a rating difference is a <em>prediction of goal differential</em>. Ninety-seven against ninety-five means the first team is expected to win by about two. That makes ratings addable and averageable in a way that poll positions are not, so the whole projection can be done in rating space and converted to ranks at the end.</p>

<p>Second, ratings are only comparable inside a connected web of games. USA 14U and Canadian U15 teams do meet often enough at tournaments that MHR carries them on one scale &mdash; the two lists share an anchor near 99.99 each season, and in 2023&ndash;24 the top American 14U team sat at 97.17 while a Canadian club held the top of the band, which only makes sense on a shared scale. But 12U and 14U teams essentially never play each other, so the younger band floats on its own scale with its own spread. Last season the top 100 of the 14U/U15 band had a standard deviation of 1.84 rating points; the 12U/U13 band had 2.45. A 12U rating cannot be dropped into a 14U list untranslated.</p>

<h3>The roster arithmetic this has to model</h3>

<p>At USA Hockey Tier 1, a 14U team in 2026&ndash;27 carries 2012s as majors and 2013s as minors. Both halves are already on the record:</p>
<ul>
  <li>The <strong>2012s</strong> were the minors on last season&rsquo;s 14U teams. Their old team&rsquo;s rating is the best available read on them &mdash; imperfect, because that rating also reflects the 2011s who have now aged out.</li>
  <li>The <strong>2013s</strong> were the majors on last season&rsquo;s 12U teams, and typically the strongest players on them.</li>
</ul>
<p>Canadian girls&rsquo; hockey uses two-year bands with the same boundaries &mdash; U13 is 2013/2014, U15 is 2011/2012 &mdash; so U15 teams age up on exactly the same schedule. That is why MHR carries no Canadian girls&rsquo; U14 list: there is nothing between U13 and U15 to carry.</p>

<h3>Fitting it instead of guessing the weights</h3>

<p>The obvious move is to blend the two prior ratings and argue about the weights. Rather than argue, the weights were estimated from history. MHR keeps prior seasons, so the same age-up has already happened twice with known outcomes: 2023&ndash;24 &rarr; 2024&ndash;25, and 2024&ndash;25 &rarr; 2025&ndash;26. Each organization&rsquo;s teams were matched across seasons and across age levels by name, state or province, and rank within the organization, so a club&rsquo;s second team maps to its second team rather than its first. Every rating was converted to a z-score inside its own season-and-age-band pool, which removes the year-to-year drift in where MHR anchors the scale. Then ordinary least squares on 219 matched teams:</p>

<div class="eq">z<sub>new</sub> = <span class="hi">0.554</span> &middot; z<sub>prior older team</sub> &nbsp;+&nbsp; <span class="hi">0.349</span> &middot; z<sub>prior younger team</sub> &nbsp;&minus;&nbsp; 0.061<br>
<span class="cm">R&sup2; = 0.507&nbsp;&nbsp;&middot;&nbsp;&nbsp;residual SD = 0.734 z &asymp; 1.35 rating points&nbsp;&nbsp;&middot;&nbsp;&nbsp;t on the younger term = 5.6</span></div>

<p>So the returning group carries about <strong>57%</strong> of the signal and the incoming class about <strong>43%</strong>. The coefficients sum to 0.90, which is the model regressing to the mean on its own: a team two standard deviations clear of the field is projected about 1.8 standard deviations clear next season, because some of any single season&rsquo;s margin is luck that does not repeat.</p>

<p>A separate fit for organizations whose younger team is unranked uses the returning rating alone (coefficient 0.790) plus a small empirical penalty of &minus;0.075 z, which is what those teams actually underperformed by in the training seasons. Fitting the United States and Canada separately was tested and rejected &mdash; the country interactions were nowhere near significant (F = 0.76 on 3 and 213 degrees of freedom) and made cross-validated error worse, so one set of coefficients governs both lists and the two rankings stay on a single scale.</p>

<h3>What the validation actually says</h3>

<p>The model was refit on the 2023&ndash;24 &rarr; 2024&ndash;25 transition alone and asked to predict the following season, which it had never seen:</p>

<div class="grid2">
  <div class="panel">
    <h4>Holdout &mdash; 109 teams</h4>
    <table>
      <tr><td>Carry last rating forward</td><td>&rho; 0.666</td></tr>
      <tr><td>Returning group only, fitted</td><td>&rho; 0.666</td></tr>
      <tr><td>Returning + incoming class</td><td>&rho; 0.742</td></tr>
    </table>
  </div>
  <div class="panel">
    <h4>Prediction error (z units)</h4>
    <table>
      <tr><td>Carry last rating forward</td><td>0.860</td></tr>
      <tr><td>Returning group only, fitted</td><td>0.830</td></tr>
      <tr><td>Returning + incoming class</td><td>0.785</td></tr>
    </table>
  </div>
</div>

<p>Knowing what the 12U class did is worth about eight points of rank correlation over the standard assumption that a program stays where it was. That is the whole case for the method &mdash; and the residual scatter is the honest ceiling.</p>

<h3>Why the rank is worth less than it looks</h3>

<p>A handful of programs are genuinely clear of the field. Below them the list is dense: a great many teams are separated by less than the error bar, so their order is largely arbitrary and a single result moves a team dozens of places without telling you much.</p>

<p>Measured on the current American list, <strong>&plusmn;1.35 rating points</strong> around the team ranked 5th covers ranks 2 to 22. Around 15th it covers 5 to 36, and around 26th, 7 to 46. Only the top four or so sit outside everyone else&rsquo;s error bar. <strong>Read the rating, and read the gap to the teams either side; the rank on its own is the least informative number on the page.</strong></p>

<h3>Worked example</h3>
<div class="eq">Windy City Storm &mdash; 14U (IL)<br>
2025&ndash;26 14U rating 96.98 &rarr; z = (96.98 &minus; 94.42) / 1.84 = <span class="hi">+1.391</span><br>
2025&ndash;26 12U rating 96.77 &rarr; z = (96.77 &minus; 93.68) / 2.45 = <span class="hi">+1.262</span><br>
z<sub>2026&ndash;27</sub> = 0.554(1.391) + 0.349(1.262) &minus; 0.061 = <span class="hi">+1.150</span><br>
projected rating = 94.42 + 1.150 &times; 1.84 = <span class="hi">96.54</span> &nbsp; <span class="cm">&rarr; USA 12th, North America 18th</span></div>

<h2>Once the season starts</h2>

<p>A projection is a starting belief, not a verdict. Every finished game is recorded in a ledger, and each team&rsquo;s rating is pulled from its projection towards what its own games imply &mdash; the average of each opponent&rsquo;s rating plus the goal differential, capped at seven as MHR caps it, solved over several passes so that beating a team who then beats everyone counts for more.</p>

<p>How far a team is pulled depends on how much it has played. The weight is the projection&rsquo;s variance against the games&rsquo;, which for five games works out near half. <strong>A team that has not played does not move at all</strong>, which is why an early tournament reorders the teams in it and leaves everyone else within two or three places of where they were.</p>

<h3>Two reasons an old game counts less</h3>

<p><strong>Rust</strong> is measured in games, not weeks. A team&rsquo;s first outing of a season understates it: girls arrive from other programs, lines are new, and some teams come in off a tune-up weekend against real opposition while others come in cold. An opening game therefore carries about 40% of the weight of a settled one, and the discount is gone by roughly the sixth.</p>

<p><strong>Form</strong> is measured in days, and never stops applying: a game in September says less about a team in January than one played last week. The half-life is about six weeks &mdash; deliberately long enough that a single weekend&rsquo;s games weigh the same as each other, because what separates a team&rsquo;s Friday from its Sunday is rust, not form.</p>

<p>Keeping these apart matters later in the season, when an early-season game is both old and rusty and each discount has to be applied for its own reason.</p>

<h3>When the projection is simply wrong</h3>

<p>Turnover at 14U is not an accident of one year. The strongest programs in a region recruit the best girls from the weaker ones every season, and the &plusmn;1.35 band is fitted on real age-up transitions, so it already prices that in <em>on average</em>. But it is one number for every team, and for some the projection is just wrong.</p>

<p>So the prior has tails. A gap between projection and results that the games plainly contradict is better explained by a wrong projection than by unlucky hockey, and the further apart they are, the faster the projection yields. A team whose results land two standard deviations from its projection gives the games about 70% of the weight rather than the usual 53%.</p>

<h3>What happens when MHR publishes</h3>

<p>MyHockeyRankings starts each season from nothing rather than carrying last year forward, and a team appears only once enough of its games have been reported. Early on that means a list that is both incomplete and volatile, with teams surfacing near the top on a handful of results.</p>

<p>So MHR is treated as a second measurement of the same thing rather than as an answer to defer to. Its rating enters slowly, weighted by how much it is built on; the two rating scales are compared through the teams that appear in both lists rather than assumed to match, since MHR re-anchors every season; and once a team is in MHR its games are counted there instead of here, never in both. As the season fills in, MHR comes to dominate and the projection fades out of the answer entirely.</p>

<h2>What a rating gap is worth</h2>

<p>A rating difference is meant to predict goal difference. Measured over all 208 games of the season so far &mdash; each one scored against the two ratings as they stood immediately <em>before</em> it, so no game helped predict itself &mdash; it does, but loosely. The typical miss is 2.56 goals, against a spread of only 1.98 goals in the predictions themselves. The noise is larger than the signal.</p>

<p>Fitting the favourite&rsquo;s chance of winning a decided game against the gap gives</p>

<div class="eq">P(favourite wins) = 1 / (1 + e<sup>&minus;0.554 &times; gap</sup>)</div>

<p>with a standard error of 0.098 on the slope, five and a half of them clear of zero. So the ratings carry real information, and not very much of it per game. Folding back the games that finish level:</p>

<table class="mini">
  <thead><tr><th><span class="lgo">Rating gap</span><span class="ism">Gap</span></th><th class="num"><span class="lgo">Favourite</span><span class="ism">Fav</span></th><th class="num">Level</th><th class="num"><span class="lgo">Underdog</span><span class="ism">Dog</span></th></tr></thead>
  <tbody>
    <tr><td>0.5</td><td class="num">52%</td><td class="num">9%</td><td class="num">39%</td></tr>
    <tr><td>1.0</td><td class="num">58%</td><td class="num">9%</td><td class="num">33%</td></tr>
    <tr><td>2.0</td><td class="num">68%</td><td class="num">9%</td><td class="num">23%</td></tr>
    <tr><td>3.0</td><td class="num">76%</td><td class="num">9%</td><td class="num">15%</td></tr>
    <tr><td>4.0</td><td class="num">82%</td><td class="num">9%</td><td class="num">9%</td></tr>
  </tbody>
</table>

<p>Across every game played, <strong>the underdog won or drew 38 per cent of the time</strong>. Inside the top of a field like this, where two good teams are rarely more than two rating points apart, roughly a third of games go the other way. The common view that anyone can beat anyone on the day is very nearly right, and stops being right around a four-point gap.</p>

<p>The same curve is what the schedule shows beside each predicted winner. It also agrees with the simulation behind the bracket odds &mdash; which arrives at the question a different way, by redrawing every team&rsquo;s rating from its own uncertainty band and then drawing goals &mdash; to within a few points from half a goal of gap up to three. Two independent routes to the same place is the main reason to trust either.</p>

<h2>Where this will be wrong</h2>
<ul>
  <li><strong>Rosters are invisible to it.</strong> The model sees organizations, not players. A club that loses four 2012s to a prep school or a rival program, or lands a transfer class, will move in ways no rating history predicts. The single biggest source of error at the top of the list.</li>
  <li><strong>Minnesota runs on a different chassis.</strong> The MN Tier 1 clubs &mdash; Lakers, Green Giants, Walleye, Blue Ox, Moose, Loons and the rest &mdash; field no ranked 12U teams, because Minnesota&rsquo;s 12U girls play association hockey. Ten of the American top 30 are therefore projected on the returning group alone: eight Minnesota entries plus Lovell Academy and Team Wisconsin. Those placements carry the wider &plusmn;1.44 band. The Minnesota clubs are also re-drafted from a district pool each season, so program-level persistence is doing heavier lifting for them than for a club that keeps a roster together.</li>
  <li><strong>The cross-border scale is thin.</strong> American and Canadian teams are on one MHR scale, but that scale rests on a modest number of tournament games between them. If the true offset between the two countries is off by even half a goal, thirty places shuffle in the North American 60. Treat the American and Canadian portions of that list as two ordered groups interleaved with less confidence than either group carries internally.</li>
  <li><strong>Second and third teams move around.</strong> Matching a club&rsquo;s Major2 to its Major2 assumes the tier structure holds. Where a club collapses or adds a team, the mapping is approximate. Middlesex Islanders&rsquo; top 14U squad, for instance, appears in this year&rsquo;s MHR listing as Platinum rather than Tier 1.</li>
  <li><strong>It is a preseason estimate, not a ranking.</strong> Once real games are recorded, MHR&rsquo;s own numbers dominate anything a projection can offer. The useful life of this page is September through about mid-November.</li>
</ul>

<h2>Keeping it current</h2>
<p>MHR published its first 2026&ndash;27 ratings on <strong>30 September</strong>, for every team with at least five recorded games. From that date each of those teams starts from its projection blended with its live MHR rating, weighted by games played, so the live number takes over gradually rather than all at once. Games this site tracked before the snapshot are not counted a second time, since MHR&rsquo;s rating already holds them; games after it adjust the blend exactly as before. Ratings, seeds and analysis for anything before 30 September are unchanged.</p>
<p>Two numbers in that blend were measured rather than assumed, on the teams in both lists. <strong>The scales differ by half a goal</strong>: MHR pins its top team at 99.99 each season, and its live list sits about half a goal below the projections, so it is moved up by that much before blending, refitted on every refresh. <strong>How much a game of MHR is worth</strong> was fitted too, at about 8 goals&sup2; per game, a little more than a single goal difference carries because an early MHR rating rests on opponents who are barely rated themselves.</p>
<p><strong>A projection that is plainly wrong gives way.</strong> The projection is right on average, but some teams are simply better or worse than their history said. So, as with the games this site tracks, the further MHR&rsquo;s number sits from a team&rsquo;s projection, the less the projection is allowed to hold it back. A team whose MHR rating agrees with its projection is about half MHR at five games and 70% at twelve; one MHR has two and a half goals away from its projection is already 64% MHR at five games and 84% at fourteen. Neither is ever entirely MHR, because the projection still carries information early in the season.</p>
<p>Teams MHR has not yet listed, and a few whose MHR name could be either of two teams, keep their projection until the next snapshot.</p>

</section>'''

SCRIPT = r'''<script>
const DATA = __DATA__;

// Places gained or lost since the order before the last MHR refresh. Blank
// until that order has been worked out, and when there is none to compare
// with -- the first snapshot of a season, or ratings.json still in flight.
function mv(prev, now, since){
  // On the list this week and not last: rated on MHR alone from this refresh.
  if(prev == null) return (since && now != null && isFinite(now)) ? '<span class="mv fl">new</span>' : '';
  const d = prev - now;
  if(d === 0) return '<span class="mv fl">&mdash;</span>';
  const cls = d > 0 ? 'up' : 'dn';
  const arrow = d > 0 ? '▲' : '▼';
  return '<span class="mv ' + cls + '">' + arrow + ' ' + Math.abs(d) + '</span>';
}

function inputs(r){
  // No projection behind a team rated on MHR alone, so nothing to show here.
  if(r.basis === 'mhr only') return '<span class="muted">MHR only</span>';
  const older = '#' + r.pr + ' (' + r.prv.toFixed(2) + ')';
  const younger = r.fr ? '#' + r.fr + ' (' + r.fv.toFixed(2) + ')' : 'n/r';
  return older + '&nbsp;&middot;&nbsp;' + younger;
}

// ratings.json keys on the MHR name; a renamed club carries its old name in rn.
let ADJ = {};
function adjOf(r){
  return ADJ[r.n] || (r.rn ? ADJ[r.rn] : null) || null;
}

function shiftCell(a){
  if(!a || !a.gp) return '<td class="shift num flat hide-sm">&mdash;</td>';
  const v = a.shift;
  const cls = Math.abs(v) < 0.005 ? 'flat' : (v > 0 ? 'up' : 'dn');
  const txt = (v > 0 ? '+' : v < 0 ? '&minus;' : '') + Math.abs(v).toFixed(2);
  return '<td class="shift num hide-sm ' + cls + '">' + txt + '</td>';
}

// `hide-sm` is a column a phone does not get. What survives is the rank, the
// team and the rating it is ranked on; the move badge rides under the rating
// rather than taking a column of its own in front of the name.
const COLS = [
  {k: 'r',     label: '#',    cls: 'num', dir: 1},
  {k: null,    label: 'Move', cls: 'hide-sm'},
  {k: 'n',     label: 'Team', dir: 1},
  {k: 'p',     label: 'Proj', cls: 'num hide-sm', dir: -1},
  {k: 'adj',   label: 'Adj',  cls: 'num', dir: -1},
  {k: 'gp',    label: 'GP',   cls: 'num hide-sm', dir: -1},
  {k: 'shift', label: 'Move on results', cls: 'num hide-sm', dir: -1},
  {k: null,    label: 'Inputs &mdash; older &middot; younger', cls: 'hide-sm'}
];

// The number in the first column, and the ranking the page is actually for.
// Before any games it is the projected order; once a team has played, its
// adjusted rating decides. Recomputed within each pool, because the American
// and North American lists are separate rankings.
function rankOrder(rows, map, day){
  const of = function(r){ return map[r.n] || (r.rn ? map[r.rn] : null) || null; };
  // A row rated on MHR alone is not on the list before the week it arrived.
  const d = day || localDay();
  return rows.filter(function(r){ return !r.since || d >= String(r.since); })
             .sort(function(x, y){
    const a = of(x), b = of(y);
    const av = a ? a.adj : x.p, bv = b ? b.adj : y.p;
    if(av !== bv) return bv - av;
    return x.pub - y.pub;
  });
}

function reseed(rows){
  rows.forEach(function(r){ if(r.since) r.r = Infinity; });
  rankOrder(rows, ADJ).forEach(function(r, i){ r.r = i + 1; });
}

// The Move column's baseline: the order this page showed the day before the
// latest MHR refresh, rebuilt rather than stored. ratings.json keeps every
// weekly snapshot, so this is simply the adjustment as of that day -- which
// picks last week's snapshot by itself, with the ledger cut there too: what a
// reader saw then, games entered since and all.
function lastWeek(){
  const R = ADJ_IN.ratings, res = ADJ_IN.results;
  if(!R || !R.live || !Array.isArray(R.snapshots) || !res) return null;
  const cut = new Date(Date.parse(R.live.asOf) - 86400000).toISOString().slice(0, 10);
  const games = (res.games || []).filter(function(g){
    return String(g.date) <= cut && !(g.recorded && String(g.recorded) > cut);
  });
  const map = adjustRatings(R, {games: games}, cut);
  map.__day = cut;
  return map;
}

function reseedLastWeek(rows, map){
  rows.forEach(function(r){ r.wk = null; });
  if(!map) return;
  rankOrder(rows, map, map.__day).forEach(function(r, i){ r.wk = i + 1; });
}

function keyOf(r, k){
  if(k === 'r') return r.r;
  if(k === 'n') return String(r.n).toLowerCase();
  if(k === 'p') return r.p;
  const a = adjOf(r);
  if(k === 'adj') return a ? a.adj : -Infinity;
  if(k === 'gp') return a ? a.gp : -1;
  if(k === 'shift') return (a && a.gp) ? a.shift : -Infinity;
  return 0;
}

function render(rows, showCountry, sortKey, dir){
  const list = rows.slice();
  if(sortKey){
    list.sort(function(x, y){
      const a = keyOf(x, sortKey), b = keyOf(y, sortKey);
      if(a < b) return -dir;
      if(a > b) return dir;
      return x.r - y.r;          // stable, and the published rank breaks ties
    });
  }

  let h = '<table><thead><tr>';
  for(const c of COLS){
    if(c.label === 'Team' && showCountry){
      h += head(c, sortKey, dir) + '<th class="hide-sm">Nat</th>';
    } else {
      h += head(c, sortKey, dir);
    }
  }
  h += '</tr></thead><tbody>';

  for(const r of list){
    const a = adjOf(r);
    const hl = r.n.indexOf('Windy City') === 0 ? ' class="hl"' : '';
    h += '<tr' + hl + '>'
      + '<td class="rk num">' + r.r + '</td>'
      + '<td class="hide-sm">' + mv(r.wk, r.r, r.since) + '</td>'
      + '<td class="team">' + r.n + '<span class="loc">' + r.s
      +   (showCountry ? '<span class="ism"> &middot; ' + r.c + '</span>' : '')
      + '</span></td>'
      + (showCountry ? '<td class="hide-sm"><span class="flag">' + r.c
                     + '</span></td>' : '')
      + '<td class="proj num hide-sm">' + r.p.toFixed(2) + '</td>'
      // The move badge has no column of its own on a phone, so it rides here.
      + '<td class="adj num">' + (a ? a.adj.toFixed(2) : '&mdash;')
      +   '<span class="tsm">' + mv(r.wk, r.r, r.since) + '</span></td>'
      + '<td class="gp num hide-sm">' + (a ? a.gp : '&mdash;') + '</td>'
      + shiftCell(a)
      + '<td class="inp hide-sm">' + inputs(r) + '</td>'
      + '</tr>';
  }
  return h + '</tbody></table>';
}

function head(c, sortKey, dir){
  const cls = (c.cls ? c.cls + ' ' : '') + (c.k ? 'srt' : '');
  if(!c.k) return '<th class="' + cls.trim() + '">' + c.label + '</th>';
  const on = c.k === sortKey;
  const aria = on ? ' aria-sort="' + (dir > 0 ? 'ascending' : 'descending') + '"' : '';
  const car = on ? (dir > 0 ? '&#9650;' : '&#9660;') : '&#9660;';
  return '<th class="' + cls.trim() + '" data-k="' + c.k + '" tabindex="0" role="button"'
       + aria + '>' + c.label + '<span class="car">' + car + '</span></th>';
}

// Every rated team is ranked and the top of the order is shown, so a team plays
// its way on and off the list. `top` is how many rows a tab shows; ranks, the
// Move baseline and the Storm's figures are worked out over all of them.
const PANELS = {
  'p-usa': {rows: DATA.usa, country: false, key: 'r', dir: 1, top: 30},
  'p-na':  {rows: DATA.na,  country: true,  key: 'r', dir: 1, top: 60}
};

// Keep the published order as the tie-break, then rank on the projection until
// results arrive.
for(const id in PANELS){
  PANELS[id].rows.forEach(function(r){ if(r.pub == null) r.pub = r.r; });
  reseed(PANELS[id].rows);
}

function paint(id){
  const st = PANELS[id];
  const shown = st.rows.filter(function(r){ return r.r <= st.top; });
  document.getElementById(id).innerHTML = render(shown, st.country, st.key, st.dir);
}

// The three figures beside the Storm's paragraph are the same numbers the
// tables carry, so they are read off the same rows every paint. Written into
// the markup they were the preseason projection for ever, which stopped being
// true the first weekend of the season -- the card still said 96.54 and 18th
// while the table under it had the Storm five places and half a point away.
const STORM_ROW = 'Windy City Storm';

function stormRow(id){
  const st = PANELS[id];
  if(!st) return null;
  return st.rows.filter(function(r){
    return String(r.n).indexOf(STORM_ROW) === 0;
  })[0] || null;
}

function drawStormFigs(){
  const set = function(id, text, title){
    const e = document.getElementById(id);
    if(!e) return;
    e.textContent = text;
    if(title) e.title = title;
  };
  const usa = stormRow('p-usa'), na = stormRow('p-na');
  const row = usa || na;
  if(!row) return;
  const a = adjOf(row);
  const played = !!(a && a.gp);
  const was = 'Preseason projection ' + row.p.toFixed(2);
  if(usa) set('st-usa', usa.r, played ? 'After ' + a.gp + ' games' : null);
  if(na) set('st-na', na.r, played ? 'After ' + a.gp + ' games' : null);
  set('st-rating', (played ? a.adj : row.p).toFixed(2), played ? was : null);
  set('st-rating-c', played ? 'rating' : 'proj. rating');
}

function paintAll(){
  for(const id in PANELS) paint(id);
  drawStormFigs();
}

for(const id in PANELS){
  const panel = document.getElementById(id);
  const onSort = function(ev){
    const th = ev.target.closest ? ev.target.closest('th[data-k]') : null;
    if(!th) return;
    const st = PANELS[id];
    const k = th.getAttribute('data-k');
    const col = COLS.filter(function(c){ return c.k === k; })[0];
    // Same column again reverses; a new column starts in its natural direction.
    st.dir = (st.key === k) ? -st.dir : (col && col.dir ? col.dir : 1);
    st.key = k;
    paint(id);
  };
  panel.addEventListener('click', onSort);
  panel.addEventListener('keydown', function(ev){
    if(ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); onSort(ev); }
  });
}

paintAll();

// Adjusted ratings arrive after first paint, so the table is never blank while
// two files are in flight. Neither page writes anything back.
loadAdjustment(false).then(function(map){
  ADJ = map || {};
  for(const id in PANELS) reseed(PANELS[id].rows);
  const live = ADJ_IN.ratings && ADJ_IN.ratings.live;
  // Only once the viewer's day has reached the snapshot: before it the page
  // is not on that snapshot yet, so there is nothing to have moved from.
  const wk = (live && localDay() >= live.asOf) ? lastWeek() : null;
  for(const id in PANELS) reseedLastWeek(PANELS[id].rows, wk);
  const since = document.getElementById('mv-since');
  if(since && wk){
    since.textContent = ' on ' + new Date(live.asOf + 'T12:00:00Z')
      .toLocaleDateString('en-US', {month: 'long', day: 'numeric', timeZone: 'UTC'});
  }
  const played = Object.keys(ADJ).filter(function(k){ return ADJ[k].gp > 0; }).length;
  const mhr = (live && localDay() >= live.asOf)
    ? 'Since <b>' + String(live.asOf) + '</b> that includes MyHockeyRankings&rsquo; own '
      + 'live rating for the <b>' + live.matched + '</b> teams it has rated, '
      + 'which counts games this site never saw. '
    : '';
  const note = document.getElementById('adj-note');
  if(note){
    note.innerHTML = played
      ? '<b>The ranking is on Adj</b>, which blends each projection with what '
        + 'that team&rsquo;s games imply &mdash; weighted by how many it has played, '
        + 'how wide its projection band is, how recent each game was and how early '
        + 'in its season. ' + mhr + '<b>' + played + '</b> teams have a game on record; the rest '
        + 'sit on their projection and have not moved. '
        + '<a href="methodology.html">How this works &rarr;</a>'
      : '<b>Adj</b> will diverge from <b>Proj</b> once games are played. '
        + 'No results are on record yet, so every team still sits on its projection.';
  }
  paintAll();
});

const tabs = [['tab-usa','p-usa'], ['tab-na','p-na']];
for(const [tid, pid] of tabs){
  document.getElementById(tid).addEventListener('click', () => {
    for(const [t, p] of tabs){
      const on = t === tid;
      document.getElementById(t).setAttribute('aria-selected', on ? 'true' : 'false');
      document.getElementById(p).hidden = !on;
    }
  });
}
</script>'''

GAMES_MAIN = r'''<header class="masthead">
  <div class="eyebrow">Season log &middot; 2026&ndash;27</div>
  <h1 id="g-name">Windy City Storm</h1>
  <p class="dek" id="g-dek"></p>
  <div class="stamp" id="g-meta"></div>
  <p class="disclaimer">Every game on the schedule, in order. Tournament games come from that tournament&rsquo;s file, the rest from the regional log. <a href="methodology.html">How a result moves a rating &rarr;</a></p>
</header>

<div class="t-empty" id="g-empty" hidden>
  <b>No games on record yet</b>
  Add them to <code>events/regional-games.json</code>, then run <code>build/results.py</code>.
</div>

<div id="g-body" hidden>
  <div class="storm">
    <div>
      <h3 id="g-rec"></h3>
      <p id="g-line"></p>
    </div>
    <div class="figs" id="g-figs"></div>
  </div>

  <div class="tablewrap">
    <div id="g-list"></div>
  </div>

  <div class="legend">
    <span><b>Rating</b> = the Storm&rsquo;s adjusted rating with this game and everything before it counted. The figure in the card above is the whole ledger, so it can sit a hundredth away from the last row: other teams kept playing.</span>
    <span><b>Opp</b> = the opponent&rsquo;s adjusted rating at faceoff, their own earlier games included. <b>Pred</b> = the goal difference the two implied, from the Storm&rsquo;s side.</span>
    <span>Before a game is played the <b>Result</b> column shows the Storm&rsquo;s chance of winning it outright, from the curve on the <a href="methodology.html">methodology page</a>. On a phone, where <b>Pred</b> is dropped, the expected goal difference sits under it.</span>
    <span><b>unranked</b> = MyHockeyRankings does not rate the opponent, so the game is on the record but moves nothing.</span>
  </div>

  <div id="g-add"></div>
</div>'''


GAMES_SCRIPT = r'''<script>
// The Storm's season in one list. build/results.py collects it out of every
// event file -- tournaments and the regional log alike -- so this page reads one
// small file rather than every schedule of the season.
const LOG_FILE = 'events/regional-games.json';
const EDIT_KEY = 'jets2026';
const LS_EDIT = 'scoreEdit';

const el = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);

const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function lsGet(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }
function lsSet(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
function lsDel(k){ try { localStorage.removeItem(k); } catch(e){} }

// Same gate as the tournament page, and the same obscurity: the key is in this
// page's source and unlocks nothing but a form that writes to the clipboard.
(function(){
  const q = new URLSearchParams(location.search);
  if(!q.has('edit')) return;
  const v = q.get('edit');
  if(v === EDIT_KEY) lsSet(LS_EDIT, '1');
  else if(v === 'off') lsDel(LS_EDIT);
  q.delete('edit');
  const rest = q.toString();
  history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
})();

const EDITING = lsGet(LS_EDIT) === '1';

// Faceoff times are authored in the rink's own offset and rendered as authored.
function dayLabel(iso){
  // A bare date parses as UTC midnight, which is the previous day everywhere
  // west of Greenwich. Noon local is the same calendar day in every timezone.
  const text = String(iso || '');
  const d = new Date(text.indexOf('T') < 0 ? text + 'T12:00:00' : text);
  if(isNaN(d)) return text.slice(0, 10);
  return DAYS[d.getDay()] + ' ' + d.getDate() + ' ' + MONTHS[d.getMonth()];
}

function clockOf(iso){
  const m = /T(\d{2}):(\d{2})/.exec(String(iso || ''));
  if(!m) return '';
  let h = +m[1];
  const ap = h >= 12 ? 'PM' : 'AM';
  h = h % 12 || 12;
  return h + ':' + m[2] + ' ' + ap;
}

function signed(v){
  if(v == null) return '<span class="muted">&mdash;</span>';
  const s = v >= 0 ? '+' : '−';
  return '<span class="t-gd">' + s + Math.abs(v).toFixed(1) + '</span>';
}

// ---------------------------------------------------------------- the season
let LOG = null;              // the regional file, fetched only to edit it
let RANKED = [];             // every MHR name, for the opponent box

// adjustUpTo() is the shared, memoised one: a rating with the ledger cut at an
// instant. Two per row, and a full pass costs well under a millisecond, so a
// season of them is not worth being clever about.
function justBefore(start){
  const t = Date.parse(start);
  return isNaN(t) ? 0 : t - 1;
}

function rateAt(map, name){
  const a = name ? map[name] : null;
  return a && typeof a.adj === 'number' ? a.adj : null;
}

function ledgerTieShare(){
  const all = (LEDGER && LEDGER.games) || [];
  if(all.length < 20) return 0.09;
  return all.filter(function(g){
    return g.homeScore === g.awayScore; }).length / all.length;
}

function resultOf(g){
  if(g.gf == null || g.ga == null) return null;
  if(g.gf > g.ga) return 'W';
  if(g.gf < g.ga) return 'L';
  return 'T';
}

function drawSeason(){
  const rows = (LEDGER && LEDGER.storm) || [];
  if(!rows.length){ el('g-empty').hidden = false; return; }
  el('g-body').hidden = false;
  el('g-name').textContent = LEDGER.stormName || 'Season';

  const me = LEDGER.stormMhr;
  const played = rows.filter(r => r.gf != null);
  // The card is where the Storm stand now, so it is the whole ledger -- the
  // same number the rankings page carries. Cutting it at their own last faceoff
  // would leave out games other teams played after it, which move the Storm
  // through their opponents' ratings, and put a second answer on the site.
  const now = ADJ_ALL;

  // No rank on this page. The rankings page ranks inside its published top
  // sixty, and ranking inside the whole rated list instead would put a second,
  // different number for the same team on the same site. The opponent's rating
  // is what the prediction is built from and needs no pool at all.

  // --- the card -------------------------------------------------------------
  const w = played.filter(r => resultOf(r) === 'W').length;
  const l = played.filter(r => resultOf(r) === 'L').length;
  const t = played.filter(r => resultOf(r) === 'T').length;
  el('g-rec').textContent = played.length
    ? w + '–' + l + (t ? '–' + t : '')
    : 'No games played yet';

  const gf = played.reduce((a, r) => a + r.gf, 0);
  const ga = played.reduce((a, r) => a + r.ga, 0);
  const ahead = rows.filter(r => r.gf == null);
  const unrated = played.filter(r => !r.rated);
  const bits = [];
  if(played.length){
    bits.push(played.length + (played.length === 1 ? ' game played, ' : ' games played, ')
      + gf + ' for and ' + ga + ' against.');
  }
  if(ahead.length){
    bits.push(ahead.length + (ahead.length === 1 ? ' game' : ' games')
      + ' still to come, the next on ' + dayLabel(ahead[0].start)
      + ' against ' + esc(ahead[0].opp) + '.');
  }
  if(unrated.length){
    bits.push('<b>' + unrated.length + '</b> of them against a team MyHockeyRankings '
      + 'does not rate, which the rating cannot use.');
  }
  el('g-line').innerHTML = bits.join(' ');

  const mine = now[me];
  const figs = [];
  figs.push(['Games', String(played.length), false]);
  if(mine){
    figs.push(['Rating', mine.adj.toFixed(2), false]);
    if(mine.gp) figs.push(['Shift', (mine.adj >= mine.proj ? '+' : '−')
      + Math.abs(mine.adj - mine.proj).toFixed(2), true]);
  }
  el('g-figs').innerHTML = figs.map(f =>
    '<div class="fig' + (f[2] ? ' sm' : '') + '"><div class="n">' + esc(f[1])
    + '</div><div class="c">' + esc(f[0]) + '</div></div>').join('');

  // --- the table ------------------------------------------------------------
  // On a phone the rink goes under the opponent and the rating under the
  // score, because a column each put both of them off the edge -- and what a
  // parent opens this on a phone to read is who, where, and what the score was.
  let h = '<table><thead><tr><th>Date</th><th>Opponent</th>'
        + '<th class="hide-sm">Rink</th>'
        + '<th class="num hide-sm">Opp</th><th class="num hide-sm">Pred</th>'
        + '<th class="num">Result</th><th class="num hide-sm">Rating</th>'
        + '</tr></thead><tbody>';



  const TIE = ledgerTieShare();

  let block = null;
  for(const g of rows){
    // A new block wherever the run of games changes event, so the tournaments
    // read as blocks and a regional game between two of them stands on its own.
    if(g.event !== block){
      block = g.event;
      h += '<tr class="dayrow"><td colspan="7">' + esc(g.eventName || g.event)
         + '</td></tr>';
    }
    // Going in: everything that had finished by the time this one faced off,
    // including the opponent's own game that morning.
    const before = adjustUpTo(justBefore(g.start));
    const pred = (function(){
      const a = rateAt(before, me), b = rateAt(before, g.oppMhr);
      return (a == null || b == null) ? null : a - b;
    })();
    const res = resultOf(g);
    // A team MHR does not rate can still have a supplied estimate. It is shown
    // in grey, because it is ours rather than a rating the ledger stands behind.
    const rated = rateAt(before, g.oppMhr);
    const foe = rated != null ? rated
              : (typeof g.oppRating === 'number' ? g.oppRating : null);
    const est = rated == null && foe != null;
    const after = g.gf == null ? null : rateAt(adjustUpTo(g.start), me);

    h += '<tr>'
      + '<td class="t-when">' + esc(dayLabel(g.start))
      +   (clockOf(g.start) ? '<br>' + esc(clockOf(g.start)) : '') + '</td>'
      + '<td class="team">' + (g.home ? 'vs ' : 'at ') + esc(g.opp || 'TBD')
      +   (g.rated ? '' : '<span class="unrk">unranked</span>')
      +   (g.rink ? '<span class="tsm">' + esc(g.rink) + '</span>' : '') + '</td>'
      + '<td class="inp hide-sm">' + esc(g.rink || '') + '</td>'
      + '<td class="num hide-sm">' + (foe == null
          ? '<span class="muted">&mdash;</span>'
          : (est ? '<span class="muted" title="our estimate, not a rating">'
                   + foe.toFixed(2) + '</span>' : foe.toFixed(2))) + '</td>'
      + '<td class="num hide-sm">' + signed(pred) + '</td>'
      // Before it is played, the column that will hold the score holds the
      // chance instead -- and it is the one column a phone still shows.
      + '<td class="num">' + (res
          ? '<span class="t-score">' + g.gf + '–' + g.ga + '</span>'
            + '<span class="mv ' + (res === 'W' ? 'up' : res === 'L' ? 'dn' : 'fl')
            + '" style="margin-left:8px">' + res + '</span>'
          : (pred == null ? '<span class="muted">&mdash;</span>'
             : '<span class="t-wp" title="chance of winning outright">'
               + Math.round((pred >= 0 ? winOdds(pred, TIE).fav
                                       : winOdds(pred, TIE).dog) * 100)
               + '%</span>'
               // Pred is one of the columns a phone drops, so the expected
               // goal difference rides here where a phone still sees it.
               + '<span class="tsm">' + (pred >= 0 ? '+' : '\u2212')
               + Math.abs(pred).toFixed(1) + ' expected</span>'))
      +   (after == null ? ''
           : '<span class="tsm">rated ' + after.toFixed(2) + '</span>') + '</td>'
      + '<td class="adj num hide-sm">' + (after == null
          ? '<span class="muted">&mdash;</span>' : after.toFixed(2)) + '</td>'
      + '</tr>';
  }
  el('g-list').innerHTML = h + '</tbody></table>';
}

// ------------------------------------------------------------------ add a game
// There is nothing to capture for a regional game -- no GameSheet, no site to
// read -- so this builds the file rather than parsing one. It emits the whole
// of events/regional-games.json, teams included, because a new opponent needs a
// row there before results.py can key the game by MHR name.
function drawAdd(){
  if(!EDITING || !LOG) return;
  const box = el('g-add');
  box.innerHTML =
    '<div class="t-sec"><h2>Add a game</h2>'
    + '<p class="t-sub">For games away from a tournament. The opponent has to be '
    + 'named exactly as MyHockeyRankings names it, which is what the list below '
    + 'is for &mdash; a name it does not know is a game the rating cannot use. '
    + 'Copy the file, paste it over <b>' + esc(LOG_FILE) + '</b>, then run '
    + '<b>build/results.py</b> and commit.</p>'
    + '<div class="ga-form">'
    +   '<label>Date<input type="date" id="ga-date"></label>'
    +   '<label>Faceoff<input type="time" id="ga-time" value="19:00"></label>'
    +   '<label>Home or away<select id="ga-ha">'
    +     '<option value="home">Home</option><option value="away">Away</option>'
    +   '</select></label>'
    +   '<label class="wide">Opponent<input id="ga-opp" list="ga-teams" '
    +     'placeholder="Milwaukee Jr Admirals 14U" autocomplete="off"></label>'
    +   '<label>Our goals<input type="number" min="0" max="30" id="ga-gf"></label>'
    +   '<label>Their goals<input type="number" min="0" max="30" id="ga-ga"></label>'
    +   '<label class="wide">Rink<input id="ga-rink" placeholder="optional"></label>'
    + '</div>'
    + '<datalist id="ga-teams">'
    +   RANKED.map(x => '<option value="' + esc(x) + '"></option>').join('')
    + '</datalist>'
    + '<div class="sc-bar">'
    +   '<button type="button" class="sc-act" id="ga-add">Add to the file</button>'
    +   '<button type="button" class="sc-act" id="ga-copy">Copy the file</button>'
    + '</div>'
    + '<p class="sc-note" id="ga-note"></p>'
    + '<textarea class="sc-out" id="ga-out" readonly hidden></textarea></div>';

  el('ga-add').addEventListener('click', addGame);
  el('ga-copy').addEventListener('click', copyLog);
}

function slug(s){
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// MHR's own name, minus the age band and the tier it puts in brackets.
function shortName(mhr){
  return String(mhr).replace(/\s*\([^)]*\)\s*/g, ' ')
                    .replace(/\s+(14U|U15|U15 AA|U15 AAA)\s*$/i, '')
                    .replace(/\s+/g, ' ').trim();
}

function addGame(){
  const note = el('ga-note');
  const say = function(cls, msg){ note.innerHTML = '<span class="' + cls + '">' + msg + '</span>'; };
  const date = (el('ga-date').value || '').trim();
  const opp = (el('ga-opp').value || '').trim();
  if(!date) return say('bad', 'A date is needed.');
  if(!opp) return say('bad', 'An opponent is needed.');
  if(RANKED.indexOf(opp) < 0){
    say('warn', '<b>' + esc(opp) + '</b> is not a name MyHockeyRankings uses, so the '
      + 'game will be on the record but will not move any rating. Added anyway.');
  }
  const gf = el('ga-gf').value === '' ? null : +el('ga-gf').value;
  const ga = el('ga-ga').value === '' ? null : +el('ga-ga').value;
  const home = el('ga-ha').value === 'home';
  const oppId = slug(shortName(opp)) || slug(opp);
  const meId = (LOG.teams[0] || {}).id || 'windy-city-storm';

  if(!LOG.teams.some(t => t.id === oppId)){
    LOG.teams.push({id: oppId, name: shortName(opp), mhrName: opp});
  }
  // The offset is the rink's, and Chicago in the hockey season is -05:00 from
  // the first Sunday in November and -06:00 after it. Authored, never converted.
  const t = (el('ga-time').value || '19:00') + ':00';
  const off = centralOffset(date);
  let id = date + '-' + oppId;
  let k = 2;
  while(LOG.games.some(g => g.id === id)) id = date + '-' + oppId + '-' + (k++);

  LOG.games.push({
    id: id, date: date, start: date + 'T' + t + off,
    home: home ? meId : oppId, away: home ? oppId : meId,
    homeScore: home ? gf : ga, awayScore: home ? ga : gf,
    rink: (el('ga-rink').value || '').trim() || null,
    round: 'regional'
  });
  LOG.games.sort((a, b) => String(a.start).localeCompare(String(b.start)));
  if(RANKED.indexOf(opp) >= 0){
    say('ok', '<b>' + esc(shortName(opp)) + '</b> on ' + esc(date)
      + ' added. <b>' + LOG.games.length + '</b> games in the file. Press '
      + '<b>Copy the file</b> when you have entered them all.');
  }
  el('ga-opp').value = '';
  el('ga-gf').value = '';
  el('ga-ga').value = '';
}

// Central time by the US rule, arithmetically -- the same reason build_page.py
// does it that way rather than asking a timezone database Windows does not ship.
function centralOffset(date){
  const d = new Date(date + 'T12:00:00Z');
  const y = d.getUTCFullYear();
  const march = new Date(Date.UTC(y, 2, 1));
  const start = new Date(Date.UTC(y, 2, 1 + ((7 - march.getUTCDay()) % 7) + 7));
  const nov = new Date(Date.UTC(y, 10, 1));
  const end = new Date(Date.UTC(y, 10, 1 + ((7 - nov.getUTCDay()) % 7)));
  return (d >= start && d < end) ? '-05:00' : '-06:00';
}

function copyLog(){
  const text = JSON.stringify(LOG, null, 1) + '\n';
  const out = el('ga-out'), note = el('ga-note');
  const done = function(){
    note.innerHTML = '<span class="ok">Copied the whole of ' + esc(LOG_FILE)
      + ', <b>' + LOG.games.length + '</b> games. Paste it over that file, run '
      + '<b>build/results.py</b>, and commit both it and results.json.</span>';
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){ out.hidden = true; done(); },
      function(){ out.hidden = false; out.value = text; out.focus(); out.select();
                  note.innerHTML = '<span class="warn">Clipboard blocked &mdash; it is '
                    + 'selected in the box below.</span>'; });
  } else {
    out.hidden = false; out.value = text; out.focus(); out.select();
  }
}

// ------------------------------------------------------------------------ boot
// loadAdjustment() fetches both files and keeps them on ADJ_IN, which is what
// adjustAsOf() cuts. The log file is only needed to add to it.
let RATINGS = null, LEDGER = null, ADJ_ALL = null;

Promise.all([loadAdjustment(false),
             EDITING ? grab(LOG_FILE, false) : Promise.resolve(null)])
  .then(function(all){
    ADJ_ALL = all[0] || {};
    RATINGS = ADJ_IN.ratings;
    LEDGER = ADJ_IN.results;
    LOG = all[1];
    if(LOG && !Array.isArray(LOG.teams)) LOG.teams = [];
    if(LOG && !Array.isArray(LOG.games)) LOG.games = [];
    RANKED = ((RATINGS && RATINGS.teams) || []).map(t => t.n).sort();
    if(!RATINGS || !LEDGER){ el('g-empty').hidden = false; return; }
    // The newest thing the ratings rest on: the MHR snapshot once there is one.
    const asOf = (RATINGS.live && RATINGS.live.asOf) || String(RATINGS.generated || '');
    el('g-meta').innerHTML = '<span>Ratings as of <b>'
      + esc(asOf.slice(0, 10)) + '</b></span>'
      + '<span>Games <b>' + ((LEDGER.storm || []).length) + '</b></span>';
    drawSeason();
    drawAdd();
  });
</script>'''


TOURNAMENTS_MAIN = r'''<header class="masthead">
  <div class="eyebrow">Tournament tracker &middot; 2026&ndash;27</div>
  <h1 id="t-name">Tournament</h1>
  <p class="dek" id="t-dates"></p>
  <div class="t-pick" id="t-pick" hidden>
    <label for="t-event">Tournament</label>
    <select id="t-event"></select>
  </div>
  <div class="stamp" id="t-meta"></div>
  <div class="t-bar">
    <button type="button" class="t-refresh" id="t-refresh">Refresh</button>
    <span class="t-run" id="t-run" role="status" aria-live="polite"></span>
    <span class="t-said" id="t-said" role="status" aria-live="polite"></span>
  </div>
  <p class="disclaimer">Predictions are rating differences, not measured results &mdash; a typical miss is about 2.5 goals.</p>
</header>

<div class="t-empty" id="t-empty" hidden>
  <b>No tournament data yet</b>
  Add the tournament to <code>events/index.json</code> and drop its file in <code>events/</code>. Every section below fills in automatically.
</div>

<div id="t-body" hidden>

<div class="tabs" role="tablist">
  <button class="tab" role="tab" id="tab-storm" aria-controls="p-storm" aria-selected="true">Jets</button>
  <button class="tab" role="tab" id="tab-brackets" aria-controls="p-brackets" aria-selected="false">Brackets</button>
  <button class="tab" role="tab" id="tab-sched" aria-controls="p-sched" aria-selected="false">Schedule</button>
  <button class="tab" role="tab" id="tab-team" aria-controls="p-team" aria-selected="false" hidden>Team</button>
  <button class="tab" role="tab" id="tab-ask" aria-controls="p-ask" aria-selected="false">Ask</button>
  <button class="tab" role="tab" id="tab-analysis" aria-controls="p-analysis" aria-selected="false" hidden>Analysis</button>
  <button class="tab" role="tab" id="tab-update" aria-controls="p-update" aria-selected="false" hidden>Update</button>
</div>

<div class="tpanel" id="p-storm">

<div class="storm" id="t-storm" hidden>
  <div>
    <h3 id="t-storm-name">Chicago Jets 11U AA</h3>
    <p id="t-storm-line"></p>
    <table class="t-mini"><tbody id="t-storm-games"></tbody></table>
    <p class="scout-link" id="t-scout-link" hidden></p>
    <div class="scout" id="t-scout" hidden></div>
  </div>
  <div class="figs" id="t-storm-figs"></div>
</div>

</div>

<div class="tpanel" id="p-brackets" hidden>

<section class="t-sec" id="t-sec-stand" hidden>
  <h2>Standings and advancement</h2>
  <p class="t-sub" id="t-adv-rule"></p>
  <div id="t-standings"></div>
  <p class="t-note" id="t-tiebreak"></p>
</section>

<section class="t-sec" id="t-sec-diff" hidden>
  <h2>Bracket difficulty</h2>
  <p class="t-sub">Groups ordered hardest first, by the mean rating of the teams drawn into them, <b>as they stood the day the tournament started</b> &mdash; how hard the draw was is a question about who you drew, not about what they did afterwards. A team with no MyHockeyRankings entry is badged and counted, using the estimated rating supplied for it.</p>
  <div class="tablewrap" id="t-difficulty"></div>
</section>

</div>

<div class="tpanel" id="p-sched" hidden>

<section class="t-sec" id="t-sec-sched" hidden>
  <h2>Full schedule</h2>
  <div class="sfil" id="t-filter" hidden>
    <div class="sfil-bar">
      <input type="search" id="t-filter-q" class="sfil-q" autocomplete="off"
             placeholder="Find a team" aria-label="Find a team to filter the schedule">
      <button type="button" class="sfil-all" id="t-filter-all">All teams</button>
      <span class="sfil-said" id="t-filter-said" role="status" aria-live="polite"></span>
    </div>
    <div class="sfil-picked" id="t-filter-picked"></div>
    <div class="sfil-list" id="t-filter-list" role="group" aria-label="Teams" hidden></div>
  </div>
  <p class="t-sub">Predicted goal differential is the gap between the two teams&rsquo; ratings, signed towards the home side. Fractional values are expected: a rating gap of 1.8 means the home team is favoured by about two goals. Games already played show the final score instead.</p>
  <p class="t-sub" id="t-note"></p>
  <div class="tablewrap" id="t-schedule"></div>
  <p class="t-note" id="t-legend"></p>
</section>

</div>

<div class="tpanel" id="p-ask" hidden>
  <h2>Ask about the tournament</h2>
  <p class="t-sub">Answers come from the same ten thousand simulations the Brackets tab uses, so a number here is the page&rsquo;s own. There is no model behind it: it knows a fixed set of questions and will say so rather than guess.</p>
  <div class="ask-bar">
    <input id="t-ask-in" type="text" autocomplete="off" placeholder="Who do we need to win?">
    <button type="button" class="sc-act" id="t-ask-go">Ask</button>
  </div>
  <div id="t-ask-out"></div>
</div>

<div class="tpanel" id="p-team" hidden>
  <div class="storm">
    <div>
      <h3 id="t-tm-name"></h3>
      <p id="t-tm-line"></p>
      <table class="t-mini"><tbody id="t-tm-games"></tbody></table>
    </div>
    <div class="figs" id="t-tm-figs"></div>
  </div>
  <p class="t-note" id="t-tm-note"></p>
</div>

<div class="tpanel" id="p-analysis" hidden>

<section class="t-sec" id="t-sec-analysis" hidden>
  <h2>What the tournament changed</h2>
  <p class="t-sub" id="t-an-lede"></p>
  <div id="t-an-movers"></div>
  <div class="tablewrap" id="t-an-table"></div>
  <p class="t-note" id="t-an-note"></p>
</section>

</div>

<!-- The score entry panel is built into this one, and only when unlocked. -->
<div class="tpanel" id="p-update" hidden></div>

</div>'''

TOURNAMENTS_SCRIPT = r'''<script>
const DEFAULT_RULES = {win:2, tie:1, loss:0, advance:2, tiebreakers:[]};
const STORM_PREFIX = 'Chicago Jets';
const DAYS = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const el = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c]);

// Faceoff times render exactly as authored, in the rink's own offset. Converting
// to the reader's clock would move an 8:10 AM start for anyone reading from
// another timezone -- which is most of a travel-team parent group.
function when(iso){
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso || '');
  if(!m) return '<span class="muted">TBD</span>';
  const day = DAYS[new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])).getUTCDay()];
  const hour = (+m[4]) % 12 || 12;
  const ampm = (+m[4]) < 12 ? 'AM' : 'PM';
  return day + ' ' + (+m[3]) + ' ' + MONTHS[+m[2] - 1] + '<br>' + hour + ':' + m[5] + ' ' + ampm;
}

// ratingForPrediction is the number to predict from: an unranked team has no
// MHR rating but may still carry an estimate supplied alongside it.
function dayLabel(iso){
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  if(!m) return 'Date to be confirmed';
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  try {
    return new Intl.DateTimeFormat('en-GB', {
      timeZone: 'UTC', weekday: 'long', day: 'numeric', month: 'long'
    }).format(d);
  } catch(e){
    return DAYS[d.getUTCDay()] + ' ' + (+m[3]) + ' ' + MONTHS[+m[2] - 1];
  }
}

// Every prediction, margin and simulation draw on this page goes through here.
// The in-season adjusted rating wins when the team is in ratings.json;
// ratingForPrediction is the preseason fallback, and the only option for a team
// with no MHR entry at all.
let ADJ = {};

function rating(t){
  if(!t) return null;
  const a = t.mhrName ? ADJ[t.mhrName] : null;
  if(a && typeof a.adj === 'number') return a.adj;
  if(typeof t.ratingForPrediction === 'number') return t.ratingForPrediction;
  return typeof t.rating === 'number' ? t.rating : null;
}

// rating() with the ledger cut somewhere other than today. Same fallbacks: the
// adjusted number if there is one, then the supplied estimate, then MHR's own.
function rateWith(t, asOf){
  if(!t) return null;
  const a = (asOf && t.mhrName) ? asOf[t.mhrName] : null;
  if(a && typeof a.adj === 'number') return a.adj;
  if(typeof t.ratingForPrediction === 'number') return t.ratingForPrediction;
  return typeof t.rating === 'number' ? t.rating : null;
}

// A seed here has only ever meant one thing: where this team stood in this
// field when the tournament began. So it is worked out rather than carried in
// the file -- a number written down in August had Chicago Mission arriving at
// the second tournament of the season seeded 8th, behind an Oakville side the
// list already put five places below them.
//
// But it is worked out **as of the eve of the tournament**, not as of today.
// A seed is a fact about a starting field: it is what the draw was made on, it
// is what the Analysis tab measures movement away from, and a tournament that
// finished in September cannot be reseeded in November because somebody else
// played a game. Only the predictions use the live rating, because a prediction
// should use the best estimate there is.
//
// `asOf` is null when there is no ledger to cut -- offline, or before
// results.json arrives -- and the projection stands in.
function assignSeeds(teams, asOf){
  const rate = function(t){ return rateWith(t, asOf); };
  const ranked = teams.filter(function(t){ return rate(t) != null; });
  const rest = teams.filter(function(t){ return rate(t) == null; });
  ranked.sort(function(a, b){ return rate(b) - rate(a); });
  ranked.forEach(function(t, i){ t.seed = i + 1; });
  rest.forEach(function(t, i){ t.seed = ranked.length + i + 1; });
}

// Rendered in the tournament's own timezone, named by tournament.timezone as an
// IANA zone. Going through Intl rather than a fixed offset is what makes the
// label say EDT in September and EST in November without being told.
function stamp(iso, tz){
  if(tz){
    const d = new Date(iso);
    if(!isNaN(d.getTime())){
      try {
        const parts = new Intl.DateTimeFormat('en-US', {
          timeZone: tz, day: 'numeric', month: 'short', year: 'numeric',
          hour: 'numeric', minute: '2-digit', timeZoneName: 'short'
        }).formatToParts(d);
        const get = t => {
          const hit = parts.find(x => x.type === t);
          return hit ? hit.value : '';
        };
        if(get('day') && get('hour')){
          return get('day') + ' ' + get('month') + ' ' + get('year') + ', '
               + get('hour') + ':' + get('minute') + ' ' + get('dayPeriod')
               + ' ' + get('timeZoneName');
        }
      } catch(e){
        // Unknown zone or an engine without full ICU: fall through and read
        // the offset out of the string instead.
      }
    }
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::\d{2})?(Z|[+-]\d{2}:\d{2})?/.exec(iso || '');
  if(!m) return esc(iso);
  const hour = (+m[4]) % 12 || 12;
  const ampm = (+m[4]) < 12 ? 'AM' : 'PM';
  let zone = '';
  if(m[6] === 'Z' || m[6] === '+00:00') zone = ' UTC';
  else if(m[6]) zone = ' UTC' + m[6].replace(':00', '');
  return (+m[3]) + ' ' + MONTHS[+m[2] - 1] + ' ' + m[1] + ', '
       + hour + ':' + m[5] + ' ' + ampm + zone;
}

// A win in regulation, in overtime and in a shootout can all be worth
// different points. Overtime falls back to the shootout values when the rules
// do not name it separately, so a tournament without overtime behaves as
// before; set overtimeWin / overtimeLoss in the event file where it differs.
function scoring(rules){
  const pick = (a, b, dflt) => typeof rules[a] === 'number' ? rules[a]
                             : typeof rules[b] === 'number' ? rules[b] : dflt;
  const soWin = pick('shootoutWin', 'win', 2);
  const soLoss = pick('shootoutLoss', 'tie', 1);
  return {
    reg: pick('regulationWin', 'win', 2),
    otWin: typeof rules.overtimeWin === 'number' ? rules.overtimeWin : soWin,
    otLoss: typeof rules.overtimeLoss === 'number' ? rules.overtimeLoss : soLoss,
    soWin: soWin,
    soLoss: soLoss,
    loss: pick('loss', 'loss', 0)
  };
}

// The playoff brackets a tournament seeds into, best first, as ranges of
// seats in the overall seeding order.
//
// Two shapes. A `brackets` list seeds each finishing position in a group as its
// own cohort -- eight group winners split into Gold and Silver, the eight
// runners-up into Bronze and Brass -- which is how a showcase of eight groups
// works. The older goldBerths / silverBerths pair seeds the whole field in one
// line instead, group winners first. Neither can express the other, so the file
// says which it is and this returns the same shape either way.
function bracketSpec(rules, groupCount){
  const list = rules && rules.brackets;
  // An empty list is an answer, not a missing one: some tournaments simply
  // have no playoff.
  if(Array.isArray(list) && !list.length) return {byPlace: true, blocks: []};
  if(Array.isArray(list) && list.length){
    return {byPlace: true, blocks: list.map(function(b){
      const lo = (b.seeds && b.seeds[0]) || 1;
      const hi = (b.seeds && b.seeds[1]) || groupCount;
      const base = ((b.place || 1) - 1) * groupCount;
      return {key: b.key, name: b.name || b.key, place: b.place || 1,
              lo: lo, hi: hi, from: base + lo - 1, to: base + hi - 1};
    })};
  }
  const gold = typeof rules.goldBerths === 'number' ? rules.goldBerths : 8;
  const silver = typeof rules.silverBerths === 'number' ? rules.silverBerths : gold;
  // silverBerths: 0 is a tournament with one playoff bracket and a placement
  // game for the rest, not a Silver bracket nobody can reach.
  const blocks = [{key: 'gold', name: rules.goldName || 'Gold', from: 0, to: gold - 1}];
  if(silver > 0) blocks.push({key: 'silver', name: 'Silver', from: gold, to: gold + silver - 1});
  return {byPlace: false, blocks: blocks};
}

// How often a game ends level. A rules question rather than a rating one, so it
// is read off this tournament's own finished games once there are enough to
// mean anything, and guessed from the rules before that.
function tieShare(games, rules){
  const done = (games || []).filter(function(g){
    return isPlayed(g) && g.home && g.away;
  });
  if(done.length >= 20){
    return done.filter(function(g){
      return g.homeScore === g.awayScore; }).length / done.length;
  }
  return rules && rules.noTies ? 0.05 : 0.09;
}

// "REG", "OT" or "SO" -- how the game was decided, however it was recorded.
function decisionOf(g){
  const d = String(g.decision || (g.shootout ? 'SO' : 'REG')).toUpperCase();
  return (d === 'OT' || d === 'SO') ? d : 'REG';
}

function isPlayed(g){ return g.homeScore != null && g.awayScore != null; }
function isStorm(t){ return !!t && String(t.name).indexOf(STORM_PREFIX) === 0; }

// `instead` replaces the seed in the brackets, already escaped -- the Storm
// callout puts a confidence there for an opponent it has worked out rather
// than been told.
// A team's name is a way in to its own page wherever it appears. An anchor
// with no href would not be focusable and a button would inherit the wrong
// font in a table cell, so it is a span the keyboard can reach.
function tlink(team, inner){
  if(!team || !team.id) return inner;
  return '<span class="tl" role="link" tabindex="0" data-t="' + esc(team.id)
       + '" title="' + esc(team.name) + '&rsquo;s games">' + inner + '</span>';
}

function label(t, id, withSeed, instead){
  if(!t) return '<span class="muted">' + esc(id || 'TBD') + '</span>';
  let h = tlink(t, esc(t.name));
  const paren = instead != null ? instead
              : (withSeed && t.seed != null ? esc(t.seed) : null);
  if(paren != null){
    h += '<span class="t-seed">(' + paren + ')</span>';
  }
  if(t.basis === 'unranked'){
    h += '<span class="unrk" title="' + esc(t.note || 'Not ranked by MyHockeyRankings')
       + '">unranked</span>';
  }
  return h;
}

function signed(n){ return (n > 0 ? '+' : n < 0 ? '&minus;' : '') + Math.abs(n).toFixed(1); }

// GitHub Pages puts the event file behind a CDN cache. During a tournament
// the whole point is to see the copy the scraper wrote minutes ago, so a manual
// refresh appends a unique query string that the cache has never seen.
// A season runs to a dozen tournaments, each its own file under events/ with
// events/index.json listing them. The page opens on the next one whose
// schedule is here; with nothing ahead, on the last one played. ?event=<id>
// picks a particular one, so a link can point at any of them.
let EVENTS = [];
let EVENT = null;

function loadIndex(bust){
  return grab('events/index.json', bust).then(function(doc){
    // A row with kind "games" is a season log, not a tournament: no groups, no
    // bracket, no dates to sort on. The ledger reads it the same way, but this
    // page cannot render it and must not offer it in the picker.
    EVENTS = ((doc && doc.events) || []).filter(function(e){
      return (e.kind || 'tournament') !== 'games';
    });
    return EVENTS;
  });
}

function chooseEvent(list, wanted){
  if(!list.length) return null;
  const byId = list.filter(function(e){ return e.id === wanted; })[0];
  if(byId) return byId;
  const today = new Date().toISOString().slice(0, 10);
  const ahead = list.filter(function(e){ return String(e.end || e.start) >= today; })
                    .sort(function(a, b){ return String(a.start).localeCompare(String(b.start)); });
  if(ahead.length) return ahead[0];
  return list.slice().sort(function(a, b){
    return String(b.end || b.start).localeCompare(String(a.end || a.start)); })[0];
}

function load(bust){
  const file = (EVENT && EVENT.file) || 'events/ccm-world-invite-chicago.json';
  return grab(file, bust);
}

// A tournament that is listed but whose schedule has not been published yet.
function hasSchedule(doc){
  return !!(doc && (((doc.games || []).length) || ((doc.teams || []).length)));
}

// The most recent tournament that has already finished.
function lastPlayed(list, notId){
  const today = new Date().toISOString().slice(0, 10);
  return list.filter(function(e){
      return e.id !== notId && String(e.end || e.start) < today; })
    .sort(function(a, b){
      return String(b.end || b.start).localeCompare(String(a.end || a.start)); })[0];
}

function ago(iso){
  const t = Date.parse(iso);
  if(isNaN(t)) return null;
  const secs = Math.max(0, (Date.now() - t) / 1000);
  if(secs < 45) return 'just now';
  const mins = Math.round(secs / 60);
  if(mins < 60) return mins + ' min ago';
  const hrs = Math.round(mins / 60);
  if(hrs < 24) return hrs + (hrs === 1 ? ' hour ago' : ' hours ago');
  const days = Math.round(hrs / 24);
  return days + (days === 1 ? ' day ago' : ' days ago');
}


// ---------------------------------------------------------------- score entry
// Obscurity, not security: the key below is readable in this page's source. It
// gates nothing but whether an editing panel is drawn, and that panel writes
// only to this browser's own localStorage -- it cannot change published data.
const EDIT_KEY = 'jets2026';
const BOOKMARKLET = __BOOKMARKLET__;
const LS_EDIT = 'scoreEdit';
const LS_MANUAL = 'manualScores';
// Cached per event, and so are typed scores: game numbers repeat between
// tournaments, and a 144 from September must not turn up in November's table.
function lsKey(base){ return base + '.' + ((EVENT && EVENT.id) || 'default'); }

// The path the copy tells you to paste into. Named, not guessed, because a
// season has a dozen of these and pasting into the wrong one is silent.
function eventFile(){ return (EVENT && EVENT.file) || 'the event file'; }
const LS_CACHE = 'tournamentCache';

// True when the network copy could not be fetched and the page is running on
// the last one it saved. Everything still works, but the corrected list built
// from it would be the file as it was, not as it is -- paste that and you undo
// whatever has been published since. So the page says so, and will not hand it
// over until a refresh succeeds.
let FROM_CACHE = false;

function lsGet(k){ try { return localStorage.getItem(k); } catch(e){ return null; } }
function lsSet(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
function lsDel(k){ try { localStorage.removeItem(k); } catch(e){} }

// ?edit=storm2026 unlocks, ?edit=off locks. Either way the parameter is stripped
// straight back out of the address bar, so it cannot be copied into a link that
// gets shared around. The flag lives in localStorage, so it survives a hard
// refresh and needs no network.
(function(){
  const q = new URLSearchParams(location.search);
  if(!q.has('edit')) return;
  const v = q.get('edit');
  if(v === EDIT_KEY) lsSet(LS_EDIT, '1');
  else if(v === 'off') lsDel(LS_EDIT);
  q.delete('edit');
  const rest = q.toString();
  history.replaceState(null, '', location.pathname + (rest ? '?' + rest : '') + location.hash);
})();

const EDITING = lsGet(LS_EDIT) === '1';

function manualAll(){
  try { return JSON.parse(lsGet(lsKey(LS_MANUAL)) || '{}') || {}; } catch(e){ return {}; }
}
function manualSave(m){ lsSet(lsKey(LS_MANUAL), JSON.stringify(m)); }

// A manual entry beats a scraped one and stays until it is cleared. The scraped
// value is kept alongside so a stale override can be spotted rather than
// silently winning.
function withManual(data){
  const m = manualAll();
  if(!data || !Object.keys(m).length) return data;
  const copy = JSON.parse(JSON.stringify(data));
  for(const g of copy.games){
    const e = m[g.id];
    if(!e) continue;
    if(e.home != null) g.homeScore = e.home;
    if(e.away != null) g.awayScore = e.away;
    if(e.decision) g.decision = e.decision;
  }
  return copy;
}

// The top of the score-entry panel. A tournament run on GameSheet can have a
// whole day read off it at once, which is worth three paragraphs of explaining.
// One that is not has nothing to capture from, and saying otherwise sends
// somebody looking for a day link that was never going to be there -- so it
// gets a link to its own schedule and the plain instruction to type.
//
// Which it is comes from the file: gsSeason is what the capture needs, and a
// tournament without one is not on GameSheet.
function captureBlock(data){
  const t = (data && data.tournament) || {};
  if(t.gsSeason){
    return '<div class="sc-bm">'
      +   '<div class="sc-help">'
      +   '<p><b>Capture from GameSheet.</b> Two ways in, and the first needs nothing installed.</p>'
      +   '<p><b>On a phone or iPad.</b> Open a day below, select the whole list, copy it, and paste it in the box. Safari refuses bookmarklets outright, so this is the way there.</p>'
      +   '<p><b>On a computer.</b> Drag <b>Grab GameSheet</b> onto your bookmarks bar &mdash; it is a bookmark to install, not a button to press here. Open a day, click the bookmark on <em>that</em> tab, scroll the whole list while the counter climbs, then press Copy in its panel. It keeps the capture across days and across tabs left open.</p>'
      +   '<p>Either way, paste below and press <b>Import scores</b>. Capture a day again whenever anything changes &mdash; the bracket filling in, or games moved after a rink loses power. If the schedule has changed, the box below holds the corrected list: paste it into this tournament&rsquo;s file in <b>events/</b> as the whole <b>games</b> value.</p>'
      +   '</div>'
      +   '<div id="sc-daylinks"></div>'
      +   '<a id="sc-bmlink" href="' + BOOKMARKLET + '">Grab GameSheet</a>'
      +   '<button type="button" class="sc-act" id="sc-bmcopy">Copy its code</button>'
      +   '<textarea class="sc-paste" id="sc-paste" placeholder="Paste the copied schedule here, or what the bookmarklet gives you."></textarea>'
      +   '<button type="button" class="sc-act" id="sc-doimport">Import scores</button>'
      +   '<div class="sc-result" id="sc-result"></div>'
      +   '<textarea class="sc-out" id="sc-slots" readonly hidden></textarea>'
      + '</div>';
  }
  return '<div class="sc-bm">'
    +   '<div class="sc-help">'
    +   '<p><b>This tournament is not on GameSheet</b>, so there is nothing to '
    +     'capture and no bookmarklet to install. Scores go in by hand below.</p>'
    +   '<p>Type both numbers for a game, then press <b>Copy for the event file</b> '
    +     'and paste what it gives you into ' + esc(eventFile()) + ' as the whole '
    +     '<b>games</b> value. Until that is committed the scores live in this '
    +     'browser and no other phone can see them.</p>'
    +   '</div>'
    + (t.source
       ? '<a href="' + esc(t.source) + '" target="_blank" rel="noopener noreferrer">'
         + 'Tournament schedule</a>'
       : '')
    + '</div>';
}

// One link per day of the tournament, filtered to the 14U divisions and in
// list view -- the same URLs the capture is meant to be run against. The season
// and division ids live in the event file so a different event needs no code.
function dayLinks(data){
  const t = (data && data.tournament) || {};
  if(!t.gsSeason || !Array.isArray(t.gsDivisions) || !t.gsDivisions.length) return '';

  const days = [];
  (data.games || []).forEach(function(g){
    const d = String(g.start || '').slice(0, 10);
    if(d && days.indexOf(d) < 0) days.push(d);
  });
  if(!days.length) return '';
  days.sort();

  const divs = t.gsDivisions.join(',');
  return '<div class="sc-days">' + days.map(function(d){
    const url = 'https://gamesheetstats.com/seasons/' + encodeURIComponent(t.gsSeason)
      + '/games?filter[division]=' + divs
      + '&configuration[compact-view]=compact'
      + '&filter[start_time_from]=' + d + '&filter[start_time_to]=' + d;
    const played = (data.games || []).filter(function(g){
      return String(g.start || '').slice(0, 10) === d;
    }).length;
    return '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">'
         + dayLabel(d + 'T12:00')
         + '<b>' + played + ' in our file</b></a>';
  }).join('') + '</div>';
}

function todayInTournament(tz){
  try {
    return new Intl.DateTimeFormat('en-CA', {timeZone: tz || 'UTC', year: 'numeric',
      month: '2-digit', day: '2-digit'}).format(new Date());
  } catch(e){
    return new Date().toISOString().slice(0, 10);
  }
}

let scShowAll = false;
let scTimer = null;

function buildPanel(data){
  if(!EDITING || !data || !data.games) return;

  let sec = el('t-edit');
  if(!sec){
    sec = document.createElement('section');
    sec.className = 't-sec';
    sec.id = 't-edit';
    sec.innerHTML =
      '<h2>Score entry</h2>'
      + '<p class="t-sub">Everything here is kept in this browser only, overrides '
      + 'anything published, and feeds the standings and the bracket odds '
      + 'straight away.</p>'
      // Capture leads, where there is one: it is short, and it is how most of a
      // day arrives.
      + captureBlock(data)
      + '<p class="t-sub"><b>Or type them in.</b> Each team&rsquo;s goals go beside '
      + 'its name.</p>'
      + '<div class="sc-bar">'
      +   '<button type="button" class="sc-toggle" id="sc-today" aria-pressed="true">Today</button>'
      +   '<button type="button" class="sc-toggle" id="sc-all" aria-pressed="false">All games</button>'
      +   '<button type="button" class="sc-act" id="sc-copy">Copy for the event file</button>'
      +   '<button type="button" class="sc-act" id="sc-clearall">Clear all</button>'
      + '</div>'
      + '<p class="sc-note" id="sc-note"></p>'
      + '<div class="sc-list" id="sc-list"></div>'
      + '<textarea class="sc-out" id="sc-out" readonly hidden></textarea>';
    el('p-update').appendChild(sec);
    const tab = el('tab-update');
    if(tab) tab.hidden = false;

    el('sc-today').addEventListener('click', function(){ setScope(false); });
    el('sc-all').addEventListener('click', function(){ setScope(true); });
    el('sc-copy').addEventListener('click', copyCorrections);
    el('sc-clearall').addEventListener('click', function(){
      if(!Object.keys(manualAll()).length) return;
      manualSave({});
      renderPanel(lastRaw);
      recompute();
    });
    const slot = el('sc-daylinks');
    if(slot) slot.innerHTML = dayLinks(data);
    const bml = el('sc-bmlink');
    if(bml) bml.addEventListener('click', function(ev){
      // Dragging does not fire a click, so this costs nothing and saves the
      // confusion of running the capture against this page instead of theirs.
      ev.preventDefault();
      el('sc-result').innerHTML = '<span class="warn">That link installs the '
        + 'bookmarklet &mdash; it does nothing useful here, because the games are on '
        + 'GameSheet&rsquo;s page, not this one. Drag it to your bookmarks bar (or tap '
        + '<b>Copy its code</b>), then open a day above and click your bookmark '
        + '<b>on that tab</b>.</span>';
    });

    const imp = el('sc-doimport');
    if(imp) imp.addEventListener('click', function(){
      const box = el('sc-paste'), res = el('sc-result');
      const r = importCapture(box.value || '');
      if(r.error){ res.innerHTML = '<span class="bad">' + esc(r.error) + '</span>'; return; }

      let msg = '<b>' + r.rows + '</b> rows read. <span class="ok"><b>' + r.applied
              + '</b> score' + (r.applied === 1 ? '' : 's') + ' applied</span>'
              + (r.same ? ', ' + r.same + ' already matched' : '') + '.';
      if(r.noGame.length){
        msg += '<br><span class="warn">' + r.noGame.length + ' game number'
             + (r.noGame.length === 1 ? '' : 's') + ' not in our schedule: '
             + esc(r.noGame.slice(0, 8).join(', ')) + '</span>';
      }
      if(r.noTeam.length){
        msg += '<br><span class="warn">Unmatched team names: '
             + esc(r.noTeam.slice(0, 5).join('; ')) + '</span>';
      }
      if(r.moved.length){
        const when = function(x){
          return x.from.slice(5, 10) + ' ' + clockOf(x.from)
               + (x.fromRink ? ' ' + shortRink(x.fromRink) : '');
        };
        msg += '<br><span class="warn">' + r.moved.length + ' game'
             + (r.moved.length === 1 ? ' has' : 's have') + ' been rescheduled: '
             + r.moved.slice(0, 6).map(function(x){
                 return esc(x.id + ' ' + when(x)) + ' &rarr; '
                      + esc((x.noTime ? '' : clockOf(x.to) + ' ')
                            + (x.toRink ? shortRink(x.toRink) : ''))
                      + (x.noTime ? ' (time hidden once it starts)' : '');
               }).join('; ') + '</span>';
      }
      if(r.gone.length){
        // Kept, not dropped: a capture that stopped halfway down the list looks
        // exactly like a day of cancellations, and only you can tell which.
        msg += '<br><span class="warn">' + r.gone.length + ' game'
             + (r.gone.length === 1 ? ' is' : 's are') + ' not in this capture: '
             + esc(r.gone.slice(0, 8).map(function(g){ return g.id; }).join(', '))
             + '. They are kept below. Delete them by hand if they were '
             + 'cancelled, or scroll the whole list and capture again.</span>';
      }
      if(r.slots.length){
        msg += '<br><span class="warn">' + r.slots.length + ' bracket game'
             + (r.slots.length === 1 ? '' : 's') + ' not on file.</span>';
      }
      if(r.unplaced.length){
        msg += '<br><span class="warn">' + r.unplaced.length + ' finished bracket game'
             + (r.unplaced.length === 1 ? '' : 's') + ' could not be placed, because '
             + 'the schedule does not have those teams in a game yet: '
             + esc(r.unplaced.slice(0, 5).join('; ')) + '. Capture the day again once '
             + 'the pairing is posted, or add it by hand.</span>';
      }
      if(r.level.length){
        msg += '<br><span class="warn">' + r.level.length + ' game'
             + (r.level.length === 1 ? ' is' : 's are') + ' level with no shootout '
             + 'recorded, so still being played: ' + esc(r.level.slice(0, 6).join(', '))
             + '. Left alone.</span>';
      }
      if(r.filled.length){
        const set = r.filled.filter(function(x){ return x.was; }).length;
        const one = r.filled.length === 1;
        msg += '<br><span class="ok">' + r.filled.length + ' game' + (one ? '' : 's')
             + (set === r.filled.length
                  ? ' now ' + (one ? 'has' : 'have') + ' teams'
                  : (one ? ' has a different fixture' : ' have different fixtures')) + ': '
             + esc(r.filled.slice(0, 6).map(function(x){
                 return x.visitor + ' v ' + x.home;
               }).join('; ')) + '</span>';
      }
      // Anything the page cannot store itself goes out as the whole corrected
      // list, so one paste settles it rather than a hunt through the file.
      if(r.schedule){
        msg += '<br><span class="warn">'
             + (r.held ? r.held + ' score' + (r.held === 1 ? ' is' : 's are')
                       + ' held in this browser only &mdash; no phone '
                       + 'can see ' + (r.held === 1 ? 'it' : 'them')
                       + ' until published. ' : '')
             + 'Copy the list below and paste it into ' + eventFile() + ' as '
             + 'the whole <b>games</b> value, then commit.</span>';
        el('sc-slots').hidden = false;
        el('sc-slots').value = JSON.stringify(r.schedule, null, 1);
      }
      res.innerHTML = msg;
      box.value = '';
      renderPanel(lastRaw);
      recompute();
    });
    const bmc = el('sc-bmcopy');
    if(bmc) bmc.addEventListener('click', function(){
      const out = el('sc-out');
      const done = function(m){ el('sc-note').textContent = m; };
      if(navigator.clipboard && navigator.clipboard.writeText){
        navigator.clipboard.writeText(BOOKMARKLET).then(function(){
          done('Bookmarklet copied. Make any bookmark, then edit it and paste this as its address.');
        }, function(){ out.value = BOOKMARKLET; selectAll(out);
                       done('Select all in the box and copy it.'); });
      } else {
        out.value = BOOKMARKLET; selectAll(out);
        done('Select all in the box and copy it.');
      }
    });
    el('sc-list').addEventListener('input', onScoreInput);
    el('sc-list').addEventListener('click', onPanelClick);

    // "Today" is the right default while the tournament is on and misleading
    // every other day -- an empty panel reads as broken rather than as a day
    // off. Open on everything when today has nothing scheduled.
    const day = todayInTournament((data.tournament || {}).timezone);
    const anyToday = data.games.some(function(g){
      return g.home && g.away && String(g.start).slice(0, 10) === day;
    });
    setScope(!anyToday);
    return;
  }
  renderPanel(data);
}

function setScope(all){
  scShowAll = all;
  el('sc-today').setAttribute('aria-pressed', all ? 'false' : 'true');
  el('sc-all').setAttribute('aria-pressed', all ? 'true' : 'false');
  renderPanel(lastRaw);
}

function renderPanel(data){
  if(!EDITING || !data || !el('sc-list')) return;
  const m = manualAll();
  const names = {};
  data.teams.forEach(function(t){ names[t.id] = t.name; });
  const today = todayInTournament((data.tournament || {}).timezone);

  const playable = data.games
    .filter(function(g){ return g.home && g.away; })
    .sort(function(a, b){ return String(a.start).localeCompare(String(b.start)); });
  const rows = scShowAll ? playable
    : playable.filter(function(g){ return String(g.start).slice(0, 10) === today; });

  let mismatches = 0;
  let h = '';
  for(const g of rows){
    const e = m[g.id];
    const scraped = g.homeScore != null && g.awayScore != null;
    const clash = !!e && scraped
      && (e.home !== g.homeScore || e.away !== g.awayScore);
    if(clash) mismatches++;

    const how = (e && e.decision) ? e.decision : (scraped ? decisionOf(g) : null);
    const src = e ? '<span class="sc-src is-manual">manual</span>'
      : scraped ? '<span class="sc-src is-scraped">scraped</span>' : '';
    const decTag = (how === 'OT' || how === 'SO')
      ? '<span class="sc-src">' + how + '</span>' : '';
    const val = function(side){
      if(e && e[side] != null) return e[side];
      const sc = side === 'home' ? g.homeScore : g.awayScore;
      return sc == null ? '' : sc;
    };
    const box = function(side){
      return '<input class="sc-in" type="text" inputmode="numeric" pattern="[0-9]*" '
        + 'maxlength="2" data-id="' + esc(g.id) + '" data-side="' + side + '" '
        + 'aria-label="Goals for ' + esc(names[g[side]] || '') + '" '
        + 'value="' + val(side) + '">';
    };
    const isStorm = /^Chicago Jets/.test(names[g.home] || '') || /^Chicago Jets/.test(names[g.away] || '');

    h += '<div class="sc-game' + (clash ? ' mismatch' : '') + (isStorm ? ' hl' : '') + '" '
      +      'data-id="' + esc(g.id) + '">'
      + '<div class="sc-head"><span class="sc-num">#' + esc(g.id) + '</span>'
      +   (g.group ? '<span class="flag">' + esc(g.group) + '</span>' : '')
      +   '<span>' + when(g.start).replace('<br>', ' &middot; ') + '</span>'
      +   src + decTag + '</div>'
      // Two rows, each a team and its own box. Never one combined field, and
      // never labelled home or away -- the name beside the box is the label.
      + '<div class="sc-row"><span class="sc-name">' + esc(names[g.home] || g.home)
      +   '</span>' + box('home') + '</div>'
      + '<div class="sc-row"><span class="sc-name">' + esc(names[g.away] || g.away)
      +   '</span>' + box('away') + '</div>'
      + '<div class="sc-dec" role="group" aria-label="How game ' + esc(g.id) + ' was decided">'
      +   ['REG', 'OT', 'SO'].map(function(d){
            const on = (e && e.decision ? e.decision : 'REG') === d;
            return '<button type="button" data-dec="' + esc(g.id) + '" data-how="' + d
                 + '" aria-pressed="' + (on ? 'true' : 'false') + '">'
                 + (d === 'REG' ? 'Regulation' : d) + '</button>';
          }).join('')
      + '</div>'
      + '<div class="sc-foot">'
      +   (e ? '<button type="button" class="sc-clear" data-clear="' + esc(g.id) + '">Clear</button>' : '')
      +   (clash ? '<span class="sc-flag">scraped since: ' + g.homeScore + '&ndash;'
                 + g.awayScore + '</span>' : '')
      + '</div></div>';
  }

  el('sc-list').innerHTML = h || '<p class="t-note">No games on this day.</p>';
  const kept = Object.keys(m).length;
  el('sc-note').innerHTML =
    rows.length + ' game' + (rows.length === 1 ? '' : 's') + ' shown &middot; '
    + kept + ' manual entr' + (kept === 1 ? 'y' : 'ies') + ' stored'
    + (mismatches ? ' &middot; <b>' + mismatches + ' disagree with a newer scraped score</b>' : '');
}

function onScoreInput(ev){
  const t = ev.target;
  if(!t || !t.classList || !t.classList.contains('sc-in')) return;
  const clean = String(t.value).replace(/[^0-9]/g, '').slice(0, 2);
  if(clean !== t.value) t.value = clean;

  const m = manualAll();
  const id = t.getAttribute('data-id');
  const side = t.getAttribute('data-side');
  const entry = m[id] || {home: null, away: null};
  entry[side] = clean === '' ? null : parseInt(clean, 10);
  entry.at = new Date().toISOString();
  if(entry.home == null && entry.away == null) delete m[id];
  else m[id] = entry;
  manualSave(m);
  recompute();
}

function onPanelClick(ev){
  if(!ev.target.closest) return;

  const dec = ev.target.closest('[data-dec]');
  if(dec){
    const m = manualAll();
    const id = dec.getAttribute('data-dec');
    // Only meaningful alongside a score, so it starts an entry if there is none.
    const entry = m[id] || {home: null, away: null};
    entry.decision = dec.getAttribute('data-how');
    entry.at = new Date().toISOString();
    m[id] = entry;
    manualSave(m);
    renderPanel(lastRaw);
    recompute();
    return;
  }

  const btn = ev.target.closest('[data-clear]');
  if(!btn) return;
  const m = manualAll();
  delete m[btn.getAttribute('data-clear')];
  manualSave(m);
  renderPanel(lastRaw);
  recompute();
}

// The simulation is ten thousand iterations; do not run it on every keystroke.
function recompute(){
  drawImport();   // cheap, and the line beside Refresh is about to be wrong
  if(scTimer) clearTimeout(scTimer);
  scTimer = setTimeout(function(){
    scTimer = null;
    if(lastRaw) draw(withManual(lastRaw));
    renderPanelNote();
  }, 250);
}

function renderPanelNote(){
  if(EDITING && el('sc-list')) renderPanel(lastRaw);
}

// Team names, not home and away. the event file's "home" is GameSheet's
// visitor -- they are swapped for every game -- so anything keyed on position
// would put the scores on the wrong team.
function normName(s){
  return String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9]/g, '');
}

// Select the schedule, copy, paste. No bookmarklet, which is the only way this
// works on an iPad: Safari refuses a javascript: bookmark outright and the
// Shortcuts route is four steps of setup. The text is regular enough to read
// straight -- every game is a block that starts with its date.
//
//   Sep 5, 2026 / Cambridge Roadrunners / 14U Group D / 3-2 /
//   Buffalo Jr Sabres / 14U Group D / <rink> / 187 / Tournament
//
// The two division lines are the anchors: a team name is the line above one,
// the score or faceoff time sits between them, and the rink and game number
// follow the second. Reading it that way rather than by counting lines
// survives the optional rows -- SO, Live, "Watch on LiveBarn", the NOW divider.
const TEXT_MONTHS = {jan: 1, feb: 2, mar: 3, apr: 4, may: 5, jun: 6,
                     jul: 7, aug: 8, sep: 9, oct: 10, nov: 11, dec: 12};
const TEXT_DATE = /^([A-Za-z]{3})[a-z]*\s+(\d{1,2}),\s*(\d{4})$/;
const TEXT_DIV = /^(?:\d+U|U\d+)\b/i;
const TEXT_TIME = /^\d{1,2}:\d{2}\s*(AM|PM)$/i;
const TEXT_SCORE = /^(\d+)\s*[-–—]\s*(\d+)$/;
const TEXT_DECISION = /^(?:F\/)?(OT|SO)$/i;
const TEXT_NOISE = /^(tournament|playoff|exhibition|now|final|watch on livebarn|watch)$/i;

function rowsFromText(text){
  const lines = String(text).split('\n')
    .map(function(x){ return x.replace(/\s+/g, ' ').trim(); })
    .filter(function(x){ return x && !TEXT_NOISE.test(x); });

  const starts = [];
  lines.forEach(function(x, i){ if(TEXT_DATE.test(x)) starts.push(i); });
  if(!starts.length) return null;

  const out = [];
  for(let k = 0; k < starts.length; k++){
    const block = lines.slice(starts[k], k + 1 < starts.length ? starts[k + 1] : lines.length);
    const dm = block[0].match(TEXT_DATE);
    const month = TEXT_MONTHS[dm[1].toLowerCase()];
    if(!month) continue;
    const date = dm[3] + '-' + ('0' + month).slice(-2) + '-' + ('0' + dm[2]).slice(-2);

    const divs = [];
    block.forEach(function(x, i){ if(i > 0 && TEXT_DIV.test(x)) divs.push(i); });
    if(divs.length < 2) continue;
    const a = divs[0], b = divs[1];
    if(a < 2 || b < a + 2) continue;

    const team = function(x){ return /^(tbd|to be determined|--|-)$/i.test(x) ? null : x; };
    const row = {n: null, label: null, date: date, time: null,
                 rink: block[b + 1] || null, division: block[a] || null,
                 visitor: team(block[a - 1]), home: team(block[b - 1]),
                 visitorScore: null, homeScore: null, decision: null};

    let live = false;
    for(let i = a + 1; i < b - 1; i++){
      const v = block[i], sm = v.match(TEXT_SCORE);
      if(sm){ row.visitorScore = +sm[1]; row.homeScore = +sm[2]; continue; }
      if(TEXT_DECISION.test(v)){ row.decision = v.replace(/^F\//i, '').toUpperCase(); continue; }
      if(TEXT_TIME.test(v)){ row.time = v; continue; }
      if(/^live$/i.test(v)) live = true;
    }
    // A running score is not a result, exactly as the bookmarklet has it.
    if(live){ row.visitorScore = row.homeScore = row.decision = null; row.live = true; }
    else if(row.visitorScore !== null && !row.decision) row.decision = 'REG';

    const num = block[b + 2];
    if(!num) continue;
    if(/^\d+$/.test(num)) row.n = num;
    else { row.n = num; row.label = num; }
    out.push(row);
  }
  return out.length ? out : null;
}

// Which game on file a captured row is. The number settles it where there is
// one, but a bracket game has none -- the site prints the round name where the
// number goes -- so once one is played it cannot be looked up at all. The two
// teams identify it instead: a pair meets once, and where a pair meets twice
// across the weekend the date separates them.
function matchGame(r, byNum, teamId){
  if(byNum[r.n]) return byNum[r.n];
  const v = teamId[normName(r.visitor)], h = teamId[normName(r.home)];
  if(!v || !h) return null;
  const pair = [v, h].sort().join('|');
  let hits = lastRaw.games.filter(function(g){
    return g.home && g.away && [g.home, g.away].sort().join('|') === pair;
  });
  // Two teams can meet twice over a weekend -- a group game and a bracket one,
  // or two rounds of the bracket. The day decides between them, and a single
  // hit on the wrong day is still the wrong game: Madison against Boston on
  // Sunday matched their Saturday consolation game and read as a reschedule.
  if(r.date){
    hits = hits.filter(function(g){
      return String(g.start).slice(0, 10) === String(r.date);
    });
  }
  return hits.length === 1 ? hits[0] : null;
}

// Which game on file each captured row is, decided for the whole capture at
// once because the later answers depend on the earlier ones.
//
// Three passes. The number or the teams settle most rows. A bracket row that
// still shows a faceoff time is the slot at that time on that sheet. What is
// left are bracket games that have started, whose time the site has replaced
// with a score -- and the only thing left to place those by is the order a
// sheet plays its games in: a finished game is earlier than one in progress,
// and both are earlier than one still to come. So the leftovers go into the
// remaining slots on their own rink in that order.
// "14U Gold Semifinal" and "14U Semifinal" are the same round; "14U
// Championship" and "14U Gold Championship" are too. Reduce both sides to the
// word that matters so a captured row can be matched to the slot waiting for
// it, whatever the site is calling it today.
function roundKey(text){
  const v = String(text || '').toLowerCase();
  if(/championship|final\b/.test(v) && !/semi|quarter/.test(v)) return 'final';
  if(/semi/.test(v)) return 'semi';
  if(/quarter|qtr/.test(v)) return 'quarter';
  if(/consol/.test(v)) return 'consolation';
  return null;
}

function placeRows(rows, byNum, teamId){
  const at = new Array(rows.length).fill(null);
  const taken = {};

  rows.forEach(function(r, i){
    const g = matchGame(r, byNum, teamId);
    if(g){ at[i] = g; taken[g.id] = true; }
  });

  const free = {};
  lastRaw.games.forEach(function(g){
    if(g.home || g.away || taken[g.id]) return;
    const k = String(g.start).slice(0, 10) + '|' + (g.rink || '');
    (free[k] = free[k] || []).push(g);
  });
  for(const k in free){
    free[k].sort(function(a, b){ return String(a.start).localeCompare(String(b.start)); });
  }
  const claim = function(i, g){
    at[i] = g;
    taken[g.id] = true;
    const k = String(g.start).slice(0, 10) + '|' + (g.rink || '');
    const pool = free[k] || [];
    const w = pool.indexOf(g);
    if(w >= 0) pool.splice(w, 1);
  };

  rows.forEach(function(r, i){
    if(at[i] || (!r.visitor && !r.home)) return;
    const start = slotStart(r);
    if(!start) return;
    const hit = (free[String(r.date) + '|' + (r.rink || '')] || []).filter(function(g){
      return g.start === start;
    })[0];
    if(hit) claim(i, hit);
  });

  const waiting = [];
  rows.forEach(function(r, i){
    if(at[i] || (!r.visitor && !r.home) || slotStart(r)) return;
    waiting.push(i);
  });
  const stage = function(r){ return r.homeScore != null ? 0 : (r.live ? 1 : 2); };
  waiting.sort(function(a, b){ return stage(rows[a]) - stage(rows[b]); });
  waiting.forEach(function(i){
    const pool = free[String(rows[i].date) + '|' + (rows[i].rink || '')];
    if(!pool || !pool.length) return;
    // The round is the strongest thing left. A semifinal and a final both
    // played on the same sheet with their times gone were being handed out in
    // the order they happened to be captured, which put the final's score in
    // the semifinal's slot and the semifinal's in the final's.
    const want = roundKey(rows[i].label || rows[i].n);
    const same = want && pool.filter(function(g){ return roundKey(g.label) === want; })[0];
    claim(i, same || pool[0]);
  });

  return at;
}

// Every row imported this session, in the order it arrived. Copy for
// the event file rebuilds from these as well as from the file, because
// otherwise it hands back the schedule as the file has it and silently drops
// the teams the import just worked out -- which is how two Silver semifinals
// came back carrying scores and no teams.
const SEEN_ROWS = [];

function importCapture(text){
  if(!lastRaw) return {error: 'No schedule loaded yet. Refresh the page first.'};
  let doc = null;
  try { doc = JSON.parse(text); } catch(e){ doc = null; }

  const rows = doc && Array.isArray(doc.rows) ? doc.rows
             : (Array.isArray(doc) ? doc : rowsFromText(text));
  if(!rows) return {error: 'No games in that paste. Copy the schedule from the '
                         + 'GameSheet page, or paste what the bookmarklet gives you.'};

  const byNum = {};
  lastRaw.games.forEach(function(g){ byNum[g.id] = g; });
  const teamId = {};
  lastRaw.teams.forEach(function(t){
    [t.name, t.mhrName, t.gsName].forEach(function(a){
      if(a) teamId[normName(a)] = t.id;
    });
  });

  const m = manualAll();
  const placed = placeRows(rows, byNum, teamId);
  const out = {applied: 0, same: 0, noGame: [], noTeam: [], slots: [],
               moved: [], gone: [], filled: [], level: [], unplaced: [],
               schedule: null, rows: rows.length};
  // These rules send a tied game to a shootout, so a level score with no OT or
  // SO marker is not a result -- it is a game still being played, or one
  // between periods with the badge gone. Taking it as final gave both sides a
  // point they had not earned and moved a group.
  const noTies = !!((lastRaw.rules || {}).noTies);

  // A game can be moved as well as played -- a rink losing power moves a whole
  // evening. Scores would still land, because they match on the game number,
  // but the page would go on showing the faceoff time that no longer applies.
  const seen = {};
  for(let ri = 0; ri < rows.length; ri++){
    const r = rows[ri];
    const g = placed[ri];
    if(!g) continue;
    seen[g.id] = true;
    const start = slotStart(r);
    if(start && g.start !== start){
      out.moved.push({id: g.id, from: g.start, to: start,
                      fromRink: g.rink, toRink: r.rink || g.rink});
    } else if(r.rink && g.rink && r.rink !== g.rink){
      // Once a game starts the score sits where the faceoff time was, so a
      // capture can no longer read it. The sheet moved and the time may have
      // moved with it; say so rather than showing the old one as if confirmed.
      out.moved.push({id: g.id, from: g.start, to: g.start,
                      fromRink: g.rink, toRink: r.rink, noTime: !start});
    }
  }
  // The bracket filling in changes no time and no sheet, so only the teams can
  // give it away. Compared as a pair, because the file stores GameSheet's
  // visitor as its home.
  for(let ri = 0; ri < rows.length; ri++){
    const r = rows[ri];
    if(!r.visitor || !r.home) continue;
    const vId = teamId[normName(r.visitor)], hId = teamId[normName(r.home)];
    if(!vId || !hId) continue;
    const g = placed[ri];
    if(!g) continue;
    if([g.home, g.away].sort().join('|') !== [vId, hId].sort().join('|')){
      out.filled.push({id: g.id, n: r.n, visitor: r.visitor, home: r.home,
                       was: !g.home && !g.away});
    }
  }

  // Only days the capture covers can be judged: a day nobody looked at is not
  // a day whose games were cancelled.
  const days = {};
  rows.forEach(function(r){ if(r.date) days[r.date] = true; });
  const claimed = {};
  rows.forEach(function(r){ const st = slotStart(r);
    if(st) claimed[st + '|' + (r.rink || '')] = true; });
  lastRaw.games.forEach(function(g){
    if(!days[String(g.start).slice(0, 10)] || seen[g.id]) return;
    if(claimed[g.start + '|' + (g.rink || '')]) return;
    out.gone.push(g);
  });

  for(let ri = 0; ri < rows.length; ri++){
    const r = rows[ri];
    if(r.homeScore == null || r.visitorScore == null){
      // A bracket slot we do not have on file yet -- worth reporting, but the
      // page cannot add games to the event file. A slot has no game number
      // until its teams are known, so being on file means a game already
      // stands at that time on that sheet, which is the only thing that can.
      if(!placed[ri] && !onFile(r)) out.slots.push(r);
      continue;
    }
    const g = placed[ri];
    // The rule is about round-robin games -- "round-robin games tied after
    // regulation go to a 3-player shootout" -- so only a group game that shows
    // level is a game still being played. A bracket game can genuinely finish
    // level: one did, on the last sheet of a long Saturday night.
    if(noTies && r.homeScore === r.visitorScore
       && !(r.decision && r.decision !== 'REG')
       && (!g || g.round === 'group')){
      out.level.push(r.n);
      continue;
    }
    if(!g){
      // Nowhere left to put it: no number, no slot on file naming those two,
      // no faceoff time, and no free slot on that sheet either. Name whose
      // game it was rather than reporting a round name as a number.
      if(r.visitor && r.home && !/^\d+$/.test(String(r.n))){
        out.unplaced.push(r.visitor + ' v ' + r.home);
      } else {
        out.noGame.push(r.n);
      }
      continue;
    }

    const vId = teamId[normName(r.visitor)], hId = teamId[normName(r.home)];
    if(!vId || !hId){
      out.noTeam.push((!vId ? r.visitor : r.home) + ' (game ' + r.n + ')');
      continue;
    }
    const scoreFor = {};
    scoreFor[vId] = r.visitorScore;
    scoreFor[hId] = r.homeScore;
    // A bracket slot this capture has only just filled has no teams on file
    // yet, so there is nothing to orient the score against. It takes the same
    // convention the rest of the file uses, and that the corrected list is
    // about to write: our home is GameSheet's visitor.
    const home = g.home ? scoreFor[g.home] : r.visitorScore;
    const away = g.away ? scoreFor[g.away] : r.homeScore;
    if(home == null || away == null){
      out.noTeam.push(r.visitor + ' v ' + r.home + ' (game ' + r.n + ' is a different fixture)');
      continue;
    }

    // Keyed by the game's own id, not by what the site printed in the number
    // column. For a group game those are the same string; for a bracket game
    // the column holds the round name, and a score filed under "14U
    // Consolation" is a score nothing ever reads back.
    const had = m[g.id];
    if(had && had.home === home && had.away === away
       && (had.decision || 'REG') === (r.decision || 'REG')){
      out.same++;
      continue;
    }
    m[g.id] = {home: home, away: away, decision: r.decision || 'REG',
               at: new Date().toISOString()};
    out.applied++;
  }

  rows.forEach(function(r){ SEEN_ROWS.push(r); });
  manualSave(m);
  out.held = unpublished().length;
  if(out.moved.length || out.gone.length || out.slots.length || out.filled.length
     || out.unplaced.length || out.held){
    out.schedule = rebuildGames(rows, placed);
  }
  return out;
}

// "2026-09-05T17:40:00-04:00" as the rink would say it.
function clockOf(iso){
  let h = +String(iso).slice(11, 13);
  const ap = h < 12 ? 'am' : 'pm';
  h = h % 12 || 12;
  return h + ':' + String(iso).slice(14, 16) + ap;
}

// "Ice Castle Arena Roadside Rink" -> "Roadside": the word that tells the
// sheets apart, not the four they share.
function shortRink(name){
  const w = String(name || '').split(/\s+/).filter(function(x){
    return !/^(rink|arena|ice|center|centre|recreation|the|main)$/i.test(x);
  });
  return w.length ? w[w.length - 1] : String(name || '');
}

// Bracket rows the page cannot store itself, shaped for the event file.
// GameSheet does not number these: a dozen rows all say "14U QTR / CONSOL", so
// the text in that column is a round name, not an id. An existing stand-in at
// the same time and rink lends its id so pasting replaces rather than
// duplicates; anything genuinely new gets one derived from when it starts,
// which is unique and obviously ours.
// A captured row's faceoff time as the schedule writes it. The offset is
// borrowed from the file rather than assumed: the rink's local time is what
// GameSheet shows and what the event file already carries.
function slotStart(r){
  if(!r.date || !r.time) return null;
  const t = String(r.time).match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
  if(!t) return null;
  const offset = ((lastRaw.games.find(function(g){ return g.start; }) || {}).start || '')
                   .slice(19) || '+00:00';
  let hh = (+t[1]) % 12;
  if(/pm/i.test(t[3])) hh += 12;
  return r.date + 'T' + ('0' + hh).slice(-2) + ':' + t[2] + ':00' + offset;
}

// One sheet holds one game at a time, so a game already standing there is the
// one this row describes.
function onFile(r){
  const start = slotStart(r);
  if(!start) return false;
  return lastRaw.games.some(function(g){
    return g.start === start && (!g.rink || !r.rink || g.rink === r.rink);
  });
}

// The whole games list as the capture says it should be. Days the capture did
// not cover pass through untouched, so capturing Saturday alone cannot lose
// Friday. Ids are kept wherever a game can be recognised -- by its number, or
// for a bracket slot by the sheet it stands on -- so scores already entered
// against them survive the rewrite.
function rebuildGames(rows, placed){
  const byNum = {}, teamId = {};
  lastRaw.games.forEach(function(g){ byNum[g.id] = g; });
  lastRaw.teams.forEach(function(t){
    [t.name, t.mhrName, t.gsName].forEach(function(a){
      if(a) teamId[normName(a)] = t.id;
    });
  });

  // Nothing is dropped for going unmentioned. The list is capped and you scroll
  // it, so a capture that stopped halfway is indistinguishable from a day whose
  // games were cancelled -- and getting that wrong deletes real games from the
  // schedule. Only a row that plainly supersedes another takes its place.
  const keep = {};
  lastRaw.games.forEach(function(g){ keep[g.id] = g; });

  const tag = function(rink){
    return String(rink || '').split(/[^A-Za-z]+/)
      .filter(Boolean).map(function(w){ return w[0].toUpperCase(); }).join('');
  };

  const seats = placed || placeRows(rows, byNum, teamId);

  rows.forEach(function(r, ri){
    const start = slotStart(r);
    const rink = r.rink || null;
    const standIn = seats[ri] || lastRaw.games.filter(function(g){
      return g.start === start && (!g.rink || !rink || g.rink === rink)
             && !g.home && !g.away;
    })[0];
    const old = standIn;

    // the event file's home is GameSheet's visitor. Every fixture in the file
    // is stored that way, so a newly filled bracket game is stored that way too.
    const vId = teamId[normName(r.visitor)], hId = teamId[normName(r.home)];
    // Both sides for a group game; a bracket pairing can be posted one side at
    // a time, and half of one still belongs on the schedule.
    const known = !!(vId && hId);
    const either = !!(vId || hId);

    if(!old && !start && !/^\d+$/.test(String(r.n))) return;   // nowhere to put it
    let id = /^\d+$/.test(String(r.n)) ? String(r.n)
           : (old ? old.id
              : (start ? 'P' + start.slice(8, 10) + start.slice(11, 13)
                             + start.slice(14, 16) + tag(rink)
                       : String(r.n)));
    let k = 2;
    while(keep[id] && (!old || keep[id].id !== old.id)) id = id + '-' + (k++);

    // An empty slot that has been given a number and two teams is not a second
    // game beside the one it became.
    if(standIn && standIn.id !== id) delete keep[standIn.id];

    const div = String(r.division || '').match(/group\s+([A-Z])/i);
    // A bracket game keeps the division of whoever qualified for it, so the
    // first quarterfinal came back labelled group B. A playoff game belongs to
    // no group; only a game that is one takes the letter.
    const isGroup = known && (old ? old.round === 'group' : !!div);
    keep[id] = {id: id,
                group: isGroup ? ((old && old.group) || (div ? div[1].toUpperCase() : null)) : null,
                round: isGroup ? 'group' : 'playoff',
                // A slot labelled "QTR / CONSOL" gets a truer name once the
                // teams are in it -- "Consolation" -- so the capture's label
                // wins where it has one.
                label: known ? (r.label || (old ? old.label : null))
                             : (r.label || r.n || null),
                start: start || (old ? old.start : null),
                rink: rink || (old ? old.rink : null),
                home: either ? (vId || null) : null,
                away: either ? (hId || null) : null,
                homeScore: old ? old.homeScore : null,
                awayScore: old ? old.awayScore : null};
    if(known) applyStored(keep[id]);
  });

  const out = Object.keys(keep).map(function(k){ return keep[k]; });
  out.forEach(function(g){ applyStored(g); if(g.label == null) delete g.label; });
  return out.sort(function(a, b){
    return String(a.start).localeCompare(String(b.start))
        || String(a.rink).localeCompare(String(b.rink));
  });
}

function slotsAsGames(slots){
  const startOf = slotStart;

  // Two sheets can face off in the same minute -- three pairs did on this
  // Sunday -- so the time alone is not an identity. The rink's initials
  // separate them and stay readable in the file: P061110ICAT.
  const tag = function(rink){
    return String(rink || '').split(/[^A-Za-z]+/)
      .filter(Boolean).map(function(w){ return w[0].toUpperCase(); }).join('');
  };
  const taken = {};
  lastRaw.games.forEach(function(g){ taken[g.id] = true; });

  return slots.map(function(r){
    const start = startOf(r);
    const mine = lastRaw.games.filter(function(g){
      return g.start === start && (!g.rink || !r.rink || g.rink === r.rink)
             && !g.home && !g.away;
    })[0];
    let id = mine ? mine.id
           : (start ? 'P' + start.slice(8, 10) + start.slice(11, 13)
                          + start.slice(14, 16) + tag(r.rink)
                    : String(r.n));
    // Belt and braces: a rink named only in punctuation would tag as nothing.
    if(!mine){ let n = 2; while(taken[id]) id = id + '-' + (n++); }
    taken[id] = true;
    return {id: id, group: null, round: 'playoff',
            label: r.label || r.n || null,
            start: start, rink: r.rink || null,
            home: null, away: null, homeScore: null, awayScore: null};
  });
}

// A score typed or imported here lives in this browser and nowhere else, so
// the phone in your pocket cannot see it. Writing it into the game as well as
// the schedule makes one paste enough to publish the lot.
function applyStored(g){
  const e = manualAll()[g.id];
  if(!e || e.home == null || e.away == null) return;
  g.homeScore = e.home;
  g.awayScore = e.away;
  if(e.decision && e.decision !== 'REG') g.decision = e.decision;
  else delete g.decision;
}

// Scores held here that the file does not already carry.
function unpublished(){
  if(!lastRaw) return [];
  const m = manualAll();
  return lastRaw.games.filter(function(g){
    const e = m[g.id];
    if(!e || e.home == null || e.away == null) return false;
    return g.homeScore !== e.home || g.awayScore !== e.away
        || (g.decision || 'REG') !== (e.decision || 'REG');
  });
}

function corrections(){
  const m = manualAll();
  if(!lastRaw) return [];
  const byId = {}, names = {};
  lastRaw.games.forEach(function(g){ byId[g.id] = g; });
  lastRaw.teams.forEach(function(t){ names[t.id] = t.name; });
  return Object.keys(m).sort(function(a, b){ return Number(a) - Number(b); })
    .map(function(id){
      const g = byId[id] || {};
      return {id: id, home: names[g.home] || null, away: names[g.away] || null,
              homeScore: m[id].home, awayScore: m[id].away};
    });
}

// iOS will not select the contents of a readonly field, and focus() alone does
// nothing there, so the fallback used to leave a box of text with no way to
// take it. Unlocking the field and laying a range over it is what works on a
// phone; setSelectionRange covers everything else.
function selectAll(el){
  el.hidden = false;
  const wasReadOnly = el.readOnly;
  el.readOnly = false;
  el.contentEditable = 'true';
  try {
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  } catch(e){}
  el.contentEditable = 'false';
  el.readOnly = wasReadOnly;
  el.focus();
  try { el.setSelectionRange(0, String(el.value).length); } catch(e){}
}

function copyCorrections(){
  // Rebuild from everything imported this session, not from the file alone.
  if(FROM_CACHE){
    const note = el('sc-note');
    if(note) note.innerHTML = '<b>Not copied.</b> This page is showing its offline '
      + 'copy, because ' + eventFile() + ' could not be fetched. A list built from it '
      + 'would undo anything published since. Press <b>Refresh</b> first &mdash; '
      + 'scores you have entered are kept either way.';
    return;
  }
  const games = rebuildGames(SEEN_ROWS);
  const text = JSON.stringify(games, null, 1);
  const out = el('sc-out');
  const shown = function(msg){
    const note = el('sc-note');
    if(note) note.innerHTML = msg;
  };
  const fallback = function(){
    out.value = text;
    selectAll(out);
    shown('Clipboard blocked &mdash; it is selected in the box below. '
        + 'Long-press it, tap <b>Copy</b>, and send that.');
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(function(){
      out.hidden = true;
      const held = unpublished().length;
      shown('Copied all ' + games.length + ' games, ' + held + ' of them carrying a '
          + 'score this file does not have yet. Paste it into ' + eventFile()
          + ' as the whole <b>games</b> value, then commit, so every phone sees it.');
    }, fallback);
  } else {
    fallback();
  }
}

// Nothing scrapes any more -- the tournament site refuses an automated browser
// -- so the only thing worth saying beside Refresh is when scores last landed.
// Every entry carries the moment it was stored, whether it arrived by import or
// by hand, so the newest of those is the answer without anything extra kept.
// Nothing scrapes any more, so there is no run to report on. What a reader
// wants beside Refresh is how much of the tournament has been played and how
// old the answer is. Counting only this browser's own entries said "no scores
// entered yet" to everyone but the person who typed them, which was true and
// useless. Published results count too, because those are what the page is
// showing. Scores held here and not yet published get their own mention: on
// the phone in the stands they do not exist.
function drawImport(){
  const head = el('t-run');
  if(!head) return;
  if(!lastRaw){ head.innerHTML = '<span>waiting for the schedule</span>'; return; }

  const m = manualAll();
  let fixtures = 0, scored = 0;
  lastRaw.games.forEach(function(g){
    if(!g.home || !g.away) return;   // a bracket slot is not a fixture yet
    fixtures++;
    const e = m[g.id];
    if(g.homeScore != null || (e && e.home != null && e.away != null)) scored++;
  });

  const bits = [scored + ' of ' + fixtures + ' games scored'];
  if(FROM_CACHE) bits.push('<b>offline copy &mdash; refresh before publishing</b>');
  if(lastUpdated){
    bits.push('<span title="' + esc(stamp(lastUpdated, lastZone)) + '">updated '
            + esc(ago(lastUpdated) || 'at an unknown time') + '</span>');
  }
  const held = unpublished().length;
  if(held){
    bits.push('<b>' + held + ' not published yet</b>');
  }
  head.innerHTML = '<span>' + bits.join(' &middot; ') + '</span>';
}

let lastUpdated = '';
let lastZone = '';
let lastRaw = null;

function drawPicker(){
  const box = el('t-pick'), sel = el('t-event');
  if(!box || EVENTS.length < 2){ if(box) box.hidden = true; return; }
  box.hidden = false;
  sel.innerHTML = EVENTS.slice().sort(function(a, b){
      return String(b.start).localeCompare(String(a.start));
    }).map(function(e){
      return '<option value="' + esc(e.id) + '"'
           + (EVENT && e.id === EVENT.id ? ' selected' : '') + '>'
           + esc(e.name) + ' &middot; ' + esc(e.dates || e.start) + '</option>';
    }).join('');
}

// `pre` is a copy of the event file already in hand, so the boot sequence can
// look at one before deciding to show it without fetching it twice.
function showEvent(bust, pre){
  const doc = pre ? Promise.resolve(pre) : load(bust);
  return Promise.all([doc, loadAdjustment(bust)]).then(function(all){
    ADJ = all[1] || {};
    // Hotel wifi drops. The last good copy is kept so the page -- and the score
    // entry panel with it -- still works with no network at all.
    let data = all[0];
    if(data){ lsSet(lsKey(LS_CACHE), JSON.stringify(data)); FROM_CACHE = false; }
    else {
      try { data = JSON.parse(lsGet(lsKey(LS_CACHE)) || 'null'); } catch(e){ data = null; }
      FROM_CACHE = !!data;
    }
    lastRaw = data;
    SEEN_ROWS.length = 0;      // rows imported for one event mean nothing in another
    draw(withManual(data));
    buildPanel(data);
    drawImport();
    drawPicker();
    clampLong();
  });
}

loadIndex(false).then(function(list){
  const q = new URLSearchParams(location.search);
  const wanted = q.get('event');
  EVENT = chooseEvent(list, wanted);
  if(!EVENT || wanted || list.length < 2) return showEvent(false);
  // falls through to the schedule-published check below
  // The default is the next tournament -- unless its schedule has not been
  // published yet, in which case the last one played is what there is to look
  // at. Decided from the file rather than a flag in the index, so the two
  // cannot drift apart.
  return load(false).then(function(doc){
    if(hasSchedule(doc)) return showEvent(false, doc);
    const back = lastPlayed(list, EVENT.id);
    if(!back) return showEvent(false, doc);
    EVENT = back;
    return showEvent(false);
  });
}).then(applyTeamParam);

document.addEventListener('change', function(ev){
  if(!ev.target || ev.target.id !== 't-event') return;
  const picked = EVENTS.filter(function(e){ return e.id === ev.target.value; })[0];
  if(!picked || (EVENT && picked.id === EVENT.id)) return;
  EVENT = picked;
  // The address follows the choice, so a tournament can be linked to.
  const q = new URLSearchParams(location.search);
  q.set('event', picked.id);
  history.replaceState(null, '', location.pathname + '?' + q.toString());
  showEvent(true);
});

// One page of four sections was a long scroll on a phone, and the section you
// wanted was rarely the one on screen. Update comes last because it is only
// there for whoever has the key, so its absence cannot leave the strip without
// a first tab.
const TABS = [['tab-storm', 'p-storm'], ['tab-brackets', 'p-brackets'],
              ['tab-sched', 'p-sched'], ['tab-ask', 'p-ask'], ['tab-team', 'p-team'],
              ['tab-analysis', 'p-analysis'], ['tab-update', 'p-update']];

function showTab(want){
  TABS.forEach(function(pair){
    const on = pair[0] === want;
    const tab = el(pair[0]), panel = el(pair[1]);
    if(!tab || !panel) return;
    tab.setAttribute('aria-selected', on ? 'true' : 'false');
    panel.hidden = !on;
  });
  // A panel that was hidden has no layout, so nothing in it could be measured
  // for clamping until now.
  clampLong();
}

TABS.forEach(function(pair){
  const tab = el(pair[0]);
  if(tab) tab.addEventListener('click', function(){ showTab(pair[0]); });
});

// Three lines is enough to decide whether you want the rest. The button only
// appears where the text actually overflows, which has to be measured after
// the text is in place and its panel is visible.
function clampLong(){
  const all = document.querySelectorAll('.t-sub, .t-note, .sc-help');
  for(let i = 0; i < all.length; i++){
    const box = all[i];
    if(box.getAttribute('data-clamp')) continue;
    if(!box.offsetParent && box.offsetHeight === 0) continue;   // still hidden
    box.classList.add('clamp');
    if(box.scrollHeight <= box.clientHeight + 2){
      box.classList.remove('clamp');
      box.setAttribute('data-clamp', 'fits');
      continue;
    }
    const more = document.createElement('button');
    more.type = 'button';
    more.className = 'clamp-more';
    more.textContent = 'Show more';
    more.addEventListener('click', function(){
      const open = box.classList.toggle('open');
      more.textContent = open ? 'Show less' : 'Show more';
    });
    if(box.parentNode) box.parentNode.insertBefore(more, box.nextSibling);
    box.setAttribute('data-clamp', 'on');
  }
}

const refresh = el('t-refresh');
refresh.addEventListener('click', function(){
  refresh.disabled = true;
  refresh.textContent = 'Checking';
  el('t-said').textContent = '';
  Promise.all([load(true), loadAdjustment(true)]).then(function(both){
    refresh.disabled = false;
    refresh.textContent = 'Refresh';
    ADJ = both[1] || {};
    if(both[0] == null){
      drawImport();
      el('t-said').textContent = 'Could not reach ' + eventFile() + '. Try again in a moment.';
      return;
    }
    lsSet(lsKey(LS_CACHE), JSON.stringify(both[0]));
    FROM_CACHE = false;
    lastRaw = both[0];
    draw(withManual(both[0]));
    buildPanel(both[0]);
    drawImport();          // after draw(), which sets the zone the hover time uses
    clampLong();
    el('t-said').textContent = lastUpdated
      ? 'Reloaded \u2014 file updated ' + stamp(lastUpdated, lastZone)
      : 'Reloaded.';
  });
});

function draw(data){
  // Refresh calls this again on the same DOM, so every section starts hidden
  // and only comes back if the new data still fills it.
  ['t-empty', 't-body', 't-storm', 't-sec-diff', 't-sec-sched', 't-sec-stand']
    .forEach(function(id){ el(id).hidden = true; });
  AS_OF = {};

  const meta = (data && data.tournament) || {};
  const teams = (data && Array.isArray(data.teams)) ? data.teams : [];
  const games = (data && Array.isArray(data.games)) ? data.games : [];
  const rules = Object.assign({}, DEFAULT_RULES, (data && data.rules) || {});

  lastUpdated = meta.updated || '';
  lastZone = meta.timezone || '';
  el('t-name').textContent = meta.name || 'Tournament';
  el('t-dates').textContent = [meta.dates, meta.location].filter(Boolean).join(' \u00b7 ');

  const bits = [];
  if(meta.division) bits.push('<span>Division <b>' + esc(meta.division) + '</b></span>');
  if(meta.updated){
    bits.push('<span>Data as of <b>' + stamp(meta.updated, meta.timezone) + '</b></span>');
  }
  if(meta.source){
    bits.push('<span>Source <b><a href="' + esc(meta.source) + '" target="_blank"'
             + ' rel="noopener noreferrer">tournament site</a></b></span>');
  }
  el('t-meta').innerHTML = bits.join('');
  el('t-note').textContent = meta.note || '';

  if(!teams.length && !games.length){
    el('t-empty').hidden = false;
    return;
  }
  el('t-body').hidden = false;

  // How the field stood the night before the first faceoff. The seeds are that,
  // and so is the draw: which group was the hard one is a question about the
  // teams you were drawn against, not about what those teams did afterwards.
  const eve = eveOf(games);
  const EVE = (eve && ADJ_IN.ratings) ? adjustAsOf(eve) : null;
  assignSeeds(teams, EVE);

  const byId = {};
  teams.forEach(t => { byId[t.id] = t; });

  const groups = [];
  teams.concat(games).forEach(x => {
    if(x.group && groups.indexOf(x.group) < 0) groups.push(x.group);
  });
  groups.sort();

  // Positive favours the home side, by construction.
  function gap(g){
    const h = rating(byId[g.home]), a = rating(byId[g.away]);
    return (h == null || a == null) ? null : h - a;
  }

  const TIE_SHARE = tieShare(games, rules);

  function outcome(g){
    if(isPlayed(g)){
      return '<span class="t-score">' + g.homeScore + '&ndash;' + g.awayScore + '</span>';
    }
    if(!g.home && !g.away) return '<span class="muted">&mdash;</span>';
    const d = gap(g);
    if(d == null) return '<span class="muted">no rating</span>';
    const odds = winOdds(d, TIE_SHARE);
    if(Math.abs(d) < 0.05){
      return 'even <span class="t-wp">' + Math.round(odds.fav * 100) + '%</span>';
    }
    return esc((d > 0 ? byId[g.home] : byId[g.away]).name)
         + ' <span class="t-wp">' + Math.round(odds.fav * 100) + '%</span>';
  }

  // The predicted winner's name is already in the matchup beside it, so on a
  // phone that column spends its width repeating a name rather than adding one.
  // The differential says the same thing in five characters, read from the
  // first team named -- which is the one the matchup leads with.
  function brief(g){
    if(isPlayed(g)){
      return '<span class="t-score">' + g.homeScore + '&ndash;' + g.awayScore + '</span>';
    }
    const d = (!g.home && !g.away) ? null : gap(g);
    return d == null ? '<span class="muted">&mdash;</span>' : signed(d);
  }

  const storm = teams.filter(isStorm)[0];
  const odds = simulate(teams, games, byId, rules, groups,
                        storm ? storm.id : undefined);

  // Everything a team's own page needs, kept where a click can find it later.
  LAST = {teams: teams, games: games, byId: byId, gap: gap, odds: odds,
          rules: rules, groups: groups, groupCount: groups.length,
          scouting: (data && data.scouting) || {}};
  for(const k in ASK_ODDS) delete ASK_ODDS[k];   // a new score invalidates them

  drawStorm(teams, games, byId, gap, odds, rules, groups.length);
  drawDifficulty(groups, teams, EVE);
  drawSchedule(games, byId, gap, outcome, brief);
  drawStandings(groups, teams, games, byId, rules, odds);
  drawTeam();
  drawAnalysis(teams, games, byId);
}

// Live from the first result. A tournament half-played is worth watching, so
// long as the page says how far through it is: a team two games into five is
// mid-sentence, and the count is what tells you so.
function playedSoFar(games){
  let done = 0, total = 0;
  for(const g of games){
    if(!g.home || !g.away) continue;
    total++;
    if(g.homeScore != null) done++;
  }
  return {done: done, total: total};
}

// Before and after, on the North American list, because that is the one pool
// holding every team here. "Before" is the preseason projection, which is where
// each of them stood when nobody had played anybody.
// A game against a team MyHockeyRankings does not rate still happened, so it
// is counted; it just cannot move a rating, which the asterisk says.
function gpCell(r){
  if(!r.useless) return String(r.gp);
  return '<span title="' + r.useless + ' of these was against a team '
       + 'MyHockeyRankings does not rate, so it cannot move the rating">'
       + r.gp + '<span class="muted">*</span></span>';
}

function drawAnalysis(teams, games, byId){
  const sec = el('t-sec-analysis'), tab = el('tab-analysis');
  if(!sec) return;
  const count = playedSoFar(games);
  sec.hidden = !count.done;
  if(tab) tab.hidden = !count.done;
  if(!count.done) return;

  // Isolate this tournament: rank the list as it stood the day before it
  // started, then as it stands with its games in. Otherwise a tournament in
  // November would be credited with everything that happened in September.
  const days = games.map(function(g){ return String(g.start).slice(0, 10); })
                    .filter(Boolean).sort();
  const eve = eveOf(games);
  const last = (EVENT && EVENT.end) || days[days.length - 1];
  if(!eve || !last){ sec.hidden = true; if(tab) tab.hidden = true; return; }
  const wasMap = adjustAsOf(eve), nowMap = adjustAsOf(last);

  const pool = Object.keys(nowMap).filter(function(n){ return nowMap[n].na; });
  if(pool.length < 2){ sec.hidden = true; if(tab) tab.hidden = true; return; }
  const before = {}, after = {};
  pool.slice().sort(function(a, b){ return wasMap[b].adj - wasMap[a].adj; })
      .forEach(function(n, i){ before[n] = i + 1; });
  pool.slice().sort(function(a, b){ return nowMap[b].adj - nowMap[a].adj; })
      .forEach(function(n, i){ after[n] = i + 1; });

  // A team can be rated and still not be on the published list -- a summer-only
  // programme, say. It has no rank to move between, so it is named rather than
  // given a number the rankings page would not recognise.
  const offList = [];
  const rows = [];
  teams.forEach(function(t){
    const a = t.mhrName && nowMap[t.mhrName];
    if(!a) return;
    if(before[t.mhrName] == null || after[t.mhrName] == null){
      if(a.gp) offList.push(t.name);
      return;
    }
    const b = wasMap[t.mhrName];
    // Games played here, from the schedule. `a.gp - b.gp` counts what the
    // ledger could use instead, which drops a game against a team MHR does
    // not rate -- right for the rating, wrong for a column headed GP.
    let gp = 0, useless = 0;
    games.forEach(function(g){
      if(!isPlayed(g) || (g.home !== t.id && g.away !== t.id)) return;
      gp++;
      const foe = byId[g.home === t.id ? g.away : g.home];
      if(!foe || !foe.mhrName) useless++;
    });
    rows.push({name: t.name, id: t.id, gp: gp, useless: useless,
               was: before[t.mhrName], now: after[t.mhrName],
               move: before[t.mhrName] - after[t.mhrName],
               proj: b ? b.adj : a.proj, adj: a.adj});
  });
  if(!rows.length){ sec.hidden = true; if(tab) tab.hidden = true; return; }

  const up = rows.filter(function(r){ return r.gp && r.move > 0; }).length;
  const down = rows.filter(function(r){ return r.gp && r.move < 0; }).length;
  const biggest = rows.filter(function(r){ return r.gp; })
    .sort(function(a, b){ return Math.abs(b.move) - Math.abs(a.move); })[0];
  if(!biggest){ sec.hidden = true; if(tab) tab.hidden = true; return; }
  const played = rows.filter(function(r){ return r.gp; }).length;
  const whole = count.done === count.total;
  el('t-an-lede').innerHTML =
    '<b>' + count.done + ' of ' + count.total + '</b> games played'
    + (whole ? '. ' : ' so far. ')
    + played + ' of these teams have a result on record: <b>' + up
    + '</b> have climbed the USA 11U list, <b>' + down + '</b> have fallen, '
    + (played - up - down) + (played - up - down === 1 ? ' is' : ' are')
    + ' where they started. '
    + esc(biggest.name) + ' has moved furthest, ' + Math.abs(biggest.move)
    + ' places ' + (biggest.move > 0 ? 'up' : 'down') + '.'
    + (whole ? '' : ' Everything here moves again with the next result.');

  const card = function(title, list){
    return '<div class="anx"><h3>' + title + '</h3><ol class="anlist">'
      + list.map(function(r){
          return '<li' + (isStorm(r) ? ' class="hl"' : '') + '><span class="ann">'
               + esc(r.name) + '</span><span class="anm ' + (r.move > 0 ? 'up' : 'dn')
               + '">' + (r.move > 0 ? '▲ ' : '▼ ') + Math.abs(r.move)
               + '</span><span class="anr">' + r.was + ' &rarr; ' + r.now + '</span></li>';
        }).join('')
      + '</ol></div>';
  };
  const byMove = rows.filter(function(r){ return r.gp; })
                     .sort(function(a, b){ return b.move - a.move; });
  if(!byMove.length){ sec.hidden = true; if(tab) tab.hidden = true; return; }
  el('t-an-movers').innerHTML =
    '<div class="anwrap">'
    + card('Biggest risers', byMove.slice(0, 5))
    + card('Biggest fallers', byMove.slice(-5).reverse())
    + '</div>';

  el('t-an-table').innerHTML =
    '<table><thead><tr><th>Team</th><th class="num hide-sm">GP</th>'
    + '<th class="num">Before</th><th class="num">After</th><th class="num">Move</th>'
    + '<th class="num hide-sm">Rating</th></tr></thead><tbody>'
    + byMove.map(function(r){
        // Before, After and Move are what this tab is for; the games played and
        // the rating that moved ride under the name on a phone.
        return '<tr' + (isStorm(r) ? ' class="hl"' : '') + '><td class="team">'
          + esc(r.name) + '<span class="tsm">' + r.gp + ' game'
          + (r.gp === 1 ? '' : 's') + (r.useless ? ', ' + r.useless + ' unrated' : '')
          + ' &middot; ' + r.proj.toFixed(2)
          + ' &rarr; ' + r.adj.toFixed(2) + '</span>'
          + '</td><td class="num hide-sm">' + gpCell(r) + '</td><td class="num">'
          + r.was + '</td><td class="num">' + r.now + '</td><td class="num">'
          + mvCell(r.move) + '</td><td class="num hide-sm">' + r.proj.toFixed(2)
          + ' &rarr; ' + r.adj.toFixed(2) + '</td></tr>';
      }).join('')
    + '</tbody></table>';

  el('t-an-note').innerHTML =
    (offList.length
      ? '<b>' + esc(offList.join(', ')) + '</b> '
        + (offList.length === 1 ? 'is rated but is not' : 'are rated but are not')
        + ' on the USA 11U list, so ' + (offList.length === 1 ? 'it has' : 'they have')
        + ' no rank to move between and ' + (offList.length === 1 ? 'is' : 'are') + ' left out above. '
      : '')
    + 'A <b>*</b> beside the games played means one of them was against a team '
    + 'MyHockeyRankings does not rate. Those games are on the record but cannot '
    + 'move a rating, because an implied rating needs the opponent&rsquo;s '
    + 'rating to be implied from. '
    + 'Before is the list as it stood the day this tournament started, so a '
    + 'later tournament is not credited with an earlier one. After is the same '
    + 'list with these results in. Ranks are on MyHockeyRankings&rsquo; USA 11U list, '
    + 'counted over every team on it; a team MHR lists only at 12U has no rank there. '
    + 'That list is dense, so a place or two is noise &mdash; read the rating change '
    + 'alongside the move.';
}

function mvCell(d){
  if(!d) return '<span class="mv fl">&mdash;</span>';
  return '<span class="mv ' + (d > 0 ? 'up' : 'dn') + '">'
       + (d > 0 ? '▲ ' : '▼ ') + Math.abs(d) + '</span>';
}

let LAST = null;

function drawStorm(teams, games, byId, gap, odds, rules, groupCount){
  const storm = teams.filter(isStorm)[0];
  if(!storm) return;

  // Every game they are named in, in order: the list is a running tally of who
  // they have played, so a bracket game belongs in it as much as a group one.
  const mine = games.filter(g => g.home === storm.id || g.away === storm.id)
                    .sort((x, y) => String(x.start).localeCompare(String(y.start)));
  if(!mine.length) return;

  el('t-storm').hidden = false;
  el('t-storm-name').textContent = storm.name;

  // gap() is signed towards the home team; flip it when the Storm is away so
  // every number in this callout reads from the Storm's point of view.
  function ourGap(g){
    const d = gap(g);
    return d == null ? null : (g.home === storm.id ? d : -d);
  }

  const rated = mine.map(ourGap).filter(d => d != null);
  const wins = rated.filter(d => d > 0).length;
  const form = rated.length
    ? 'Favoured in ' + wins + ' of ' + rated.length + ' rated games.'
    : 'No opponent ratings yet, so no predicted results.';
  // The headline follows where the Storm can still realistically finish. Once
  // Gold is out of reach the number would be a permanent zero, which tells a
  // parent nothing; the goalposts move, and the label says so plainly.
  const tiers = tierList(odds, rules, groupCount);
  const noPlayoff = !tiers.length;
  let ti = 0;
  while(ti < tiers.length){
    const p = oddsPct(odds, storm.id, tiers[ti].key);
    if(p == null || p >= 1) break;
    ti++;
  }
  const tier = ti < tiers.length ? tiers[ti].key : 'cons';
  const tierName = ti < tiers.length ? tiers[ti].name : null;
  const headline = oddsText(odds, storm.id, tier);
  const runs = odds ? odds.runs.toLocaleString() : '';

  let tail = '';
  const leftover = rules && rules.leftover ? rules.leftover : 'the consolation bracket';
  const what = tierName ? 'a ' + tierName + ' berth' : leftover;
  if(headline === 'Clinched'){
    tail = ' The Jets take ' + what + ' in every one of ' + runs
         + ' simulations of the rest of the group stage.';
  } else if(headline != null){
    tail = ' Across ' + runs + ' simulations of the rest of the group stage, the Jets '
         + 'land ' + what + ' in ' + headline + ' of them.';
  }
  if(noPlayoff){
    tail = '';        // nothing to be in or out of
  } else if(ti > 0 && tierName){
    tail += ' <b>Out of ' + esc(andList(tiers.slice(0, ti).map(nameOf)))
          + ' contention</b> &mdash; the headline below is the ' + esc(tierName)
          + ' bracket now.';
  } else if(tier === 'cons'){
    // No headline figure to point at any more, so the sentence carries it.
    const gone = esc(andList(tiers.map(nameOf)));
    tail = headline === 'Clinched'
      ? ' <b>Out of ' + gone + ' contention</b> &mdash; the weekend finishes in '
        + leftover + '.'
      : tail + ' <b>Out of ' + gone + ' contention.</b>';
  }
  el('t-storm-line').innerHTML = form + tail;

  // The group schedule was known on day one, so there is nothing to predict
  // about it. A bracket game is different: it exists on the schedule long
  // before anyone qualifies for it. When no game on the schedule names the
  // Storm, the next one is a bracket game, and the seeding says who they would
  // meet. Worth a row only when one opponent is likelier than all the others
  // put together; below that there is no single answer to give.
  //
  // Only while a bracket slot is still waiting for its teams. A tournament with
  // no playoff, or one whose bracket has filled and been played, has no next
  // game to guess at -- the NIT's last Sunday put "next Washington Pride" under
  // a finished 4-0 weekend, because the seeding pairs teams whether or not
  // there is a bracket for the pairing to happen in.
  let next = null;
  const ahead = games.filter(function(g){
    return (g.home === storm.id || g.away === storm.id) && !isPlayed(g);
  });
  const slotsOpen = games.some(function(g){
    return !isPlayed(g) && (g.home == null || g.away == null);
  });
  if(odds && !noPlayoff && slotsOpen && !ahead.length && odds.oppRuns){
    let foe = null, hits = 0;
    for(const id in odds.opp){
      if(odds.opp[id] > hits){ hits = odds.opp[id]; foe = id; }
    }
    const share = hits / odds.oppRuns;
    if(foe && byId[foe] && share > 0.5){
      next = {team: byId[foe], share: share};
    }
  }

  let rows = gameRows(storm, mine, byId, gap);
  if(next){
    // Once the runs are unanimous the confidence has nothing left to say, so
    // the brackets go back to carrying the seed like every row above.
    const sure = next.share > 0.995;
    const d = rating(storm) == null || rating(next.team) == null
            ? null : rating(storm) - rating(next.team);
    rows += '<tr><td><span class="muted">next</span> '
          + label(next.team, next.team.id, true,
                  sure ? null : Math.round(next.share * 100) + '%')
          + '</td><td>' + (d == null ? '<span class="muted">&mdash;</span>' : signed(d))
          + '</td></tr>';
  }
  el('t-storm-games').innerHTML = rows;
  drawScout(storm, mine, next, games, byId);

  // [caption, value, small?]
  const figs = [];
  const small = function(t){
    figs.push([t.name, oddsLetter(oddsText(odds, storm.id, t.key)), true]);
  };
  if(noPlayoff){
    // no berths to report
  } else if(tier === 'cons'){
    // A placement game is simply what is left once every bracket is gone, so a
    // figure for it would repeat the E's beside it -- and the caption would be
    // twice the width of any other in the row, which is what broke it. The two
    // brackets nearest the exit are the ones worth still showing.
    tiers.slice(-2).forEach(small);
  } else if(headline != null){
    // "Clinched" in full ran into the Group figure beside it on a phone, so the
    // headline takes the same C / E the tables use, with the word on hover.
    figs.push([tierName + ' berth', oddsLetter(headline), false]);
    // The tiers that dropped away stay visible, small, so the reader can see
    // what the headline used to be. Two of them at most: the row has a group,
    // a seed and a rating to fit as well.
    tiers.slice(Math.max(0, ti - 2), ti).forEach(small);
  }
  if(storm.group) figs.push(['Group', esc(storm.group), false]);
  if(storm.seed != null) figs.push(['Seed', esc(storm.seed), false]);
  if(rating(storm) != null) figs.push(['Rating', rating(storm).toFixed(2), false]);
  el('t-storm-figs').innerHTML = figsHtml(figs);
}

// ------------------------------------------------------- scouting report --
// Once the Storm reach a playoff round, a link under their games opens a report
// on the next opponent: the game itself, the matchup on ratings, what that team
// did here and against whom, and -- when the event file carries one -- a short
// prioritised list written by hand under `scouting[teamId]`.
//
// Players appear by jersey number only, never by name: the owner's decision of
// 24 October, recorded in CLAUDE.md. Numbers and stats are public on GameSheet;
// names stay off this site.
//
// The opponent is always the one the tournament has named: on the Storm's next
// unplayed playoff game, or -- when the pairing is announced before its time
// and rink are -- `scouting.next` in the event file, entered by hand. Never the
// simulation's guess (the owner's call, 24 October). Nothing in the group
// stage.
let SCOUT_OPEN = false;

function drawScout(storm, mine, next, games, byId){
  const link = el('t-scout-link'), box = el('t-scout');
  if(!link || !box) return;
  link.hidden = true; box.hidden = true;

  const g = mine.filter(function(x){
    return !isPlayed(x) && x.round !== 'group' && x.home && x.away;
  }).sort(function(a, b){ return String(a.start).localeCompare(String(b.start)); })[0];
  let foe = g ? byId[g.home === storm.id ? g.away : g.home] : null;
  const named = LAST && LAST.scouting ? LAST.scouting.next : null;
  if(!foe && named && byId[named]) foe = byId[named];
  if(!foe) return;

  const nm = function(t){ return t ? esc(t.name) : '?'; };
  const r = function(t){ const v = rating(t); return v == null ? null : v; };

  // What a team did at this tournament, and how strong its opponents were.
  function record(t){
    let w = 0, l = 0, tie = 0, gf = 0, ga = 0, otw = 0, otl = 0;
    const opp = [], lines = [];
    games.forEach(function(x){
      if(!isPlayed(x) || (x.home !== t.id && x.away !== t.id)) return;
      const home = x.home === t.id, o = byId[home ? x.away : x.home];
      const us = home ? x.homeScore : x.awayScore, them = home ? x.awayScore : x.homeScore;
      const how = decisionOf(x);
      gf += us; ga += them;
      if(us === them) tie++;
      else if(us > them){ w++; if(how !== 'REG') otw++; }
      else { l++; if(how !== 'REG') otl++; }
      if(r(o) != null) opp.push(r(o));
      lines.push((us > them ? 'W' : us < them ? 'L' : 'T') + ' ' + us + '&ndash;' + them
        + (how !== 'REG' ? ' ' + how : '') + ' vs ' + nm(o)
        + (r(o) != null ? ' <span class="muted">(' + r(o).toFixed(2) + ')</span>' : ''));
    });
    const sos = opp.length ? opp.reduce(function(a, b){ return a + b; }, 0) / opp.length : null;
    return {w: w, l: l, t: tie, gf: gf, ga: ga, otw: otw, otl: otl, sos: sos, lines: lines,
            gp: lines.length};
  }
  const them = record(foe), us = record(storm);

  let h = '<h4>Scouting report: ' + nm(foe) + '</h4>';
  h += '<p class="muted">' + (g
    ? esc(g.label || 'Playoff') + ' &middot; ' + when(g.start).replace('<br>', ' ')
      + (g.rink ? ' &middot; ' + esc(g.rink) : '')
    : 'Time and rink not posted yet.') + '</p>';

  // Hand-written keys first: they are the point of the report.
  const notes = LAST && LAST.scouting ? LAST.scouting[foe.id] : null;
  if(notes && Array.isArray(notes.keys) && notes.keys.length){
    h += '<h5>Things to know</h5><ol>'
       + notes.keys.map(function(k){ return '<li>' + esc(k) + '</li>'; }).join('') + '</ol>';
    // Players by jersey number only -- never a name (see CLAUDE.md).
    if(Array.isArray(notes.players) && notes.players.length){
      h += '<h5>Who produces</h5><table class="t-mini"><tbody>'
         + '<tr><td class="muted">#</td><td class="muted">Pos</td><td class="num muted">G</td>'
         + '<td class="num muted">A</td><td class="num muted">Pts</td><td class="muted"></td></tr>'
         + notes.players.map(function(p){
             return '<tr><td><b>' + esc(p.no) + '</b></td><td>' + esc(p.pos || '') + '</td><td class="num">'
               + esc(p.g) + '</td><td class="num">' + esc(p.a) + '</td><td class="num">' + esc(p.pts)
               + '</td><td class="muted">' + esc(p.note || '') + '</td></tr>';
           }).join('') + '</tbody></table>';
    }
    if(Array.isArray(notes.goalies) && notes.goalies.length){
      h += '<h5>Goalies</h5><table class="t-mini"><tbody>'
         + '<tr><td class="muted">#</td><td class="num muted">GP</td><td class="num muted">Shots</td>'
         + '<td class="num muted">GA</td><td class="num muted">Sv%</td><td class="muted"></td></tr>'
         + notes.goalies.map(function(p){
             return '<tr><td><b>' + esc(p.no) + '</b></td><td class="num">' + esc(p.gp) + '</td><td class="num">'
               + esc(p.sa) + '</td><td class="num">' + esc(p.ga) + '</td><td class="num">' + esc(p.svp)
               + '</td><td class="muted">' + esc(p.note || '') + '</td></tr>';
           }).join('') + '</tbody></table>';
    }
    if(notes.asOf || notes.source){
      h += '<p class="muted">' + [notes.asOf ? 'As of ' + esc(notes.asOf) : '',
                                  notes.source ? esc(notes.source) : ''].filter(Boolean).join(' &middot; ') + '</p>';
    }
  }

  // The matchup on ratings. A playoff game ends with a winner, so no tie share.
  const rs = r(storm), rf = r(foe);
  if(rs != null && rf != null){
    const d = rs - rf, o = winOdds(d, 0);
    h += '<h5>The matchup</h5><p>' + nm(storm) + ' ' + rs.toFixed(2) + ', ' + nm(foe) + ' '
       + rf.toFixed(2) + '. ' + (Math.abs(d) < 0.05 ? 'Even on paper'
         : (d > 0 ? nm(storm) : nm(foe)) + ' by ' + Math.abs(d).toFixed(2) + ' goals')
       + '; the Jets win about <b>' + Math.round((d >= 0 ? o.fav : o.dog) * 100) + '%</b> of the time.</p>';
  }

  // Their tournament, set against the Storm's.
  if(them.gp){
    const rec = function(x){ return x.w + '-' + x.l + '-' + x.t + (x.otw || x.otl ? ' <span class="muted">(' + (x.otw + x.otl) + ' after regulation)</span>' : ''); };
    h += '<h5>At this tournament</h5><p>' + nm(foe) + ' ' + rec(them) + ', goals '
       + them.gf + '&ndash;' + them.ga + ' (' + (them.gf / them.gp).toFixed(1) + ' for and '
       + (them.ga / them.gp).toFixed(1) + ' against a game).</p><ol>'
       + them.lines.map(function(x){ return '<li>' + x + '</li>'; }).join('') + '</ol>';
    if(them.sos != null && us.sos != null){
      const diff = us.sos - them.sos;
      h += '<p>Their opponents averaged <b>' + them.sos.toFixed(2) + '</b>; the Jets&rsquo; averaged <b>'
         + us.sos.toFixed(2) + '</b>. '
         + (Math.abs(diff) < 0.25 ? 'Both have faced about the same strength.'
            : (diff > 0 ? 'The Jets have faced the stronger field, by ' : nm(foe) + ' have faced the stronger field, by ')
              + Math.abs(diff).toFixed(2) + ' goals a game &mdash; weigh their goal record with that in mind.')
         + '</p>';
    }
  }

  box.innerHTML = h;
  link.innerHTML = '<a href="#t-scout" id="t-scout-toggle">' + (SCOUT_OPEN ? 'Hide' : 'Scouting report:')
    + ' ' + nm(foe) + (SCOUT_OPEN ? '' : ' &rarr;') + '</a>';
  link.hidden = false;
  box.hidden = !SCOUT_OPEN;
  el('t-scout-toggle').addEventListener('click', function(ev){
    ev.preventDefault();
    SCOUT_OPEN = !SCOUT_OPEN;
    drawScout(storm, mine, next, games, byId);
  });
}

// One row per game: who, and either the score or what the ratings expect. The
// `vs`/`at` and the sign are both read from this team's side.
function gameRows(team, mine, byId, gap){
  let rows = '';
  for(const g of mine){
    const home = g.home === team.id;
    const opp = byId[home ? g.away : g.home];
    const d = gap(g);
    const ours = d == null ? null : (home ? d : -d);
    let right;
    if(isPlayed(g)){
      const us = home ? g.homeScore : g.awayScore;
      const them = home ? g.awayScore : g.homeScore;
      right = '<span class="t-score">' + us + '&ndash;' + them + '</span>';
    } else {
      right = ours == null ? '<span class="muted">&mdash;</span>' : signed(ours);
    }
    rows += '<tr><td>' + (home ? 'vs ' : 'at ')
          + label(opp, home ? g.away : g.home, true)
          + '</td><td>' + right + '</td></tr>';
  }
  return rows;
}

function figsHtml(figs){
  return figs.map(function(f){
    const v = (f[1] && f[1].n !== undefined) ? f[1] : {n: f[1], title: null};
    return '<div class="fig' + (f[2] ? ' sm' : '') + '"><div class="n"'
         + (v.title ? ' title="' + esc(v.title) + '"' : '') + '>' + v.n
         + '</div><div class="c">' + f[0] + '</div></div>';
  }).join('');
}


// ------------------------------------------------------------- a team's page --
// Whoever you clicked, rendered the way the Storm's own panel is. No narrative:
// the Storm tab argues about what is still reachable, and sixty-four copies of
// that argument would be noise. This states the record and shows the games.
let PICKED_TEAM = null;

// ------------------------------------------------------------------- ask ----
// A question box with no model behind it. Every answer here is computed from
// the same 10,000 runs the brackets tab already shows, so the numbers are the
// page's own and cannot drift from it. It understands a fixed set of questions
// and says so plainly when it does not, which is the trade: it will never
// invent a number, and it will never surprise you with one either.
const ASK_ODDS = {};

function askOdds(focusId){
  if(!focusId || !LAST) return LAST && LAST.odds;
  if(LAST.odds && focusId === LAST.odds.focus) return LAST.odds;
  if(!ASK_ODDS[focusId]){
    ASK_ODDS[focusId] = simulate(LAST.teams, LAST.games, LAST.byId, LAST.rules,
                                 LAST.groups, focusId);
  }
  return ASK_ODDS[focusId];
}

// The longest team name mentioned wins, so "North York Storm" is not read as
// the Storm and "Team Illinois" is not read as a stray "team".
function askTeam(q){
  let best = null;
  for(const t of LAST.teams){
    const n = t.name.toLowerCase();
    if(q.indexOf(n) >= 0 && (!best || n.length > best.name.length)) best = t;
  }
  if(best) return best;
  if(/\b(we|us|our|ours|jets)\b/.test(q)) return LAST.teams.filter(isStorm)[0];
  return null;
}

function askTeams(q){
  const found = [];
  for(const t of LAST.teams){
    if(q.indexOf(t.name.toLowerCase()) >= 0) found.push(t);
  }
  // Drop a name wholly inside a longer one that also matched.
  return found.filter(function(t){
    return !found.some(function(o){
      return o !== t && o.name.toLowerCase().indexOf(t.name.toLowerCase()) >= 0;
    });
  });
}

function askTier(q){
  const tiers = tierList(LAST.odds, LAST.rules, LAST.groupCount);
  return tiers.filter(function(t){ return q.indexOf(t.name.toLowerCase()) >= 0; })[0];
}

function pct(v){ return v == null ? '&mdash;' : (v < 0.5 && v > 0 ? '<1' : Math.round(v)) + '%'; }

function askRow(cells){
  return '<tr>' + cells.map(function(c, i){
    return '<td' + (i ? ' class="num"' : '') + '>' + c + '</td>';
  }).join('') + '</tr>';
}

function askTable(rows){
  return '<table class="t-mini"><tbody>' + rows.join('') + '</tbody></table>';
}

// ---- the answers ------------------------------------------------------------
function ansBest(tier){
  const odds = LAST.odds;
  const list = Object.keys(odds[tier.key] || {})
    .map(function(id){ return [id, odds[tier.key][id] / odds.runs * 100]; })
    .filter(function(x){ return x[1] > 0; })
    .sort(function(a, b){ return b[1] - a[1]; }).slice(0, 6);
  if(!list.length) return 'Nobody has a live chance of ' + esc(tier.name) + ' yet.';
  return '<p>Best chance of <b>' + esc(tier.name) + '</b>, across '
    + LAST.odds.runs.toLocaleString() + ' simulations:</p>'
    + askTable(list.map(function(x){
        return askRow([label(LAST.byId[x[0]], x[0], true), pct(x[1])]);
      }));
}

function ansChances(team){
  const tiers = tierList(LAST.odds, LAST.rules, LAST.groupCount);
  const rows = tiers.map(function(t){
    return askRow([esc(t.name), pct(oddsPct(LAST.odds, team.id, t.key))]);
  });
  rows.push(askRow(['<span class="muted">'
    + esc(LAST.rules.leftoverShort || 'Consolation') + '</span>',
    pct(oddsPct(LAST.odds, team.id, 'cons'))]));
  return '<p><b>' + esc(team.name) + '</b> from here:</p>' + askTable(rows);
}

// "Who do we need to win?" -- their own games first, because those are
// decisive, then the outside results that move it most.
function ansNeed(team, tier){
  const odds = askOdds(team.id);
  if(!odds || !odds.swing) return 'No games left to simulate.';
  const key = (tier || tierList(odds, LAST.rules, LAST.groupCount)
    .filter(function(t){ return (oddsPct(odds, team.id, t.key) || 0) >= 1; })[0]
    || {key: 'cons', name: LAST.rules.leftoverShort || 'Consolation'});
  const base = (odds[key.key] || {})[team.id] / odds.runs * 100;

  const nm = function(id){ return LAST.byId[id] ? LAST.byId[id].name : id; };
  const rows = odds.swing.map(function(s){
    const ways = s.ways.map(function(w){
      return {label: w.o === 0 ? nm(s.home) : w.o === 1 ? nm(s.away) : 'a tie',
              win: w.o !== 2, p: (w.odds[key.key] || 0) * 100};
    });
    const hi = Math.max.apply(null, ways.map(function(w){ return w.p; }));
    const lo = Math.min.apply(null, ways.map(function(w){ return w.p; }));
    return {s: s, ways: ways, swing: hi - lo,
            own: s.home === team.id || s.away === team.id};
  }).sort(function(a, b){ return b.swing - a.swing; });

  const mine = rows.filter(function(r){ return r.own; });
  const others = rows.filter(function(r){ return !r.own; }).slice(0, 3);
  let h = '<p><b>' + esc(team.name) + '</b> reach <b>' + esc(key.name)
        + '</b> in ' + pct(base) + ' of runs. What moves that:</p>';

  if(mine.length){
    h += askTable(mine.map(function(r){
      const best = r.ways.slice().sort(function(a, b){ return b.p - a.p; })[0];
      const rest = r.ways.filter(function(w){ return w !== best; });
      const worst = Math.max.apply(null, rest.map(function(w){ return w.p; }));
      const opp = nm(r.s.home === team.id ? r.s.away : r.s.home);
      return askRow(['<b>' + (best.win && best.label === team.name
                              ? 'win' : 'do not lose')
        + '</b> <span class="muted">vs ' + esc(opp) + '</span>',
        pct(best.p) + ' <span class="muted">/ ' + pct(worst) + '</span>']);
    }));
  }
  if(others.length){
    h += '<p class="t-sub">Then the outside results that matter most. The '
       + 'second figure is the best of the other ways that game can go.</p>'
       + askTable(others.map(function(r){
      const best = r.ways.slice().sort(function(a, b){ return b.p - a.p; })[0];
      const rest = r.ways.filter(function(w){ return w !== best; });
      const worst = Math.max.apply(null, rest.map(function(w){ return w.p; }));
      const other = best.label === nm(r.s.home) ? nm(r.s.away) : nm(r.s.home);
      return askRow([best.win
          ? '<b>' + esc(best.label) + '</b> <span class="muted">beat '
            + esc(other) + '</span>'
          : '<b>a tie</b> <span class="muted">in ' + esc(nm(r.s.away)) + ' at '
            + esc(nm(r.s.home)) + '</span>',
        pct(best.p) + ' <span class="muted">/ ' + pct(worst) + '</span>']);
    }));
  }
  return h;
}

function ansBiggestGame(team){
  const odds = askOdds(team.id);
  if(!odds || !odds.swing || !odds.swing.length) return 'No games left.';
  const tiers = tierList(odds, LAST.rules, LAST.groupCount);
  const key = tiers.filter(function(t){
    return (oddsPct(odds, team.id, t.key) || 0) >= 1; })[0] || tiers[tiers.length - 1];
  const nm = function(id){ return LAST.byId[id] ? LAST.byId[id].name : id; };
  let top = null;
  odds.swing.forEach(function(s){
    if(s.home === team.id || s.away === team.id) return;
    const ps = s.ways.map(function(w){ return (w.odds[key.key] || 0) * 100; });
    const sw = Math.max.apply(null, ps) - Math.min.apply(null, ps);
    if(!top || sw > top.sw) top = {s: s, sw: sw, ways: s.ways};
  });
  if(!top) return 'Only their own games are left.';
  const best = top.ways.slice().sort(function(a, b){
    return (b.odds[key.key] || 0) - (a.odds[key.key] || 0); })[0];
  const who = best.o === 0 ? nm(top.s.home) : best.o === 1 ? nm(top.s.away) : 'a tie';
  return '<p>Other than their own games, the one that moves <b>' + esc(team.name)
    + '</b>&rsquo;s ' + esc(key.name) + ' chance most is <b>'
    + esc(nm(top.s.away)) + ' at ' + esc(nm(top.s.home)) + '</b>, worth '
    + Math.round(top.sw) + ' points of probability. Best case is <b>' + esc(who)
    + '</b>.</p>' + askTable(top.ways.slice().sort(function(a, b){
        return (b.odds[key.key] || 0) - (a.odds[key.key] || 0); }).map(function(w){
      const lab = w.o === 0 ? nm(top.s.home) + ' win'
                : w.o === 1 ? nm(top.s.away) + ' win' : 'tie';
      return askRow([esc(lab), pct((w.odds[key.key] || 0) * 100)]);
    }));
}

function ansNext(team){
  const next = LAST.games.filter(function(g){
    return (g.home === team.id || g.away === team.id) && !isPlayed(g);
  }).sort(function(a, b){ return String(a.start).localeCompare(String(b.start)); })[0];
  if(!next) return '<b>' + esc(team.name) + '</b> have finished their games.';
  const home = next.home === team.id;
  const opp = LAST.byId[home ? next.away : next.home];
  const d = LAST.gap(next);
  const ours = d == null ? null : (home ? d : -d);
  return '<p><b>' + esc(team.name) + '</b> play <b>'
    + (opp ? label(opp, opp.id, true) : 'a team not yet known') + '</b> '
    + (home ? 'at home' : 'away') + ', '
    + esc(String(when(next.start)).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim())
    + (next.rink ? ', ' + esc(next.rink) : '') + '. '
    + (ours == null ? 'No prediction: the opponent is not rated.'
       : 'The ratings make that ' + (ours >= 0 ? 'theirs by ' : 'against them by ')
         + Math.abs(ours).toFixed(1) + ' goals.') + '</p>';
}

function ansHead(a, b){
  const ra = rating(a), rb = rating(b);
  if(ra == null || rb == null){
    return 'One of those two has no rating, so there is nothing to compare.';
  }
  const d = ra - rb;
  const met = LAST.games.filter(function(g){
    return isPlayed(g) && ((g.home === a.id && g.away === b.id)
                        || (g.home === b.id && g.away === a.id));
  });
  let h = '<p>' + esc(a.name) + ' ' + ra.toFixed(2) + ', ' + esc(b.name) + ' '
        + rb.toFixed(2) + '. The ratings favour <b>'
        + esc(Math.abs(d) < 0.05 ? 'neither' : (d > 0 ? a.name : b.name)) + '</b>'
        + (Math.abs(d) < 0.05 ? '.' : ' by ' + Math.abs(d).toFixed(1) + ' goals.') + '</p>';
  if(met.length){
    h += askTable(met.map(function(g){
      return askRow([esc(dayLabel(g.start)),
        esc(LAST.byId[g.away].name) + ' ' + g.awayScore + '&ndash;' + g.homeScore
        + ' ' + esc(LAST.byId[g.home].name)]);
    }));
  }
  return h;
}

function ansTough(){
  const groups = LAST.groups.map(function(gid){
    const inG = LAST.teams.filter(function(t){ return t.group === gid; });
    const rated = inG.filter(function(t){ return rating(t) != null; });
    const mean = rated.length ? rated.reduce(function(s, t){
      return s + rating(t); }, 0) / rated.length : null;
    return [gid, mean];
  }).filter(function(x){ return x[1] != null; })
    .sort(function(a, b){ return b[1] - a[1]; });
  return '<p>Groups by the mean rating of the teams in them, hardest first:</p>'
    + askTable(groups.map(function(x){
        return askRow([esc(x[0]), x[1].toFixed(2)]); }));
}

function ansUpset(){
  const done = LAST.games.filter(isPlayed).map(function(g){
    const d = LAST.gap(g);
    if(d == null) return null;
    const actual = g.homeScore - g.awayScore;
    return {g: g, miss: Math.abs(actual - d), d: d, actual: actual};
  }).filter(Boolean).sort(function(a, b){ return b.miss - a.miss; }).slice(0, 5);
  if(!done.length) return 'No rated games have been played yet.';
  return '<p>Where the ratings were furthest out, worst first:</p>'
    + askTable(done.map(function(x){
        return askRow([esc(LAST.byId[x.g.away].name) + ' ' + x.g.awayScore
          + '&ndash;' + x.g.homeScore + ' ' + esc(LAST.byId[x.g.home].name),
          'off by ' + x.miss.toFixed(1)]);
      }));
}

const ASK_HELP =
  '<p>It answers from the tournament&rsquo;s own numbers, so it only knows a '
  + 'fixed set of questions. These all work:</p><ul class="ask-eg">'
  + ['Who has the best chance of Bronze?',
     'What are the Jets&rsquo; chances?',
     'Who do we need to win?',
     'What game is our best chance?',
     'Who do the Jets play next?',
     'Chicago Mission v Oakville Hornets',
     'Which group is toughest?',
     'Biggest upset so far?'].map(function(q){
       return '<li><span class="ask-q">' + q + '</span></li>'; }).join('')
  + '</ul>';

function askAnswer(raw){
  if(!LAST) return 'Nothing loaded yet.';
  const q = ' ' + String(raw || '').toLowerCase().replace(/[?.!,]/g, ' ') + ' ';
  const team = askTeam(q);
  const tier = askTier(q);
  const pair = askTeams(q);

  if(/\b(help|what can|examples?)\b/.test(q)) return ASK_HELP;
  if(/\b(need|root|rooting|depend|help us|hoping)\b/.test(q)){
    return ansNeed(team || LAST.teams.filter(isStorm)[0], tier);
  }
  if(/\b(best|biggest|most important|matters most)\b/.test(q)
     && /\b(game|match|result)\b/.test(q)){
    return ansBiggestGame(team || LAST.teams.filter(isStorm)[0]);
  }
  if(/\bnext\b/.test(q) && team) return ansNext(team);
  if(/\b(tough|hard|strong|difficult)/.test(q) && /\b(group|pool)s?\b/.test(q)){
    return ansTough();
  }
  if(/\b(upset|surprise|wrong|off)\b/.test(q)) return ansUpset();
  if(pair.length >= 2) return ansHead(pair[0], pair[1]);
  if(tier && /\b(who|best|highest|most likely|favourite|favorite)\b/.test(q)){
    return ansBest(tier);
  }
  if(team && /\b(chance|chances|odds|make|makes|making|finish|doing)\b/.test(q)){
    return ansChances(team);
  }
  // A bare team name is a fair way to ask about that team. A sentence that
  // merely mentions one is not, and answering it anyway would be the confident
  // non-answer this box exists to avoid.
  if(team && q.split(team.name.toLowerCase()).join(' ')
              .replace(/[^a-z]/g, '').length < 4){
    return ansChances(team);
  }
  if(tier) return ansBest(tier);
  return '<p>That one it cannot answer.</p>' + ASK_HELP;
}

function askRun(text){
  const box = el('t-ask-out');
  if(!box) return;
  const q = String(text || '').trim();
  if(!q){ box.innerHTML = ASK_HELP; return; }
  el('t-ask-in').value = q;
  box.innerHTML = '<p class="muted">Working&hellip;</p>';
  // The re-run for a team other than the Storm takes about half a second, so
  // let the "working" line paint before it blocks.
  setTimeout(function(){
    let out;
    try { out = askAnswer(q); }
    catch(e){ out = '<p>That one broke it. ' + esc(String(e.message || e)) + '</p>'; }
    box.innerHTML = out;
  }, 20);
}

document.addEventListener('click', function(ev){
  if(ev.target && ev.target.id === 't-ask-go') askRun(el('t-ask-in').value);
  const eg = ev.target && ev.target.closest ? ev.target.closest('.ask-q') : null;
  if(eg) askRun(eg.textContent);
});
document.addEventListener('keydown', function(ev){
  if(ev.key === 'Enter' && ev.target && ev.target.id === 't-ask-in'){
    ev.preventDefault();
    askRun(ev.target.value);
  }
});

function drawTeam(){
  const tab = el('tab-team');
  const data = LAST;
  if(!PICKED_TEAM || !data){ if(tab) tab.hidden = true; return; }
  const t = (data.byId || {})[PICKED_TEAM];
  if(!t){ if(tab) tab.hidden = true; return; }

  const mine = data.games.filter(function(g){
    return g.home === t.id || g.away === t.id;
  }).sort(function(x, y){ return String(x.start).localeCompare(String(y.start)); });

  if(tab){
    tab.hidden = false;
    // The tab says whose page it is, so a reader who came back to it later
    // does not have to open it to find out.
    tab.textContent = t.name.length > 18 ? t.name.slice(0, 17) + '\u2026' : t.name;
  }
  el('t-tm-name').innerHTML = esc(t.name) + tagFor(t)
    + (t.basis === 'unranked' ? '<span class="unrk">unranked</span>' : '');

  const pts = scoring(data.rules);
  let w = 0, l = 0, tie = 0, gf = 0, ga = 0, points = 0;
  mine.forEach(function(g){
    if(!isPlayed(g)) return;
    const home = g.home === t.id;
    const us = home ? g.homeScore : g.awayScore;
    const them = home ? g.awayScore : g.homeScore;
    gf += us; ga += them;
    const how = decisionOf(g);
    if(us > them){
      w++; points += how === 'SO' ? pts.soWin : how === 'OT' ? pts.otWin : pts.reg;
    } else if(us < them){
      l++; points += how === 'SO' ? pts.soLoss : how === 'OT' ? pts.otLoss : pts.loss;
    } else { tie++; points += pts.soLoss; }
  });

  const played = w + l + tie;
  const bits = [];
  if(played){
    bits.push('<b>' + w + '&ndash;' + l + (tie ? '&ndash;' + tie : '') + '</b> so far, '
      + gf + ' for and ' + ga + ' against, ' + points
      + (points === 1 ? ' point.' : ' points.'));
  } else {
    bits.push('No games played yet.');
  }
  const left = mine.filter(function(g){ return !isPlayed(g); }).length;
  if(left) bits.push(left + (left === 1 ? ' game' : ' games') + ' still to come.');
  el('t-tm-line').innerHTML = bits.join(' ');
  el('t-tm-games').innerHTML = gameRows(t, mine, data.byId, data.gap);

  const tiers = tierList(data.odds, data.rules, data.groupCount);
  const figs = [];
  const best = tiers.filter(function(x){
    const v = oddsPct(data.odds, t.id, x.key);
    return v != null && v >= 1;
  })[0];
  if(best){
    // The same C / E as the Storm card and the tables: the full word overran
    // the Group figure on a phone.
    figs.push([best.name + ' berth', oddsLetter(oddsText(data.odds, t.id, best.key)), false]);
  } else if(data.odds){
    figs.push([(data.rules.leftoverShort || 'Cons'), '&ndash;', true]);
  }
  if(t.group) figs.push(['Group', esc(t.group), false]);
  if(t.seed != null) figs.push(['Seed', esc(t.seed), false]);
  if(rating(t) != null) figs.push(['Rating', rating(t).toFixed(2), false]);
  el('t-tm-figs').innerHTML = figsHtml(figs);

  el('t-tm-note').innerHTML = 'Seeded on where this team stood the day the '
    + 'tournament began. <b>vs</b> is at home and <b>at</b> is away, as the '
    + 'tournament lists them; the number on the right is the score once a game '
    + 'is played, and before that the goal difference the two ratings imply.';
}

// The address carries the choice, so a team's page can be sent to someone.
// Applied once the first draw has the teams to look the id up in.
function applyTeamParam(){
  const want = new URLSearchParams(location.search).get('team');
  if(want) showTeam(want);
}

function showTeam(id){
  PICKED_TEAM = id;
  drawTeam();
  if(!el('tab-team').hidden) showTab('tab-team');
  const q = new URLSearchParams(location.search);
  q.set('team', id);
  history.replaceState(null, '', location.pathname + '?' + q.toString());
}

// One listener for every name on the page, however the panel was redrawn.
document.addEventListener('click', function(ev){
  const hit = ev.target.closest ? ev.target.closest('.tl') : null;
  if(hit && hit.getAttribute('data-t')) showTeam(hit.getAttribute('data-t'));
});
document.addEventListener('keydown', function(ev){
  if(ev.key !== 'Enter' && ev.key !== ' ') return;
  const hit = ev.target.closest ? ev.target.closest('.tl') : null;
  if(hit && hit.getAttribute('data-t')){
    ev.preventDefault();
    showTeam(hit.getAttribute('data-t'));
  }
});

// Measured on the eve of the tournament, not today. A group's mean rating is
// how hard the draw was, and reading it off ratings this tournament has since
// moved makes it circular -- Labor Day had group A's toughest team listed as
// the side that won it rather than the side seeded to, beside a seed from the
// other answer.
function drawDifficulty(groups, teams, asOf){
  const at = t => rateWith(t, asOf);
  const rows = groups.map(gid => {
    const inGroup = teams.filter(t => t.group === gid);
    const rated = inGroup.filter(t => at(t) != null);
    const mean = rated.length
      ? rated.reduce((sum, t) => sum + at(t), 0) / rated.length : null;
    const top = rated.slice().sort((a, b) => at(b) - at(a))[0];
    return {gid: gid, n: inGroup.length, unranked: inGroup.length - rated.length,
            mean: mean, top: top};
  }).sort((a, b) => (b.mean == null ? -Infinity : b.mean)
                  - (a.mean == null ? -Infinity : a.mean));

  if(!rows.length) return;
  el('t-sec-diff').hidden = false;

  let h = '<table><thead><tr><th>Group</th><th class="num hide-sm">Teams</th>'
        + '<th class="num"><span class="lgo">Mean rating</span>'
        +   '<span class="ism">Rating</span></th>'
        + '<th>Toughest team</th></tr></thead><tbody>';
  for(const r of rows){
    const hasStorm = teams.some(t => t.group === r.gid && isStorm(t));
    h += '<tr' + (hasStorm ? ' class="hl"' : '') + '>'
      + '<td class="rk">' + esc(r.gid)
      +   '<span class="tsm">' + r.n + ' teams'
      +     (r.unranked ? ', ' + r.unranked + ' unranked' : '') + '</span></td>'
      + '<td class="num hide-sm">' + r.n + (r.unranked ? ' <span class="muted">('
        + r.unranked + ' unranked)</span>' : '') + '</td>'
      + '<td class="proj num">' + (r.mean == null ? '&mdash;' : r.mean.toFixed(2)) + '</td>'
      + '<td class="team">' + (r.top ? label(r.top, r.top.id, true) + tagFor(r.top)
                                      : '<span class="muted">&mdash;</span>')
      + '</td></tr>';
  }
  el('t-difficulty').innerHTML = h + '</tbody></table>';
}

// Which teams the schedule is narrowed to. Empty means everyone, which is the
// only state that shows the bracket games nobody has qualified for yet.
const PICKED = {};

function pickedCount(){
  let n = 0;
  for(const k in PICKED){ if(PICKED[k]) n++; }
  return n;
}

// Every team is a toggle. The search box decides which toggles are on screen,
// not which teams exist, so a chosen team never disappears behind a query --
// and seventy of them stay usable without a dropdown to scroll through.
let FILTER_WIRED = false;
let FILTER_OPEN = false;

function drawFilter(games, byId){
  const box = el('t-filter');
  if(!box) return;
  const seen = {};
  games.forEach(function(g){
    if(g.home) seen[g.home] = true;
    if(g.away) seen[g.away] = true;
  });
  const byName = function(a, b){
    return String((byId[a] || {}).name).localeCompare(String((byId[b] || {}).name));
  };
  const ids = Object.keys(seen).sort(byName);
  if(ids.length < 2){ box.hidden = true; return; }
  box.hidden = false;

  const chip = function(id, chosen){
    return '<button type="button" class="sfil-t" data-team="' + esc(id) + '"'
         + (chosen ? ' title="Tap anywhere on this to remove it"' : '')
         + ' aria-pressed="' + (chosen ? 'true' : 'false') + '">'
         + esc((byId[id] || {}).name || id)
         + (chosen ? '<span class="sfil-x" aria-hidden="true">&times;</span>' : '')
         + '</button>';
  };

  // The chosen ones sit above the box and stay put; the list below is only
  // there while you are choosing.
  el('t-filter-picked').innerHTML = ids.filter(function(id){ return PICKED[id]; })
    .map(function(id){ return chip(id, true); }).join('');

  const list = el('t-filter-list');
  list.hidden = !FILTER_OPEN;
  if(!FILTER_OPEN) list.innerHTML = '';
  if(FILTER_OPEN){
    const q = normName(el('t-filter-q').value || '');
    const shown = ids.filter(function(id){
      return !q || normName((byId[id] || {}).name).indexOf(q) >= 0;
    });
    list.innerHTML = shown.length
      ? shown.map(function(id){ return chip(id, !!PICKED[id]); }).join('')
      : '<p class="sfil-none">No team by that name.</p>';
  }

  if(FILTER_WIRED) return;
  FILTER_WIRED = true;

  const redraw = function(){ if(lastRaw) draw(withManual(lastRaw)); };

  // An empty box with nothing chosen is a filter doing nothing, and the list
  // under it is clutter. True however the box came to be empty: a cross, a
  // backspace, or All teams.
  const settle = function(){
    if(!pickedCount() && !el('t-filter-q').value.trim()) FILTER_OPEN = false;
  };

  const toggle = function(ev){
    const b = ev.target.closest && ev.target.closest('[data-team]');
    if(!b) return;
    const id = b.getAttribute('data-team');
    PICKED[id] = !PICKED[id];
    settle();
    redraw();
  };
  list.addEventListener('click', toggle);
  el('t-filter-picked').addEventListener('click', toggle);

  const open = function(){
    if(FILTER_OPEN) return;
    FILTER_OPEN = true;
    if(lastRaw) drawFilter(lastRaw.games, byId);
  };
  const shut = function(){
    if(!FILTER_OPEN) return;
    FILTER_OPEN = false;
    if(lastRaw) drawFilter(lastRaw.games, byId);
  };
  el('t-filter-q').addEventListener('focus', open);
  // Tapping the box is how it opens, and it has to keep working after the
  // list has closed under a cursor that never left.
  el('t-filter-q').addEventListener('click', open);
  el('t-filter-q').addEventListener('input', function(){
    FILTER_OPEN = true;
    settle();
    if(lastRaw) drawFilter(lastRaw.games, byId);
  });
  el('t-filter-q').addEventListener('keydown', function(ev){
    if(ev.key === 'Escape'){ el('t-filter-q').blur(); shut(); }
  });
  // Anything outside the block closes it. pointerdown rather than click, so a
  // tap that lands on the page behind does not also fire something there.
  document.addEventListener('pointerdown', function(ev){
    if(!FILTER_OPEN) return;
    if(box.contains && box.contains(ev.target)) return;
    shut();
  });
  el('t-filter-all').addEventListener('click', function(){
    for(const k in PICKED) delete PICKED[k];
    el('t-filter-q').value = '';
    FILTER_OPEN = false;      // nothing chosen and nothing typed: put it away
    redraw();
  });
}

function drawSchedule(games, byId, gap, outcome, brief){
  const all = games.slice().sort((a, b) =>
    String(a.start || '').localeCompare(String(b.start || '')));

  if(!all.length) return;
  el('t-sec-sched').hidden = false;
  drawFilter(games, byId);

  const chosen = pickedCount();
  const list = chosen
    ? all.filter(function(g){ return PICKED[g.home] || PICKED[g.away]; })
    : all;

  const said = el('t-filter-said');
  if(said){
    said.textContent = !chosen ? ''
      : list.length + (list.length === 1 ? ' game for ' : ' games for ')
        + chosen + (chosen === 1 ? ' team' : ' teams');
  }
  if(!list.length){
    el('t-schedule').innerHTML = '<p class="sfil-none">No games for those teams.</p>';
    return;
  }

  // The opening round: a game that is the earliest fixture for both of its
  // teams. In a six-group round robin that falls out as one slate covering
  // every team once, which is where the seeding is worth repeating.
  const firstFor = {};
  for(const g of all){
    if(!g.home || !g.away) continue;
    if(!firstFor[g.home]) firstFor[g.home] = g.id;
    if(!firstFor[g.away]) firstFor[g.away] = g.id;
  }
  const opener = g => !!g.home && !!g.away
    && firstFor[g.home] === g.id && firstFor[g.away] === g.id;

  let h = '<table><thead><tr><th>Faceoff</th><th class="hide-sm">Grp</th>'
        + '<th>Matchup</th><th class="hide-sm">Rink</th>'
        + '<th class="num hide-sm">Pred GD</th>'
        + '<th><span class="lgo">Predicted winner</span>'
        +   '<span class="ism">Score</span></th></tr></thead><tbody>';
  // The list runs to 43 games; a heading per day keeps it navigable. `list` is
  // already sorted by start, so each date is contiguous.
  let onDay = null;
  for(const g of list){
    const day = (String(g.start || '').match(/^\d{4}-\d{2}-\d{2}/) || [''])[0];
    if(day !== onDay){
      onDay = day;
      h += '<tr class="dayrow"><td colspan="6">' + dayLabel(g.start) + '</td></tr>';
    }
    const home = byId[g.home], away = byId[g.away];
    const d = gap(g);
    const hl = (isStorm(home) || isStorm(away)) ? ' class="hl"' : '';
    // Playoff slots exist on the schedule before anyone has qualified for them.
    const blank = !g.home && !g.away;
    const seeded = opener(g);
    const matchup = blank
      ? '<span class="muted">' + esc(g.label || 'To be determined') + '</span>'
      : label(home, g.home, seeded) + ' <span class="muted">v</span> '
        + label(away, g.away, seeded);
    h += '<tr' + hl + '>'
      + '<td class="t-when">' + when(g.start) + '</td>'
      + '<td class="hide-sm">' + (g.group ? '<span class="flag">' + esc(g.group)
                                          + '</span>'
                          : '<span class="muted">&mdash;</span>') + '</td>'
      // On a phone the rink is the one thing you actually need in the stands,
      // so it moves under the matchup rather than off the edge behind it.
      + '<td class="team">' + matchup
      +   (g.rink ? '<span class="tsm">' + esc(g.rink) + '</span>' : '') + '</td>'
      + '<td class="inp hide-sm">' + esc(g.rink || '') + '</td>'
      + '<td class="num t-gd hide-sm">' + (d == null
        ? '<span class="muted">&mdash;</span>' : signed(d)) + '</td>'
      + '<td><span class="lgo">' + outcome(g) + '</span>'
      +      '<span class="ism">' + brief(g) + '</span></td>'
      + '</tr>';
  }
  el('t-schedule').innerHTML = h + '</tbody></table>';
  el('t-legend').innerHTML = '<b>Pred GD</b> is the home team&rsquo;s rating minus the '
    + 'away team&rsquo;s, so a positive number favours the home side. '
    + 'The number in parentheses on each team&rsquo;s opening game is its seed &mdash; '
    + 'the tournament field ordered by rating, 1 strongest. '
    + 'The percentage beside the predicted winner is how often a team that far '
    + 'ahead has actually won outright, measured over 208 games of this season '
    + 'against the ratings as they stood before each one. It is not a forecast '
    + 'of this game so much as a record of how little a rating gap settles: '
    + 'the underdog or a draw took 38 per cent of those games.';
}

function drawStandings(groups, teams, games, byId, rules, odds){
  if(!teams.length) return;
  el('t-sec-stand').hidden = false;

  const pts = scoring(rules);
  const spec = bracketSpec(rules, groups.length);
  const tiers = tierList(odds, rules, groups.length);
  // A column each stops fitting a phone past two brackets, so from three on the
  // cell names the one bracket the team most often seeds into instead.
  const oneCol = tiers.length > 2;
  // The header has to be written before the rows are counted, so ask the rules
  // rather than the tally: a tournament that breaks every tie never shows a T.
  const anyTies = !rules.noTies;
  let unresolved = false;

  let out = '<div class="gwrap">';
  for(const gid of groups){
    const inGroup = teams.filter(function(t){ return t.group === gid; });
    if(!inGroup.length) continue;

    const row = {};
    inGroup.forEach(function(t){
      row[t.id] = {id: t.id, seed: t.seed, gp: 0, w: 0, l: 0, t: 0, ot: 0, so: 0,
                   gf: 0, ga: 0, pts: 0};
    });

    const done = games.filter(function(g){
      return g.group === gid && isPlayed(g) && row[g.home] && row[g.away];
    });
    for(const g of done){
      const h = row[g.home], a = row[g.away];
      h.gp++; a.gp++;
      h.gf += g.homeScore; h.ga += g.awayScore;
      a.gf += g.awayScore; a.ga += g.homeScore;
      if(g.homeScore !== g.awayScore){
        // The winning goal is in the score whether it came in regulation, in
        // overtime or in a shootout; only the points differ.
        const took = g.homeScore > g.awayScore ? h : a;
        const lost = g.homeScore > g.awayScore ? a : h;
        const how = decisionOf(g);
        took.w++; lost.l++;
        if(how === 'SO'){ took.pts += pts.soWin; lost.pts += pts.soLoss; took.so++; lost.so++; }
        else if(how === 'OT'){ took.pts += pts.otWin; lost.pts += pts.otLoss; took.ot++; lost.ot++; }
        else { took.pts += pts.reg; lost.pts += pts.loss; }
      } else if(g.shootout === 'home' || g.shootout === 'away'){
        const took = g.shootout === 'home' ? h : a;
        const lost = g.shootout === 'home' ? a : h;
        took.w++; lost.l++; took.so++; lost.so++;
        took.pts += pts.soWin; lost.pts += pts.soLoss;
      } else {
        h.pts += pts.soLoss; a.pts += pts.soLoss;
        if(rules.noTies){ h.so++; a.so++; unresolved = true; }
        else { h.t++; a.t++; }
      }
    }

    // Seed order until the group has played something; the standings rules
    // take over the moment there is a result to rank on.
    const table = Object.keys(row).map(function(k){ return row[k]; });
    if(done.length) orderGroup(table, done, pts);
    else table.sort(function(x, y){
      return (x.seed == null ? 999 : x.seed) - (y.seed == null ? 999 : y.seed);
    });

    out += '<div class="gcard"><h4>Group ' + esc(gid) + '</h4>'
         + '<table class="st"><thead><tr><th>Team</th>'
         + '<th class="num hide-sm">Seed</th>'
         + '<th class="num">' + (anyTies ? 'W-L-T' : 'W-L') + '</th>'
         + '<th class="num hide-sm">GF/GA</th>'
         + '<th class="num">Pts</th>'
         + (oneCol ? '<th class="num">Bracket</th>'
                   : tiers.map(function(t){
                       return '<th class="num">' + esc(t.name.charAt(0)) + '%</th>';
                     }).join(''))
         + '</tr></thead><tbody>';

    for(const r of table){
      const team = byId[r.id];
      const cells = oneCol
        ? oddsBest(odds, r.id, tiers, rules)
        : tiers.map(function(t){
            return oddsShort(oddsText(odds, r.id, t.key));
          }).join('');
      // Seed and goals ride under the name on a phone rather than taking two
      // columns in front of the points and the odds.
      const under = [];
      if(r.seed != null) under.push('seed ' + r.seed);
      if(r.gp) under.push(r.gf + '/' + r.ga);
      out += '<tr' + (isStorm(team) ? ' class="hl"' : '') + '>'
           + '<td class="tm">' + tlink(team, esc(team ? team.name : r.id)) + tagFor(team)
           +   (under.length ? '<span class="tsm">' + under.join(' &middot; ')
                             + '</span>' : '') + '</td>'
           + numCell(r.seed == null ? null : r.seed, 'hide-sm')
           + numCell(r.gp ? r.w + '-' + r.l + (r.t ? '-' + r.t : '') : null)
           + numCell(r.gp ? r.gf + '/' + r.ga : null, 'hide-sm')
           + numCell(r.gp ? r.pts : null)
           + cells
           + '</tr>';
    }
    out += '</tbody></table></div>';
  }
  out += '</div>';
  el('t-standings').innerHTML = out;

  describeRules(rules, pts, spec, tiers, groups.length, unresolved);
}

// The brackets in the order a team would rather be in them. The simulation
// carries them once it has run, but the columns have to be right before the
// first puck drops too, so the rules are the fallback rather than a guess at
// Gold and Silver.
function tierList(odds, rules, groupCount){
  if(odds && odds.tiers) return odds.tiers;
  if(!rules) return [{key: 'gold', name: 'Gold'}, {key: 'silver', name: 'Silver'}];
  return bracketSpec(rules, groupCount).blocks.map(function(b){
    return {key: b.key, name: b.name};
  });
}

function nameOf(t){ return t.name; }

function ordinal(k){
  const tens = k % 100;
  if(tens >= 11 && tens <= 13) return k + 'th';
  return k + (['th', 'st', 'nd', 'rd'][k % 10] || 'th');
}

// "Gold and Silver", "Gold, Silver and Bronze".
function andList(names){
  if(names.length < 2) return names.join('');
  return names.slice(0, -1).join(', ') + ' and ' + names[names.length - 1];
}

// One cell for the whole playoff picture: the bracket this team seeds into most
// often, and how often. A team out of every bracket plays a placement game, and
// says so rather than showing a zero against a bracket it cannot reach.
function oddsBest(odds, id, tiers, rules){
  if(!odds) return '<td class="num gold pend">&mdash;</td>';
  let best = null, hits = -1;
  for(const t of tiers){
    const pool = odds[t.key];
    const v = pool && pool[id];
    if(v !== undefined && v > hits){ hits = v; best = t; }
  }
  if(!best) return '<td class="num gold pend">&mdash;</td>';
  if(hits === 0){
    return '<td class="num gold" title="Out of every bracket">'
         + esc(rules && rules.leftoverShort ? rules.leftoverShort : 'Cons') + '</td>';
  }
  if(hits === odds.runs){
    return '<td class="num gold" title="Clinched">' + esc(best.name) + '</td>';
  }
  const pct = hits / odds.runs * 100;
  return '<td class="num gold">' + esc(best.name) + ' '
       + (pct < 1 ? '&lt;1' : Math.round(pct)) + '%</td>';
}

// "Eliminated" and "Clinched" are each about seven characters wider than any
// percentage, and between them they set the width of both odds columns -- wide
// enough to push the card into a horizontal scroll. Abbreviated here, with the
// full word on hover and in the note below the tables.
// E and C, the same letters the standings use, with the word on hover.
function oddsLetter(text){
  if(text === 'Eliminated') return {n: 'E', title: 'Eliminated'};
  if(text === 'Clinched') return {n: 'C', title: 'Clinched'};
  return {n: text, title: null};
}

function oddsShort(text){
  if(text == null) return '<td class="num gold pend">&mdash;</td>';
  if(text === 'Eliminated') return '<td class="num gold" title="Eliminated">E</td>';
  if(text === 'Clinched') return '<td class="num gold" title="Clinched">C</td>';
  return '<td class="num gold">' + text + '</td>';
}

// Anything with no data behind it yet renders as an em-dash, not a zero.
function numCell(v, extra){
  const cls = 'num' + (extra ? ' ' + extra : '');
  return v == null ? '<td class="' + cls + ' pend">&mdash;</td>'
                   : '<td class="' + cls + '">' + v + '</td>';
}

function tagFor(t){
  if(!t || t.basis !== 'summer-only') return '';
  return '<span class="tag" title="' + esc(t.note || 'Summer-only select team')
       + '">summer-only</span>';
}

const SIM_RUNS = 10000;
const SIM_GOALS = 6.0;   // expected total goals in a game

// The simulation runs off a seeded generator rather than Math.random, so the
// same scores always produce the same percentages. A reader who refreshes twice
// should not see the Storm's chances wobble by a point for no reason.
const SIM_SEED = 0x5f3759df;

function mulberry32(a){
  return function(){
    a = a + 0x6d2b79f5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}

function hash32(str){
  let h = 0x811c9dc5;
  for(let i = 0; i < str.length; i++){
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

// Sorted, so the seed depends on the scores themselves and not on the order
// the games happen to sit in the file.
function seedFrom(games){
  const parts = [];
  for(const g of games){
    if(!isPlayed(g)) continue;
    parts.push(String(g.id) + ':' + g.home + '>' + g.away
             + ':' + g.homeScore + '-' + g.awayScore);
  }
  parts.sort();
  return (SIM_SEED ^ hash32(parts.join('|'))) | 0;
}

// Box-Muller. Only the cosine half is taken; caching the spare is not worth
// the bookkeeping at this volume.
function gauss(rand){
  let u = 0;
  while(u === 0) u = rand();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rand());
}

// Knuth's method. Fine at these rates -- lambda tops out near 6, so the loop
// runs a handful of times.
function poisson(rand, lambda){
  const L = Math.exp(-lambda);
  let k = 0, p = 1;
  do { k++; p *= rand(); } while(p > L);
  return k - 1;
}

// Returns {runs, tiers, <bracket key>: {teamId: iterations seeded into it},
// cons: {...}, opp, oppRuns}, or null when no game has finished yet -- we do not
// project a playoff field before puck drop. `tiers` names the brackets in
// order, so a caller never has to know what this tournament calls them.
function simulate(teams, games, byId, rules, groups, focusId){
  if(!games.some(isPlayed)) return null;

  const pts = scoring(rules);
  const ids = teams.map(t => t.id);
  const n = ids.length;
  const at = {};
  ids.forEach(function(id, i){ at[id] = i; });

  const groupAt = groups.map(function(gid){
    return ids.map(function(id, i){ return byId[id].group === gid ? i : -1; })
              .filter(function(i){ return i >= 0; });
  });

  const rand = mulberry32(seedFrom(games));

  const spec = bracketSpec(rules, groups.length);
  const blocks = spec.blocks;
  // Everything past the last bracket plays a placement game instead, and that
  // leftover is one more block for the purpose of pairing teams off.
  const leftover = blocks.length ? blocks[blocks.length - 1].to + 1 : 0;
  // Each bracket of eight pairs mirrored -- 1 v 8, 2 v 7 and so on -- which is
  // what the tournament's own first posted pairing turned out to be. So the
  // seeding already says who the Storm meet, and counting that across the runs
  // gives the same kind of number as the berth odds.
  const stormAt = (function(){
    for(let i = 0; i < ids.length; i++){ if(isStorm(byId[ids[i]])) return i; }
    return -1;
  })();
  const faced = new Int32Array(n);
  const seatOf = new Int32Array(n);

  // A pairing the tournament has already posted is a fact about the final
  // seeding, not a guess about it. A run that puts those two teams anywhere
  // but opposite each other is a run that cannot happen, so it does not get a
  // say in who the Storm meet. Without this the answer was 64 per cent; the
  // one posted game rules out most of what the other 36 were.
  const settled = games.filter(function(g){
    return g.round !== 'group' && byId[g.home] && byId[g.away];
  }).map(function(g){ return [at[g.home], at[g.away]]; });

  function blockOf(i){
    for(let k = 0; k < blocks.length; k++){
      if(i >= blocks[k].from && i <= blocks[k].to) return k;
    }
    return -1;
  }
  function blockStart(i, len){
    const k = blockOf(i);
    return k < 0 ? leftover : blocks[k].from;
  }
  function blockEnd(i, len){
    const k = blockOf(i);
    return k < 0 ? len : blocks[k].to + 1;
  }

  const fixtures = games.filter(function(g){
    return g.round === 'group' && byId[g.home] && byId[g.away];
  }).map(function(g){
    // How a finished game finished is worth as much as the score: a shootout
    // win pays two rather than three, and the standings table has always known
    // that. The simulation did not -- it read the score alone and paid every
    // played game as regulation, which handed the loser's point away and put
    // the wrong team top of a group that was already decided.
    const done = isPlayed(g);
    return {
      id: g.id,
      h: at[g.home], a: at[g.away], done: done,
      hs: done ? g.homeScore : 0, as: done ? g.awayScore : 0,
      how: done ? decisionOf(g) : null,
      won: g.shootout === 'home' ? 'h' : g.shootout === 'away' ? 'a' : null
    };
  });

  // A projection is an estimate, and `band` is its standard deviation. Each
  // iteration redraws every rating from N(rating, band) and holds it for that
  // whole iteration, so a team is consistently good or bad across its three
  // games rather than re-rolled per fixture. That propagates the projection
  // error into the odds instead of treating the ratings as exact.
  const base = new Float64Array(n);
  const sd = new Float64Array(n);
  const drawn = new Float64Array(n);
  ids.forEach(function(id, i){
    const r = rating(byId[id]);
    base[i] = r == null ? NaN : r;
    sd[i] = typeof byId[id].band === 'number' ? byId[id].band : 0;
  });

  const P = new Int32Array(n), GF = new Int32Array(n), GA = new Int32Array(n);
  const MP = new Int32Array(n * n);   // points i took off j
  const MF = new Int32Array(n * n);   // goals i scored against j
  const rnd = new Float64Array(n);
  const tally = blocks.map(function(){ return new Int32Array(n); });
  const cons = new Int32Array(n);

  // The rooting guide. For each still-to-play fixture and each way it can go,
  // how many runs went that way and how many of those put the focus team in
  // each bracket. Three outcomes: 0 home win, 1 away win, 2 level.
  const focusAt = (focusId != null && at[focusId] != null) ? at[focusId] : -1;
  const OUT = 3;
  const condRuns = focusAt < 0 ? null : new Int32Array(fixtures.length * OUT);
  const condHit = focusAt < 0 ? null
                : new Int32Array(fixtures.length * OUT * blocks.length);
  const thisRun = focusAt < 0 ? null : new Int8Array(fixtures.length);

  function quotient(i, pool){
    let f = 0, against = 0;
    for(let k = 0; k < pool.length; k++){
      const j = pool[k];
      if(j === i) continue;
      f += MF[i * n + j];
      against += MF[j * n + i];
    }
    const total = f + against;
    return total === 0 ? 0 : f / total;
  }

  function mutual(i, pool){
    let v = 0;
    for(let k = 0; k < pool.length; k++){
      if(pool[k] !== i) v += MP[i * n + pool[k]];
    }
    return v;
  }

  // the event file splits its tiebreakers: two teams level go to head-to-head
  // first, three or more go to goal quotient first. The final coin flip is a
  // genuine random draw, which is what the published rules actually say.
  function orderTied(pool){
    const h2hFirst = pool.length === 2;
    return pool.slice().sort(function(x, y){
      const a1 = h2hFirst ? mutual(x, pool) : quotient(x, pool);
      const b1 = h2hFirst ? mutual(y, pool) : quotient(y, pool);
      if(b1 !== a1) return b1 - a1;
      const a2 = h2hFirst ? quotient(x, pool) : mutual(x, pool);
      const b2 = h2hFirst ? quotient(y, pool) : mutual(y, pool);
      if(b2 !== a2) return b2 - a2;
      if(GA[x] !== GA[y]) return GA[x] - GA[y];
      return rnd[x] - rnd[y];
    });
  }

  function rank(pool){
    const byPoints = pool.slice().sort(function(x, y){ return P[y] - P[x]; });
    const out = [];
    let i = 0;
    while(i < byPoints.length){
      let j = i + 1;
      while(j < byPoints.length && P[byPoints[j]] === P[byPoints[i]]) j++;
      if(j - i === 1) out.push(byPoints[i]);
      else Array.prototype.push.apply(out, orderTied(byPoints.slice(i, j)));
      i = j;
    }
    return out;
  }

  for(let run = 0; run < SIM_RUNS; run++){
    P.fill(0); GF.fill(0); GA.fill(0); MP.fill(0); MF.fill(0);
    for(let i = 0; i < n; i++){
      rnd[i] = rand();
      drawn[i] = base[i] !== base[i] ? NaN : base[i] + sd[i] * gauss(rand);
    }

    for(let f = 0; f < fixtures.length; f++){
      const g = fixtures[f];
      let hs, as;
      if(g.done){ hs = g.hs; as = g.as; }
      else {
        const dh = drawn[g.h], da = drawn[g.a];
        const d = (dh !== dh || da !== da) ? 0 : dh - da;
        hs = poisson(rand, Math.max(0.3, (SIM_GOALS + d) / 2));
        as = poisson(rand, Math.max(0.3, (SIM_GOALS - d) / 2));
      }

      GF[g.h] += hs; GA[g.h] += as;
      GF[g.a] += as; GA[g.a] += hs;
      MF[g.h * n + g.a] += hs;
      MF[g.a * n + g.h] += as;

      let ph, pa;
      if(g.done && g.how && g.how !== 'REG'){
        const win = g.how === 'OT' ? pts.otWin : pts.soWin;
        const lose = g.how === 'OT' ? pts.otLoss : pts.soLoss;
        if(hs > as){ ph = win; pa = lose; }
        else if(as > hs){ ph = lose; pa = win; }
        else if(g.won === 'h'){ ph = win; pa = lose; }
        else if(g.won === 'a'){ ph = lose; pa = win; }
        else { ph = lose; pa = lose; }
      }
      else if(hs > as){ ph = pts.reg; pa = pts.loss; }
      else if(as > hs){ ph = pts.loss; pa = pts.reg; }
      // A game that finished level with no shootout winner recorded gives both
      // sides the losing point, as the standings do, rather than inventing one.
      // Only a game still to be played is worth a coin toss.
      else if(g.done){ ph = pts.soLoss; pa = pts.soLoss; }
      else if(rand() < 0.5){ ph = pts.soWin; pa = pts.soLoss; }
      else { ph = pts.soLoss; pa = pts.soWin; }

      if(thisRun) thisRun[f] = hs > as ? 0 : as > hs ? 1 : 2;

      P[g.h] += ph; P[g.a] += pa;
      MP[g.h * n + g.a] += ph;
      MP[g.a * n + g.h] += pa;
    }

    // Head-to-head cannot arbitrate between teams that never met, so the
    // cross-group order falls back to goal quotient, then goals allowed, then
    // the coin flip.
    //
    // Where the two formats differ is how far down that grouping goes. Seeding
    // by place keeps every finishing position its own cohort, so no runner-up
    // can outseed a group winner and no third place can outseed a runner-up.
    // The older format separates the winners and then ranks everyone else in
    // one line.
    const cohorts = [];
    const placed = [];
    for(let gi = 0; gi < groupAt.length; gi++){
      const ranked = rank(groupAt[gi]);
      placed.push(ranked);
      for(let r = 0; r < ranked.length; r++){
        (cohorts[r] || (cohorts[r] = [])).push(ranked[r]);
      }
    }
    let seeding;
    if(spec.byPlace){
      for(let c = 0; c < cohorts.length; c++) cohorts[c].sort(crossCmp);
      seeding = [].concat.apply([], cohorts);
    } else if(rules.autoPlaces){
      // Automatic berths that differ by group -- the top two of a group of
      // four, the top three of a group of six -- seeded ahead of the wildcards.
      const winners = [], others = [];
      for(let gi = 0; gi < placed.length; gi++){
        const k = rules.autoPlaces[groups[gi]] || 1;
        winners.push.apply(winners, placed[gi].slice(0, k));
        others.push.apply(others, placed[gi].slice(k));
      }
      winners.sort(crossCmp);
      others.sort(crossCmp);
      seeding = winners.concat(others);
    } else {
      const winners = (cohorts[0] || []).slice();
      const others = [].concat.apply([], cohorts.slice(1));
      winners.sort(crossCmp);
      others.sort(crossCmp);
      seeding = winners.concat(others);
    }
    const len = seeding.length;
    for(let i = 0; i < len; i++) seatOf[seeding[i]] = i;

    // Who a team meets first in the playoff. Mirrored inside its bracket by
    // default; with `rules.crossover` and two groups, the other group's team
    // one place away instead -- 1A v 2B, 2A v 1B, 3A v 4B, 4A v 3B -- which
    // is the Goya format and which no ordering of seats can express.
    const cross = rules.crossover && placed.length === 2;
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
      if(cross){
        for(let gi = 0; gi < 2; gi++){
          const p = placed[gi].indexOf(i);
          if(p >= 0) return placed[1 - gi][p ^ 1];
        }
        return undefined;
      }
      const s = seatOf[i];
      return seeding[blockStart(s, len) + blockEnd(s, len) - 1 - s];
    }
    if(stormAt >= 0){
      let agrees = true;
      for(let k = 0; k < settled.length && agrees; k++){
        agrees = partner(settled[k][0]) === settled[k][1];
      }
      if(agrees){
        const foe = partner(stormAt);
        if(foe !== undefined && foe !== stormAt) faced[foe]++;
      }
    }
    let focusBlock = -2;
    for(let seed = 0; seed < seeding.length; seed++){
      const k = blockOf(seed);
      if(k < 0) cons[seeding[seed]]++;
      else tally[k][seeding[seed]]++;
      if(seeding[seed] === focusAt) focusBlock = k;
    }

    if(condRuns){
      for(let f = 0; f < fixtures.length; f++){
        if(fixtures[f].done) continue;      // nothing left to root for
        const slot = f * OUT + thisRun[f];
        condRuns[slot]++;
        if(focusBlock >= 0) condHit[slot * blocks.length + focusBlock]++;
      }
    }
  }

  function crossCmp(x, y){
    if(P[y] !== P[x]) return P[y] - P[x];
    const qx = GF[x] + GA[x] === 0 ? 0 : GF[x] / (GF[x] + GA[x]);
    const qy = GF[y] + GA[y] === 0 ? 0 : GF[y] / (GF[y] + GA[y]);
    if(qy !== qx) return qy - qx;
    if(GA[x] !== GA[y]) return GA[x] - GA[y];
    return rnd[x] - rnd[y];
  }

  // `tiers` is the running order every caller reads the brackets in, so the
  // page never has to know what a given tournament calls them.
  const out = {runs: SIM_RUNS, cons: {}, opp: {}, oppRuns: 0,
               tiers: blocks.map(function(b){ return {key: b.key, name: b.name}; })};
  ids.forEach(function(id, i){
    if(faced[i]){ out.opp[id] = faced[i]; out.oppRuns += faced[i]; }
  });
  blocks.forEach(function(b, k){
    out[b.key] = {};
    ids.forEach(function(id, i){ out[b.key][id] = tally[k][i]; });
  });
  ids.forEach(function(id, i){ out.cons[id] = cons[i]; });

  // One row per remaining fixture: who is playing, and for each way it can go
  // the share of those runs that put the focus team in each bracket. A caller
  // compares those against the team's own overall odds to see what swings it.
  if(condRuns){
    out.focus = focusId;
    out.swing = [];
    for(let f = 0; f < fixtures.length; f++){
      if(fixtures[f].done) continue;
      const ways = [];
      for(let o = 0; o < OUT; o++){
        const runs = condRuns[f * OUT + o];
        if(!runs) continue;
        const per = {};
        blocks.forEach(function(b, k){
          per[b.key] = condHit[(f * OUT + o) * blocks.length + k] / runs;
        });
        ways.push({o: o, runs: runs, share: runs / SIM_RUNS, odds: per});
      }
      out.swing.push({id: fixtures[f].id, home: ids[fixtures[f].h],
                      away: ids[fixtures[f].a], ways: ways});
    }
  }
  return out;
}

// null means "nothing to show yet", which every caller renders as an em-dash.
function oddsPct(odds, id, tier){
  if(!odds) return null;
  const pool = odds[tier || 'gold'];
  const hit = pool && pool[id];
  return hit === undefined ? null : hit / odds.runs * 100;
}

function oddsText(odds, id, tier){
  if(!odds) return null;
  const pool = odds[tier || 'gold'];
  const hit = pool && pool[id];
  if(hit === undefined) return null;
  // Eliminated is reserved for a clean zero; anything that merely rounds to
  // zero is still alive and says so.
  if(hit === odds.runs) return 'Clinched';
  if(hit === 0) return 'Eliminated';
  const pct = hit / odds.runs * 100;
  return pct < 0.5 ? '&lt;1%' : pct > 99.5 ? '&gt;99%' : Math.round(pct) + '%';
}

// Points first, then the published tiebreakers as far as the schedule can
// carry them. A tie is broken inside its own run, so head-to-head means the
// record among exactly the teams that are level -- which is what the rule
// says, and not the same as each team's record against the whole group.
function orderGroup(table, done, pts){
  table.sort(function(a, b){ return b.pts - a.pts; });

  const headToHead = function(ids){
    const got = {};
    ids.forEach(function(id){ got[id] = 0; });
    done.forEach(function(g){
      if(!(g.home in got) || !(g.away in got)) return;
      const how = decisionOf(g);
      let ph, pa;
      if(g.homeScore > g.awayScore){
        ph = how === 'SO' ? pts.soWin : how === 'OT' ? pts.otWin : pts.reg;
        pa = how === 'SO' ? pts.soLoss : how === 'OT' ? pts.otLoss : pts.loss;
      } else if(g.awayScore > g.homeScore){
        pa = how === 'SO' ? pts.soWin : how === 'OT' ? pts.otWin : pts.reg;
        ph = how === 'SO' ? pts.soLoss : how === 'OT' ? pts.otLoss : pts.loss;
      } else { ph = pts.soLoss; pa = pts.soLoss; }
      got[g.home] += ph;
      got[g.away] += pa;
    });
    return got;
  };

  let i = 0;
  while(i < table.length){
    let j = i + 1;
    while(j < table.length && table[j].pts === table[i].pts) j++;
    if(j - i > 1){
      const run = table.slice(i, j);
      const mini = headToHead(run.map(function(r){ return r.id; }));
      run.sort(function(a, b){
        return (mini[b.id] - mini[a.id])
            || (b.w - a.w)
            || ((b.gf - b.ga) - (a.gf - a.ga))
            || (a.ga - b.ga)
            || (b.gf - a.gf);
      });
      for(let k = 0; k < run.length; k++) table[i + k] = run[k];
    }
    i = j;
  }
  return table;
}

function byRank(x, y){
  return y.pts - x.pts || (y.gf - y.ga) - (x.gf - x.ga) || y.gf - x.gf;
}

function describeRules(rules, pts, spec, tiers, groupCount, unresolved){
  const parts = ['Regulation win ' + pts.reg];
  const hasOT = typeof rules.overtimeWin === 'number'
             || typeof rules.overtimeLoss === 'number';
  const hasSO = typeof rules.shootoutWin === 'number'
             || typeof rules.shootoutLoss === 'number';
  if(hasOT){
    parts.push('overtime win ' + pts.otWin, 'overtime loss ' + pts.otLoss);
  }
  if(hasSO || !hasOT){
    parts.push('shootout win ' + pts.soWin, 'shootout loss ' + pts.soLoss);
  }
  // DEFAULT_RULES supplies a tie value to every tournament, so the field being
  // there proves nothing. What settles it is whether a round-robin game can end
  // level at all, which is exactly what noTies denies.
  if(!rules.noTies && typeof rules.tie === 'number') parts.push('tie ' + rules.tie);
  parts.push('loss ' + pts.loss);
  const scale = parts.join(', ') + '.';
  let route;
  // A format the seat ranges cannot describe in words, such as a crossover,
  // says itself in the file.
  if(rules.route){
    route = rules.route;
  } else if(spec.byPlace){
    route = spec.blocks.map(function(b){
      return b.name + ' takes seeds ' + b.lo + '-' + b.hi + ' of the '
           + ordinal(b.place) + ' places';
    }).join('; ') + '.';
  } else {
    const berths = spec.blocks[0] ? spec.blocks[0].to + 1 : null;
    const autos = rules.autoPlaces
      ? Object.keys(rules.autoPlaces).reduce(function(a, k){ return a + rules.autoPlaces[k]; }, 0)
      : groupCount;
    const wildcards = berths == null ? 0 : Math.max(0, berths - autos);
    route = berths == null
      ? 'Top ' + (rules.advance || 2) + ' in each group advance.'
      : berths + ' berths: ' + (rules.autoBerths || 'each group winner')
        + (wildcards ? ', then ' + (rules.wildcards || wildcards + ' wildcards') : '') + '.';
  }
  el('t-adv-rule').textContent = scale + ' ' + route
    + (rules.noTies ? ' Note: ' + rules.noTies + '.' : '')
    + (rules.overtime ? ' ' + rules.overtime : '');

  const breaks = [];
  if(rules.tiebreakersTwoTeams){
    breaks.push('<b>Two teams level:</b> ' + esc(rules.tiebreakersTwoTeams.join(', ')));
  }
  if(rules.tiebreakersThreePlus){
    breaks.push('<b>Three or more level:</b> ' + esc(rules.tiebreakersThreePlus.join(', ')));
  }
  if(!breaks.length && rules.tiebreakers && rules.tiebreakers.length){
    breaks.push('<b>Tiebreakers:</b> ' + esc(rules.tiebreakers.join(', ')));
  }
  const heads = tiers.map(function(t){ return '<b>' + esc(t.name.charAt(0)) + '%</b>'; });
  let note = (tiers.length > 2
        ? 'The <b>Bracket</b> column names the bracket a team seeds into most often '
          + 'across ' + SIM_RUNS.toLocaleString() + ' simulated completions of the '
          + 'group stage, and how often. '
        : andList(heads) + ' are the ' + andList(tiers.map(nameOf)) + ' shares of '
          + SIM_RUNS.toLocaleString()
          + ' simulated completions of the group stage in which the team seeds into '
          + 'that bracket. ')
           + (spec.byPlace
              ? 'Each finishing position is seeded as its own cohort, so a runner-up '
                + 'cannot outseed a group winner however many points it takes. '
              : (rules.autoPlaces ? 'The automatic qualifiers' : 'The group winners')
                + ' take the top seeds and everyone else is ordered on '
                + 'total points across all groups. ')
           + 'Finished games are held fixed. Each iteration first '
           + 'redraws every rating from a normal centred on its projection with that '
           + "team's own uncertainty band, so the odds carry the projection error "
           + 'rather than pretending the ratings are exact; each remaining game then '
           + 'draws goals from a Poisson fitted to those drawn ratings, with a '
           + 'coin-flip shootout when they finish level. '
           + 'Before any game is final the column reads a dash. '
           + '"Clinched" and "Eliminated" mean every single iteration agreed, which is '
           + 'strong evidence rather than a proof, and '
           + '&ldquo;Eliminated&rdquo; a clean zero rather than a rounded one; in '
           + 'the tables those are shortened to <b>C</b> and <b>E</b>. The '
           + 'generator is seeded from the scores themselves, so the same results '
           + 'always give the same percentages. ';
  note += breaks.join('. ') + (breaks.length ? '. ' : '');
  note += 'The order shown applies points, then the published tiebreakers as far '
        + 'as the schedule carries them: the record among exactly the teams that '
        + 'are level, then most wins, then goal difference, then fewest goals '
        + 'allowed. Anything the tournament uses beyond those, such as a first '
        + 'goal or a coin toss, is not computable from a schedule, so a group still '
        + 'level after those four may not be settled here the way the tournament '
        + 'settles it.';

  if(unresolved){
    note += ' A game level after regulation with no recorded shootout winner scores '
          + 'the shootout-loss point for both sides &mdash; add "shootout": "home" or '
          + '"away" to that game to resolve it.';
  }
  el('t-tiebreak').innerHTML = note;
}
</script>'''

# Relative hrefs: this is a GitHub Pages *project* site served from
# /boys-hockey-rankings/, so a leading slash would resolve to the wrong root.
NAV = [('index.html', 'Boys Hockey Rankings')]

ADJUST = r'''
// ---------------------------------------------------------------- adjustment
// Both pages derive adjusted ratings the same way, from the same two files, and
// neither writes anything back. ratings.json is the prior for all 251 ranked
// teams; results.json is the ledger of finished games. The universe has to be
// the whole ranked list, not just the rows on screen, because an opponent can
// sit well outside the top 30 and its rating still feeds the arithmetic.

const ADJ_PASSES = 6;
const ADJ_CAP = 7;        // MHR caps single-game goal differential at 7
const ADJ_NOISE = 6.25;   // per-game variance of an implied rating, in goals^2
const ADJ_TAIL = 4;       // degrees of freedom in the prior; lower = fatter tails
// From this snapshot a team starting on MHR's number keeps a plain prior. The
// tail was sized for a projection 1.35 wide; MHR's band is a third of that, so
// one 4-goal upset read as nine bands and moved the Storm 0.77 on 1 November.
// Dated so every seed and Analysis before it stays exactly as published.
const ADJ_MHR_PLAIN_FROM = '2026-10-28';

// Rust. A team's first games of a season understate it: girls arrive from other
// programmes, lines are new, and some teams come in off a tune-up weekend while
// others come in cold. It wears off, so a team's opening game counts about 40%
// of a settled one and it is gone by about the sixth. Indexed by games into
// that team's season, not by date -- in December an early-season game is both
// old and rusty, and these must discount it for one reason each.
const ADJ_RUST_DROP = 0.60;
const ADJ_RUST_GAMES = 2;

// Form, which is the other reason. Calendar time, and it never stops applying.
// Long enough that a weekend's games weigh the same as each other: what
// separates Friday from Sunday is rust, not form.
const ADJ_FORM_HALFLIFE = 45;   // days

function grab(name, bust){
  const url = bust ? name + '?t=' + Date.now() : name;
  return fetch(url, {cache: 'no-store'})
    .then(function(r){ return r.ok ? r.json() : null; })
    .catch(function(){ return null; });
}

// The raw inputs are kept as well as the answer, so a page can re-run the
// arithmetic over a slice of the season -- what one tournament changed, rather
// than what the whole season has.
let ADJ_IN = {ratings: null, results: null};

function loadAdjustment(bust){
  return Promise.all([grab('ratings.json', bust), grab('results.json', bust)])
    .then(function(both){
      ADJ_IN = {ratings: both[0], results: both[1]};
      return adjustRatings(both[0], both[1], localDay());
    });
}

// The same ranking, with the season cut off at a date.
// Memoised for the life of one draw: the seeds and both halves of the Analysis
// tab all want a cut-off answer, and the same cut-off asked twice must give the
// same one. draw() clears it, because a typed score changes the ledger.
let AS_OF = {};

function adjustAsOf(cut){
  if(AS_OF[cut]) return AS_OF[cut];
  const all = (ADJ_IN.results && ADJ_IN.results.games) || [];
  // What was known on that day, not just what had been played by it: a game
  // entered late carries `recorded`, and a tournament seeded before then was
  // seeded without it. Great Lakes' August games came in on 30 September and
  // must not reseed Labor Day.
  AS_OF[cut] = adjustRatings(ADJ_IN.ratings,
    {games: all.filter(function(g){
      return String(g.date) <= cut && !(g.recorded && String(g.recorded) > cut);
    })}, cut);
  return AS_OF[cut];
}

// The same thing cut at an instant rather than a day. The ledger times every
// game, so "what were these two worth going into this one" has an answer even
// when both teams played that morning -- which is the difference between a
// running rating per game and one per day.
//
// Compared as epoch milliseconds, not as strings: the games carry their own
// rink's offset, and -04:00 and -05:00 do not sort against each other as text.
const UP_TO = {};

function adjustUpTo(instant){
  const t = typeof instant === 'number' ? instant : Date.parse(instant);
  if(isNaN(t)) return adjustRatings(ADJ_IN.ratings, {games: []}, '0000-00-00');
  if(UP_TO[t]) return UP_TO[t];
  const all = (ADJ_IN.results && ADJ_IN.results.games) || [];
  // The instant's day, in UTC. It only decides which side of the MHR snapshot
  // this falls, and no game is played around midnight UTC on a snapshot day.
  const day = new Date(t).toISOString().slice(0, 10);
  UP_TO[t] = adjustRatings(ADJ_IN.ratings, {games: all.filter(function(g){
    // A game entered late is left out of any moment before it was entered,
    // as adjustAsOf() does: a game already played keeps the numbers it had.
    if(g.recorded && String(g.recorded) > day) return false;
    // A row with no faceoff on it is an older ledger; take it as end of its day.
    const s = Date.parse(g.start || (String(g.date) + 'T23:59:59Z'));
    return !isNaN(s) && s <= t;
  })}, day);
  return UP_TO[t];
}

// The day before the first faceoff. What a team was worth then is the only
// honest basis for a seed, and it is also the Analysis tab's "before" column,
// so the two cannot disagree.
function eveOf(games){
  const days = (games || []).map(function(g){ return String(g.start || '').slice(0, 10); })
                            .filter(Boolean).sort();
  // Only the tournament page has a chosen event; elsewhere the games say.
  const chosen = (typeof EVENT !== 'undefined' && EVENT) ? EVENT.start : null;
  const first = chosen || days[0];
  if(!first) return null;
  const t = Date.parse(first);
  return isNaN(t) ? null : new Date(t - 86400000).toISOString().slice(0, 10);
}

// Fitted on 208 games across two tournaments, each scored against the ratings
// as they stood before it. Slope 0.554 per rating point, standard error 0.098.
// See the methodology page.
const WIN_SLOPE = 0.554;

// The favourite's chance of winning outright, given the rating gap.
function winOdds(gap, tie){
  const p = 1 / (1 + Math.exp(-WIN_SLOPE * Math.abs(gap)));
  return {fav: p * (1 - tie), tie: tie, dog: (1 - p) * (1 - tie)};
}

// The day a computation is for, as YYYY-MM-DD, in the viewer's own calendar.
function localDay(){
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

// Returns {mhrName: {proj, prior, band, adj, gp, shift}} for every rated team.
//
// `on` is the day the answer is for. From ratings.live.asOf on, a team MHR has
// rated starts from `live` -- its projection blended with MHR's live rating by
// games played, see build/live.py -- instead of `proj`, and the ledger's games
// before that day are dropped from its side, because MHR's number already holds
// them. Its opponent keeps its side of the same game unless MHR rated it too.
// Before asOf nothing changes, so a seed frozen at a September eve stays put.
//
// Every weekly snapshot is kept (`ratings.snapshots`, and `snaps[asOf]` =
// [live, liveBand, mgp] on each team), and the one in force on `on` is the
// latest captured on or before it. So a date between two Wednesdays reads the
// MHR numbers a reader had that week, and a past tournament's seeds and
// Analysis stop moving every time a new capture arrives -- with only the
// newest snapshot kept, the NIT's 14 October eve fell back to the bare
// projection on 21 October and its Analysis went from 32 -> 28 to 29 -> 26.
// A file with no history (compare_blends builds its own) keeps the old
// one-snapshot behaviour.
function adjustRatings(ratings, results, on){
  const teams = (ratings && ratings.teams) || [];
  const games = (results && results.games) || [];
  const day = String(on || localDay());
  let snap = null, take;
  if(ratings && Array.isArray(ratings.snapshots)){
    for(const s of ratings.snapshots){
      if(s && s.asOf && s.asOf <= day && (!snap || s.asOf > snap)) snap = s.asOf;
    }
    take = function(t){
      const v = snap && t.snaps && t.snaps[snap];
      return v ? {live: v[0], band: v[1], mgp: v[2]} : null;
    };
  } else {
    const cur = ratings && ratings.live && ratings.live.asOf;
    if(cur && day >= cur) snap = cur;
    take = function(t){
      return snap && typeof t.live === 'number'
        ? {live: t.live, band: t.liveBand, mgp: t.mgp} : null;
    };
  }

  const proj = {}, prior = {}, band = {}, pool = {}, mgp = {};
  let adj = {};
  for(const t of teams){
    if(!t || typeof t.proj !== 'number') continue;
    // A team added from MHR's own lists does not exist before the snapshot it
    // arrived with, so no earlier seed, Analysis or running rating moves.
    if(t.since && day < String(t.since)) continue;
    const L = take(t);
    proj[t.n] = t.proj;
    prior[t.n] = L ? L.live : t.proj;
    band[t.n] = L ? L.band
              : (typeof t.band === 'number' ? t.band : 0);
    if(L) mgp[t.n] = L.mgp || 0;
    pool[t.n] = {usa: !!t.usa, na: !!t.na};
    adj[t.n] = prior[t.n];
  }

  // Every finished game, recorded once from each side's point of view. A game
  // against a team with no projection is skipped: there is no rating to carry.
  const seen = {};
  let latest = '';
  for(const g of games){
    if(!g || g.homeScore == null || g.awayScore == null) continue;
    if(!(g.home in proj) || !(g.away in proj)) continue;
    let gd = g.homeScore - g.awayScore;
    gd = Math.max(-ADJ_CAP, Math.min(ADJ_CAP, gd));
    const on = String(g.date || '');
    if(on > latest) latest = on;
    const missing = g.mhrMissing ? String(g.mhrMissing) : null;
    (seen[g.home] = seen[g.home] || []).push({opp: g.away, gd: gd, on: on, missing: missing});
    (seen[g.away] = seen[g.away] || []).push({opp: g.home, gd: -gd, on: on, missing: missing});
  }

  const dayMs = 86400000;
  const days = function(a, b){
    const x = Date.parse(a), y = Date.parse(b);
    return (isNaN(x) || isNaN(y)) ? 0 : Math.max(0, (y - x) / dayMs);
  };

  // Each team's games oldest first, so "games into the season" means what it
  // says, then a weight per game: rust by position, form by date. The weights
  // are worked out over every game before any are dropped, so a team's first
  // game after the snapshot is still its twentieth, not a rusty first.
  const weights = {};
  for(const name in seen){
    const mine = seen[name];
    mine.sort(function(x, y){ return String(x.on).localeCompare(String(y.on)); });
    let w = mine.map(function(m, i){
      const rust = 1 - ADJ_RUST_DROP * Math.exp(-i / ADJ_RUST_GAMES);
      const form = Math.pow(0.5, days(m.on, latest) / ADJ_FORM_HALFLIFE);
      return rust * form;
    });
    // A game marked mhrMissing with this snapshot's date was played before it
    // but is not in MHR's number yet -- MHR counts a game at its next weekly
    // update, not on the day -- so it stays. The marker names one snapshot,
    // so the next capture, which will have counted it, drops it as usual.
    if(name in mgp){
      const keep = mine.map(function(m){ return String(m.on) >= snap || m.missing === snap; });
      seen[name] = mine.filter(function(m, i){ return keep[i]; });
      w = w.filter(function(x, i){ return keep[i]; });
    }
    weights[name] = w;
  }

  for(let pass = 0; pass < ADJ_PASSES; pass++){
    const prev = adj;
    const next = {};
    for(const name in proj){
      const mine = seen[name];
      if(!mine || !mine.length){ next[name] = prior[name]; continue; }
      const w = weights[name];
      let total = 0, sw = 0, sw2 = 0, oppVar = 0;
      for(let i = 0; i < mine.length; i++){
        total += w[i] * (prev[mine[i].opp] + mine[i].gd);
        sw += w[i];
        sw2 += w[i] * w[i];
        oppVar += w[i] * w[i] * band[mine[i].opp] * band[mine[i].opp];
      }
      const implied = total / sw;
      // Kish's effective sample size: five games weighted unevenly are worth
      // fewer than five equal ones, and the variance should say so.
      const neff = (sw * sw) / sw2;

      // What the games are worth. The opponents' own ratings are estimates, so
      // their error rides along in every implied rating and belongs here too.
      const obs = ADJ_NOISE / neff + oppVar / (sw * sw);

      // A prior with tails. Turnover at 14U is annual and the band is fitted on
      // real age-up transitions, so it is right on average -- but it is one
      // number for every team, and some projections are simply wrong. A gap the
      // games plainly contradict is better explained by a wrong projection than
      // by unlucky results, so the prior widens as the gap grows and yields.
      // MHR's own number has already absorbed 20-30 games, so it gets no tail.
      const z = (implied - prior[name]) / band[name];
      const b2 = (name in mgp && snap >= ADJ_MHR_PLAIN_FROM)
        ? band[name] * band[name]
        : band[name] * band[name] * (ADJ_TAIL + z * z) / (ADJ_TAIL + 1);

      next[name] = prior[name] + (b2 / (b2 + obs)) * (implied - prior[name]);
    }
    // Whole pass off the previous pass's values, so the result does not depend
    // on the order teams happen to sit in the file.
    adj = next;
  }

  // `proj` stays the preseason projection, so shift is the whole season's move:
  // MHR's games and ours. `gp` is every game that move rests on.
  const out = {};
  for(const name in proj){
    const played = (seen[name] || []).length + (mgp[name] || 0);
    out[name] = {proj: proj[name], prior: prior[name], band: band[name], adj: adj[name],
                 usa: pool[name].usa, na: pool[name].na,
                 gp: played, shift: adj[name] - proj[name]};
  }
  return out;
}
'''


def with_adjust(script):
    """Both page scripts open with the shared adjustment module."""
    assert script.startswith('<script>'), 'script must open with its tag'
    return script.replace('<script>', '<script>' + ADJUST, 1)


PAGES = [
    ('index.html', 'Boys Hockey Rankings',
     TOURNAMENTS_MAIN, with_adjust(TOURNAMENTS_SCRIPT)),
]


def nav_html(current):
    links = []
    for href, label in NAV:
        here = ' aria-current="page"' if href == current else ''
        links.append('  <a href="{}"{}>{}</a>'.format(href, here, label))
    return '\n'.join(links)


def central_stamp():
    """Masthead date in US Central time, e.g. '1 Sep 2026, 5:57 PM CDT'.

    The DST rule is applied here rather than looked up: Windows ships no
    timezone database, so both `TZ=America/Chicago date` under Git Bash and
    zoneinfo's ZoneInfo('America/Chicago') fail on this machine -- and the
    shell one fails *silently*, falling back to GMT and stamping the page with
    the wrong zone. Central is UTC-6, or UTC-5 between 02:00 on the second
    Sunday in March and 02:00 on the first Sunday in November.
    """
    utc = datetime.now(timezone.utc)

    def nth_sunday(month, n):
        first = datetime(utc.year, month, 1, tzinfo=timezone.utc)
        return first + timedelta(days=(6 - first.weekday()) % 7, weeks=n - 1)

    begins = nth_sunday(3, 2) + timedelta(hours=8)    # 02:00 CST
    ends = nth_sunday(11, 1) + timedelta(hours=7)     # 02:00 CDT
    daylight = begins <= utc < ends

    name = 'CDT' if daylight else 'CST'
    now = utc.astimezone(timezone(timedelta(hours=-5 if daylight else -6), name))

    # Windows strftime has no %-d / %-I, so build the unpadded parts by hand.
    return '{} {} {}, {}:{:02d} {} {}'.format(
        now.day, now.strftime('%b'), now.year,
        (now.hour % 12) or 12, now.minute,
        'AM' if now.hour < 12 else 'PM', name)


def render(title, main, current, script, stamp):
    """__MAIN__ and __SCRIPT__ are filled first: the blocks they carry hold the
    __UPDATED__ and __DATA__ holes that the following two replacements fill."""
    return (SHELL.replace('__TITLE__', title)
                 .replace('__NAV__', nav_html(current))
                 .replace('__MAIN__', main)
                 .replace('__SCRIPT__', script)
                 .replace('__UPDATED__', stamp)
                 .replace('__DATA__', json.dumps(data, separators=(',', ':')))
                 .replace('__BOOKMARKLET__', json.dumps(BOOKMARKLET_URL)))


stamp = central_stamp()

for filename, title, main, script in PAGES:
    page = render(title, main, filename, script, stamp)
    left = sorted(set(re.findall(r'__[A-Z]+__', page)))
    if left:
        raise SystemExit('unfilled placeholder in {}: {}'.format(filename, left))
    out = ROOT / filename
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write(page)
    print('ok', len(page), 'bytes ->', out)

print('stamp:', stamp)
