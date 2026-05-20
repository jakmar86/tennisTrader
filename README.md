# TennisTrader

An automated tennis trading system for Betfair, built in Python with a React dashboard.

## Overview

TennisTrader uses a Bradley-Terry paired comparison model with surface adjustment
to identify value in Betfair tennis match odds markets. It calculates edge against
market-implied odds, sizes stakes using Half Kelly, places back bets via the Betfair
API, monitors matches in-play, and executes optimal lay bets based on game state.

## Why Tennis

- Mathematically tractable -- serve probability drives everything
- Binary outcomes per match -- clean model validation
- Matches every day -- year-round opportunity
- In-play odds swing dramatically on breaks of serve
- Less sharp money at ATP 250 / Challenger level
- Real closing odds available from tennis-data.co.uk -- no synthetic odds problem

## Data Sources

- Jeff Sackmann GitHub -- comprehensive ATP/WTA match data (free)
- tennis-data.co.uk   -- match results + real Betfair/bookmaker odds (free)

## Architecture

```
data_pipeline     ->  Jeff Sackmann + tennis-data.co.uk
bradley_terry     ->  Player strength ratings (surface adjusted)
match_model       ->  Match/set/game win probabilities
odds_fetcher      ->  Live Betfair tennis market odds
value_engine      ->  Edge calculation + Half Kelly staking
bet_placer        ->  Supervised/autonomous back bet placement
inplay_monitor    ->  Point-by-point monitoring loop
exit_engine       ->  Tennis-specific green-up logic
lay_placer        ->  Optimal lay order execution
settler           ->  Post-match P&L calculation
logger            ->  SQLite trade history
dashboard         ->  React frontend + FastAPI backend
```

## Build Phases

- Phase 1A -- Data pipeline + Bradley-Terry model + backtest vs real odds
- Phase 1B -- Betfair API integration + live odds fetch
- Phase 1C -- Bet placement + in-play monitor + exit engine
- Phase 2  -- Live paper trading (Wimbledon, US Open)
- Phase 3  -- Micro stakes live validation
- Phase 4  -- Scale + surface specialisation

## License

Private -- Dellally Limited
