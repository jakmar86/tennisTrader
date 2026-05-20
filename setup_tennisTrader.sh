#!/bin/bash
# TennisTrader -- Full repo setup script
# Run from ~/tennisTrader on the LXC

set -e
echo "Setting up TennisTrader repo..."

# ── Folder structure ──────────────────────────────────────────────────────────
mkdir -p config data/raw/atp data/raw/wta data/raw/odds data/processed data/db src dashboard/frontend dashboard/backend tests scripts

# ── .gitignore ────────────────────────────────────────────────────────────────
cat > .gitignore << 'EOF'
.env
__pycache__/
*.py[cod]
venv/
.venv/
data/raw/
data/processed/
data/db/
certs/
.vscode/
.idea/
.DS_Store
*.log
EOF

# ── .env.example ──────────────────────────────────────────────────────────────
cat > .env.example << 'EOF'
# TennisTrader -- Environment Variables
# Copy to .env and fill in. NEVER commit .env to GitHub.

BETFAIR_USERNAME=your_betfair_username
BETFAIR_PASSWORD=your_betfair_password
BETFAIR_APP_KEY=your_app_key
BETFAIR_CERT_PATH=/home/scoretrader/certs/client-2048.crt
BETFAIR_KEY_PATH=/home/scoretrader/certs/client-2048.key

WHATSAPP_NUMBER=+447XXXXXXXXX
EOF

# ── requirements.txt ──────────────────────────────────────────────────────────
cat > requirements.txt << 'EOF'
# Betfair API
betfairlightweight==2.23.2

# Data
pandas==2.2.2
numpy==1.26.4
scipy==1.13.0
requests==2.31.0

# Environment
python-dotenv==1.0.1

# API backend (Phase 1C)
fastapi==0.111.0
uvicorn==0.29.0

# Testing
pytest==8.2.0
EOF

# ── README.md ─────────────────────────────────────────────────────────────────
cat > README.md << 'EOF'
# TennisTrader

An automated tennis trading system for Betfair, built in Python with a React dashboard.

## Overview

TennisTrader uses a Bradley-Terry paired comparison model with surface adjustment
to identify value in Betfair tennis match odds markets. It calculates edge against
market-implied odds, sizes stakes using Half Kelly, places back bets via the Betfair
API, monitors matches in-play, and executes optimal lay bets based on game state.

## Why Tennis

- Mathematically tractable -- serve probability drives everything
- Binary outcomes per match -- clean model validation
- Matches every day -- year-round opportunity
- In-play odds swing dramatically on breaks of serve
- Less sharp money at ATP 250 / Challenger level
- Real closing odds available from tennis-data.co.uk -- no synthetic odds problem

## Data Sources

- Jeff Sackmann GitHub -- comprehensive ATP/WTA match data (free)
- tennis-data.co.uk   -- match results + real Betfair/bookmaker odds (free)

## Architecture

```
data_pipeline     ->  Jeff Sackmann + tennis-data.co.uk
bradley_terry     ->  Player strength ratings (surface adjusted)
match_model       ->  Match/set/game win probabilities
odds_fetcher      ->  Live Betfair tennis market odds
value_engine      ->  Edge calculation + Half Kelly staking
bet_placer        ->  Supervised/autonomous back bet placement
inplay_monitor    ->  Point-by-point monitoring loop
exit_engine       ->  Tennis-specific green-up logic
lay_placer        ->  Optimal lay order execution
settler           ->  Post-match P&L calculation
logger            ->  SQLite trade history
dashboard         ->  React frontend + FastAPI backend
```

## Build Phases

- Phase 1A -- Data pipeline + Bradley-Terry model + backtest vs real odds
- Phase 1B -- Betfair API integration + live odds fetch
- Phase 1C -- Bet placement + in-play monitor + exit engine
- Phase 2  -- Live paper trading (Wimbledon, US Open)
- Phase 3  -- Micro stakes live validation
- Phase 4  -- Scale + surface specialisation

## License

Private -- Dellally Limited
EOF

# ── conftest.py ───────────────────────────────────────────────────────────────
cat > conftest.py << 'EOF'
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
EOF

# ── pyproject.toml ────────────────────────────────────────────────────────────
cat > pyproject.toml << 'EOF'
[tool.pytest.ini_options]
pythonpath = ["."]
EOF

# ── config/__init__.py ────────────────────────────────────────────────────────
touch config/__init__.py

# ── config/config.py ──────────────────────────────────────────────────────────
cat > config/config.py << 'EOF'
"""
TennisTrader -- Configuration
Single control panel for all settings.
"""

config = {

    # -------------------------------------------------------------------------
    # MODE
    # -------------------------------------------------------------------------
    "supervised": True,               # True = WhatsApp approval before placing

    # -------------------------------------------------------------------------
    # STAKING
    # -------------------------------------------------------------------------
    "betting_bank":                   1000,
    "kelly_fraction":                 0.5,
    "supervised_stake_multiplier":    0.5,
    "max_match_stake_supervised":     30,
    "max_match_stake_live":           100,

    # -------------------------------------------------------------------------
    # VALUE FILTER
    # -------------------------------------------------------------------------
    "min_edge_pct":                   1.5,   # Slightly higher than football
    "odds_drift_threshold":           0.15,
    "min_odds":                       1.40,  # Don't back odds-on shots
    "max_odds":                       8.00,  # Don't back big outsiders

    # -------------------------------------------------------------------------
    # MODEL
    # -------------------------------------------------------------------------
    "min_matches_required":           20,    # Minimum matches to rate a player
    "recency_half_life_days":         180,   # Weight recent matches more heavily
    "surfaces": ["hard", "clay", "grass"],

    # -------------------------------------------------------------------------
    # IN-PLAY EXIT ENGINE
    # -------------------------------------------------------------------------
    "poll_interval_seconds":          15,    # Tennis moves fast -- poll more often
    "greenup_profit_threshold":       1.20,  # Green up combined position at 120%
    "cut_loss_min_minute":            0,     # Tennis uses sets not minutes
    "cut_loss_set_threshold":         2,     # Cut after losing 2 sets in best of 3

    # -------------------------------------------------------------------------
    # TOURNAMENTS
    # -------------------------------------------------------------------------
    "tour": ["ATP", "WTA"],
    "min_tournament_level": "250",    # 250, 500, 1000, Grand Slam
    # Grand Slams have most liquidity
    # ATP 250 has least sharp money -- most edge potential

    # -------------------------------------------------------------------------
    # DATA
    # -------------------------------------------------------------------------
    "seasons":                        5,     # 5 seasons of historical data
    "raw_data_path":                  "data/raw/",
    "processed_data_path":            "data/processed/",
    "db_path":                        "data/db/tennisTrader.db",
    "sackmann_atp_path":              "data/raw/atp/",
    "sackmann_wta_path":              "data/raw/wta/",
    "odds_data_path":                 "data/raw/odds/",

    # -------------------------------------------------------------------------
    # BETFAIR API
    # -------------------------------------------------------------------------
    "betfair_username_env":           "BETFAIR_USERNAME",
    "betfair_password_env":           "BETFAIR_PASSWORD",
    "betfair_app_key_env":            "BETFAIR_APP_KEY",
    "betfair_cert_path_env":          "BETFAIR_CERT_PATH",
    "betfair_key_path_env":           "BETFAIR_KEY_PATH",

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------
    "whatsapp_number_env":            "WHATSAPP_NUMBER",
    "notify_on_placement":            True,
    "notify_on_exit":                 True,
    "notify_on_error":                True,

    # -------------------------------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------------------------------
    "dashboard_host":                 "0.0.0.0",
    "dashboard_port":                 8001,   # Different port to ScoreTrader
}
EOF

