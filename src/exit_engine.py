"""
TennisTrader -- Exit Engine
Tennis-specific green-up and loss-cut logic.

Tennis exit triggers differ from football:
  - Set won by backed player   -> odds shorten, assess green-up
  - Set lost by backed player  -> odds lengthen, assess cut
  - Two sets down (best of 3)  -> match effectively over, cut
  - Match point reached        -> green up immediately

Phase 1C: Implementation target.
"""

from config.config import config


def calculate_exit_score(backed_player: str,
                         current_set_score: tuple,
                         current_odds: float,
                         back_odds: float,
                         stake: float,
                         best_of: int = 3) -> dict:
    """
    Calculate exit recommendation based on current match state.

    Returns dict:
        action:      "GREEN_UP" / "CUT" / "HOLD"
        lay_pct:     Fraction of position to lay
        reason:      Human-readable explanation
        locked_pnl:  Guaranteed P&L if green-up executed now
    """
    sets_won  = current_set_score[0]
    sets_lost = current_set_score[1]
    sets_needed = (best_of // 2) + 1

    # Calculate current green-up value
    green_up_profit = (stake * back_odds / current_odds) - stake
    threshold       = stake * config["greenup_profit_threshold"]

    # Match effectively over -- backed player two sets down in best of 3
    if sets_lost >= sets_needed - 1 and sets_won == 0 and best_of == 3:
        return {
            "action":     "CUT",
            "lay_pct":    0.0,
            "reason":     "Two sets down -- cut remaining value",
            "locked_pnl": -stake,
        }

    # Green up if profit threshold exceeded
    if green_up_profit >= threshold:
        return {
            "action":     "GREEN_UP",
            "lay_pct":    1.0,
            "reason":     f"Profit threshold reached -- lock in £{green_up_profit:.2f}",
            "locked_pnl": round(green_up_profit, 2),
        }

    # Backed player winning -- hold
    if sets_won > sets_lost:
        return {
            "action":     "HOLD",
            "lay_pct":    0.0,
            "reason":     "Ahead in sets -- hold position",
            "locked_pnl": 0.0,
        }

    return {
        "action":     "HOLD",
        "lay_pct":    0.0,
        "reason":     "Monitoring",
        "locked_pnl": 0.0,
    }
