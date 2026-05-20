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
