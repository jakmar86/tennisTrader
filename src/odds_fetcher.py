"""
TennisTrader -- Odds Fetcher
Fetches tennis match odds from Betfair API.
Phase 1B: Implementation target -- requires API credentials.
"""

TENNIS_EVENT_TYPE_ID = "2"    # Betfair event type ID for tennis
MATCH_ODDS_MARKET    = "MATCH_ODDS"


def find_tennis_markets(tournament: str = None, date: str = None) -> list:
    """
    Find upcoming tennis match odds markets on Betfair.
    Phase 1B: stub.
    """
    pass


def fetch_match_odds(market_id: str) -> dict:
    """
    Fetch current best available odds for a tennis match.
    Returns dict: {player_a: odds, player_b: odds}
    Phase 1B: stub.
    """
    pass


def get_implied_probability(odds: float) -> float:
    if odds <= 1.0:
        return 0.0
    return 1.0 / odds
