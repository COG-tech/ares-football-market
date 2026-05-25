#!/usr/bin/env python3
"""
Download open Football-Data.co.uk match CSVs for leagues represented on the site.

The site already uses Football-Data CSV rows for its public match layer. This
script reads the website league JSON files, keeps only leagues that can be
matched to Football-Data sources, downloads every available CSV for those
leagues, and writes raw plus normalized combined outputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import pandas as pd
import requests


BASE_URL = "https://www.football-data.co.uk/"
DEFAULT_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (ARES football open data downloader)"


@dataclass(frozen=True)
class LeagueSource:
    key: str
    canonical_name: str
    country: str
    kind: str
    aliases: tuple[str, ...]
    page: str = ""
    code: str = ""
    file_rel: str = ""
    source_league_name: str = ""


LEGACY_SOURCES: tuple[LeagueSource, ...] = (
    LeagueSource("E0", "Premier League", "England", "legacy", ("Premier League",), "englandm.php", "E0"),
    LeagueSource("E1", "Championship", "England", "legacy", ("Championship", "EFL Championship"), "englandm.php", "E1"),
    LeagueSource("E2", "League One", "England", "legacy", ("League One",), "englandm.php", "E2"),
    LeagueSource("E3", "League Two", "England", "legacy", ("League Two",), "englandm.php", "E3"),
    LeagueSource("SC0", "Premiership", "Scotland", "legacy", ("Premiership", "Scottish Premiership"), "scotlandm.php", "SC0"),
    LeagueSource("D1", "Bundesliga", "Germany", "legacy", ("Bundesliga",), "germanym.php", "D1"),
    LeagueSource("D2", "2. Bundesliga", "Germany", "legacy", ("2. Bundesliga",), "germanym.php", "D2"),
    LeagueSource("I1", "Serie A", "Italy", "legacy", ("Serie A",), "italym.php", "I1"),
    LeagueSource("I2", "Serie B", "Italy", "legacy", ("Serie B",), "italym.php", "I2"),
    LeagueSource("SP1", "La Liga", "Spain", "legacy", ("La Liga",), "spainm.php", "SP1"),
    LeagueSource("SP2", "Segunda Division", "Spain", ("legacy"), ("Segunda Division", "LaLiga 2"), "spainm.php", "SP2"),
    LeagueSource("F1", "Ligue 1", "France", "legacy", ("Ligue 1",), "francem.php", "F1"),
    LeagueSource("F2", "Ligue 2", "France", "legacy", ("Ligue 2",), "francem.php", "F2"),
    LeagueSource("N1", "Eredivisie", "Netherlands", "legacy", ("Eredivisie",), "netherlandsm.php", "N1"),
    LeagueSource("B1", "Jupiler League", "Belgium", "legacy", ("Jupiler League", "Belgian Pro League"), "belgiumm.php", "B1"),
    LeagueSource("P1", "Primeira Liga", "Portugal", "legacy", ("Primeira Liga", "Liga Portugal"), "portugalm.php", "P1"),
    LeagueSource("T1", "Super Lig", "Turkey", "legacy", ("Super Lig",), "turkeym.php", "T1"),
)

NEW_SOURCES: tuple[LeagueSource, ...] = (
    LeagueSource("ARG", "Argentine Primera Division", "Argentina", "new", ("Argentine Primera Division", "Argentine Primera"), file_rel="new/ARG.csv", source_league_name="Liga Profesional"),
    LeagueSource("BRA", "Campeonato Brasileiro Serie A", "Brazil", "new", ("Campeonato Brasileiro Serie A", "Brazil Serie A"), file_rel="new/BRA.csv", source_league_name="Serie A"),
    LeagueSource("CHN", "Chinese Super League", "China", "new", ("Chinese Super League",), file_rel="new/CHN.csv", source_league_name="Super League"),
    LeagueSource("JPN", "J1 League", "Japan", "new", ("J1 League",), file_rel="new/JPN.csv", source_league_name="J1 League"),
    LeagueSource("MEX", "Liga MX", "Mexico", "new", ("Liga MX",), file_rel="new/MEX.csv", source_league_name="Liga MX"),
    LeagueSource("SWZ", "Swiss Super League", "Switzerland", "new", ("Swiss Super League",), file_rel="new/SWZ.csv", source_league_name="Super League"),
    LeagueSource("USA", "Major League Soccer", "USA", "new", ("Major League Soccer",), file_rel="new/USA.csv", source_league_name="MLS"),
)

ALL_SOURCES: tuple[LeagueSource, ...] = LEGACY_SOURCES + NEW_SOURCES


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def load_site_leagues(site_root: Path) -> dict[str, dict[str, Any]]:
    league_files = [
        site_root / "data" / "leagues.json",
        site_root / "data" / "public_leagues.json",
        site_root / "data" / "full" / "leagues" / "part-0000.json",
    ]
    out: dict[str, dict[str, Any]] = {}
    for path in league_files:
        if not path.exists():
            continue
        rows = read_json(path)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("league_name") or row.get("name") or row.get("league") or "").strip()
            if not name:
                continue
            key = normalize_name(name)
            if key not in out:
                out[key] = {
                    "league_name": name,
                    "countries": set(),
                    "continents": set(),
                    "source_files": set(),
                }
            if row.get("country"):
                out[key]["countries"].add(str(row.get("country")))
            if row.get("continent"):
                out[key]["continents"].add(str(row.get("continent")))
            out[key]["source_files"].add(str(path.relative_to(site_root)))

    for item in out.values():
        item["countries"] = sorted(item["countries"])
        item["continents"] = sorted(item["continents"])
        item["source_files"] = sorted(item["source_files"])
    return out


def represented_sources(site_leagues: dict[str, dict[str, Any]]) -> tuple[list[LeagueSource], list[dict[str, Any]]]:
    alias_to_source: dict[str, LeagueSource] = {}
    for source in ALL_SOURCES:
        for alias in source.aliases:
            alias_to_source[normalize_name(alias)] = source

    selected: dict[str, LeagueSource] = {}
    unsupported: list[dict[str, Any]] = []
    for key, meta in sorted(site_leagues.items(), key=lambda item: item[1]["league_name"]):
        source = alias_to_source.get(key)
        if source:
            selected[source.key] = source
        else:
            unsupported.append(
                {
                    "league_name": meta["league_name"],
                    "countries": meta["countries"],
                    "continents": meta["continents"],
                    "source_files": meta["source_files"],
                    "reason": "No Football-Data.co.uk CSV mapping in this downloader",
                }
            )
    return [selected[k] for k in sorted(selected)], unsupported


def fetch_text(url: str, timeout: int) -> str:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    return response.text


def discover_legacy_files(sources: list[LeagueSource], timeout: int) -> list[dict[str, Any]]:
    by_page: dict[str, dict[str, LeagueSource]] = {}
    for source in sources:
        if source.kind != "legacy":
            continue
        by_page.setdefault(source.page, {})[source.code] = source

    rows: list[dict[str, Any]] = []
    for page, code_map in sorted(by_page.items()):
        page_url = urljoin(BASE_URL, page)
        html = fetch_text(page_url, timeout)
        links = re.findall(r'href=["\']([^"\']+\.csv)["\']', html, flags=re.IGNORECASE)
        seen: set[tuple[str, str]] = set()
        for rel in links:
            rel_norm = rel.replace("\\", "/")
            code = Path(rel_norm).stem.upper()
            source = code_map.get(code)
            if not source:
                continue
            season_key = Path(rel_norm).parent.name
            dedupe_key = (season_key, code)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            rows.append(
                {
                    "source": source,
                    "url": urljoin(BASE_URL, rel_norm),
                    "rel": rel_norm,
                    "season_key": season_key,
                    "file_kind": "legacy_mmz4281",
                }
            )
    return rows


def discover_new_files(sources: list[LeagueSource]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in sources:
        if source.kind != "new":
            continue
        rows.append(
            {
                "source": source,
                "url": urljoin(BASE_URL, source.file_rel),
                "rel": source.file_rel,
                "season_key": "combined",
                "file_kind": "new_combined",
            }
        )
    return rows


def relative_raw_path(out_dir: Path, rel: str) -> Path:
    clean_rel = rel.replace("/", "_")
    if rel.startswith("mmz4281/"):
        parts = rel.split("/")
        if len(parts) >= 3:
            return out_dir / "raw" / "football-data.co.uk" / parts[-3] / parts[-2] / parts[-1]
    if rel.startswith("new/"):
        return out_dir / "raw" / "football-data.co.uk" / "new" / Path(rel).name
    return out_dir / "raw" / "football-data.co.uk" / clean_rel


def download_one(item: dict[str, Any], out_dir: Path, timeout: int, force: bool) -> dict[str, Any]:
    raw_path = relative_raw_path(out_dir, item["rel"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    url = item["url"]
    status = "downloaded"
    content = b""

    if raw_path.exists() and raw_path.stat().st_size > 0 and not force:
        content = raw_path.read_bytes()
        status = "cached"
    else:
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
                response.raise_for_status()
                content = response.content
                raw_path.write_bytes(content)
                break
            except Exception as exc:  # noqa: PERF203
                last_exc = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        else:
            return {
                **item,
                "raw_path": str(raw_path),
                "status": "failed",
                "error": str(last_exc),
                "bytes": 0,
                "sha256": "",
            }

    return {
        **item,
        "raw_path": str(raw_path),
        "status": status,
        "error": "",
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest() if content else "",
    }


def read_csv_frame(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "latin1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin1", on_bad_lines="skip")


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_number(value: Any) -> Any:
    if pd.isna(value) or value == "":
        return None
    try:
        number = float(value)
    except Exception:
        return None
    if number.is_integer():
        return int(number)
    return number


def normalize_legacy_rows(df: pd.DataFrame, meta: dict[str, Any]) -> list[dict[str, Any]]:
    source: LeagueSource = meta["source"]
    out: list[dict[str, Any]] = []
    for idx, row in df.iterrows():
        home = clean_text(row.get("HomeTeam"))
        away = clean_text(row.get("AwayTeam"))
        if not home or not away:
            continue
        out.append(
            {
                "match_id": f"fd_{source.key}_{meta['season_key']}_{idx + 1}",
                "source": "football-data.co.uk",
                "source_schema": "legacy_mmz4281",
                "source_url": meta["url"],
                "raw_path": str(Path(meta["raw_path"])),
                "source_season": meta["season_key"],
                "country": source.country,
                "league_code": source.code,
                "league_name": source.canonical_name,
                "date": clean_text(row.get("Date")),
                "time": clean_text(row.get("Time")),
                "home_team": home,
                "away_team": away,
                "full_time_home_goals": clean_number(row.get("FTHG")),
                "full_time_away_goals": clean_number(row.get("FTAG")),
                "full_time_result": clean_text(row.get("FTR")),
                "half_time_home_goals": clean_number(row.get("HTHG")),
                "half_time_away_goals": clean_number(row.get("HTAG")),
                "half_time_result": clean_text(row.get("HTR")),
                "referee": clean_text(row.get("Referee")),
                "home_shots": clean_number(row.get("HS")),
                "away_shots": clean_number(row.get("AS")),
                "home_shots_on_target": clean_number(row.get("HST")),
                "away_shots_on_target": clean_number(row.get("AST")),
                "home_corners": clean_number(row.get("HC")),
                "away_corners": clean_number(row.get("AC")),
                "home_yellow_cards": clean_number(row.get("HY")),
                "away_yellow_cards": clean_number(row.get("AY")),
                "home_red_cards": clean_number(row.get("HR")),
                "away_red_cards": clean_number(row.get("AR")),
                "is_placeholder": False,
            }
        )
    return out


def normalize_new_rows(df: pd.DataFrame, meta: dict[str, Any]) -> list[dict[str, Any]]:
    source: LeagueSource = meta["source"]
    out: list[dict[str, Any]] = []
    league_col = "League" if "League" in df.columns else ""
    for idx, row in df.iterrows():
        source_league = clean_text(row.get(league_col)).strip()
        if source.source_league_name and normalize_name(source.source_league_name) not in normalize_name(source_league):
            continue
        home = clean_text(row.get("Home"))
        away = clean_text(row.get("Away"))
        if not home or not away:
            continue
        out.append(
            {
                "match_id": f"fd_{source.key}_{clean_text(row.get('Season')).replace('/', '')}_{idx + 1}",
                "source": "football-data.co.uk",
                "source_schema": "new_combined",
                "source_url": meta["url"],
                "raw_path": str(Path(meta["raw_path"])),
                "source_season": clean_text(row.get("Season")),
                "country": source.country,
                "league_code": source.key,
                "league_name": source.canonical_name,
                "date": clean_text(row.get("Date")),
                "time": clean_text(row.get("Time")),
                "home_team": home,
                "away_team": away,
                "full_time_home_goals": clean_number(row.get("HG")),
                "full_time_away_goals": clean_number(row.get("AG")),
                "full_time_result": clean_text(row.get("Res")),
                "half_time_home_goals": None,
                "half_time_away_goals": None,
                "half_time_result": "",
                "referee": "",
                "home_shots": None,
                "away_shots": None,
                "home_shots_on_target": None,
                "away_shots_on_target": None,
                "home_corners": None,
                "away_corners": None,
                "home_yellow_cards": None,
                "away_yellow_cards": None,
                "home_red_cards": None,
                "away_red_cards": None,
                "is_placeholder": False,
            }
        )
    return out


def build_outputs(downloads: list[dict[str, Any]], out_dir: Path, generated_at: str) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    raw_frames: list[pd.DataFrame] = []
    normalized_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    for meta in downloads:
        source: LeagueSource = meta["source"]
        row_base = {
            "league_key": source.key,
            "league_name": source.canonical_name,
            "country": source.country,
            "source_url": meta["url"],
            "raw_path": str(Path(meta["raw_path"]).relative_to(out_dir)),
            "status": meta["status"],
            "error": meta.get("error", ""),
            "bytes": meta.get("bytes", 0),
            "sha256": meta.get("sha256", ""),
            "rows": 0,
            "columns": 0,
        }
        if meta["status"] == "failed":
            source_rows.append(row_base)
            continue

        raw_path = Path(meta["raw_path"])
        try:
            df = read_csv_frame(raw_path)
        except Exception as exc:
            source_rows.append({**row_base, "status": "parse_failed", "error": str(exc)})
            continue

        raw = df.copy()
        raw.insert(0, "_downloaded_at_utc", generated_at)
        raw.insert(1, "_source_url", meta["url"])
        raw.insert(2, "_source_file", str(raw_path.relative_to(out_dir)))
        raw.insert(3, "_football_data_key", source.key)
        raw.insert(4, "_site_league_name", source.canonical_name)
        raw_frames.append(raw)

        if meta["file_kind"] == "legacy_mmz4281":
            normalized_rows.extend(normalize_legacy_rows(df, meta))
        else:
            normalized_rows.extend(normalize_new_rows(df, meta))

        source_rows.append({**row_base, "rows": int(len(df)), "columns": int(len(df.columns))})

    raw_union = pd.concat(raw_frames, ignore_index=True, sort=False) if raw_frames else pd.DataFrame()
    normalized = pd.DataFrame(normalized_rows)
    if not normalized.empty:
        normalized = normalized.sort_values(["country", "league_name", "source_season", "date", "home_team"], kind="stable")

    raw_out = out_dir / "combined" / "matches_raw_union.csv.gz"
    norm_csv = out_dir / "combined" / "matches_normalized.csv"
    norm_json = out_dir / "combined" / "matches_normalized.json"
    raw_out.parent.mkdir(parents=True, exist_ok=True)
    raw_union.to_csv(raw_out, index=False)
    normalized.to_csv(norm_csv, index=False)
    write_json(norm_json, normalized.to_dict(orient="records"))
    return raw_union, normalized, source_rows


def build_summary(normalized: pd.DataFrame) -> pd.DataFrame:
    if normalized.empty:
        return pd.DataFrame()
    temp = normalized.copy()
    temp["_date"] = pd.to_datetime(temp["date"], dayfirst=True, errors="coerce")
    summary = (
        temp.groupby(["country", "league_code", "league_name"], dropna=False)
        .agg(
            matches=("match_id", "count"),
            seasons=("source_season", lambda values: len(set(str(v) for v in values if str(v).strip()))),
            first_date=("_date", "min"),
            last_date=("_date", "max"),
        )
        .reset_index()
    )
    for col in ("first_date", "last_date"):
        summary[col] = summary[col].dt.strftime("%Y-%m-%d").fillna("")
    return summary.sort_values(["country", "league_name"], kind="stable")


def write_unsupported_csv(path: Path, unsupported: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["league_name", "countries", "continents", "source_files", "reason"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in unsupported:
            writer.writerow(
                {
                    "league_name": row["league_name"],
                    "countries": "; ".join(row.get("countries") or []),
                    "continents": "; ".join(row.get("continents") or []),
                    "source_files": "; ".join(row.get("source_files") or []),
                    "reason": row["reason"],
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Football-Data.co.uk CSVs for represented website leagues.")
    parser.add_argument("--site-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--force", action="store_true", help="Redownload files even if raw CSVs already exist.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    site_root = args.site_root.resolve()
    out_dir = (args.out_dir or (site_root / "data" / "open_match_csv")).resolve()
    generated_at = utc_now()

    site_leagues = load_site_leagues(site_root)
    sources, unsupported = represented_sources(site_leagues)
    legacy_items = discover_legacy_files(sources, args.timeout)
    new_items = discover_new_files(sources)
    items = sorted(legacy_items + new_items, key=lambda item: (item["source"].country, item["source"].canonical_name, item["season_key"], item["rel"]))

    print(f"Site root        : {site_root}")
    print(f"Output dir       : {out_dir}")
    print(f"Represented      : {len(site_leagues)} website league names")
    print(f"Mapped           : {len(sources)} Football-Data league sources")
    print(f"Unsupported      : {len(unsupported)} website league names")
    print(f"Source CSVs      : {len(items)}")
    print(f"Dry run          : {args.dry_run}")

    if args.dry_run:
        for item in items[:50]:
            print(f"{item['source'].canonical_name}: {item['url']}")
        if len(items) > 50:
            print(f"... {len(items) - 50} more")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[dict[str, Any]] = []
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        future_map = {executor.submit(download_one, item, out_dir, args.timeout, args.force): item for item in items}
        for future in as_completed(future_map):
            result = future.result()
            downloaded.append(result)
            done += 1
            source: LeagueSource = result["source"]
            status = result["status"]
            print(f"[{done:>4}/{len(items)}] {status:10} {source.key:>4} {result['season_key']:>8} {source.canonical_name}")

    downloaded = sorted(downloaded, key=lambda item: (item["source"].country, item["source"].canonical_name, item["season_key"], item["rel"]))
    raw_union, normalized, source_rows = build_outputs(downloaded, out_dir, generated_at)
    summary = build_summary(normalized)
    summary_path = out_dir / "combined" / "league_download_summary.csv"
    summary.to_csv(summary_path, index=False)
    write_unsupported_csv(out_dir / "combined" / "unsupported_website_leagues.csv", unsupported)

    manifest = {
        "generated_at_utc": generated_at,
        "source": BASE_URL,
        "site_root": str(site_root),
        "output_dir": str(out_dir),
        "represented_website_league_names": len(site_leagues),
        "mapped_football_data_sources": len(sources),
        "unsupported_website_league_names": len(unsupported),
        "source_csvs": len(items),
        "downloaded_or_cached_csvs": len([row for row in downloaded if row["status"] in {"downloaded", "cached"}]),
        "failed_csvs": len([row for row in downloaded if row["status"] == "failed"]),
        "raw_union_rows": int(len(raw_union)),
        "normalized_match_rows": int(len(normalized)),
        "normalized_leagues": int(normalized[["country", "league_code", "league_name"]].drop_duplicates().shape[0]) if not normalized.empty else 0,
        "outputs": {
            "raw_files_root": str(out_dir / "raw"),
            "raw_union_csv_gz": str(out_dir / "combined" / "matches_raw_union.csv.gz"),
            "normalized_csv": str(out_dir / "combined" / "matches_normalized.csv"),
            "normalized_json": str(out_dir / "combined" / "matches_normalized.json"),
            "league_summary_csv": str(summary_path),
            "unsupported_website_leagues_csv": str(out_dir / "combined" / "unsupported_website_leagues.csv"),
        },
        "mapped_sources": [
            {
                "key": source.key,
                "league_name": source.canonical_name,
                "country": source.country,
                "kind": source.kind,
                "aliases": list(source.aliases),
            }
            for source in sources
        ],
        "files": source_rows,
        "unsupported_website_leagues": unsupported,
    }
    write_json(out_dir / "manifest.json", manifest)

    print("\nDone")
    print(f"Raw rows         : {len(raw_union)}")
    print(f"Normalized rows  : {len(normalized)}")
    print(f"Leagues          : {manifest['normalized_leagues']}")
    print(f"Manifest         : {out_dir / 'manifest.json'}")
    print(f"Summary          : {summary_path}")
    print(f"Unsupported CSV  : {out_dir / 'combined' / 'unsupported_website_leagues.csv'}")
    return 0 if manifest["failed_csvs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
