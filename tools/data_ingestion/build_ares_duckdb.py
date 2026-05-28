from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from common import (
    CLEAN_ROOT,
    DATA_ROOT,
    DUCKDB_PATH,
    EXPORT_ROOT,
    REGISTRY_ROOT,
    ensure_lake_layout,
    load_frame,
    read_json,
    safe_text,
)
from schemas import CANONICAL_SCHEMAS


SOURCE_TABLES = {
    "competitions": EXPORT_ROOT / "ares_competitions.parquet",
    "teams": EXPORT_ROOT / "ares_teams.parquet",
    "matches": EXPORT_ROOT / "ares_matches.parquet",
    "team_match_stats": EXPORT_ROOT / "ares_team_match_stats.parquet",
    "players": EXPORT_ROOT / "ares_players.parquet",
    "player_seasons": EXPORT_ROOT / "ares_public_player_formula_inputs.parquet",
    "events": CLEAN_ROOT / "events" / "events.parquet",
    "lineups": CLEAN_ROOT / "lineups" / "lineups.parquet",
    "market_values": EXPORT_ROOT / "ares_market_values.parquet",
    "transfers": EXPORT_ROOT / "ares_transfers.parquet",
    "wages": EXPORT_ROOT / "ares_wages.parquet",
    "clubelo": CLEAN_ROOT / "clubelo" / "clubelo_history.parquet",
}


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame({column: pd.Series(dtype="object") for column in columns})


def main() -> int:
    ensure_lake_layout()
    con = duckdb.connect(str(DUCKDB_PATH))
    try:
        registry_path = REGISTRY_ROOT / "ares_data_sources.json"
        registry = read_json(registry_path, [])
        registry_df = pd.DataFrame(registry) if isinstance(registry, list) else pd.DataFrame([registry])
        if registry_df.empty:
            registry_df = pd.DataFrame({"source_id": []})
        con.register("source_registry_df", registry_df)
        con.execute("CREATE OR REPLACE TABLE source_registry AS SELECT * FROM source_registry_df")

        for table, columns in CANONICAL_SCHEMAS.items():
            path = SOURCE_TABLES.get(table)
            frame = load_frame(path) if path else pd.DataFrame()
            if frame.empty:
                frame = _empty_frame(columns)
            for column in columns:
                if column not in frame.columns:
                    frame[column] = pd.NA
            frame = frame[columns]
            con.register(f"{table}_df", frame)
            con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM {table}_df")

        con.execute(
            """
            CREATE OR REPLACE TABLE player_formula_inputs AS
            SELECT * FROM read_parquet(?)
            """,
            [str(EXPORT_ROOT / "ares_public_player_formula_inputs.parquet")],
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE team_formula_inputs AS
            SELECT * FROM read_parquet(?)
            """,
            [str(EXPORT_ROOT / "ares_team_formula_inputs.parquet")],
        )
        con.execute(
            """
            CREATE OR REPLACE TABLE league_formula_inputs AS
            SELECT * FROM read_parquet(?)
            """,
            [str(EXPORT_ROOT / "ares_league_formula_inputs.parquet")],
        )
    finally:
        con.close()
    print(f"Wrote DuckDB database to {DUCKDB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

