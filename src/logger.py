"""
TennisTrader -- Logger
SQLite trade and event logger.
"""

import sqlite3
import datetime
from config.config import config

DB_PATH = config["db_path"]


def get_connection():
    return sqlite3.connect(DB_PATH)


def initialise_db():
    conn = get_connection()
    c    = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS matches (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at   TEXT,
        tour         TEXT,
        tournament   TEXT,
        surface      TEXT,
        round        TEXT,
        player_a     TEXT,
        player_b     TEXT,
        match_date   TEXT,
        market_id    TEXT UNIQUE,
        status       TEXT DEFAULT 'pending'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS backs (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id     INTEGER,
        placed_at    TEXT,
        player       TEXT,
        stake        REAL,
        odds         REAL,
        model_prob   REAL,
        edge_pct     REAL,
        bet_id       TEXT,
        status       TEXT DEFAULT 'open',
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS lays (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        back_id      INTEGER,
        match_id     INTEGER,
        placed_at    TEXT,
        player       TEXT,
        lay_stake    REAL,
        lay_odds     REAL,
        lay_pct      REAL,
        trigger      TEXT,
        set_score    TEXT,
        bet_id       TEXT,
        FOREIGN KEY (back_id)  REFERENCES backs(id),
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS settlements (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id     INTEGER,
        settled_at   TEXT,
        winner       TEXT,
        final_score  TEXT,
        total_backed REAL,
        total_laid   REAL,
        gross_pnl    REAL,
        commission   REAL,
        net_pnl      REAL,
        FOREIGN KEY (match_id) REFERENCES matches(id)
    )""")

    conn.commit()
    conn.close()
    print(f"Database initialised: {DB_PATH}")


def log_match(tour, tournament, surface, round_,
              player_a, player_b, match_date, market_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO matches
        (created_at, tour, tournament, surface, round,
         player_a, player_b, match_date, market_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.datetime.utcnow().isoformat(), tour, tournament,
         surface, round_, player_a, player_b, match_date, market_id))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return mid


def log_back(match_id, player, stake, odds, model_prob, edge_pct, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO backs
        (match_id, placed_at, player, stake, odds, model_prob, edge_pct, bet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, datetime.datetime.utcnow().isoformat(),
         player, stake, odds, model_prob, edge_pct, bet_id))
    conn.commit()
    bid = c.lastrowid
    conn.close()
    return bid


def log_lay(back_id, match_id, player, lay_stake,
            lay_odds, lay_pct, trigger, set_score, bet_id):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO lays
        (back_id, match_id, placed_at, player, lay_stake,
         lay_odds, lay_pct, trigger, set_score, bet_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (back_id, match_id, datetime.datetime.utcnow().isoformat(),
         player, lay_stake, lay_odds, lay_pct, trigger, set_score, bet_id))
    conn.commit()
    conn.close()


def log_settlement(match_id, winner, final_score, total_backed,
                   total_laid, gross_pnl, commission, net_pnl):
    conn = get_connection()
    c    = conn.cursor()
    c.execute("""INSERT INTO settlements
        (match_id, settled_at, winner, final_score, total_backed,
         total_laid, gross_pnl, commission, net_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (match_id, datetime.datetime.utcnow().isoformat(), winner,
         final_score, total_backed, total_laid, gross_pnl, commission, net_pnl))
    c.execute("UPDATE matches SET status='settled' WHERE id=?", (match_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    initialise_db()
