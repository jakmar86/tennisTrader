"""
TennisTrader -- In-Play Monitor
Tennis-specific in-play monitoring.

Key difference from football:
  - Poll every 15 seconds (tennis moves faster)
  - Trigger on game/set events not minutes
  - Break of serve = significant odds movement
  - Exit logic based on sets won not time

Phase 1C: Implementation target.
"""

import time
from config.config import config


def monitor_match(market_id: str, backed_player: str,
                  back_odds: float, stake: float):
    """
    Monitor a live tennis match.

    Triggers:
      - Player wins a set      -> assess green-up
      - Player loses a set     -> assess cut
      - Break of serve         -> odds movement, reassess
      - Match complete         -> settle

    Phase 1C: stub.
    """
    poll_interval = config["poll_interval_seconds"]
    while True:
        # TODO: Phase 1C
        # 1. Fetch market book
        # 2. Parse current score (sets, games)
        # 3. Check exit engine
        # 4. Place lay if triggered
        time.sleep(poll_interval)
