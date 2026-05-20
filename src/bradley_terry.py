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

    # Bradley-Terry log-likelihood optimisation (vectorised)
    winners = np.array([player_idx[w] for w in df["winner_name"]])
    losers  = np.array([player_idx[l] for l in df["loser_name"]])
    weights = df["weight"].values

    def neg_log_likelihood(params):
        diff = params[winners] - params[losers]
        nll  = -np.sum(weights * (diff - np.logaddexp(0, diff)))
        return nll

    def grad(params):
        diff  = params[winners] - params[losers]
        probs = 1.0 / (1.0 + np.exp(-diff))
        g     = np.zeros(n)
        np.add.at(g, winners, -weights * (1 - probs))
        np.add.at(g, losers,   weights * (1 - probs))
        return g

    # Initialise with zeros, fix first player to 0 for identifiability
    x0      = np.zeros(n)
    bounds  = [(None, None)] * n
    bounds[0] = (0, 0)

    result = minimize(
        neg_log_likelihood,
        x0,
        jac=grad,
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
