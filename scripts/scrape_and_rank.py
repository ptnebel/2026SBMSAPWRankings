#!/usr/bin/env python3
"""
SBMSA PeeWee NL - Nightly scraper + dual ranking engine
Outputs:
  data/results.json        - all scraped game results
  data/ratings_history.json - daily snapshot of both rating sets
  data/latest.json          - current ratings + predictions for HTML
"""

import json, re, os, sys, datetime
from collections import defaultdict
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing dependencies...")
    os.system("pip install requests beautifulsoup4 --break-system-packages -q")
    import requests
    from bs4 import BeautifulSoup

# ── CONFIG ──────────────────────────────────────────────────────────────────
DIVISION_URLS = {
    "Pee Wee East":    "https://sbmsa.net/schedule/676209/pee-wee-east",
    "Pee Wee Central": "https://sbmsa.net/schedule/676210/pee-wee-central",
    "Pee Wee West":    "https://sbmsa.net/schedule/676211/pee-wee-west",
}

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

RESULTS_FILE        = DATA_DIR / "results.json"
HISTORY_FILE        = DATA_DIR / "ratings_history.json"
LATEST_FILE         = DATA_DIR / "latest.json"
SCHEDULE_FILE       = Path(__file__).parent.parent / "data" / "schedule.json"

TODAY = datetime.date.today().isoformat()

# ── PRESEASON POWER SCORES (frozen) ─────────────────────────────────────────
PRESEASON_PS = {
    "Durham Bulls": 1.0, "Chili Peppers": 0.9403, "Red Sox": 0.9129,
    "Prospect - White": 0.9032, "Chihuahuas": 0.9022,
    "Rockies City Connect": 0.8502, "Savannah Bananas": 0.8365,
    "Nationals": 0.8147, "Naturals": 0.7569, "Oregon Ducks": 0.7504,
    "Coconuts": 0.728, "Yankees": 0.7191, "Detroit Tigers": 0.7146,
    "Lake Monsters": 0.6744, "Hooks": 0.6568, "Astros": 0.6485,
    "Missions": 0.5943, "Diamondbacks": 0.5925, "Sod Poodles": 0.5868,
    "Space City": 0.5866, "Flying Squirrels": 0.5578, "White Sox": 0.5551,
    "Blue Jays": 0.5491, "Braves": 0.527, "Spicy Meatballs": 0.5248,
    "Spring Spirit Toros": 0.5206, "Party Animals": 0.498, "Giants": 0.4913,
    "Aggies": 0.4766, "Miami Marlins": 0.4757, "Texas Longhorns": 0.4526,
    "Expos": 0.4355, "Space Cowboys": 0.4082, "Bayou City Dodgers": 0.3722,
    "Green Jays": 0.2723, "LSU Tigers": 0.2702, "Guardians": 0.268,
    "Ole Miss Rebels": 0.268, "Colt .45s": 0.2613, "Cleveland Indians": 0.201,
    "Rangers": 0.201, "LA Dodgers": 0.1787, "Yard Goats": 0.1563,
    "Monsters": 0.1563, "Outlaws": 0.134, "Rockies": 0.0893,
    "Chicago Cubs": 0.0,
}
LEAGUE_AVG_PRE = round(sum(PRESEASON_PS.values()) / len(PRESEASON_PS), 4)

# Schedule name → canonical name map
NAME_MAP = {
    "colt .45s": "Colt .45s",
    "colt 45s": "Colt .45s",
    "prospect - white": "Prospect - White",
    "prospect white": "Prospect - White",
    "miami marlins": "Miami Marlins",
    "cleveland indians": "Cleveland Indians",
    "savannah bananas": "Savannah Bananas",
    "la dodgers": "LA Dodgers",
    "durham bulls": "Durham Bulls",
    "bulls": "Durham Bulls",
    "spring spirit toros": "Spring Spirit Toros",
    "bayou city dodgers": "Bayou City Dodgers",
    "rockies city connect": "Rockies City Connect",
    "flying squirrels": "Flying Squirrels",
    "spicy meatballs": "Spicy Meatballs",
    "ole miss rebels": "Ole Miss Rebels",
    "space cowboys": "Space Cowboys",
    "space city": "Space City",
    "party animals": "Party Animals",
    "lake monsters": "Lake Monsters",
    "texas longhorns": "Texas Longhorns",
    "green jays": "Green Jays",
    "blue jays": "Blue Jays",
    "white sox": "White Sox",
    "chicago cubs": "Chicago Cubs",
    "red sox": "Red Sox",
    "lsu tigers": "LSU Tigers",
    "detroit tigers": "Detroit Tigers",
    "oregon ducks": "Oregon Ducks",
    "chili peppers": "Chili Peppers",
    "sod poodles": "Sod Poodles",
    "yard goats": "Yard Goats",
}