# ── src/__init__.py ───────────────────────────────────────────────────────────
touch src/__init__.py

# ── src/betfair_auth.py ───────────────────────────────────────────────────────
cat > src/betfair_auth.py << 'EOF'
"""
TennisTrader -- Betfair Authentication
Reuses same cert/credentials as ScoreTrader.
"""

import os
import betfairlightweight
from dotenv import load_dotenv

load_dotenv()


def get_client():
    """Authenticate with Betfair API. Returns authenticated client."""
    username  = os.getenv("BETFAIR_USERNAME")
    password  = os.getenv("BETFAIR_PASSWORD")
    app_key   = os.getenv("BETFAIR_APP_KEY")
    cert_path = os.getenv("BETFAIR_CERT_PATH")
    key_path  = os.getenv("BETFAIR_KEY_PATH")

    if not all([username, password, app_key, cert_path, key_path]):
        raise EnvironmentError(
            "Missing Betfair credentials. Check your .env file."
        )

    client = betfairlightweight.APIClient(
        username=username,
        password=password,
        app_key=app_key,
        certs=(cert_path, key_path),
    )
    client.login()
    return client


if __name__ == "__main__":
    try:
        client = get_client()
        print("Betfair authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
EOF

# ── src/data_pipeline.py ──────────────────────────────────────────────────────
cat > src/data_pipeline.py << 'EOF'
"""
TennisTrader -- Data Pipeline
Two data sources:

1. Jeff Sackmann GitHub -- comprehensive match data, serve stats, rankings
   https://github.com/JeffSackmann/tennis_atp
   https://github.com/JeffSackmann/tennis_wta

2. tennis-data.co.uk -- match results with real Betfair/bookmaker closing odds
   http://www.tennis-data.co.uk/alldata.php
   This is the key advantage over ScoreTrader -- real odds for validation

Phase 1A: Core implementation target.
"""

import os
import requests
import pandas as pd
from pathlib import Path
from config.config import config

# tennis-data.co.uk URLs
# Format: http://www.tennis-data.co.uk/YYYY/TOUR.xls
TENNIS_DATA_BASE = "http://www.tennis-data.co.uk/{year}/{tour}.xlsx"

TOURS = {
    "ATP": "atp",
    "WTA": "wta",
}

# Jeff Sackmann GitHub raw URLs
SACKMANN_BASE = "https://raw.githubusercontent.com/JeffSackmann/tennis_{tour}/master/{tour}_matches_{year}.csv"

# Key columns from tennis-data.co.uk
ODDS_COLS = [
    "Date", "Tournament", "Surface", "Round",
    "Winner", "Loser",
    "WRank", "LRank",        # ATP/WTA rankings
    "W1", "L1",              # Set 1 scores
    "W2", "L2",              # Set 2 scores
    "W3", "L3",              # Set 3 scores
    "B365W", "B365L",        # Bet365 closing odds
    "PSW", "PSL",            # Pinnacle closing odds (sharpest market)
    "MaxW", "MaxL",          # Best available odds
    "AvgW", "AvgL",          # Average odds
]

# Key columns from Jeff Sackmann
SACKMANN_COLS = [
    "tourney_date", "tourney_name", "surface", "draw_size",
    "tourney_level", "match_num",
    "winner_name", "winner_rank", "winner_rank_points",
    "loser_name",  "loser_rank",  "loser_rank_points",
    "score", "best_of", "round", "minutes",
    # Serve stats
    "w_ace", "w_df", "w_svpt", "w_1stIn", "w_1stWon", "w_2ndWon",
    "w_SvGms", "w_bpSaved", "w_bpFaced",
    "l_ace", "l_df", "l_svpt", "l_1stIn", "l_1stWon", "l_2ndWon",
    "l_SvGms", "l_bpSaved", "l_bpFaced",
]


def download_tennis_data(tour: str, year: int, out_path: str) -> str:
    """Download tennis-data.co.uk odds file for a given tour and year."""
    url   = TENNIS_DATA_BASE.format(year=year, tour=TOURS[tour])
    fname = f"{tour.lower()}_{year}_odds.xlsx"
    fpath = os.path.join(out_path, fname)

    if os.path.exists(fpath):
        print(f"  Already exists: {fname}")
        return fpath

    print(f"  Downloading odds: {url}")
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    with open(fpath, "wb") as f:
        f.write(response.content)

    print(f"  Saved: {fname}")
    return fpath


def download_sackmann(tour: str, year: int, out_path: str) -> str:
    """Download Jeff Sackmann match data for a given tour and year."""
    tour_lower = tour.lower()
    url   = SACKMANN_BASE.format(tour=tour_lower, year=year)
    fname = f"{tour_lower}_matches_{year}.csv"
    fpath = os.path.join(out_path, fname)

    if os.path.exists(fpath):
        print(f"  Already exists: {fname}")
        return fpath

    print(f"  Downloading Sackmann: {url}")
    response = requests.get(url, timeout=15)
    response.raise_for_status()

    with open(fpath, "wb") as f:
        f.write(response.content)

    print(f"  Saved: {fname}")
    return fpath


def load_odds_data(fpath: str) -> pd.DataFrame:
    """Load and clean tennis-data.co.uk odds file."""
    try:
        df = pd.read_excel(fpath)
    except Exception:
        return pd.DataFrame()

    # Keep available columns
    cols = [c for c in ODDS_COLS if c in df.columns]
    df   = df[cols].copy()
    df   = df.dropna(subset=["Winner", "Loser"])
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    return df


def load_sackmann_data(fpath: str) -> pd.DataFrame:
    """Load and clean Jeff Sackmann match data."""
    try:
        df = pd.read_csv(fpath, low_memory=False)
    except Exception:
        return pd.DataFrame()

    cols = [c for c in SACKMANN_COLS if c in df.columns]
    df   = df[cols].copy()
    df   = df.dropna(subset=["winner_name", "loser_name"])
    df["tourney_date"] = pd.to_datetime(
        df["tourney_date"].astype(str), format="%Y%m%d", errors="coerce"
    )
    return df


def run_pipeline(tours: list, seasons: int,
                 raw_path: str, processed_path: str):
    """
    Download and process all tour data.
    Produces two combined datasets:
      1. odds_data.csv    -- tennis-data.co.uk (for real odds validation)
      2. match_data.csv   -- Jeff Sackmann (for model building)
    """
    Path(raw_path).mkdir(parents=True, exist_ok=True)
    Path(processed_path).mkdir(parents=True, exist_ok=True)

    import datetime
    current_year = datetime.datetime.now().year
    years        = list(range(current_year - seasons, current_year + 1))

    odds_frames    = []
    sackmann_frames = []

    for tour in tours:
        atp_path = os.path.join(raw_path, tour.lower())
        Path(atp_path).mkdir(parents=True, exist_ok=True)

        print(f"\nProcessing: {tour}")
        for year in years:
            # Odds data
            try:
                fpath = download_tennis_data(tour, year, atp_path)
                df    = load_odds_data(fpath)
                if not df.empty:
                    df["Tour"] = tour
                    df["Year"] = year
                    odds_frames.append(df)
                    print(f"  Odds loaded: {len(df)} matches for {year}")
            except Exception as e:
                print(f"  Odds warning: {tour} {year} -- {e}")

            # Sackmann data
            try:
                fpath = download_sackmann(tour, year, atp_path)
                df    = load_sackmann_data(fpath)
                if not df.empty:
                    df["Tour"] = tour
                    sackmann_frames.append(df)
                    print(f"  Sackmann loaded: {len(df)} matches for {year}")
            except Exception as e:
                print(f"  Sackmann warning: {tour} {year} -- {e}")

    # Save combined datasets
    if odds_frames:
        odds_combined = pd.concat(odds_frames, ignore_index=True)
        odds_path     = os.path.join(processed_path, "odds_data.csv")
        odds_combined.to_csv(odds_path, index=False)
        print(f"\nOdds dataset: {len(odds_combined)} matches -> {odds_path}")
    else:
        odds_combined = pd.DataFrame()
        print("\nNo odds data loaded.")

    if sackmann_frames:
        sackmann_combined = pd.concat(sackmann_frames, ignore_index=True)
        sackmann_path     = os.path.join(processed_path, "match_data.csv")
        sackmann_combined.to_csv(sackmann_path, index=False)
        print(f"Match dataset: {len(sackmann_combined)} matches -> {sackmann_path}")
    else:
        sackmann_combined = pd.DataFrame()
        print("No match data loaded.")

    return odds_combined, sackmann_combined


if __name__ == "__main__":
    odds, matches = run_pipeline(
        tours          = config["tour"],
        seasons        = config["seasons"],
        raw_path       = config["raw_data_path"],
        processed_path = config["processed_data_path"],
    )
    print(f"\nOdds columns: {list(odds.columns) if not odds.empty else 'none'}")
    print(f"Match columns available: {list(matches.columns) if not matches.empty else 'none'}")
EOF

# ── src/bradley_terry.py ──────────────────────────────────────────────────────
cat > src/bradley_terry.py << 'EOF'
"""
TennisTrader -- Bradley-Terry Model
Player strength ratings with surface adjustment and recency weighting.

The Bradley-Terry model estimates the probability that player A beats player B:
  P(A beats B) = strength_A / (strength_A + strength_B)

We extend this with:
  1. Surface adjustment (clay / grass / hard)
  2. Recency weighting (recent matches count more)
  3. Minimum matches threshold for reliability

Phase 1A: Core implementation target.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from datetime import datetime, timedelta
from config.config import config


def compute_recency_weight(match_date: pd.Timestamp,
                           reference_date: pd.Timestamp,
                           half_life_days: int = 180) -> float:
    """
    Exponential decay weight -- matches from half_life_days ago
    count half as much as today's matches.
    """
    days_ago = (reference_date - match_date).days
    if days_ago < 0:
        return 0.0
    return 0.5 ** (days_ago / half_life_days)


def build_ratings(df: pd.DataFrame, surface: str = None,
                  reference_date: pd.Timestamp = None) -> pd.Series:
    """
    Build Bradley-Terry ratings for all players.

    Args:
        df:              Match dataframe with winner_name, loser_name, tourney_date, surface
        surface:         Filter to specific surface (hard/clay/grass) or None for all
        reference_date:  Date to calculate recency weights from (default: today)

    Returns:
        pd.Series with player names as index and rating as value
        Higher rating = stronger player
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now()

    df = df.copy()
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], errors="coerce")
    df = df.dropna(subset=["tourney_date", "winner_name", "loser_name"])

    # Filter by surface if specified
    if surface and "surface" in df.columns:
        df = df[df["surface"].str.lower() == surface.lower()]

    if df.empty:
        return pd.Series(dtype=float)

    # Calculate recency weights
    half_life = config["recency_half_life_days"]
    df["weight"] = df["tourney_date"].apply(
        lambda d: compute_recency_weight(d, reference_date, half_life)
    )
    df = df[df["weight"] > 0.01]  # Drop very old matches

    # Get unique players
    players = sorted(set(df["winner_name"]) | set(df["loser_name"]))
    n       = len(players)

    if n < 2:
        return pd.Series(dtype=float)

    player_idx = {p: i for i, p in enumerate(players)}

    # Count matches per player
    match_counts = pd.Series(0, index=players)
    for _, row in df.iterrows():
        match_counts[row["winner_name"]] += 1
        match_counts[row["loser_name"]]  += 1

    min_matches = config["min_matches_required"]

    # Bradley-Terry log-likelihood optimisation
    def neg_log_likelihood(params):
        """Negative log-likelihood of observed match outcomes."""
        nll = 0.0
        for _, row in df.iterrows():
            wi = player_idx[row["winner_name"]]
            li = player_idx[row["loser_name"]]
            w  = row["weight"]
            # Log-likelihood: log(exp(p_w) / (exp(p_w) + exp(p_l)))
            diff = params[wi] - params[li]
            nll -= w * (diff - np.log1p(np.exp(diff)))
        return nll

    # Initialise with zeros, fix first player to 0 for identifiability
    x0      = np.zeros(n)
    bounds  = [(None, None)] * n
    bounds[0] = (0, 0)

    result = minimize(
        neg_log_likelihood,
        x0,
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 1000},
    )

    ratings = pd.Series(result.x, index=players)

    # Only return players with enough matches
    qualified = match_counts[match_counts >= min_matches].index
    ratings   = ratings[ratings.index.isin(qualified)]

    # Normalise to mean 0
    ratings = ratings - ratings.mean()

    return ratings.sort_values(ascending=False)


