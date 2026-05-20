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
TENNIS_DATA_BASE_ATP = "http://www.tennis-data.co.uk/{year}/{year}.xlsx"
TENNIS_DATA_BASE_WTA = "http://www.tennis-data.co.uk/{year}w/{year}.xlsx"

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
    base  = TENNIS_DATA_BASE_ATP if tour == "ATP" else TENNIS_DATA_BASE_WTA
    url   = base.format(year=year)
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
