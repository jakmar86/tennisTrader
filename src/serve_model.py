"""
TennisTrader -- Serve Statistics Model
Enhances Bradley-Terry ratings with serve dominance metrics.

Key metrics:
  Service rating:  how dominant a player is on serve
  Return rating:   how well a player breaks opponents
  Combined:        weighted blend with BT rating

Academic basis: serve dominance explains ~65% of match outcomes
in tennis (Klaassen & Magnus 2001, updated studies).
"""

import numpy as np
import pandas as pd
from config.config import config


def compute_serve_stats(df: pd.DataFrame,
                        reference_date: pd.Timestamp = None,
                        half_life_days: int = 180) -> pd.DataFrame:
    """
    Compute weighted serve and return statistics per player.

    Returns DataFrame with columns:
        player | serve_rating | return_rating | combined_rating | matches
    """
    if reference_date is None:
        reference_date = pd.Timestamp.now()

    df = df.copy()
    df["tourney_date"] = pd.to_datetime(df["tourney_date"], errors="coerce")
    df = df.dropna(subset=["tourney_date", "winner_name", "loser_name"])

    # Required serve stat columns
    serve_cols = ["w_1stIn", "w_1stWon", "w_2ndWon", "w_SvGms",
                  "w_bpSaved", "w_bpFaced",
                  "l_1stIn", "l_1stWon", "l_2ndWon", "l_SvGms",
                  "l_bpSaved", "l_bpFaced", "w_svpt", "l_svpt"]

    available = [c for c in serve_cols if c in df.columns]
    if len(available) < 8:
        return pd.DataFrame()

    df = df.dropna(subset=available[:8])

    # Recency weights
    df["weight"] = df["tourney_date"].apply(
        lambda d: 0.5 ** ((reference_date - d).days / half_life_days)
        if (reference_date - d).days >= 0 else 0
    )
    df = df[df["weight"] > 0.01]

    players = sorted(set(df["winner_name"]) | set(df["loser_name"]))
    stats   = []

    for player in players:
        w_games = df[df["winner_name"] == player]
        l_games = df[df["loser_name"]  == player]

        # Weighted serve stats as winner
        w_weight = w_games["weight"].sum()
        l_weight = l_games["weight"].sum()
        total_w  = w_weight + l_weight

        if total_w < 1 or (len(w_games) + len(l_games)) < config["min_matches_required"]:
            continue

        # First serve percentage
        def wavg(series, weights):
            if weights.sum() == 0:
                return np.nan
            return (series * weights).sum() / weights.sum()

        # As winner: use w_ columns
        # As loser: use l_ columns
        fs_pct_w = (wavg(w_games["w_1stIn"] / w_games["w_svpt"].clip(1), w_games["weight"])
                    if len(w_games) > 0 and "w_svpt" in w_games.columns else np.nan)
        fs_pct_l = (wavg(l_games["l_1stIn"] / l_games["l_svpt"].clip(1), l_games["weight"])
                    if len(l_games) > 0 and "l_svpt" in l_games.columns else np.nan)

        fs_won_w = (wavg(w_games["w_1stWon"] / w_games["w_1stIn"].clip(1), w_games["weight"])
                    if len(w_games) > 0 else np.nan)
        fs_won_l = (wavg(l_games["l_1stWon"] / l_games["l_1stIn"].clip(1), l_games["weight"])
                    if len(l_games) > 0 else np.nan)

        ss_won_w = (wavg(w_games["w_2ndWon"] / (w_games["w_svpt"] - w_games["w_1stIn"]).clip(1),
                         w_games["weight"]) if len(w_games) > 0 else np.nan)
        ss_won_l = (wavg(l_games["l_2ndWon"] / (l_games["l_svpt"] - l_games["l_1stIn"]).clip(1),
                         l_games["weight"]) if len(l_games) > 0 else np.nan)

        bp_saved_w = (wavg(w_games["w_bpSaved"] / w_games["w_bpFaced"].clip(1), w_games["weight"])
                      if len(w_games) > 0 else np.nan)
        bp_saved_l = (wavg(l_games["l_bpSaved"] / l_games["l_bpFaced"].clip(1), l_games["weight"])
                      if len(l_games) > 0 else np.nan)

        # Combine winner and loser appearances
        def blend(a, b, wa, wb):
            if pd.isna(a) and pd.isna(b):
                return np.nan
            if pd.isna(a):
                return b
            if pd.isna(b):
                return a
            total = wa + wb
            return (a * wa + b * wb) / total if total > 0 else np.nan

        fs_pct   = blend(fs_pct_w,   fs_pct_l,   w_weight, l_weight)
        fs_won   = blend(fs_won_w,   fs_won_l,   w_weight, l_weight)
        ss_won   = blend(ss_won_w,   ss_won_l,   w_weight, l_weight)
        bp_saved = blend(bp_saved_w, bp_saved_l, w_weight, l_weight)

        if any(pd.isna(x) for x in [fs_pct, fs_won, ss_won]):
            continue

        # Serve rating: composite of first serve dominance
        # Weights from academic literature on point importance
        serve_rating = (
            0.35 * fs_pct   +   # Getting first serve in
            0.40 * fs_won   +   # Winning on first serve
            0.25 * ss_won       # Winning on second serve
        )

        # Return rating: proxy from bp_saved (lower = better returner)
        return_rating = 1.0 - (bp_saved if not pd.isna(bp_saved) else 0.65)

        stats.append({
            "player":         player,
            "serve_rating":   round(serve_rating, 4),
            "return_rating":  round(return_rating, 4),
            "matches":        len(w_games) + len(l_games),
        })

    df_stats = pd.DataFrame(stats)
    if df_stats.empty:
        return df_stats

    # Normalise to mean 0, std 1
    for col in ["serve_rating", "return_rating"]:
        mean = df_stats[col].mean()
        std  = df_stats[col].std()
        if std > 0:
            df_stats[col] = (df_stats[col] - mean) / std

    # Combined rating
    df_stats["combined_rating"] = (
        0.60 * df_stats["serve_rating"] +
        0.40 * df_stats["return_rating"]
    )

    return df_stats.set_index("player")