def match_win_probability(player_a: str, player_b: str,
                          ratings: pd.Series) -> float:
    """
    P(A beats B) using Bradley-Terry model.
    Returns probability between 0 and 1.
    """
    if player_a not in ratings.index or player_b not in ratings.index:
        return 0.5  # Unknown players -- assume 50/50

    ra = ratings[player_a]
    rb = ratings[player_b]

    return 1.0 / (1.0 + np.exp(rb - ra))


def surface_adjusted_probability(player_a: str, player_b: str,
                                  df: pd.DataFrame, surface: str,
                                  reference_date: pd.Timestamp = None) -> float:
    """
    Blend overall rating with surface-specific rating.

    Weight: 60% surface-specific + 40% overall
    Adjusts for players with strong/weak surface records.
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now()

    overall_ratings = build_ratings(df, surface=None,
                                    reference_date=reference_date)
    surface_ratings = build_ratings(df, surface=surface,
                                    reference_date=reference_date)

    # Overall probability
    p_overall = match_win_probability(player_a, player_b, overall_ratings)

    # Surface probability (fall back to overall if insufficient data)
    if (player_a in surface_ratings.index and
            player_b in surface_ratings.index):
        p_surface = match_win_probability(player_a, player_b, surface_ratings)
        # Blend: 60% surface, 40% overall
        return 0.60 * p_surface + 0.40 * p_overall
    else:
        return p_overall


if __name__ == "__main__":
    # Quick test with loaded data
    import os
    processed_path = config["processed_data_path"]
    match_file     = os.path.join(processed_path, "match_data.csv")

    if not os.path.exists(match_file):
        print("No match data found. Run data_pipeline.py first.")
    else:
        df      = pd.read_csv(match_file)
        df_atp  = df[df["Tour"] == "ATP"]

        print("Building ATP ratings (all surfaces)...")
        ratings = build_ratings(df_atp)
        print(f"\nTop 20 ATP players by rating:")
        print(ratings.head(20).to_string())

        print(f"\nSurface-adjusted probability examples:")
        pairs = [
            ("Novak Djokovic", "Carlos Alcaraz", "grass"),
            ("Carlos Alcaraz", "Jannik Sinner", "hard"),
            ("Rafael Nadal",   "Novak Djokovic", "clay"),
        ]
        for a, b, surface in pairs:
            try:
                p = surface_adjusted_probability(a, b, df_atp, surface)
                print(f"  {a} vs {b} ({surface}): {p*100:.1f}% / {(1-p)*100:.1f}%")
            except Exception as e:
                print(f"  {a} vs {b}: {e}")
EOF

# ── src/match_model.py ────────────────────────────────────────────────────────
cat > src/match_model.py << 'EOF'
"""
TennisTrader -- Match Model
Converts Bradley-Terry match win probability into set/game betting markets.