def canonicalize(name):
    """Normalize team name to canonical form."""
    n = name.strip()
    lower = n.lower()
    return NAME_MAP.get(lower, n)

# ── SCRAPER ──────────────────────────────────────────────────────────────────
def scrape_division(url, division):
    """
    Scrape completed game results from an SBMSA TeamSideline page.
    
    The page uses ASP.NET RadGrid with a desktop ScheduleGrid and a mobile
    MobileScheduleGrid. Each game row contains spans with IDs like:
      - *_AwayLabel / *_HomeLabel       → team names
      - *_AwayScoreLabel / *_HomeScoreLabel → scores (empty if not played)
      - *_DateLabel                      → date string e.g. "Mon 3/16"
    
    We parse the desktop ScheduleGrid rows since they have explicit Away/Home.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    games = []

    # Find the desktop ScheduleGrid table (not MobileScheduleGrid)
    # It has id containing "ScheduleGrid_ctl00" but NOT "Mobile"
    schedule_table = None
    for tbl in soup.find_all("table"):
        tbl_id = tbl.get("id", "")
        if "ScheduleGrid_ctl00" in tbl_id and "Mobile" not in tbl_id:
            schedule_table = tbl
            break

    if not schedule_table:
        print(f"  WARNING: Could not find ScheduleGrid for {division}")
        return []

    # Each data row has id like *_ScheduleGrid_ctl00__N
    # Within each row, find the labeled spans
    rows = schedule_table.find_all("tr", id=re.compile(r"ScheduleGrid_ctl00__\d+"))
    
    for row in rows:
        # Extract date
        date_span = row.find("span", id=re.compile(r"DateLabel$"))
        # Extract time
        time_span = row.find("span", id=re.compile(r"TimeLabel$"))
        # Away team name and score
        away_span  = row.find("span", id=re.compile(r"AwayLabel$"))
        away_score_span = row.find("span", id=re.compile(r"AwayScoreLabel$"))
        # Home team name and score
        home_span  = row.find("span", id=re.compile(r"HomeLabel$"))
        home_score_span = row.find("span", id=re.compile(r"HomeScoreLabel$"))

        if not (away_span and home_span):
            continue

        away_name = canonicalize(away_span.get_text(strip=True))
        home_name = canonicalize(home_span.get_text(strip=True))
        away_score_txt = away_score_span.get_text(strip=True) if away_score_span else ""
        home_score_txt = home_score_span.get_text(strip=True) if home_score_span else ""

        # Only record if both scores are present (game was played)
        if not away_score_txt or not home_score_txt:
            continue

        try:
            away_score = int(away_score_txt)
            home_score = int(home_score_txt)
        except ValueError:
            continue

        date_str = date_span.get_text(strip=True) if date_span else TODAY

        games.append({
            "date": date_str,
            "away": away_name,
            "home": home_name,
            "away_score": away_score,
            "home_score": home_score,
            "division": division,
            "scraped_date": TODAY,
        })

    print(f"  {division}: found {len(games)} completed games (of {len(rows)} total rows)")
    return games

# ── RANKING ENGINE ───────────────────────────────────────────────────────────
def compute_sos_rankings(game_results, all_teams, iterations=15):
    """
    SOS-weighted iterative power ranking.
    60% win quality (outcome × opponent score) + 40% run differential (capped ±10/game)
    Returns dict of team -> normalized score (0-1)
    """
    if not game_results:
        # No games played — return equal ratings
        return {t: 0.5 for t in all_teams}

    # Initialize
    scores = {t: 0.5 for t in all_teams}
    
    for _ in range(iterations):
        new_scores = {}
        for team in all_teams:
            team_games = [g for g in game_results if g["away"] == team or g["home"] == team]
            if not team_games:
                new_scores[team] = 0.5
                continue
            
            win_quality = 0.0
            run_diff_total = 0.0
            
            for g in team_games:
                is_away = g["away"] == team
                my_score = g["away_score"] if is_away else g["home_score"]
                opp_score = g["home_score"] if is_away else g["away_score"]
                opp = g["home"] if is_away else g["away"]
                opp_ps = scores.get(opp, 0.5)
                
                if my_score > opp_score:
                    outcome = 1.0
                elif my_score == opp_score:
                    outcome = 0.5
                else:
                    outcome = 0.0
                
                win_quality += outcome * opp_ps
                run_diff = max(-10, min(10, my_score - opp_score))
                run_diff_total += run_diff
            
            n = len(team_games)
            avg_wq = win_quality / n
            avg_rd = run_diff_total / n / 10.0  # normalize to -1..+1
            raw = 0.6 * avg_wq + 0.4 * ((avg_rd + 1) / 2)
            new_scores[team] = max(0.001, min(0.999, raw))
        
        scores = new_scores
    
    # Normalize 0-1
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {t: 0.5 for t in all_teams}
    return {t: round((v - lo) / (hi - lo), 4) for t, v in scores.items()}

def win_prob_bt(a_ps, h_ps, home_boost=1.05, eps=0.05):
    """Bradley-Terry win probability with home field advantage."""
    awp = (a_ps + eps) / (a_ps + eps + h_ps * home_boost + eps)
    return round(awp, 4)

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    print(f"=== SBMSA Nightly Run: {TODAY} ===\n")

    # 1. Load existing results
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            all_results = json.load(f)
    else:
        all_results = []

    existing_keys = {
        (g["date"], g["away"], g["home"]) for g in all_results
    }

    # 2. Scrape each division
    new_results = []
    for division, url in DIVISION_URLS.items():
        print(f"Scraping {division}...")
        scraped = scrape_division(url, division)
        for g in scraped:
            key = (g["date"], g["away"], g["home"])
            if key not in existing_keys:
                new_results.append(g)
                existing_keys.add(key)

    all_results.extend(new_results)
    print(f"\nTotal results: {len(all_results)} games ({len(new_results)} new today)")

    # Save results
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    # 3. Load schedule
    if not SCHEDULE_FILE.exists():
        print("ERROR: schedule.json not found")
        sys.exit(1)
    with open(SCHEDULE_FILE) as f:
        schedule = json.load(f)

    all_teams = sorted(set(
        [g["Away"].strip() if "Away" in g else g.get("away","") for g in schedule] +
        [g["Home"].strip() if "Home" in g else g.get("home","") for g in schedule]
    ))
    all_teams = [t for t in all_teams if t]

    # 4. Compute ACTUAL rankings from season results only
    season_results = [g for g in all_results if g.get("scraped_date", "") >= "2026-03-16"]
    actual_ps = compute_sos_rankings(season_results, all_teams)

    # 5. Preseason PS (frozen — map schedule names to preseason keys)
    pre_ps = {}
    for team in all_teams:
        pre_ps[team] = PRESEASON_PS.get(team, LEAGUE_AVG_PRE)
    # Normalize preseason scores same way
    vals = list(pre_ps.values())
    lo, hi = min(vals), max(vals)
    pre_ps_norm = {t: round((v - lo) / (hi - lo), 4) for t, v in pre_ps.items()}

    # 6. Compute predictions for all scheduled games
    completed_keys = {(g["date"], g["away"], g["home"]) for g in all_results}
    predictions = []
    for g in schedule:
        away = g.get("Away", g.get("away", "")).strip()
        home = g.get("Home", g.get("home", "")).strip()
        date = g.get("Date", g.get("date", "")).strip()
        time_ = g.get("Time", g.get("time", "")).strip()
        loc   = g.get("Location", g.get("loc", "")).strip()
        div   = g.get("Division", g.get("div", "")).strip()

        a_pre = pre_ps_norm.get(away, 0.5)
        h_pre = pre_ps_norm.get(home, 0.5)
        a_act = actual_ps.get(away, 0.5)
        h_act = actual_ps.get(home, 0.5)

        # Find result if completed
        result = next((r for r in all_results if r["away"]==away and r["home"]==home), None)

        predictions.append({
            "div": div, "date": date, "time": time_, "loc": loc,
            "away": away, "home": home,
            # Preseason-based predictions
            "pre_awp": win_prob_bt(a_pre, h_pre),
            "pre_hwp": round(1 - win_prob_bt(a_pre, h_pre), 4),
            "pre_aps": a_pre, "pre_hps": h_pre,
            # Actual-based predictions
            "act_awp": win_prob_bt(a_act, h_act),
            "act_hwp": round(1 - win_prob_bt(a_act, h_act), 4),
            "act_aps": a_act, "act_hps": h_act,
            # Result if played
            "played": result is not None,
            "away_score": result["away_score"] if result else None,
            "home_score": result["home_score"] if result else None,
        })

    # 7. Build team summaries
    teams_out = []
    team_divs = {}
    for g in schedule:
        away = g.get("Away", g.get("away","")).strip()
        home = g.get("Home", g.get("home","")).strip()
        div  = g.get("Division", g.get("div","")).strip()
        team_divs[away] = div
        team_divs[home] = div

    for team in sorted(all_teams):
        team_games = [p for p in predictions if p["away"]==team or p["home"]==team]
        played = [p for p in team_games if p["played"]]
        remaining = [p for p in team_games if not p["played"]]

        wins = sum(1 for p in played if
            (p["away"]==team and p["away_score"] > p["home_score"]) or
            (p["home"]==team and p["home_score"] > p["away_score"]))
        losses = sum(1 for p in played if
            (p["away"]==team and p["away_score"] < p["home_score"]) or
            (p["home"]==team and p["home_score"] < p["away_score"]))
        ties = len(played) - wins - losses

        exp_w_pre = round(sum(
            p["pre_awp"] if p["away"]==team else p["pre_hwp"]
            for p in remaining), 2)
        exp_w_act = round(sum(
            p["act_awp"] if p["away"]==team else p["act_hwp"]
            for p in remaining), 2)

        teams_out.append({
            "team": team,
            "div": team_divs.get(team, ""),
            "pre_ps": pre_ps_norm.get(team, 0.5),
            "act_ps": actual_ps.get(team, 0.5),
            "has_preseason": team in PRESEASON_PS,
            "record": f"{wins}-{losses}-{ties}",
            "wins": wins, "losses": losses, "ties": ties,
            "gp": len(played),
            "gp_total": len(team_games),
            "exp_w_pre": exp_w_pre,
            "exp_w_act": exp_w_act,
            "games": sorted([{
                "opp": p["home"] if p["away"]==team else p["away"],
                "ha": "Away" if p["away"]==team else "Home",
                "date": p["date"], "time": p["time"], "loc": p["loc"],
                "pre_wp": p["pre_awp"] if p["away"]==team else p["pre_hwp"],
                "act_wp": p["act_awp"] if p["away"]==team else p["act_hwp"],
                "played": p["played"],
                "my_score": (p["away_score"] if p["away"]==team else p["home_score"]) if p["played"] else None,
                "opp_score": (p["home_score"] if p["away"]==team else p["away_score"]) if p["played"] else None,
            } for p in team_games], key=lambda x: x["date"]),
        })

    # 8. Append to history
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    else:
        history = []

    # Only add one snapshot per day
    if not history or history[-1]["date"] != TODAY:
        history.append({
            "date": TODAY,
            "pre_ps": {t: pre_ps_norm.get(t, 0.5) for t in all_teams},
            "act_ps": {t: actual_ps.get(t, 0.5) for t in all_teams},
            "games_played": len(season_results),
        })
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
        print(f"History snapshot saved ({len(history)} days total)")

    # 9. Save latest.json
    latest = {
        "generated": TODAY,
        "games_played": len(season_results),
        "predictions": predictions,
        "teams": teams_out,
        "history": history,
        "league_avg_pre": LEAGUE_AVG_PRE,
    }
    with open(LATEST_FILE, "w") as f:
        json.dump(latest, f, indent=2)

    print(f"\nSaved: {LATEST_FILE}")
    print(f"Teams with actual results: {sum(1 for t in teams_out if t['gp'] > 0)}")
    return latest

if __name__ == "__main__":
    main()
