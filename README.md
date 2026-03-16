# SBMSA PeeWee NL — Nightly Predictions Pipeline

Automatically scrapes game results from sbmsa.net, runs dual power rankings, and rebuilds the predictions page every night via GitHub Actions.

## Repo Structure

```
├── .github/
│   └── workflows/
│       └── nightly.yml          ← GitHub Actions schedule
├── scripts/
│   ├── scrape_and_rank.py       ← scraper + SOS ranking engine
│   └── build_html.py            ← HTML generator
├── data/
│   ├── schedule.json            ← full 225-game schedule (source of truth)
│   ├── results.json             ← all scraped game results (appended nightly)
│   ├── ratings_history.json     ← daily snapshot of both rating sets
│   └── latest.json              ← current predictions + team data for HTML
├── index.html                   ← power rankings (existing)
└── season_predictions.html      ← predictions page (rebuilt nightly)
```

## How It Works

1. **Scraper** hits 3 SBMSA division pages nightly, parses completed game scores
2. **Dual Rankings Engine** computes two independent rating sets:
   - **Preseason** — frozen SOS-weighted scores from preseason results (never changes)
   - **Actual** — rebuilt from scratch each run using only regular season results
3. **Predictions** — Bradley-Terry win probabilities calculated from both models for every remaining game
4. **History** — one snapshot per day appended to `ratings_history.json` for charts
5. **HTML Builder** — regenerates `season_predictions.html` and commits it back

## One-Time Setup

### 1. Copy files to your repo
```
your-repo/
├── .github/workflows/nightly.yml
├── scripts/scrape_and_rank.py
├── scripts/build_html.py
└── data/schedule.json
```

### 2. Create empty data files (first run will populate them)
```bash
echo "[]" > data/results.json
echo "[]" > data/ratings_history.json
echo "{}" > data/latest.json
```

### 3. Verify GitHub Actions is enabled
- Go to your repo → Actions tab → enable if prompted

### 4. Set the correct division URLs in scrape_and_rank.py
```python
DIVISION_URLS = {
    "Pee Wee East":    "https://sbmsa.net/schedule/676209/pee-wee-east",
    "Pee Wee Central": "https://sbmsa.net/schedule/676210/pee-wee-central",
    "Pee Wee West":    "https://sbmsa.net/schedule/676211/pee-wee-west",
}
```

### 5. Test manually
Trigger the workflow manually from Actions → SBMSA Nightly Update → Run workflow

## Scraper Notes

The scraper tries 3 strategies to parse SBMSA pages:
1. Table rows with team names + scores
2. Text pattern matching (score regex + nearby team names)
3. Embedded JavaScript data objects

If scores aren't being picked up after the first real games are played, open an issue with the page HTML and the selectors can be tuned.

## Ratings

- **Preseason score** — locked in, never updates, based on spring tournament results
- **Actual score** — starts at 0.500 for all teams, converges as games are played
- Until ~3 games played per team, actual scores are noisy — preseason remains the better predictor
- Both scores are normalized 0–1 within each run

## Schedule

The `data/schedule.json` file is the authoritative schedule. It was manually verified to have exactly 10 games per team across all 45 teams (225 games total). If the schedule changes, update this file.