Markets modelled:
  - Match odds (winner)
  - Set betting (2-0, 2-1 for best of 3)
  - Over/Under games
  - First set winner

Phase 1A: Core implementation target.
"""

import numpy as np
from scipy.stats import binom
from config.config import config


def set_win_probability(p_match: float, serve_advantage: float = 0.05) -> float:
    """
    Estimate probability of winning a set given match win probability.
    Uses a simplified model -- in reality serve stats drive this more precisely.

    p_match:          Overall match win probability
    serve_advantage:  Small adjustment for serve dominance
    """
    # Rough approximation -- set win prob is close to match win prob
    # with slight compression toward 50% (sets are more random than matches)
    p_set = 0.5 + (p_match - 0.5) * 0.85
    return max(0.05, min(0.95, p_set))


def match_outcomes_best_of_3(p_match: float) -> dict:
    """
    Calculate set score probabilities for a best-of-3 match.

    Returns dict:
        "2-0":  P(player A wins 2-0)
        "2-1":  P(player A wins 2-1)
        "0-2":  P(player B wins 2-0)
        "1-2":  P(player B wins 2-1)
    """
    p_set = set_win_probability(p_match)
    q_set = 1 - p_set

    p_20 = p_set ** 2
    p_21 = 2 * p_set * q_set * p_set      # Win S1, lose S2, win S3 OR lose S1, win S2, win S3
    p_02 = q_set ** 2
    p_12 = 2 * p_set * q_set * q_set

    # Normalise to sum to 1
    total = p_20 + p_21 + p_02 + p_12
    return {
        "2-0": round(p_20 / total, 6),
        "2-1": round(p_21 / total, 6),
        "0-2": round(p_02 / total, 6),
        "1-2": round(p_12 / total, 6),
    }


def match_outcomes_best_of_5(p_match: float) -> dict:
    """
    Calculate set score probabilities for a best-of-5 match (Grand Slams).
    """
    p_set = set_win_probability(p_match)
    q_set = 1 - p_set

    p_30 = p_set ** 3
    p_31 = 3 * (p_set ** 3) * q_set
    p_32 = 6 * (p_set ** 3) * (q_set ** 2)
    p_03 = q_set ** 3
    p_13 = 3 * (q_set ** 3) * p_set
    p_23 = 6 * (q_set ** 3) * (p_set ** 2)

    total = p_30 + p_31 + p_32 + p_03 + p_13 + p_23
    return {
        "3-0": round(p_30 / total, 6),
        "3-1": round(p_31 / total, 6),
        "3-2": round(p_32 / total, 6),
        "0-3": round(p_03 / total, 6),
        "1-3": round(p_13 / total, 6),
        "2-3": round(p_23 / total, 6),
    }


def run_model(player_a: str, player_b: str, surface: str,
              df, best_of: int = 3,
              reference_date=None) -> dict:
    """
    Full model output for a match.

    Returns dict with:
        player_a:       Name
        player_b:       Name
        surface:        Surface
        p_a_wins:       Match win probability for player A
        p_b_wins:       Match win probability for player B
        set_scores:     Dict of set score probabilities
        market_summary: Human-readable output
    """
    from src.bradley_terry import surface_adjusted_probability

    p_a = surface_adjusted_probability(
        player_a, player_b, df, surface, reference_date
    )
    p_b = 1 - p_a

    if best_of == 5:
        set_scores = match_outcomes_best_of_5(p_a)
    else:
        set_scores = match_outcomes_best_of_3(p_a)

    return {
        "player_a":   player_a,
        "player_b":   player_b,
        "surface":    surface,
        "p_a_wins":   round(p_a, 4),
        "p_b_wins":   round(p_b, 4),
        "set_scores": set_scores,
    }


if __name__ == "__main__":
    import os
    import pandas as pd
    from config.config import config

    match_file = os.path.join(config["processed_data_path"], "match_data.csv")

    if not os.path.exists(match_file):
        print("No match data found. Run data_pipeline.py first.")
    else:
        df = pd.read_csv(match_file)
        df = df[df["Tour"] == "ATP"]

        result = run_model(
            "Carlos Alcaraz", "Jannik Sinner", "hard", df
        )

        print(f"\n{result['player_a']} vs {result['player_b']} ({result['surface']})")
        print(f"Win probability: {result['p_a_wins']*100:.1f}% / {result['p_b_wins']*100:.1f}%")
        print(f"\nSet score probabilities:")
        for score, prob in sorted(result["set_scores"].items(),
                                  key=lambda x: x[1], reverse=True):
            print(f"  {score}:  {prob*100:.1f}%")
EOF

# ── src/value_engine.py ───────────────────────────────────────────────────────
cat > src/value_engine.py << 'EOF'
"""
TennisTrader -- Value Engine
Identical logic to ScoreTrader -- sport agnostic.
Edge calculation and Half Kelly staking.
"""

from config.config import config


def calculate_edge(model_prob: float, market_odds: float) -> float:
    implied_prob = 1.0 / market_odds
    return round((model_prob - implied_prob) * 100, 2)


def kelly_stake(model_prob: float, market_odds: float,
                bank: float, fraction: float = 0.5) -> float:
    b = market_odds - 1
    p = model_prob
    q = 1 - p
    if b <= 0 or p <= 0:
        return 0.0
    raw = (b * p - q) / b
    if raw <= 0:
        return 0.0
    return round(raw * fraction * bank, 2)


def assess_match(model_prob: float, market_odds: float, bank: float) -> dict:
    """
    Assess a single match selection for value and stake size.
    Returns dict with edge, stake, and recommendation.
    """
    min_edge   = config["min_edge_pct"]
    min_odds   = config["min_odds"]
    max_odds   = config["max_odds"]
    supervised = config["supervised"]
    multiplier = config["supervised_stake_multiplier"] if supervised else 1.0
    max_stake  = (config["max_match_stake_supervised"] if supervised
                  else config["max_match_stake_live"])
    fraction   = config["kelly_fraction"]

    edge  = calculate_edge(model_prob, market_odds)
    stake = kelly_stake(model_prob, market_odds, bank, fraction)
    stake = min(round(stake * multiplier, 2), max_stake)

    value = (edge >= min_edge and
             min_odds <= market_odds <= max_odds and
             stake > 0)

    return {
        "model_prob":   model_prob,
        "market_odds":  market_odds,
        "implied_prob": round(1 / market_odds, 4),
        "edge_pct":     edge,
        "stake":        stake if value else 0,
        "value":        value,
        "recommendation": "BACK" if value else "PASS",
    }


if __name__ == "__main__":
    # Test with example match
    test_cases = [
        ("Alcaraz", 0.65, 1.72),    # Model says 65%, market implies 58%
        ("Sinner",  0.55, 1.95),    # Model says 55%, market implies 51%
        ("Djokovic", 0.72, 1.45),   # Model says 72%, market implies 69% -- tight
        ("Medvedev", 0.40, 2.80),   # Underdog value play
    ]

    print(f"{'Player':<12} {'Model%':>8} {'Odds':>6} {'Edge%':>8} {'Stake':>8} {'Rec':>6}")
    print("-" * 55)
    for name, prob, odds in test_cases:
        result = assess_match(prob, odds, bank=1000)
        print(f"{name:<12} {prob*100:>7.1f}% {odds:>6.2f} "
              f"{result['edge_pct']:>7.1f}%  "
              f"£{result['stake']:>6.2f}  {result['recommendation']:>6}")
EOF

# ── src/odds_fetcher.py ───────────────────────────────────────────────────────
cat > src/odds_fetcher.py << 'EOF'
"""
TennisTrader -- Odds Fetcher
Fetches tennis match odds from Betfair API.
Phase 1B: Implementation target -- requires API credentials.
"""

TENNIS_EVENT_TYPE_ID = "2"    # Betfair event type ID for tennis
MATCH_ODDS_MARKET    = "MATCH_ODDS"


def find_tennis_markets(tournament: str = None, date: str = None) -> list:
    """
    Find upcoming tennis match odds markets on Betfair.
    Phase 1B: stub.
    """
    pass


def fetch_match_odds(market_id: str) -> dict:
    """
    Fetch current best available odds for a tennis match.
    Returns dict: {player_a: odds, player_b: odds}
    Phase 1B: stub.
    """
    pass


def get_implied_probability(odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds
EOF

# ── src/bet_placer.py ─────────────────────────────────────────────────────────
cat > src/bet_placer.py << 'EOF'
"""
TennisTrader -- Bet Placer
Phase 1C: Implementation target.
"""


def place_back(player: str, market_id: str,
               stake: float, odds: float) -> dict:
    """Place a back bet on a tennis player. Phase 1C: stub."""
    pass
EOF

# ── src/inplay_monitor.py ─────────────────────────────────────────────────────
cat > src/inplay_monitor.py << 'EOF'
"""
TennisTrader -- In-Play Monitor
Tennis-specific in-play monitoring.

