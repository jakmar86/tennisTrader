"""
TennisTrader -- Recent Form Model
Adjusts probability based on last N match results.

Logic:
  - Players on winning streaks are underrated by historical ratings
  - Players on losing runs are overrated
  - Weight: last 5 matches on same surface most predictive
"""

import numpy as np
import pandas as pd


def get_recent_form(player: str, df: pd.DataFrame,
                    n_matches: int = 5,
                    surface: str = None,
                    reference_date: pd.Timestamp = None) -> dict:
    """
    Get recent form for a player -- last N matches.
    Returns win rate and streak info.
    """
    if reference_date is not None:
        df = df[df["tourney_date"] < reference_date]

    # All matches for this player
    player_matches = df[
        (df["winner_name"] == player) | (df["loser_name"] == player)
    ].sort_values("tourney_date", ascending=False)

    # Surface filter if specified
    if surface and "surface" in df.columns:
        surf_matches = player_matches[
            player_matches["surface"].str.lower() == surface.lower()
        ].head(n_matches)
        if len(surf_matches) >= 3:
            player_matches = surf_matches
        else:
            player_matches = player_matches.head(n_matches)
    else:
        player_matches = player_matches.head(n_matches)

    if len(player_matches) == 0:
        return {"win_rate": 0.5, "streak": 0, "matches": 0}

    wins   = len(player_matches[player_matches["winner_name"] == player])
    total  = len(player_matches)
    win_rate = wins / total

    # Current streak (positive = winning, negative = losing)
    streak = 0
    for _, row in player_matches.iterrows():
        if row["winner_name"] == player:
            if streak >= 0:
                streak += 1
            else:
                break
        else:
            if streak <= 0:
                streak -= 1
            else:
                break

    return {
        "win_rate": round(win_rate, 3),
        "streak":   streak,
        "matches":  total,
    }


def form_adjusted_probability(player_a: str, player_b: str,
                               bt_prob: float,
                               df: pd.DataFrame,
                               surface: str = None,
                               reference_date: pd.Timestamp = None,
                               form_weight: float = 0.15) -> float:
    """
    Blend BT probability with recent form differential.
    form_weight: 0.15 recommended -- form is noisy signal
    """
    form_a = get_recent_form(player_a, df, surface=surface,
                              reference_date=reference_date)
    form_b = get_recent_form(player_b, df, surface=surface,
                              reference_date=reference_date)

    if form_a["matches"] < 3 or form_b["matches"] < 3:
        return bt_prob

    # Form probability based on recent win rates
    total_wr = form_a["win_rate"] + form_b["win_rate"]
    if total_wr == 0:
        return bt_prob

    form_prob = form_a["win_rate"] / total_wr

    blended = (1 - form_weight) * bt_prob + form_weight * form_prob
    return round(float(blended), 4)


def form_adjusted_probability_no_clay(player_a, player_b, bt_prob, df,
                                       surface=None, reference_date=None,
                                       form_weight=0.15):
    """Form adjustment disabled on clay."""
    if surface and surface.lower() == "clay":
        return bt_prob
    return form_adjusted_probability(player_a, player_b, bt_prob, df,
                                     surface, reference_date, form_weight)


if __name__ == "__main__":
    import os
    from config.config import config

    match_file = os.path.join(config["processed_data_path"], "match_data.csv")
    df = pd.read_csv(match_file)
    df = df[df["Tour"] == "ATP"]
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], errors="coerce")

    players = ["Jannik Sinner", "Carlos Alcaraz", "Novak Djokovic",
               "Alexander Zverev", "Daniil Medvedev"]

    print(f"{'Player':<25} {'Win Rate':>10} {'Streak':>8} {'Matches':>8}")
    print("-" * 55)
    for player in players:
        form = get_recent_form(player, df, n_matches=10)
        print(f"{player:<25} {form['win_rate']:>10.1%} {form['streak']:>8} {form['matches']:>8}")
