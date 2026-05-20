"""
TennisTrader -- Fast Backtester
Builds ratings monthly (not per-match) for speed.
Results virtually identical to per-match rebuild.
"""

import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.abspath('.'))

from src.bradley_terry import build_ratings, match_win_probability
from src.name_utils import add_sackmann_names
from src.h2h_model import h2h_adjusted_probability
from src.form_model import form_adjusted_probability, form_adjusted_probability_no_clay
from src.value_engine import calculate_edge, kelly_stake
from config.config import config

MIN_PRIOR_MATCHES = config["min_matches_required"]
KELLY_FRACTION    = config["kelly_fraction"]
BANK              = 1000.0
MIN_EDGE          = config["min_edge_pct"]
MAX_EDGE          = config.get("max_edge_pct", 3.0)
MIN_ODDS          = config["min_odds"]
MAX_ODDS          = config["max_odds"]


def valid_odds(val):
    try:
        return pd.notna(val) and float(val) > 1.0
    except (TypeError, ValueError):
        return False


def run_fast_backtest(odds_df: pd.DataFrame,
                      match_df: pd.DataFrame) -> pd.DataFrame:

    odds_df  = odds_df.copy()
    match_df = match_df.copy()

    odds_df["Date"]           = pd.to_datetime(odds_df["Date"], errors="coerce")
    match_df["tourney_date"]  = pd.to_datetime(match_df["tourney_date"], errors="coerce")

    odds_df  = odds_df.dropna(subset=["Date","Winner","Loser"]).sort_values("Date")
    match_df = match_df.dropna(subset=["tourney_date","winner_name","loser_name"])

    # Build ratings once per month per surface
    # Cache: (year, month, surface) -> ratings Series
    print("Building monthly rating cache...")
    cache        = {}
    months       = pd.period_range(
        odds_df["Date"].min().to_period("M"),
        odds_df["Date"].max().to_period("M"),
        freq="M"
    )
    surfaces = ["hard", "clay", "grass"]

    for month in months:
        cutoff   = month.start_time
        prior_df = match_df[match_df["tourney_date"] < cutoff]
        if len(prior_df) < MIN_PRIOR_MATCHES * 2:
            continue
        # Overall ratings
        cache[(month, "all")] = build_ratings(prior_df)
        # Surface ratings
        for surface in surfaces:
            surf_df = prior_df[prior_df["surface"].str.lower() == surface]
            if len(surf_df) >= MIN_PRIOR_MATCHES:
                cache[(month, surface)] = build_ratings(surf_df)

    print(f"Cache built: {len(cache)} rating sets")
    # Convert odds names to Sackmann format
    odds_df = add_sackmann_names(odds_df, match_df)
    print(f"Running backtest on {len(odds_df)} matches...")
    print("-" * 60)

    results = []
    skipped = 0

    for idx, match in odds_df.iterrows():
        month   = match["Date"].to_period("M")
        surface = str(match.get("Surface", "hard")).lower()
        if surface not in surfaces:
            surface = "hard"

        # Get ratings
        overall_ratings = cache.get((month, "all"))
        surface_ratings = cache.get((month, surface))

        if overall_ratings is None:
            skipped += 1
            continue

        player_a = match["sackmann_winner"]
        player_b = match["sackmann_loser"]
        if not player_a or not player_b:
            skipped += 1
            continue

        # Check both players are rated
        if (player_a not in overall_ratings.index or
                player_b not in overall_ratings.index):
            skipped += 1
            continue

        # Surface-adjusted probability (60% surface, 40% overall)
        p_overall = match_win_probability(player_a, player_b, overall_ratings)

        if (surface_ratings is not None and
                player_a in surface_ratings.index and
                player_b in surface_ratings.index):
            p_surface = match_win_probability(player_a, player_b, surface_ratings)
            p_a = 0.60 * p_surface + 0.40 * p_overall
        else:
            p_a = p_overall

        # H2H adjustment
        ref_date = match["Date"] if pd.notna(match["Date"]) else None
        p_a = h2h_adjusted_probability(
            player_a, player_b, p_a, match_df, surface,
            reference_date=ref_date
        )
        # Form adjustment
        p_a = form_adjusted_probability_no_clay(
            player_a, player_b, p_a, match_df, surface,
            reference_date=ref_date
        )
        p_b = 1 - p_a

        # Get odds
        if valid_odds(match.get("PSW")) and valid_odds(match.get("PSL")):
            odds_a, odds_b, source = float(match["PSW"]), float(match["PSL"]), "Pinnacle"
        elif valid_odds(match.get("B365W")) and valid_odds(match.get("B365L")):
            odds_a, odds_b, source = float(match["B365W"]), float(match["B365L"]), "Bet365"
        elif valid_odds(match.get("AvgW")) and valid_odds(match.get("AvgL")):
            odds_a, odds_b, source = float(match["AvgW"]), float(match["AvgL"]), "Average"
        else:
            skipped += 1
            continue

        if not (MIN_ODDS <= odds_a <= MAX_ODDS and
                MIN_ODDS <= odds_b <= MAX_ODDS):
            skipped += 1
            continue

        # Assess value
        for player, prob, odds in [(player_a, p_a, odds_a), (player_b, p_b, odds_b)]:
            edge  = calculate_edge(prob, odds)
            stake = kelly_stake(prob, odds, BANK, KELLY_FRACTION)
            stake = min(stake, BANK * 0.05)

            if MIN_EDGE <= edge <= MAX_EDGE and stake > 0:
                won = (player == player_a)  # player_a is always the winner
                pnl = round((odds - 1) * stake if won else -stake, 2)

                results.append({
                    "date":        match["Date"].date(),
                    "tournament":  match.get("Tournament", ""),
                    "surface":     surface,
                    "player_a":    player_a,
                    "player_b":    player_b,
                    "backed":      player,
                    "model_prob":  round(prob * 100, 2),
                    "market_odds": odds,
                    "odds_source": source,
                    "edge_pct":    edge,
                    "stake":       stake,
                    "won":         won,
                    "pnl":         pnl,
                })

    print(f"Skipped: {skipped}")
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
        bets=("pnl","count"), staked=("stake","sum"),
        pnl=("pnl","sum"), wins=("won","sum")
    )
    by_surface["roi"]     = (by_surface["pnl"]/by_surface["staked"]*100).round(2)
    by_surface["win_pct"] = (by_surface["wins"]/by_surface["bets"]*100).round(1)
    print(by_surface.to_string())

    print(f"\nP&L BY YEAR")
    print("-" * 55)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    by_year = df.groupby("year").agg(
        bets=("pnl","count"), staked=("stake","sum"), pnl=("pnl","sum")
    )
    by_year["roi"] = (by_year["pnl"]/by_year["staked"]*100).round(2)
    print(by_year.to_string())

    print(f"\nP&L BY ODDS SOURCE")
    print("-" * 55)
    by_source = df.groupby("odds_source").agg(
        bets=("pnl","count"), staked=("stake","sum"), pnl=("pnl","sum")
    )
    by_source["roi"] = (by_source["pnl"]/by_source["staked"]*100).round(2)
    print(by_source.to_string())

    out_path = "data/processed/backtest_results.csv"
    df.to_csv(out_path, index=False)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    processed = config["processed_data_path"]
    odds_df   = pd.read_csv(f"{processed}odds_data.csv")
    match_df  = pd.read_csv(f"{processed}match_data.csv")

    # ATP only for initial backtest
    odds_df  = odds_df[odds_df["Tour"] == "ATP"]
    match_df = match_df[match_df["Tour"] == "ATP"]

    results = run_fast_backtest(odds_df, match_df)
    print_summary(results)
# This will be replaced -- see patch below