Key difference from football:
  - Poll every 15 seconds (tennis moves faster)
  - Trigger on game/set events not minutes
  - Break of serve = significant odds movement
  - Exit logic based on sets won not time

Phase 1C: Implementation target.
"""

import time
from config.config import config


def monitor_match(market_id: str, backed_player: str,
                  back_odds: float, stake: float):
    """
    Monitor a live tennis match.

    Triggers:
      - Player wins a set      -> assess green-up
      - Player loses a set     -> assess cut
      - Break of serve         -> odds movement, reassess
      - Match complete         -> settle

    Phase 1C: stub.
    """
    poll_interval = config["poll_interval_seconds"]
    while True:
        # TODO: Phase 1C
        # 1. Fetch market book
        # 2. Parse current score (sets, games)
        # 3. Check exit engine
        # 4. Place lay if triggered
        time.sleep(poll_interval)
EOF

# ── src/exit_engine.py ────────────────────────────────────────────────────────
cat > src/exit_engine.py << 'EOF'
"""
TennisTrader -- Exit Engine
Tennis-specific green-up and loss-cut logic.

Tennis exit triggers differ from football:
  - Set won by backed player   -> odds shorten, assess green-up
  - Set lost by backed player  -> odds lengthen, assess cut
  - Two sets down (best of 3)  -> match effectively over, cut
  - Match point reached        -> green up immediately

