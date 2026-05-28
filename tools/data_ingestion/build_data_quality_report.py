from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import DATA_ROOT, EXPORT_ROOT, LAKE_ROOT, ensure_lake_layout, load_frame, local_now_iso, read_json, write_json, write_text


NOW_LOCAL = local_now_iso()


def _grade(rows: int, data_status: str) -> str:
    if rows == 0:
        return "F"
    if data_status in {"PROVIDER_REQUIRED", "premium_model_required"}:
        return "D"
    if data_status in {"USER_PROVIDED"}:
        return "B"
    if data_status in {"PUBLIC_BETA_DEMO"}:
        return "C"
    return "A" if rows > 100 else "B"


def _frame_summary(name: str, path: Path, data_status: str, commercial_use_status: str, recommended: str) -> dict[str, object]:
    frame = load_frame(path)
    summary = {
        "source": name,
        "rows_loaded": int(len(frame)),
        "columns_loaded": int(len(frame.columns)),
        "date_min": "",
        "date_max": "",
        "competitions_count": 0,
        "teams_count": 0,
        "players_count": 0,
        "missing_key_fields": [],
        "duplicate_ids": 0,
        "license_status": data_status,
        "commercial_use_status": commercial_use_status,
        "recommended_ares_use": recommended,
        "grade": _grade(len(frame), data_status),
    }
    for column in ["date", "last_updated", "fetched_at"]:
        if column in frame.columns and not frame.empty:
            values = frame[column].dropna().astype(str)
            if not values.empty:
                summary["date_min"] = values.min()
                summary["date_max"] = values.max()
                break
    for key in ["competition_id", "team_id", "player_id"]:
        if key in frame.columns:
            summary[f"{key}s_count"] = int(frame[key].nunique(dropna=True))
    if "player_id" in frame.columns and not frame.empty:
        dup = frame["player_id"].duplicated().sum()
        summary["duplicate_ids"] = int(dup)
    required = [col for col in ["source_id", "data_status"] if col not in frame.columns]
    summary["missing_key_fields"] = required
    return summary


def main() -> int:
    ensure_lake_layout()
    registry = read_json(LAKE_ROOT / "registry" / "ares_data_sources.json", [])
    reports = {
        "generated_at_local": NOW_LOCAL,
        "lake_root": str(LAKE_ROOT),
        "sources": [
            _frame_summary("public_players", DATA_ROOT / "public_players.json", "PUBLIC_BETA_DEMO", "public_reference", "player public beta and formula proxy layer"),
            _frame_summary("public_clubs", DATA_ROOT / "public_clubs.json", "PUBLIC_BETA_DEMO", "public_reference", "club rollups and team formula inputs"),
            _frame_summary("public_leagues", DATA_ROOT / "public_leagues.json", "PUBLIC_BETA_DEMO", "public_reference", "league rollups and league formula inputs"),
            _frame_summary("matches", DATA_ROOT / "matches.json", "PUBLIC_OPEN", "public_reference", "historical match archive"),
            _frame_summary("open_match_team_stats", DATA_ROOT / "open_match_team_stats.json", "PUBLIC_OPEN", "public_reference", "team and league formula inputs"),
            _frame_summary("open_match_league_stats", DATA_ROOT / "open_match_league_stats.json", "PUBLIC_OPEN", "public_reference", "league formula inputs"),
        ],
        "registry_sources": len(registry) if isinstance(registry, list) else 0,
    }
    json_path = EXPORT_ROOT / "ares_data_quality_report.json"
    md_path = EXPORT_ROOT / "ares_data_quality_report.md"
    write_json(json_path, reports)
    lines = [
        "# ARES Data Quality Report",
        "",
        f"Generated at: `{NOW_LOCAL}`",
        "",
    ]
    for source in reports["sources"]:
        lines.append(f"## {source['source']}")
        lines.append(f"- rows_loaded: `{source['rows_loaded']}`")
        lines.append(f"- columns_loaded: `{source['columns_loaded']}`")
        lines.append(f"- date_min: `{source['date_min']}`")
        lines.append(f"- date_max: `{source['date_max']}`")
        lines.append(f"- duplicate_ids: `{source['duplicate_ids']}`")
        lines.append(f"- grade: `{source['grade']}`")
        lines.append(f"- recommended_ares_use: {source['recommended_ares_use']}")
        lines.append("")
    write_text(md_path, "\n".join(lines))
    print(f"Wrote quality report to {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
