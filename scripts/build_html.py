#!/usr/bin/env python3
"""
Build season_predictions.html from latest.json
"""
import json
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
OUT_FILE  = Path(__file__).parent.parent / "season_predictions.html"
LATEST    = DATA_DIR / "latest.json"
SCHEDULE  = DATA_DIR / "schedule.json"

def build():
    with open(LATEST) as f:
        latest = json.load(f)
    
    teams_json   = json.dumps(latest["teams"])
    history_json = json.dumps(latest["history"])
    preds_json   = json.dumps(latest["predictions"])
    generated    = latest["generated"]
    games_played = latest["games_played"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SBMSA PeeWee NL — Season Predictions</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root {{
  --ink:#0e0f11; --paper:#f5f2eb; --cream:#ede9df; --field:#2d5a27;
  --field-light:#3d7a35; --chalk:#f5f2eb; --dirt:#c4862a;
  --dirt-light:#e8a84a; --sky:#1a3a5c; --muted:#7a7060;
  --border:#d4cfc4; --pre-color:#2d5a9a; --act-color:#c4862a;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html{{scroll-behavior:smooth;}}
body{{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif;font-size:14px;line-height:1.5;}}

/* HEADER */
.site-header{{background:var(--field);position:relative;overflow:hidden;}}
.hd1{{position:absolute;top:-30px;right:-30px;width:180px;height:180px;background:var(--field-light);transform:rotate(45deg);opacity:.4;}}
.hd2{{position:absolute;bottom:-20px;left:60px;width:100px;height:100px;background:var(--field-light);transform:rotate(45deg);opacity:.25;}}
.header-inner{{position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:28px 24px 20px;display:flex;align-items:flex-end;justify-content:space-between;flex-wrap:wrap;gap:12px;}}
.header-title{{font-family:'Bebas Neue',sans-serif;font-size:clamp(38px,7vw,72px);color:var(--chalk);letter-spacing:2px;line-height:.9;}}
.header-sub{{font-size:11px;color:rgba(245,242,235,.65);letter-spacing:3px;text-transform:uppercase;margin-top:6px;font-family:'DM Mono',monospace;}}
.header-meta{{text-align:right;}}
.header-badge{{background:var(--dirt);color:var(--chalk);font-family:'Bebas Neue',sans-serif;font-size:13px;letter-spacing:2px;padding:6px 14px;border-radius:3px;display:inline-block;}}
.header-updated{{font-size:10px;color:rgba(245,242,235,.5);font-family:'DM Mono',monospace;margin-top:6px;}}

/* NAV */
.nav-strip{{background:var(--ink);border-bottom:3px solid var(--dirt);position:sticky;top:0;z-index:100;}}
.nav-inner{{max-width:1100px;margin:0 auto;padding:0 24px;display:flex;align-items:center;overflow-x:auto;}}
.nav-btn{{font-family:'Bebas Neue',sans-serif;font-size:15px;letter-spacing:2px;color:rgba(245,242,235,.55);padding:12px 18px;border:none;background:none;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-3px;transition:color .2s,border-color .2s;white-space:nowrap;}}
.nav-btn:hover{{color:var(--chalk);}}
.nav-btn.active{{color:var(--dirt-light);border-bottom-color:var(--dirt-light);}}

/* MAIN */
.main{{max-width:1100px;margin:0 auto;padding:28px 24px 60px;}}
.view{{display:none;}}.view.active{{display:block;}}
.section-title{{font-family:'Bebas Neue',sans-serif;font-size:28px;letter-spacing:3px;color:var(--field);border-bottom:2px solid var(--border);padding-bottom:8px;margin-bottom:20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;}}
.pill{{font-size:11px;letter-spacing:1px;background:var(--cream);color:var(--muted);padding:3px 10px;border-radius:20px;font-family:'DM Sans',sans-serif;font-weight:500;margin-top:4px;}}

/* LEGEND */
.legend-row{{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap;align-items:center;}}
.legend-dot{{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:5px;}}
.legend-pre{{background:var(--pre-color);}}
.legend-act{{background:var(--act-color);}}
.legend-label{{font-size:12px;color:var(--muted);font-family:'DM Mono',monospace;}}

/* DIV TABS */
.div-tabs{{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap;}}
.div-tab{{font-family:'Bebas Neue',sans-serif;font-size:14px;letter-spacing:2px;padding:7px 18px;border-radius:3px;border:2px solid var(--border);background:var(--cream);color:var(--muted);cursor:pointer;transition:all .15s;}}
.div-tab:hover{{border-color:var(--field);color:var(--field);}}
.div-tab.active{{background:var(--field);color:var(--chalk);border-color:var(--field);}}

/* TABLES */
.standings-table{{width:100%;border-collapse:collapse;margin-bottom:40px;}}
.standings-table thead tr{{background:var(--ink);}}
.standings-table th{{font-family:'DM Mono',monospace;font-size:10px;letter-spacing:2px;text-transform:uppercase;color:rgba(245,242,235,.6);padding:10px 12px;text-align:left;}}
.standings-table th.r{{text-align:right;}}
.standings-table tbody tr{{border-bottom:1px solid var(--border);cursor:pointer;transition:background .12s;}}
.standings-table tbody tr:hover{{background:var(--cream);}}
.standings-table td{{padding:10px 12px;}}
.standings-table td.r{{text-align:right;}}
.rank-num{{font-family:'Bebas Neue',sans-serif;font-size:20px;color:var(--border);width:28px;display:inline-block;text-align:center;}}
.rank-1 .rank-num{{color:var(--dirt);}} .rank-2 .rank-num{{color:#888;}} .rank-3 .rank-num{{color:#a07040;}}
.team-name{{font-weight:600;font-size:15px;}}
.team-div-lbl{{font-size:10px;color:var(--muted);letter-spacing:1px;text-transform:uppercase;font-family:'DM Mono',monospace;}}
.est-badge{{display:inline-block;font-size:9px;letter-spacing:1px;background:#f0e8d0;color:#a07040;padding:1px 6px;border-radius:3px;margin-left:6px;font-family:'DM Mono',monospace;vertical-align:middle;}}
.ps-bar-wrap{{display:flex;align-items:center;gap:6px;}}
.ps-bar-bg{{flex:1;height:5px;background:var(--border);border-radius:2px;overflow:hidden;min-width:50px;}}
.ps-bar{{height:100%;border-radius:2px;}}
.ps-val{{font-family:'DM Mono',monospace;font-size:12px;color:var(--muted);width:36px;text-align:right;}}
.expw-val{{font-family:'Bebas Neue',sans-serif;font-size:19px;color:var(--ink);}}
.expw-denom{{font-size:11px;color:var(--muted);}}
.record-val{{font-family:'DM Mono',monospace;font-size:12px;color:var(--muted);}}

/* SCHEDULE */
.schedule-filters{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;align-items:center;}}
.filter-label{{font-family:'DM Mono',monospace;font-size:11px;letter-spacing:1px;color:var(--muted);text-transform:uppercase;}}
.filter-select{{font-family:'DM Sans',sans-serif;font-size:13px;border:1px solid var(--border);background:var(--cream);color:var(--ink);padding:6px 10px;border-radius:3px;cursor:pointer;}}
.sched-date-group{{margin-bottom:24px;}}
.sched-date-hdr{{font-family:'Bebas Neue',sans-serif;font-size:18px;letter-spacing:3px;color:var(--sky);margin-bottom:10px;display:flex;align-items:center;gap:10px;}}
.sched-date-hdr::after{{content:'';flex:1;height:1px;background:var(--border);}}
.game-card{{background:white;border:1px solid var(--border);border-radius:4px;padding:12px 16px;margin-bottom:6px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;}}
.game-card.played{{border-left:3px solid var(--field);}}
.div-tag{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;color:white;padding:2px 7px;border-radius:2px;width:58px;text-align:center;flex-shrink:0;}}
.div-east{{background:#1a4a7a;}} .div-central{{background:#2d5a27;}} .div-west{{background:#7a3a1a;}}
.game-teams{{flex:1;min-width:180px;}}
.game-away,.game-home{{font-size:14px;font-weight:500;}}
.game-vs{{font-size:10px;color:var(--muted);margin:1px 0;}}
.game-result{{font-family:'Bebas Neue',sans-serif;font-size:22px;color:var(--ink);letter-spacing:1px;flex-shrink:0;min-width:60px;text-align:center;}}
.wp-cols{{display:flex;gap:16px;flex-wrap:wrap;}}
.wp-col{{min-width:120px;}}
.wp-col-label{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;}}
.wp-col-label.pre{{color:var(--pre-color);}} .wp-col-label.act{{color:var(--act-color);}}
.wp-row{{display:flex;align-items:center;gap:5px;margin-bottom:3px;}}
.wp-name{{font-size:11px;color:var(--muted);width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}}
.wp-bar-bg{{flex:1;height:3px;background:var(--border);border-radius:2px;overflow:hidden;}}
.wp-bar-fill{{height:100%;border-radius:2px;}}
.wp-pct{{font-family:'DM Mono',monospace;font-size:11px;font-weight:500;width:32px;text-align:right;}}
.fav-badge{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:1px;background:#fff8e8;color:var(--dirt);border:1px solid var(--dirt-light);padding:1px 6px;border-radius:2px;flex-shrink:0;}}
.tossup-badge{{font-family:'DM Mono',monospace;font-size:9px;background:#f0f0f0;color:#888;border:1px solid #ccc;padding:1px 6px;border-radius:2px;flex-shrink:0;}}
.sched-meta{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);text-align:right;flex-shrink:0;}}

/* MODAL */
.modal-backdrop{{display:none;position:fixed;inset:0;background:rgba(14,15,17,.75);z-index:200;align-items:center;justify-content:center;padding:20px;}}
.modal-backdrop.open{{display:flex;}}
.modal{{background:var(--paper);border-radius:6px;width:100%;max-width:720px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.4);}}
.modal-header{{background:var(--field);padding:20px 24px 16px;display:flex;justify-content:space-between;align-items:flex-start;}}
.modal-team-name{{font-family:'Bebas Neue',sans-serif;font-size:32px;letter-spacing:2px;color:var(--chalk);line-height:1;}}
.modal-div-label{{font-size:10px;letter-spacing:2px;color:rgba(245,242,235,.6);text-transform:uppercase;font-family:'DM Mono',monospace;margin-top:4px;}}
.modal-close{{background:none;border:none;color:rgba(245,242,235,.7);font-size:22px;cursor:pointer;padding:0;line-height:1;}}
.modal-close:hover{{color:var(--chalk);}}
.modal-stats{{display:grid;grid-template-columns:repeat(4,1fr);border-bottom:1px solid var(--border);}}
.modal-stat{{padding:14px 16px;border-right:1px solid var(--border);text-align:center;}}
.modal-stat:last-child{{border-right:none;}}
.modal-stat-val{{font-family:'Bebas Neue',sans-serif;font-size:26px;color:var(--ink);line-height:1;}}
.modal-stat-val.pre{{color:var(--pre-color);}} .modal-stat-val.act{{color:var(--act-color);}}
.modal-stat-lbl{{font-size:9px;letter-spacing:2px;text-transform:uppercase;color:var(--muted);font-family:'DM Mono',monospace;margin-top:3px;}}
.modal-body{{padding:20px 24px;}}
.modal-sub-title{{font-family:'Bebas Neue',sans-serif;font-size:16px;letter-spacing:2px;color:var(--field);margin-bottom:12px;}}

/* CHART */
.chart-wrap{{background:white;border:1px solid var(--border);border-radius:4px;padding:16px;margin-bottom:20px;}}
.chart-wrap canvas{{max-height:280px;}}

/* GAME ROWS */
.game-row{{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border);}}
.game-row:last-child{{border-bottom:none;}}
.gr-date{{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);width:70px;flex-shrink:0;}}
.gr-ha{{font-family:'Bebas Neue',sans-serif;font-size:12px;letter-spacing:1px;width:36px;flex-shrink:0;text-align:center;padding:2px 4px;border-radius:2px;}}
.ha-home{{background:var(--field);color:var(--chalk);}} .ha-away{{background:var(--cream);color:var(--muted);border:1px solid var(--border);}}
.gr-opp{{flex:1;font-weight:500;font-size:13px;}}
.gr-result{{font-family:'Bebas Neue',sans-serif;font-size:16px;width:50px;text-align:center;flex-shrink:0;}}
.gr-result.win{{color:#2d7a3a;}} .gr-result.loss{{color:#b02020;}} .gr-result.tie{{color:var(--muted);}}
.gr-wp-pre,.gr-wp-act{{font-family:'DM Mono',monospace;font-size:11px;font-weight:500;width:40px;text-align:right;flex-shrink:0;}}
.gr-wp-pre{{color:var(--pre-color);}} .gr-wp-act{{color:var(--act-color);}}
.gr-wp-lbl{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:1px;color:var(--muted);width:28px;text-align:right;flex-shrink:0;}}
.gr-loc{{font-size:10px;color:var(--muted);width:90px;flex-shrink:0;text-align:right;display:none;}}
@media(min-width:600px){{.gr-loc{{display:block;}}}}
@media(max-width:480px){{.modal-stats{{grid-template-columns:repeat(2,1fr)}}}}

/* RANKINGS DUAL */
.dual-ps-wrap{{display:flex;flex-direction:column;gap:3px;min-width:150px;}}
.dual-bar-row{{display:flex;align-items:center;gap:5px;}}
.dual-bar-lbl{{font-family:'DM Mono',monospace;font-size:9px;width:24px;letter-spacing:1px;}}
.dual-bar-lbl.pre{{color:var(--pre-color);}} .dual-bar-lbl.act{{color:var(--act-color);}}
.dual-bar-bg{{flex:1;height:4px;background:var(--border);border-radius:2px;overflow:hidden;}}
.dual-bar-fill{{height:100%;border-radius:2px;}}
.dual-bar-val{{font-family:'DM Mono',monospace;font-size:11px;width:36px;text-align:right;}}
</style>
</head>
<body>

<header class="site-header">
  <div class="hd1"></div><div class="hd2"></div>
  <div class="header-inner">
    <div>
      <div class="header-title">Season<br>Predictions</div>
      <div class="header-sub">SBMSA · PeeWee NL · 2026 Regular Season</div>
    </div>
    <div class="header-meta">
      <div class="header-badge">{games_played} Games Played</div>
      <div class="header-updated">Updated {generated}</div>
    </div>
  </div>
</header>

<nav class="nav-strip">
  <div class="nav-inner">
    <button class="nav-btn active" onclick="showView('standings',this)">Standings</button>
    <button class="nav-btn" onclick="showView('schedule',this)">Schedule</button>
    <button class="nav-btn" onclick="showView('rankings',this)">Power Rankings</button>
    <button class="nav-btn" onclick="showView('ratings',this)">Ratings History</button>
  </div>
</nav>

<main class="main">

<!-- STANDINGS -->
<div id="view-standings" class="view active">
  <div class="section-title">Predicted Standings <span class="pill">Remaining games · Both models</span></div>
  <div class="legend-row">
    <span><span class="legend-dot legend-pre"></span><span class="legend-label">PRESEASON model (SOS-weighted, frozen)</span></span>
    <span><span class="legend-dot legend-act"></span><span class="legend-label">ACTUAL model (season results only)</span></span>
  </div>
  <div class="div-tabs">
    <button class="div-tab active" onclick="filterDiv('All',this)">All Divisions</button>
    <button class="div-tab" onclick="filterDiv('Pee Wee Central',this)">Central</button>
    <button class="div-tab" onclick="filterDiv('Pee Wee East',this)">East</button>
    <button class="div-tab" onclick="filterDiv('Pee Wee West',this)">West</button>
  </div>
  <table class="standings-table">
    <thead><tr>
      <th style="width:36px">#</th><th>Team</th>
      <th class="r" style="min-width:160px">Dual Power Score</th>
      <th class="r">Record</th>
      <th class="r" style="color:var(--pre-color)">Pre ExpW</th>
      <th class="r" style="color:var(--act-color)">Act ExpW</th>
      <th class="r">GP</th>
    </tr></thead>
    <tbody id="standings-body"></tbody>
  </table>
</div>

<!-- SCHEDULE -->
<div id="view-schedule" class="view">
  <div class="section-title">Full Schedule <span class="pill">225 games · dual predictions</span></div>
  <div class="schedule-filters">
    <span class="filter-label">Division:</span>
    <select class="filter-select" id="sched-div-filter" onchange="renderSchedule()">
      <option value="All">All Divisions</option>
      <option value="Pee Wee Central">Central</option>
      <option value="Pee Wee East">East</option>
      <option value="Pee Wee West">West</option>
    </select>
    <span class="filter-label" style="margin-left:10px">Team:</span>
    <select class="filter-select" id="sched-team-filter" onchange="renderSchedule()">
      <option value="All">All Teams</option>
    </select>
    <span class="filter-label" style="margin-left:10px">Status:</span>
    <select class="filter-select" id="sched-status-filter" onchange="renderSchedule()">
      <option value="All">All Games</option>
      <option value="played">Played</option>
      <option value="upcoming">Upcoming</option>
    </select>
  </div>
  <div id="schedule-body"></div>
</div>

<!-- POWER RANKINGS -->
<div id="view-rankings" class="view">
  <div class="section-title">Power Rankings <span class="pill">Preseason frozen vs Season actual</span></div>
  <div class="legend-row">
    <span><span class="legend-dot legend-pre"></span><span class="legend-label">PRESEASON (top bar)</span></span>
    <span><span class="legend-dot legend-act"></span><span class="legend-label">ACTUAL season results (bottom bar)</span></span>
  </div>
  <div class="div-tabs">
    <button class="div-tab active" onclick="filterRankDiv('All',this)">All</button>
    <button class="div-tab" onclick="filterRankDiv('Pee Wee Central',this)">Central</button>
    <button class="div-tab" onclick="filterRankDiv('Pee Wee East',this)">East</button>
    <button class="div-tab" onclick="filterRankDiv('Pee Wee West',this)">West</button>
  </div>
  <table class="standings-table">
    <thead><tr>
      <th style="width:36px">#</th><th>Team</th><th>Division</th>
      <th class="r" style="min-width:160px">Power Scores</th>
      <th class="r">Record</th>
    </tr></thead>
    <tbody id="rankings-body"></tbody>
  </table>
</div>

<!-- RATINGS HISTORY -->
<div id="view-ratings" class="view">
  <div class="section-title">Ratings Over Time <span class="pill">Click a team to view their chart</span></div>
  <div class="legend-row">
    <span><span class="legend-dot legend-pre"></span><span class="legend-label">Preseason rating (frozen line)</span></span>
    <span><span class="legend-dot legend-act"></span><span class="legend-label">Actual season rating (updates nightly)</span></span>
  </div>
  <div class="div-tabs" id="ratings-div-tabs">
    <button class="div-tab active" onclick="filterRatingsDiv('All',this)">All</button>
    <button class="div-tab" onclick="filterRatingsDiv('Pee Wee Central',this)">Central</button>
    <button class="div-tab" onclick="filterRatingsDiv('Pee Wee East',this)">East</button>
    <button class="div-tab" onclick="filterRatingsDiv('Pee Wee West',this)">West</button>
  </div>
  <div style="margin-bottom:16px;">
    <select class="filter-select" id="ratings-team-select" onchange="showTeamRating(this.value)">
      <option value="">— Select a team —</option>
    </select>
  </div>
  <div class="chart-wrap" id="ratings-chart-wrap" style="display:none">
    <canvas id="ratings-chart"></canvas>
  </div>
  <div id="ratings-team-list"></div>
</div>

</main>

<!-- MODAL -->
<div class="modal-backdrop" id="modal-backdrop" onclick="closeModal(event)">
  <div class="modal">
    <div class="modal-header">
      <div>
        <div class="modal-team-name" id="modal-name"></div>
        <div class="modal-div-label" id="modal-div"></div>
      </div>
      <button class="modal-close" onclick="closeModalBtn()">✕</button>
    </div>
    <div class="modal-stats">
      <div class="modal-stat"><div class="modal-stat-val" id="modal-record"></div><div class="modal-stat-lbl">Record</div></div>
      <div class="modal-stat"><div class="modal-stat-val pre" id="modal-pre-ps"></div><div class="modal-stat-lbl">Pre Score</div></div>
      <div class="modal-stat"><div class="modal-stat-val act" id="modal-act-ps"></div><div class="modal-stat-lbl">Act Score</div></div>
      <div class="modal-stat"><div class="modal-stat-val" id="modal-gp"></div><div class="modal-stat-lbl">GP / Total</div></div>
    </div>
    <div class="modal-body">
      <div class="chart-wrap" style="margin-bottom:20px">
        <canvas id="modal-chart"></canvas>
      </div>
      <div class="modal-sub-title">Game Log</div>
      <div id="modal-games"></div>
    </div>
  </div>
</div>

<script>
const TEAMS   = {teams_json};
const PREDS   = {preds_json};
const HISTORY = {history_json};

let modalChart = null;
let ratingsChart = null;

function wpColor(wp){{if(wp>=.65)return'#2d7a3a';if(wp>=.55)return'#5a9a3a';if(wp>=.45)return'#c4862a';if(wp>=.35)return'#c05020';return'#b02020';}}
function psBarColorPre(ps){{if(ps>=.75)return'#1a3a7a';if(ps>=.50)return'#2d5a9a';if(ps>=.25)return'#5a7aba';return'#8aaad0';}}
function psBarColorAct(ps){{if(ps>=.75)return'#8a4a00';if(ps>=.50)return'#c4862a';if(ps>=.25)return'#e8a84a';return'#f0c878';}}
function divClass(d){{if(d.includes('East'))return'div-east';if(d.includes('Central'))return'div-central';return'div-west';}}
function divShort(d){{if(d.includes('East'))return'EAST';if(d.includes('Central'))return'CNTRL';return'WEST';}}
function parseDateKey(d){{const c=d.replace(/Mon |Tue |Wed |Thu |Fri |Sat |Sun /,'').split('/').map(Number);return c[0]*100+c[1];}}

// ── STANDINGS ──
let stDiv='All';
function filterDiv(div,el){{stDiv=div;document.querySelectorAll('.div-tab').forEach(b=>b.classList.remove('active'));el.classList.add('active');renderStandings();}}
function renderStandings(){{
  let teams=[...TEAMS].filter(t=>stDiv==='All'||t.div===stDiv);
  teams.sort((a,b)=>b.wins-a.wins||b.exp_w_pre-a.exp_w_pre);
  document.getElementById('standings-body').innerHTML=teams.map((t,i)=>{{
    const rc=i===0?'rank-1':i===1?'rank-2':i===2?'rank-3':'';
    const nd=!t.has_preseason?'<span class="est-badge">EST</span>':'';
    return`<tr class="${{rc}}" onclick="openTeam('${{t.team.replace(/'/g,"\\'")}}')">
      <td><span class="rank-num">${{i+1}}</span></td>
      <td><div class="team-name">${{t.team}}${{nd}}</div><div class="team-div-lbl">${{divShort(t.div)}}</div></td>
      <td class="r">
        <div class="dual-ps-wrap">
          <div class="dual-bar-row"><span class="dual-bar-lbl pre">PRE</span><div class="dual-bar-bg"><div class="dual-bar-fill" style="width:${{Math.round(t.pre_ps*100)}}%;background:${{psBarColorPre(t.pre_ps)}}"></div></div><span class="dual-bar-val" style="color:var(--pre-color)">${{t.pre_ps.toFixed(3)}}</span></div>
          <div class="dual-bar-row"><span class="dual-bar-lbl act">ACT</span><div class="dual-bar-bg"><div class="dual-bar-fill" style="width:${{Math.round(t.act_ps*100)}}%;background:${{psBarColorAct(t.act_ps)}}"></div></div><span class="dual-bar-val" style="color:var(--act-color)">${{t.act_ps.toFixed(3)}}</span></div>
        </div>
      </td>
      <td class="r"><span class="record-val">${{t.record}}</span></td>
      <td class="r" style="color:var(--pre-color);font-family:'Bebas Neue',sans-serif;font-size:17px">${{t.exp_w_pre}}<span style="font-size:11px;color:var(--muted)">/${{t.gp_total-t.gp}}</span></td>
      <td class="r" style="color:var(--act-color);font-family:'Bebas Neue',sans-serif;font-size:17px">${{t.exp_w_act}}<span style="font-size:11px;color:var(--muted)">/${{t.gp_total-t.gp}}</span></td>
      <td class="r" style="color:var(--muted);font-family:'DM Mono',monospace;font-size:12px">${{t.gp}}/${{t.gp_total}}</td>
    </tr>`;
  }}).join('');
}}

// ── MODAL ──
function openTeam(name){{
  const t=TEAMS.find(x=>x.team===name);if(!t)return;
  document.getElementById('modal-name').textContent=t.team;
  document.getElementById('modal-div').textContent=t.div.toUpperCase();
  document.getElementById('modal-record').textContent=t.record;
  document.getElementById('modal-pre-ps').textContent=t.pre_ps.toFixed(3);
  document.getElementById('modal-act-ps').textContent=t.act_ps.toFixed(3);
  document.getElementById('modal-gp').textContent=`${{t.gp}}/${{t.gp_total}}`;

  // Chart
  if(modalChart){{modalChart.destroy();modalChart=null;}}
  const dates=HISTORY.map(h=>h.date);
  const preData=HISTORY.map(h=>h.pre_ps[name]||null);
  const actData=HISTORY.map(h=>h.act_ps[name]||null);
  const ctx=document.getElementById('modal-chart').getContext('2d');
  modalChart=new Chart(ctx,{{
    type:'line',
    data:{{
      labels:dates,
      datasets:[
        {{label:'Preseason Rating',data:preData,borderColor:'#2d5a9a',backgroundColor:'rgba(45,90,154,.1)',tension:.3,pointRadius:3,fill:true}},
        {{label:'Actual Rating',   data:actData, borderColor:'#c4862a',backgroundColor:'rgba(196,134,42,.1)',tension:.3,pointRadius:3,fill:true}},
      ]
    }},
    options:{{responsive:true,plugins:{{legend:{{labels:{{font:{{family:"DM Sans"}}}}}}}},scales:{{y:{{min:0,max:1,ticks:{{font:{{family:"DM Mono"}}}}}},x:{{ticks:{{font:{{family:"DM Mono"}},maxRotation:45}}}}}}}}
  }});

  // Games
  const sorted=[...t.games].sort((a,b)=>parseDateKey(a.date)-parseDateKey(b.date));
  document.getElementById('modal-games').innerHTML=sorted.map(g=>{{
    let result='',rc='';
    if(g.played){{
      const win=g.my_score>g.opp_score, loss=g.my_score<g.opp_score;
      result=`${{g.my_score}}-${{g.opp_score}}`;
      rc=win?'win':loss?'loss':'tie';
    }}
    return`<div class="game-row">
      <span class="gr-date">${{g.date}}</span>
      <span class="gr-ha ${{g.ha==='Home'?'ha-home':'ha-away'}}">${{g.ha}}</span>
      <span class="gr-opp">vs ${{g.opp}}</span>
      ${{g.played?`<span class="gr-result ${{rc}}">${{result}}</span>`:'<span class="gr-result" style="color:var(--border)">—</span>'}}
      <span class="gr-wp-lbl">PRE</span><span class="gr-wp-pre">${{(g.pre_wp*100).toFixed(0)}}%</span>
      <span class="gr-wp-lbl">ACT</span><span class="gr-wp-act">${{(g.act_wp*100).toFixed(0)}}%</span>
      <span class="gr-loc">${{g.loc}}</span>
    </div>`;
  }}).join('');
  document.getElementById('modal-backdrop').classList.add('open');
}}
function closeModal(e){{if(e.target===document.getElementById('modal-backdrop'))document.getElementById('modal-backdrop').classList.remove('open');}}
function closeModalBtn(){{document.getElementById('modal-backdrop').classList.remove('open');}}

// ── SCHEDULE ──
function populateTeamFilter(){{
  const sel=document.getElementById('sched-team-filter');
  [...TEAMS].sort((a,b)=>a.team.localeCompare(b.team)).forEach(t=>{{
    const o=document.createElement('option');o.value=t.team;o.textContent=t.team;sel.appendChild(o);
  }});
}}
function renderSchedule(){{
  const df=document.getElementById('sched-div-filter').value;
  const tf=document.getElementById('sched-team-filter').value;
  const sf=document.getElementById('sched-status-filter').value;
  let filtered=PREDS.filter(g=>
    (df==='All'||g.div===df)&&
    (tf==='All'||g.away===tf||g.home===tf)&&
    (sf==='All'||(sf==='played'&&g.played)||(sf==='upcoming'&&!g.played))
  );
  const byDate={{}};
  filtered.forEach(g=>{{if(!byDate[g.date])byDate[g.date]=[];byDate[g.date].push(g);}});
  const dates=Object.keys(byDate).sort((a,b)=>parseDateKey(a)-parseDateKey(b));
  if(!filtered.length){{document.getElementById('schedule-body').innerHTML='<p style="color:var(--muted);padding:20px 0">No games match filters.</p>';return;}}
  document.getElementById('schedule-body').innerHTML=dates.map(date=>{{
    const cards=byDate[date].map(g=>{{
      const diff=Math.abs(g.pre_awp-g.pre_hwp);
      const fav=diff<.08?'<span class="tossup-badge">TOSS-UP</span>'
        :g.pre_awp>g.pre_hwp?`<span class="fav-badge">FAV: ${{g.away.split(' ').pop()}}</span>`
        :`<span class="fav-badge">FAV: ${{g.home.split(' ').pop()}}</span>`;
      const resultHtml=g.played?`<div class="game-result">${{g.away_score}}-${{g.home_score}}</div>`:'';
      return`<div class="game-card${{g.played?' played':''}}">
        <span class="div-tag ${{divClass(g.div)}}">${{divShort(g.div)}}</span>
        <div class="game-teams">
          <div class="game-away">↑ ${{g.away}}</div>
          <div class="game-vs">@ home:</div>
          <div class="game-home">⌂ ${{g.home}}</div>
        </div>
        ${{resultHtml}}
        <div class="wp-cols">
          <div class="wp-col">
            <div class="wp-col-label pre">Preseason</div>
            <div class="wp-row"><span class="wp-name">${{g.away}}</span><div class="wp-bar-bg"><div class="wp-bar-fill" style="width:${{Math.round(g.pre_awp*100)}}%;background:#2d5a9a"></div></div><span class="wp-pct" style="color:#2d5a9a">${{(g.pre_awp*100).toFixed(0)}}%</span></div>
            <div class="wp-row"><span class="wp-name">${{g.home}}</span><div class="wp-bar-bg"><div class="wp-bar-fill" style="width:${{Math.round(g.pre_hwp*100)}}%;background:#2d5a9a"></div></div><span class="wp-pct" style="color:#2d5a9a">${{(g.pre_hwp*100).toFixed(0)}}%</span></div>
          </div>
          <div class="wp-col">
            <div class="wp-col-label act">Actual</div>
            <div class="wp-row"><span class="wp-name">${{g.away}}</span><div class="wp-bar-bg"><div class="wp-bar-fill" style="width:${{Math.round(g.act_awp*100)}}%;background:#c4862a"></div></div><span class="wp-pct" style="color:#c4862a">${{(g.act_awp*100).toFixed(0)}}%</span></div>
            <div class="wp-row"><span class="wp-name">${{g.home}}</span><div class="wp-bar-bg"><div class="wp-bar-fill" style="width:${{Math.round(g.act_hwp*100)}}%;background:#c4862a"></div></div><span class="wp-pct" style="color:#c4862a">${{(g.act_hwp*100).toFixed(0)}}%</span></div>
          </div>
        </div>
        ${{fav}}
        <div class="sched-meta">${{g.time}}</div>
      </div>`;
    }}).join('');
    return`<div class="sched-date-group"><div class="sched-date-hdr">${{date}}</div>${{cards}}</div>`;
  }}).join('');
}}

// ── RANKINGS ──
let rkDiv='All';
function filterRankDiv(div,el){{rkDiv=div;document.querySelectorAll('#view-rankings .div-tab').forEach(b=>b.classList.remove('active'));el.classList.add('active');renderRankings();}}
function renderRankings(){{
  let teams=[...TEAMS].filter(t=>rkDiv==='All'||t.div===rkDiv);
  teams.sort((a,b)=>b.pre_ps-a.pre_ps);
  document.getElementById('rankings-body').innerHTML=teams.map((t,i)=>{{
    const rc=i===0?'rank-1':i===1?'rank-2':i===2?'rank-3':'';
    const nd=!t.has_preseason?'<span class="est-badge">EST</span>':'';
    return`<tr class="${{rc}}" onclick="openTeam('${{t.team.replace(/'/g,"\\'")}}')">
      <td><span class="rank-num">${{i+1}}</span></td>
      <td><div class="team-name">${{t.team}}${{nd}}</div></td>
      <td style="color:var(--muted);font-size:12px">${{t.div}}</td>
      <td class="r">
        <div class="dual-ps-wrap">
          <div class="dual-bar-row"><span class="dual-bar-lbl pre">PRE</span><div class="dual-bar-bg"><div class="dual-bar-fill" style="width:${{Math.round(t.pre_ps*100)}}%;background:${{psBarColorPre(t.pre_ps)}}"></div></div><span class="dual-bar-val" style="color:var(--pre-color)">${{t.pre_ps.toFixed(3)}}</span></div>
          <div class="dual-bar-row"><span class="dual-bar-lbl act">ACT</span><div class="dual-bar-bg"><div class="dual-bar-fill" style="width:${{Math.round(t.act_ps*100)}}%;background:${{psBarColorAct(t.act_ps)}}"></div></div><span class="dual-bar-val" style="color:var(--act-color)">${{t.act_ps.toFixed(3)}}</span></div>
        </div>
      </td>
      <td class="r"><span class="record-val">${{t.record}}</span></td>
    </tr>`;
  }}).join('');
}}

// ── RATINGS HISTORY ──
let ratDiv='All';
function filterRatingsDiv(div,el){{
  ratDiv=div;
  document.querySelectorAll('#ratings-div-tabs .div-tab').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  populateRatingsSelect();
  document.getElementById('ratings-chart-wrap').style.display='none';
  document.getElementById('ratings-team-list').innerHTML='';
}}
function populateRatingsSelect(){{
  const sel=document.getElementById('ratings-team-select');
  sel.innerHTML='<option value="">— Select a team —</option>';
  let teams=[...TEAMS].filter(t=>ratDiv==='All'||t.div===ratDiv).sort((a,b)=>a.team.localeCompare(b.team));
  teams.forEach(t=>{{const o=document.createElement('option');o.value=t.team;o.textContent=t.team;sel.appendChild(o);}});
}}
function showTeamRating(name){{
  if(!name){{document.getElementById('ratings-chart-wrap').style.display='none';return;}}
  document.getElementById('ratings-chart-wrap').style.display='block';
  const dates=HISTORY.map(h=>h.date);
  const preData=HISTORY.map(h=>h.pre_ps[name]??null);
  const actData=HISTORY.map(h=>h.act_ps[name]??null);
  if(ratingsChart){{ratingsChart.destroy();ratingsChart=null;}}
  const ctx=document.getElementById('ratings-chart').getContext('2d');
  ratingsChart=new Chart(ctx,{{
    type:'line',
    data:{{
      labels:dates,
      datasets:[
        {{label:'Preseason Rating',data:preData,borderColor:'#2d5a9a',backgroundColor:'rgba(45,90,154,.15)',tension:.3,pointRadius:4,fill:true,borderWidth:2}},
        {{label:'Actual Rating',   data:actData, borderColor:'#c4862a',backgroundColor:'rgba(196,134,42,.15)',tension:.3,pointRadius:4,fill:true,borderWidth:2}},
      ]
    }},
    options:{{
      responsive:true,
      plugins:{{
        title:{{display:true,text:name+' — Rating History',font:{{family:'Bebas Neue',size:18}},color:'#2d5a27'}},
        legend:{{labels:{{font:{{family:'DM Sans'}},color:'#0e0f11'}}}}
      }},
      scales:{{
        y:{{min:0,max:1,title:{{display:true,text:'Power Score',font:{{family:'DM Mono'}}}},ticks:{{font:{{family:'DM Mono'}}}}}},
        x:{{ticks:{{font:{{family:'DM Mono'}},maxRotation:45}}}}
      }}
    }}
  }});
}}

// ── NAV ──
function showView(name,el){{
  document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('view-'+name).classList.add('active');
  el.classList.add('active');
}}

// ── INIT ──
renderStandings();
populateTeamFilter();
renderSchedule();
renderRankings();
populateRatingsSelect();
</script>
</body>
</html>"""

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Built: {OUT_FILE} ({len(html):,} bytes)")

if __name__ == "__main__":
    build()
