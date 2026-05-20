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