Phase 1C: Implementation target.
"""

from config.config import config


def calculate_exit_score(backed_player: str,
                         current_set_score: tuple,
                         current_odds: float,
                         back_odds: float,
                         stake: float,
                         best_of: int = 3) -> dict:
    """
    Calculate exit recommendation based on current match state.

    Returns dict:
        action:      "GREEN_UP" / "CUT" / "HOLD"
        lay_pct:     Fraction of position to lay
        reason:      Human-readable explanation
        locked_pnl:  Guaranteed P&L if green-up executed now
    """
    sets_won  = current_set_score[0]
    sets_lost = current_set_score[1]
    sets_needed = (best_of // 2) + 1

    # Calculate current green-up value
    green_up_profit = (stake * back_odds / current_odds) - stake
    threshold       = stake * config["greenup_profit_threshold"]

    # Match effectively over -- backed player two sets down in best of 3
    if sets_lost >= sets_needed - 1 and sets_won == 0 and best_of == 3:
        return {
            "action":     "CUT",
            "lay_pct":    0.0,
            "reason":     "Two sets down -- cut remaining value",
            "locked_pnl": -stake,
        }

    # Green up if profit threshold exceeded
    if green_up_profit >= threshold:
        return {
            "action":     "GREEN_UP",
            "lay_pct":    1.0,
            "reason":     f"Profit threshold reached -- lock in £{green_up_profit:.2f}",
            "locked_pnl": round(green_up_profit, 2),
        }

    # Backed player winning -- hold
    if sets_won > sets_lost:
        return {
            "action":     "HOLD",
            "lay_pct":    0.0,
            "reason":     "Ahead in sets -- hold position",
            "locked_pnl": 0.0,
        }

    return {
        "action":     "HOLD",
        "lay_pct":    0.0,
        "reason":     "Monitoring",
        "locked_pnl": 0.0,
    }
EOF

# ── src/lay_placer.py ─────────────────────────────────────────────────────────
cat > src/lay_placer.py << 'EOF'
"""
TennisTrader -- Lay Placer
Identical logic to ScoreTrader.
"""


def calculate_lay_stake(back_stake: float, back_odds: float,
                        lay_odds: float, lay_pct: float = 1.0) -> float:
    return round((back_stake * back_odds) / lay_odds * lay_pct, 2)


def place_lay(market_id: str, player: str,
              lay_stake: float, lay_odds: float) -> dict:
    """Place a lay bet. Phase 1C: stub."""
    pass
EOF

# ── src/settler.py ────────────────────────────────────────────────────────────
cat > src/settler.py << 'EOF'
"""
TennisTrader -- Settler
Post-match P&L calculation.
"""


def settle_match(match_id: str) -> dict:
    """Calculate final P&L for a match. Phase 1C: stub."""
    pass


def format_settlement_message(settlement: dict) -> str:
    """Format WhatsApp settlement summary. Phase 1C: stub."""
    pass
EOF

# ── src/logger.py ─────────────────────────────────────────────────────────────
cat > src/logger.py << 'EOF'
"""
TennisTrader -- Logger
SQLite trade and event logger.
"""

import sqlite3
import datetime
from config.config import config

DB_PATH = config["db_path"]


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialise_db():
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS matches (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        tour         TEXT,
        tournament   TEXT,
        surface      TEXT,
        round        TEXT,
        player_a     TEXT,
        player_b     TEXT,
        match_date   TEXT,
        market_id    TEXT UNIQUE,
        status       TEXT DEFAULT 'pending'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS backs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id     INTEGER,
        placed_at    TEXT,
        player       TEXT,
        stake        REAL,
        odds         REAL,
        model_prob   REAL,
        edge_pct     REAL,
        bet_id       TEXT,
        status       TEXT DEFAULT 'open',
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lays (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        back_id      INTEGER,
        match_id     INTEGER,
        placed_at    TEXT,
        player       TEXT,
        lay_stake    REAL,
        lay_odds     REAL,
        lay_pct      REAL,
        trigger      TEXT,
        set_score    TEXT,
        bet_id       TEXT,
        FOREIGN KEY (back_id)  REFERENCES backs(id),
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS settlements (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id     INTEGER,
        settled_at   TEXT,
        winner       TEXT,
        final_score  TEXT,
        total_backed REAL,
        total_laid   REAL,
        gross_pnl    REAL,
        commission   REAL,
        net_pnl      REAL,
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    conn.commit()
    conn.close()
    print(f"Database initialised: {DB_PATH}")


def log_match(tour, tournament, surface, round_,
              player_a, player_b, match_date, market_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO matches
        (created_at, tour, tournament, surface, round,
         player_a, player_b, match_date, market_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.datetime.utcnow().isoformat(), tour, tournament,
         surface, round_, player_a, player_b, match_date, market_id))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return mid


def log_back(match_id, player, stake, odds, model_prob, edge_pct, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO backs
        (match_id, placed_at, player, stake, odds, model_prob, edge_pct, bet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, datetime.datetime.utcnow().isoformat(),
         player, stake, odds, model_prob, edge_pct, bet_id))
    conn.commit()
    bid = c.lastrowid
    conn.close()
    return bid


def log_lay(back_id, match_id, player, lay_stake,
            lay_odds, lay_pct, trigger, set_score, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO lays
        (back_id, match_id, placed_at, player, lay_stake,
         lay_odds, lay_pct, trigger, set_score, bet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (back_id, match_id, datetime.datetime.utcnow().isoformat(),
         player, lay_stake, lay_odds, lay_pct, trigger, set_score, bet_id))
    conn.commit()
    conn.close()


def log_settlement(match_id, winner, final_score, total_backed,
                   total_laid, gross_pnl, commission, net_pnl):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO settlements
        (match_id, settled_at, winner, final_score, total_backed,
         total_laid, gross_pnl, commission, net_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, datetime.datetime.utcnow().isoformat(), winner,
         final_score, total_backed, total_laid, gross_pnl, commission, net_pnl))
    c.execute("UPDATE matches SET status='settled' WHERE id=?", (match_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialise_db()
EOF

# ── main.py ───────────────────────────────────────────────────────────────────
cat > main.py << 'EOF'
"""
TennisTrader -- Main Orchestrator
Entry point for the pre-match pipeline.

