"""TennisTrader -- Bradley-Terry Model Tests"""

import numpy as np
import pandas as pd
import pytest
from src.bradley_terry import match_win_probability, compute_recency_weight
from src.match_model import match_outcomes_best_of_3, match_outcomes_best_of_5


def test_match_win_probability_symmetry():
    """P(A beats B) + P(B beats A) should equal 1."""
    ratings = pd.Series({"Player A": 1.5, "Player B": 0.5})
    p_ab = match_win_probability("Player A", "Player B", ratings)
    p_ba = match_win_probability("Player B", "Player A", ratings)
    assert abs(p_ab + p_ba - 1.0) < 0.001


def test_match_win_probability_unknown_player():
    """Unknown player should return 0.5."""
    ratings = pd.Series({"Player A": 1.0})
    p = match_win_probability("Player A", "Unknown", ratings)
    assert p == 0.5


def test_recency_weight_today():
    """Match today should have weight 1.0."""
    today = pd.Timestamp.now()
    w = compute_recency_weight(today, today, half_life_days=180)
    assert abs(w - 1.0) < 0.001


def test_recency_weight_half_life():
    """Match at half_life_days ago should have weight ~0.5."""
    today    = pd.Timestamp.now()
    past     = today - pd.Timedelta(days=180)
    w        = compute_recency_weight(past, today, half_life_days=180)
    assert abs(w - 0.5) < 0.01


def test_best_of_3_sums_to_one():
    """Set score probabilities should sum to 1."""
    outcomes = match_outcomes_best_of_3(0.65)
    assert abs(sum(outcomes.values()) - 1.0) < 0.001


def test_best_of_5_sums_to_one():
    """Set score probabilities should sum to 1."""
    outcomes = match_outcomes_best_of_5(0.65)
    assert abs(sum(outcomes.values()) - 1.0) < 0.001


def test_stronger_player_wins_more():
    """Stronger player should win 2-0 more often than weaker player."""
    outcomes = match_outcomes_best_of_3(0.70)
    assert outcomes["2-0"] > outcomes["0-2"]


def test_even_match_is_symmetric():
    """50/50 match should have symmetric set score probabilities."""
    outcomes = match_outcomes_best_of_3(0.50)
    assert abs(outcomes["2-0"] - outcomes["0-2"]) < 0.001
    assert abs(outcomes["2-1"] - outcomes["1-2"]) < 0.001
