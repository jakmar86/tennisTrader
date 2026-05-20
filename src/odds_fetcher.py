"""
TennisTrader -- Odds Fetcher
Fetches live tennis match odds from Betfair API.
"""

import betfairlightweight
from betfairlightweight import filters
from src.betfair_auth import get_client

TENNIS_EVENT_TYPE_ID = "2"
MATCH_ODDS_MARKET    = "MATCH_ODDS"


def find_tennis_markets(hours_ahead: int = 24) -> list:
    """
    Find upcoming tennis match odds markets on Betfair.
    Returns list of market catalogues.
    """
    client = get_client()

    market_filter = filters.market_filter(
        event_type_ids=[TENNIS_EVENT_TYPE_ID],
        market_type_codes=[MATCH_ODDS_MARKET],
        market_start_time={
            "from": "2026-01-01T00:00:00Z",
            "to":   "2026-12-31T00:00:00Z",
        }
    )

    markets = client.betting.list_market_catalogue(
        filter=market_filter,
        market_projection=["EVENT", "RUNNER_DESCRIPTION", "MARKET_START_TIME"],
        max_results=50,
        sort="FIRST_TO_START",
    )

    return markets


def fetch_match_odds(market_id: str) -> dict:
    """
    Fetch current best available odds for a tennis match.
    Returns dict: {player_name: best_back_odds}
    """
    client = get_client()

    market_books = client.betting.list_market_book(
        market_ids=[market_id],
        price_projection=filters.price_projection(
            price_data=["EX_BEST_OFFERS"]
        )
    )

    if not market_books:
        return {}

    book    = market_books[0]
    result  = {}

    for runner in book.runners:
        if runner.ex and runner.ex.available_to_back:
            best_back = runner.ex.available_to_back[0].price
            # Find runner name from market catalogue
            result[runner.selection_id] = best_back

    return result


if __name__ == "__main__":
    print("Fetching live tennis markets...")
    try:
        markets = find_tennis_markets()
        print(f"Found {len(markets)} tennis markets\n")
        for m in markets[:10]:
            print(f"  {m.market_id}  {m.market_name}  "
                  f"{m.event.name if m.event else ''}  "
                  f"Start: {m.market_start_time}")
    except Exception as e:
        print(f"Error: {e}")