Usage:
    python main.py
    python main.py --date 2026-06-30
    python main.py --tournament wimbledon
"""

import argparse
import datetime
from config.config import config
from src.logger import initialise_db


def run(match_date: str = None, tournament: str = None):
    if match_date is None:
        match_date = datetime.date.today().isoformat()

    print(f"\nTennisTrader -- {match_date}")
    if tournament:
        print(f"Tournament filter: {tournament}")
    print("=" * 50)

    initialise_db()

    # Phase 1A: data pipeline -> bradley-terry model -> value engine
    # Phase 1B: odds fetch -> pre-match selections
    # Phase 1C: bet placement -> inplay monitor

    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TennisTrader")
    parser.add_argument("--date",       type=str, default=None)
    parser.add_argument("--tournament", type=str, default=None)
    args = parser.parse_args()
    run(args.date, args.tournament)
EOF

# ── scripts/backtest.py ───────────────────────────────────────────────────────
cat > scripts/backtest.py << 'EOF'
"""
TennisTrader -- Backtester
Validates the Bradley-Terry model against real Betfair/Pinnacle closing odds.

KEY ADVANTAGE OVER SCORETRADER:
tennis-data.co.uk includes real closing odds (B365, Pinnacle, Average).
This means we test against actual market prices -- no synthetic odds problem.
Pinnacle odds are the sharpest available and the best benchmark for edge.

