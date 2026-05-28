from __future__ import annotations

import argparse
from pathlib import Path
from typing import Callable

from build_ares_duckdb import main as build_duckdb
from build_ares_formula_inputs import main as build_formula_inputs
from build_data_quality_report import main as build_quality_report
from common import ensure_lake_layout, source_skip_record, write_json
from source_registry import REGISTRY_PATH, build_source_registry, main as build_registry


SOURCE_SKIPS = {
    "football_data_org": "missing API token",
    "statsbomb_open": "missing local clone or configured download source",
    "clubelo": "missing local ClubElo file",
    "fbref_manual": "missing user-provided CSV exports",
    "capology_manual": "missing user-provided CSV exports",
    "kaggle_transfermarkt": "missing Kaggle export files or API key",
    "sportmonks": "missing SPORTMONKS_TOKEN",
    "api_football": "missing API_FOOTBALL_KEY",
}


def run_source_pipeline(source: str, refresh: str = "current") -> int:
    ensure_lake_layout()
    if source in {"all", "source_registry"}:
        build_registry()
    if source in {"all", "formula_inputs", "football_data_co_uk"}:
        build_formula_inputs()
    if source in {"all", "build_duckdb", "football_data_co_uk"}:
        build_duckdb()
    if source in {"all", "quality_report", "football_data_co_uk"}:
        build_quality_report()
    if source not in {"all", "source_registry", "formula_inputs", "build_duckdb", "quality_report", "football_data_co_uk"}:
        reason = SOURCE_SKIPS.get(source, "source is not connected in this workspace")
        write_json(Path(r"D:\ARES\football\data_lake\logs") / f"{source}_skip.json", source_skip_record(source, reason))
        print(f"Skipped {source}: {reason}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the ARES data pipeline.")
    parser.add_argument("--source", default="all", choices=["all", "football_data_co_uk", "football_data_org", "statsbomb_open", "fbref_manual", "capology_manual", "kaggle_transfermarkt", "clubelo", "sportmonks", "api_football", "source_registry", "formula_inputs", "build_duckdb", "quality_report"])
    parser.add_argument("--refresh", default="current", choices=["current", "full"])
    parser.add_argument("--build-duckdb", action="store_true")
    parser.add_argument("--build-formula-inputs", action="store_true")
    parser.add_argument("--quality-report", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ensure_lake_layout()
    if args.source == "all":
        build_registry()
        build_formula_inputs()
        build_duckdb()
        build_quality_report()
    else:
        run_source_pipeline(args.source, args.refresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
