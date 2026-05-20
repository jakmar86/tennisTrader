"""
TennisTrader -- Name Utilities
Converts tennis-data.co.uk name format (Last F.) 
to Jeff Sackmann format (First Last).
"""

import pandas as pd


def build_name_lookup(match_df: pd.DataFrame) -> dict:
    """
    Build lookup dict from Sackmann match data.
    Returns {last_name_lower: {initial: full_name}}
    """
    players = set(match_df["winner_name"].dropna()) | set(match_df["loser_name"].dropna())
    lookup  = {}

    for name in players:
        parts = name.strip().split()
        if len(parts) >= 2:
            last    = parts[-1].lower()
            initial = parts[0][0].upper()
            if last not in lookup:
                lookup[last] = {}
            lookup[last][initial] = name

    return lookup


def convert_name(odds_name: str, lookup: dict) -> str:
    """
    Convert odds format name to Sackmann format.
    'Alcaraz C.' -> 'Carlos Alcaraz'
    'Struff J.L.' -> 'Jan Lennard Struff'
    Returns original name if not found.
    """
    if not isinstance(odds_name, str):
        return ""

    tokens  = odds_name.strip().split()
    last    = tokens[0].lower()
    initial = tokens[1][0].upper() if len(tokens) > 1 else ""

    return lookup.get(last, {}).get(initial, "")


def add_sackmann_names(odds_df: pd.DataFrame,
                       match_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add sackmann_winner and sackmann_loser columns to odds_df.
    """
    lookup           = build_name_lookup(match_df)
    odds_df          = odds_df.copy()
    odds_df["sackmann_winner"] = odds_df["Winner"].apply(
        lambda x: convert_name(x, lookup)
    )
    odds_df["sackmann_loser"]  = odds_df["Loser"].apply(
        lambda x: convert_name(x, lookup)
    )

    matched = (odds_df["sackmann_winner"] != "").sum()
    total   = len(odds_df)
    print(f"Name matching: {matched:,}/{total:,} ({matched/total*100:.1f}%) winners matched")

    return odds_df


if __name__ == "__main__":
    match_df = pd.read_csv("data/processed/match_data.csv")
    odds_df  = pd.read_csv("data/processed/odds_data.csv")

    odds_df  = add_sackmann_names(odds_df, match_df)
    print(odds_df[["Winner","sackmann_winner","Loser","sackmann_loser"]].head(10).to_string())