Phase 1A: Implementation target.
"""

import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.bradley_terry import surface_adjusted_probability, build_ratings
from src.value_engine import calculate_edge, kelly_stake, assess_match
from config.config import config

MIN_PRIOR_MATCHES = config["min_matches_required"]
KELLY_FRACTION    = config["kelly_fraction"]
BANK              = 1000.0
MIN_EDGE          = config["min_edge_pct"]
MIN_ODDS          = config["min_odds"]
MAX_ODDS          = config["max_odds"]


def run_backtest(odds_df: pd.DataFrame,
                 match_df: pd.DataFrame) -> pd.DataFrame:
    """
    For each match in odds_df:
      1. Build ratings using only prior match_df data
      2. Generate model probability
      3. Compare against real closing odds (Pinnacle preferred)
      4. Simulate bet if edge found
      5. Calculate P&L

    Returns DataFrame of all simulated bets.
    """
    odds_df = odds_df.copy()
    odds_df["Date"] = pd.to_datetime(odds_df["Date"], errors="coerce")
    odds_df = odds_df.dropna(subset=["Date", "Winner", "Loser"])
    odds_df = odds_df.sort_values("Date").reset_index(drop=True)

    match_df = match_df.copy()
    match_df["tourney_date"] = pd.to_datetime(
        match_df["tourney_date"], errors="coerce"
    )

    results = []
    skipped = 0

    print(f"Running backtest on {len(odds_df)} matches...")
    print(f"Min edge: {MIN_EDGE}%  |  Kelly: {KELLY_FRACTION}  |  Bank: £{BANK}")
    print("-" * 60)

    for idx, match in odds_df.iterrows():
        # Use only prior data
        prior_match_df = match_df[
            match_df["tourney_date"] < match["Date"]
        ]

        if len(prior_match_df) < MIN_PRIOR_MATCHES * 2:
            skipped += 1
            continue

        player_a = match["Winner"]
        player_b = match["Loser"]
        surface  = match.get("Surface", "hard").lower()

        # Get real closing odds -- prefer Pinnacle, fall back to Bet365, then Average
        if "PSW" in match and pd.notna(match.get("PSW")) and match["PSW"] > 1:
            odds_a = float(match["PSW"])
            odds_b = float(match["PSL"])
            odds_source = "Pinnacle"
        elif "B365W" in match and pd.notna(match.get("B365W")) and match["B365W"] > 1:
            odds_a = float(match["B365W"])
            odds_b = float(match["B365L"])
            odds_source = "Bet365"
        elif "AvgW" in match and pd.notna(match.get("AvgW")) and match["AvgW"] > 1:
            odds_a = float(match["AvgW"])
            odds_b = float(match["AvgL"])
            odds_source = "Average"
        else:
            skipped += 1
            continue

        # Check odds are in acceptable range
        if not (MIN_ODDS <= odds_a <= MAX_ODDS and
                MIN_ODDS <= odds_b <= MAX_ODDS):
            skipped += 1
            continue

        try:
            # Model probability
            p_a = surface_adjusted_probability(
                player_a, player_b, prior_match_df, surface
            )
            p_b = 1 - p_a

            # Assess both players for value
            for player, prob, odds in [
                (player_a, p_a, odds_a),
                (player_b, p_b, odds_b),
            ]:
                assessment = assess_match(prob, odds, BANK)

                if assessment["value"]:
                    won = (player == player_a)  # Winner is always player_a in odds_df
                    pnl = round(
                        (odds - 1) * assessment["stake"] if won
                        else -assessment["stake"], 2
                    )

                    results.append({
                        "date":         match["Date"].date(),
                        "tournament":   match.get("Tournament", ""),
                        "surface":      surface,
                        "player_a":     player_a,
                        "player_b":     player_b,
                        "backed":       player,
                        "model_prob":   round(prob * 100, 2),
                        "market_odds":  odds,
                        "odds_source":  odds_source,
                        "edge_pct":     assessment["edge_pct"],
                        "stake":        assessment["stake"],
                        "won":          won,
                        "pnl":          pnl,
                    })

        except Exception:
            skipped += 1
            continue

    print(f"Skipped: {skipped} matches")
    return pd.DataFrame(results)


def print_summary(df: pd.DataFrame):
    if df.empty:
        print("No results.")
        return

    total_bets   = len(df)
    total_staked = df["stake"].sum()
    total_pnl    = df["pnl"].sum()
    winners      = df["won"].sum()
    roi          = (total_pnl / total_staked * 100) if total_staked > 0 else 0
    strike_rate  = (winners / total_bets * 100) if total_bets > 0 else 0

    print(f"\nBACKTEST RESULTS")
    print("=" * 55)
    print(f"Total bets:       {total_bets:,}")
    print(f"Winners:          {winners:,}  ({strike_rate:.1f}%)")
    print(f"Total staked:     £{total_staked:,.2f}")
    print(f"Total P&L:        £{total_pnl:,.2f}")
    print(f"ROI:              {roi:.2f}%")

    print(f"\nP&L BY SURFACE")
    print("-" * 55)
    by_surface = df.groupby("surface").agg(
        bets   = ("pnl", "count"),
        staked = ("stake", "sum"),
        pnl    = ("pnl", "sum"),
        wins   = ("won", "sum"),
    )
    by_surface["roi"]      = (by_surface["pnl"] / by_surface["staked"] * 100).round(2)
    by_surface["win_pct"]  = (by_surface["wins"] / by_surface["bets"] * 100).round(1)
    print(by_surface.to_string())

    print(f"\nP&L BY YEAR")
    print("-" * 55)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    by_year = df.groupby("year").agg(
        bets   = ("pnl", "count"),
        staked = ("stake", "sum"),
        pnl    = ("pnl", "sum"),
    )
    by_year["roi"] = (by_year["pnl"] / by_year["staked"] * 100).round(2)
    print(by_year.to_string())

    print(f"\nP&L BY ODDS SOURCE")
    print("-" * 55)
    by_source = df.groupby("odds_source").agg(
        bets   = ("pnl", "count"),
        staked = ("stake", "sum"),
        pnl    = ("pnl", "sum"),
    )
    by_source["roi"] = (by_source["pnl"] / by_source["staked"] * 100).round(2)
    print(by_source.to_string())

    out_path = "data/processed/backtest_results.csv"
    df.to_csv(out_path, index=False)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    processed = config["processed_data_path"]
    odds_file  = os.path.join(processed, "odds_data.csv")
    match_file = os.path.join(processed, "match_data.csv")

    if not os.path.exists(odds_file) or not os.path.exists(match_file):
        print("Data not found. Run data_pipeline.py first.")
    else:
        odds_df  = pd.read_csv(odds_file)
        match_df = pd.read_csv(match_file)

        # Filter to ATP only for initial backtest
        odds_df  = odds_df[odds_df["Tour"] == "ATP"]
        match_df = match_df[match_df["Tour"] == "ATP"]

        results = run_backtest(odds_df, match_df)
        print_summary(results)
EOF

# ── tests/test_bradley_terry.py ───────────────────────────────────────────────
cat > tests/test_bradley_terry.py << 'EOF'
"""TennisTrader -- Bradley-Terry Model Tests"""

import numpy as np
import pandas as pd
import pytest
from src.bradley_terry import match_win_probability, compute_recency_weight
from src.match_model import match_outcomes_best_of_3, match_outcomes_best_of_5


def test_match_win_probability_symmetry():
    """P(A beats B) + P(B beats A) should equal 1."""
    ratings = pd.Series({"Player A": 1.5, "Player B": 0.5})
    p_ab = match_win_probability("Player A", "Player B", ratings)
    p_ba = match_win_probability("Player B", "Player A", ratings)
    assert abs(p_ab + p_ba - 1.0) < 0.001


def test_match_win_probability_unknown_player():
    """Unknown player should return 0.5."""
    ratings = pd.Series({"Player A": 1.0})
    p = match_win_probability("Player A", "Unknown", ratings)
    assert p == 0.5


def test_recency_weight_today():
    """Match today should have weight 1.0."""
    today = pd.Timestamp.now()
    w = compute_recency_weight(today, today, half_life_days=180)
    assert abs(w - 1.0) < 0.001


def test_recency_weight_half_life():
    """Match at half_life_days ago should have weight ~0.5."""
    today    = pd.Timestamp.now()
    past     = today - pd.Timedelta(days=180)
    w        = compute_recency_weight(past, today, half_life_days=180)
    assert abs(w - 0.5) < 0.01


def test_best_of_3_sums_to_one():
    """Set score probabilities should sum to 1."""
    outcomes = match_outcomes_best_of_3(0.65)
    assert abs(sum(outcomes.values()) - 1.0) < 0.001


def test_best_of_5_sums_to_one():
    """Set score probabilities should sum to 1."""
    outcomes = match_outcomes_best_of_5(0.65)
    assert abs(sum(outcomes.values()) - 1.0) < 0.001


def test_stronger_player_wins_more():
    """Stronger player should win 2-0 more often than weaker player."""
    outcomes = match_outcomes_best_of_3(0.70)
    assert outcomes["2-0"] > outcomes["0-2"]


def test_even_match_is_symmetric():
    """50/50 match should have symmetric set score probabilities."""
    outcomes = match_outcomes_best_of_3(0.50)
    assert abs(outcomes["2-0"] - outcomes["0-2"]) < 0.001
    assert abs(outcomes["2-1"] - outcomes["1-2"]) < 0.001
EOF

# ── Git setup ─────────────────────────────────────────────────────────────────
git config user.name "Mark"
git config user.email "jakmar86@github.com"
git add .
git commit -m "Initial scaffold -- TennisTrader Phase 1A"
git branch -M main
git push -u origin main

echo ""
echo "================================================"
echo "TennisTrader scaffold complete and pushed!"
echo "================================================"
