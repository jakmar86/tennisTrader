"""
TennisTrader -- Head to Head Model
Adjusts match win probability based on historical H2H records.

Logic:
  - If players have met 3+ times, H2H record has predictive value
  - Weight H2H more heavily on same surface
  - Blend with BT probability based on H2H sample size
  - Small samples (1-2 matches) get minimal weight
"""

import numpy as np
import pandas as pd


def get_h2h_record(player_a: str, player_b: str,
                   df: pd.DataFrame,
                   surface: str = None,
                   reference_date: pd.Timestamp = None) -> dict:
    """
    Get H2H record between two players from prior match data.
    Returns dict with wins_a, wins_b, total, surface_wins_a, surface_wins_b
    """
    if reference_date is not None:
        df = df[df["tourney_date"] < reference_date]

    # All matches between these two players
    h2h = df[
        ((df["winner_name"] == player_a) & (df["loser_name"] == player_b)) |
        ((df["winner_name"] == player_b) & (df["loser_name"] == player_a))
    ]

    wins_a = len(h2h[h2h["winner_name"] == player_a])
    wins_b = len(h2h[h2h["winner_name"] == player_b])
    total  = wins_a + wins_b

    # Surface specific
    if surface and "surface" in df.columns:
        h2h_surf    = h2h[h2h["surface"].str.lower() == surface.lower()]
        surf_wins_a = len(h2h_surf[h2h_surf["winner_name"] == player_a])
        surf_wins_b = len(h2h_surf[h2h_surf["winner_name"] == player_b])
        surf_total  = surf_wins_a + surf_wins_b
    else:
        surf_wins_a = surf_wins_b = surf_total = 0

    return {
        "wins_a":       wins_a,
        "wins_b":       wins_b,
        "total":        total,
        "surf_wins_a":  surf_wins_a,
        "surf_wins_b":  surf_wins_b,
        "surf_total":   surf_total,
    }


def h2h_adjusted_probability(player_a: str, player_b: str,
                              bt_prob: float,
                              df: pd.DataFrame,
                              surface: str = None,
                              reference_date: pd.Timestamp = None) -> float:
    """
    Blend BT probability with H2H record.

    Blending weight scales with H2H sample size:
      0-2 meetings:   0% H2H weight (too small)
      3-5 meetings:   15% H2H weight
      6-9 meetings:   25% H2H weight
      10+ meetings:   35% H2H weight (Djokovic/Nadal type rivalries)

    Surface H2H gets extra weight when available.
    """
    h2h = get_h2h_record(player_a, player_b, df, surface, reference_date)

    total = h2h["total"]

    if total < 3:
        return bt_prob

    # H2H win probability for player A
    h2h_prob = h2h["wins_a"] / total

    # Surface H2H overrides overall if sufficient sample
    if h2h["surf_total"] >= 3:
        surf_h2h_prob = h2h["surf_wins_a"] / h2h["surf_total"]
        # Blend overall and surface H2H
        h2h_prob = 0.40 * h2h_prob + 0.60 * surf_h2h_prob

    # Weight based on sample size
    if total >= 10:
        h2h_weight = 0.35
    elif total >= 6:
        h2h_weight = 0.25
    else:
        h2h_weight = 0.15

    blended = (1 - h2h_weight) * bt_prob + h2h_weight * h2h_prob
    return round(float(blended), 4)


if __name__ == "__main__":
    import os
    from config.config import config

    match_file = os.path.join(config["processed_data_path"], "match_data.csv")
    df = pd.read_csv(match_file)
    df = df[df["Tour"] == "ATP"]
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], errors="coerce")

    # Test famous rivalries
    rivalries = [
        ("Novak Djokovic", "Rafael Nadal",   "clay"),
        ("Novak Djokovic", "Rafael Nadal",   "hard"),
        ("Carlos Alcaraz", "Jannik Sinner",  "hard"),
        ("Novak Djokovic", "Carlos Alcaraz", "grass"),
    ]

    print(f"{'Matchup':<45} {'Surface':<8} {'H2H':<10} {'Wins A':>8} {'Wins B':>8}")
    print("-" * 85)
    for a, b, surface in rivalries:
        h2h = get_h2h_record(a, b, df, surface)
        matchup = f"{a} vs {b}"
        print(f"{matchup:<45} {surface:<8} {h2h['total']:<10} "
              f"{h2h['wins_a']:>8} {h2h['wins_b']:>8}")
