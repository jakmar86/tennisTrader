"""
TennisTrader -- Main Orchestrator
Entry point for the pre-match pipeline.

Usage:
    python main.py
    python main.py --date 2026-06-30
    python main.py --tournament wimbledon
"""

import argparse
import datetime
from config.config import config
from src.logger import initialise_db


def run(match_date: str = None, tournament: str = None):
    if match_date is None:
        match_date = datetime.date.today().isoformat()

    print(f"\nTennisTrader -- {match_date}")
    if tournament:
        print(f"Tournament filter: {tournament}")
    print("=" * 50)

    initialise_db()

    # Phase 1A: data pipeline -> bradley-terry model -> value engine
    # Phase 1B: odds fetch -> pre-match selections
    # Phase 1C: bet placement -> inplay monitor

    print("\nPipeline complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TennisTrader")
    parser.add_argument("--date",       type=str, default=None)
    parser.add_argument("--tournament", type=str, default=None)
    args = parser.parse_args()
    run(args.date, args.tournament)
