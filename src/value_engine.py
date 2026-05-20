"""
TennisTrader -- Value Engine
Identical logic to ScoreTrader -- sport agnostic.
Edge calculation and Half Kelly staking.
"""

from config.config import config


def calculate_edge(model_prob: float, market_odds: float) -> float:
    implied_prob = 1.0 / market_odds
    return round((model_prob - implied_prob) * 100, 2)


def kelly_stake(model_prob: float, market_odds: float,
                bank: float, fraction: float = 0.5) -> float:
    b = market_odds - 1
    p = model_prob
    q = 1 - p
    if b <= 0 or p <= 0:
        return 0.0
    raw = (b * p - q) / b
    if raw <= 0:
        return 0.0
    return round(raw * fraction * bank, 2)


def assess_match(model_prob: float, market_odds: float, bank: float) -> dict:
    """
    Assess a single match selection for value and stake size.
    Returns dict with edge, stake, and recommendation.
    """
    min_edge   = config["min_edge_pct"]
    min_odds   = config["min_odds"]
    max_odds   = config["max_odds"]
    supervised = config["supervised"]
    multiplier = config["supervised_stake_multiplier"] if supervised else 1.0
    max_stake  = (config["max_match_stake_supervised"] if supervised
                  else config["max_match_stake_live"])
    fraction   = config["kelly_fraction"]

    edge  = calculate_edge(model_prob, market_odds)
    stake = kelly_stake(model_prob, market_odds, bank, fraction)
    stake = min(round(stake * multiplier, 2), max_stake)

    value = (edge >= min_edge and
             min_odds <= market_odds <= max_odds and
             stake > 0)

    return {
        "model_prob":   model_prob,
        "market_odds":  market_odds,
        "implied_prob": round(1 / market_odds, 4),
        "edge_pct":     edge,
        "stake":        stake if value else 0,
        "value":        value,
        "recommendation": "BACK" if value else "PASS",
    }


if __name__ == "__main__":
    # Test with example match
    test_cases = [
        ("Alcaraz", 0.65, 1.72),    # Model says 65%, market implies 58%
        ("Sinner",  0.55, 1.95),    # Model says 55%, market implies 51%
        ("Djokovic", 0.72, 1.45),   # Model says 72%, market implies 69% -- tight
        ("Medvedev", 0.40, 2.80),   # Underdog value play
    ]

    print(f"{'Player':<12} {'Model%':>8} {'Odds':>6} {'Edge%':>8} {'Stake':>8} {'Rec':>6}")
    print("-" * 55)
    for name, prob, odds in test_cases:
        result = assess_match(prob, odds, bank=1000)
        print(f"{name:<12} {prob*100:>7.1f}% {odds:>6.2f} "
              f"{result['edge_pct']:>7.1f}%  "
              f"£{result['stake']:>6.2f}  {result['recommendation']:>6}")
