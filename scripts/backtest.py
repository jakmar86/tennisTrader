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
