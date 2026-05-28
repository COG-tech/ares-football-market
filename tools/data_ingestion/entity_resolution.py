from __future__ import annotations

from pathlib import Path

import pandas as pd

from common import DATA_ROOT, REGISTRY_ROOT, clean_name, ensure_lake_layout, load_frame, write_csv


def build_aliases(frame: pd.DataFrame, id_col: str, name_col: str, output_path: Path) -> None:
    rows = []
    for _, row in frame.iterrows():
        name = row.get(name_col)
        if not name:
            continue
        rows.append({"entity_id": row.get(id_col), "alias": name, "alias_clean": clean_name(name), "entity_name": name})
    write_csv(output_path, rows, ["entity_id", "alias", "alias_clean", "entity_name"])


def main() -> int:
    ensure_lake_layout()
    players = load_frame(DATA_ROOT / "public_players.json")
    clubs = load_frame(DATA_ROOT / "public_clubs.json")
    leagues = load_frame(DATA_ROOT / "public_leagues.json")
    if not players.empty:
        build_aliases(players, "player_id", "player_name", REGISTRY_ROOT / "player_aliases.csv")
    if not clubs.empty:
        build_aliases(clubs, "club_id", "club_name", REGISTRY_ROOT / "team_aliases.csv")
    if not leagues.empty:
        build_aliases(leagues, "league_id", "league_name", REGISTRY_ROOT / "competition_aliases.csv")
    review = []
    for _, row in players.head(50).iterrows():
        review.append(
            {
                "entity_type": "player",
                "entity_id": row.get("player_id"),
                "entity_name": row.get("player_name"),
                "match_confidence": 100,
                "resolution_status": "exact_public_beta_row",
            }
        )
    write_csv(REGISTRY_ROOT / "entity_match_review.csv", review, ["entity_type", "entity_id", "entity_name", "match_confidence", "resolution_status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