def serve_adjusted_probability(player_a: str, player_b: str,
                                bt_prob: float,
                                serve_stats: pd.DataFrame,
                                serve_weight: float = 0.30) -> float:
    """
    Blend Bradley-Terry probability with serve-stats probability.

    serve_weight: how much to weight serve stats vs BT rating
                  0.0 = pure BT, 1.0 = pure serve stats
                  0.30 = 30% serve stats, 70% BT (recommended starting point)
    """
    if serve_stats.empty:
        return bt_prob

    if (player_a not in serve_stats.index or
            player_b not in serve_stats.index):
        return bt_prob

    rating_a = serve_stats.loc[player_a, "combined_rating"]
    rating_b = serve_stats.loc[player_b, "combined_rating"]

    # Convert serve rating differential to probability
    diff          = rating_a - rating_b
    serve_prob_a  = 1.0 / (1.0 + np.exp(-diff))

    # Blend
    blended = (1 - serve_weight) * bt_prob + serve_weight * serve_prob_a

    return round(float(blended), 4)


if __name__ == "__main__":
    import os
    match_file = os.path.join(config["processed_data_path"], "match_data.csv")

    if not os.path.exists(match_file):
        print("No match data found. Run data_pipeline.py first.")
    else:
        df = pd.read_csv(match_file)
        df = df[df["Tour"] == "ATP"]

        print("Computing ATP serve statistics...")
        stats = compute_serve_stats(df)

        if not stats.empty:
            print(f"\nTop 15 ATP players by serve rating:")
            print(stats.sort_values("serve_rating", ascending=False)
                  .head(15)[["serve_rating","return_rating","combined_rating","matches"]]
                  .to_string())

            print(f"\nTop 15 ATP players by return rating:")
            print(stats.sort_values("return_rating", ascending=False)
                  .head(15)[["serve_rating","return_rating","combined_rating","matches"]]
                  .to_string())
        else:
            print("No serve stats computed -- check data columns.")
