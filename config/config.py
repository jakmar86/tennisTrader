"""
TennisTrader -- Configuration
Single control panel for all settings.
"""

config = {

    # -------------------------------------------------------------------------
    # MODE
    # -------------------------------------------------------------------------
    "supervised": True,               # True = WhatsApp approval before placing

    # -------------------------------------------------------------------------
    # STAKING
    # -------------------------------------------------------------------------
    "betting_bank":                   1000,
    "kelly_fraction":                 0.5,
    "supervised_stake_multiplier":    0.5,
    "max_match_stake_supervised":     30,
    "max_match_stake_live":           100,

    # -------------------------------------------------------------------------
    # VALUE FILTER
    # -------------------------------------------------------------------------
    "min_edge_pct":                   1.5,   # Slightly higher than football
    "odds_drift_threshold":           0.15,
    "min_odds":                       1.40,  # Don't back odds-on shots
    "max_odds":                       8.00,  # Don't back big outsiders

    # -------------------------------------------------------------------------
    # MODEL
    # -------------------------------------------------------------------------
    "min_matches_required":           20,    # Minimum matches to rate a player
    "recency_half_life_days":         180,   # Weight recent matches more heavily
    "surfaces": ["hard", "clay", "grass"],

    # -------------------------------------------------------------------------
    # IN-PLAY EXIT ENGINE
    # -------------------------------------------------------------------------
    "poll_interval_seconds":          15,    # Tennis moves fast -- poll more often
    "greenup_profit_threshold":       1.20,  # Green up combined position at 120%
    "cut_loss_min_minute":            0,     # Tennis uses sets not minutes
    "cut_loss_set_threshold":         2,     # Cut after losing 2 sets in best of 3

    # -------------------------------------------------------------------------
    # TOURNAMENTS
    # -------------------------------------------------------------------------
    "tour": ["ATP", "WTA"],
    "min_tournament_level": "250",    # 250, 500, 1000, Grand Slam
    # Grand Slams have most liquidity
    # ATP 250 has least sharp money -- most edge potential

    # -------------------------------------------------------------------------
    # DATA
    # -------------------------------------------------------------------------
    "seasons":                        5,     # 5 seasons of historical data
    "raw_data_path":                  "data/raw/",
    "processed_data_path":            "data/processed/",
    "db_path":                        "data/db/tennisTrader.db",
    "sackmann_atp_path":              "data/raw/atp/",
    "sackmann_wta_path":              "data/raw/wta/",
    "odds_data_path":                 "data/raw/odds/",

    # -------------------------------------------------------------------------
    # BETFAIR API
    # -------------------------------------------------------------------------
    "betfair_username_env":           "BETFAIR_USERNAME",
    "betfair_password_env":           "BETFAIR_PASSWORD",
    "betfair_app_key_env":            "BETFAIR_APP_KEY",
    "betfair_cert_path_env":          "BETFAIR_CERT_PATH",
    "betfair_key_path_env":           "BETFAIR_KEY_PATH",

    # -------------------------------------------------------------------------
    # NOTIFICATIONS
    # -------------------------------------------------------------------------
    "whatsapp_number_env":            "WHATSAPP_NUMBER",
    "notify_on_placement":            True,
    "notify_on_exit":                 True,
    "notify_on_error":                True,

    # -------------------------------------------------------------------------
    # DASHBOARD
    # -------------------------------------------------------------------------
    "dashboard_host":                 "0.0.0.0",
    "dashboard_port":                 8001,   # Different port to ScoreTrader
}
