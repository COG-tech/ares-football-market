#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SITE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE_ROOT = Path(r"D:\aRES\football\open_match_csv")
TODAY = date.today().isoformat()
NOW_UTC = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
CHUNK_SIZE = 25000
LATEST_LIMIT = 5000


MATCH_COLUMNS = [
    "match_id",
    "source_season",
    "country",
    "league_code",
    "league_name",
    "date",
    "time",
    "home_team",
    "away_team",
    "full_time_home_goals",
    "full_time_away_goals",
    "full_time_result",
    "half_time_home_goals",
    "half_time_away_goals",
    "half_time_result",
    "referee",
    "source_url",
    "source_confidence",
    "is_placeholder",
]


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        if compact:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def parse_date(value: str) -> datetime:
    value = (value or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return datetime.min


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in MATCH_COLUMNS:
        if col == "source_confidence":
            out[col] = "Open match CSV"
        elif col == "is_placeholder":
            out[col] = False
        else:
            out[col] = row.get(col, "")
    for col in ["full_time_home_goals", "full_time_away_goals", "half_time_home_goals", "half_time_away_goals"]:
        raw = out.get(col, "")
        if raw == "":
            out[col] = None
            continue
        try:
            val = float(raw)
            out[col] = int(val) if val.is_integer() else val
        except ValueError:
            out[col] = None
    return out


def load_matches(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [clean_row(row) for row in reader]
    rows.sort(key=lambda row: (parse_date(str(row.get("date", ""))), str(row.get("country", "")), str(row.get("league_name", ""))), reverse=True)
    return rows


def split_chunks(rows: list[dict[str, Any]], out_dir: Path) -> list[dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("part-*.json"):
        old.unlink()
    parts = []
    for idx in range(0, len(rows), CHUNK_SIZE):
        part_no = idx // CHUNK_SIZE
        chunk = rows[idx : idx + CHUNK_SIZE]
        rel = f"full/matches/part-{part_no:04d}.json"
        write_json(SITE_ROOT / "data" / rel, chunk, compact=True)
        parts.append({"path": rel, "rows": len(chunk)})
    return parts


def league_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("country", "")), str(row.get("league_code", "")), str(row.get("league_name", "")))
        grouped.setdefault(key, []).append(row)

    out = []
    for (country, code, name), league_rows in grouped.items():
        dates = [parse_date(str(row.get("date", ""))) for row in league_rows]
        dates = [d for d in dates if d != datetime.min]
        seasons = sorted({str(row.get("source_season", "")) for row in league_rows if str(row.get("source_season", "")).strip()})
        teams = set()
        for row in league_rows:
            if row.get("home_team"):
                teams.add(str(row["home_team"]))
            if row.get("away_team"):
                teams.add(str(row["away_team"]))
        out.append(
            {
                "country": country,
                "league_code": code,
                "league_name": name,
                "matches": len(league_rows),
                "seasons": len(seasons),
                "clubs_seen": len(teams),
                "first_date": min(dates).date().isoformat() if dates else "",
                "last_date": max(dates).date().isoformat() if dates else "",
                "source": "Football-Data.co.uk open CSV",
            }
        )
    out.sort(key=lambda row: (row["country"], row["league_name"]))
    return out


def latest_by_league(rows: list[dict[str, Any]], per_league: int = 25) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    out = []
    for row in rows:
        key = str(row.get("league_code", ""))
        if counts[key] >= per_league:
            continue
        out.append(row)
        counts[key] += 1
    return out


def update_data_status(match_count: int, league_count: int, archive_manifest: dict[str, Any]) -> None:
    path = SITE_ROOT / "data" / "data_status.json"
    status = read_json(path, {}) or {}
    status.update(
        {
            "last_updated": TODAY,
            "open_match_rows": match_count,
            "open_match_leagues": league_count,
            "open_match_source": "Football-Data.co.uk open CSV",
            "open_match_cache_generated_at_utc": NOW_UTC,
            "open_match_source_manifest_generated_at_utc": archive_manifest.get("generated_at_utc", ""),
        }
    )
    write_json(path, status)


def update_full_manifest(match_count: int, parts: list[dict[str, Any]]) -> None:
    path = SITE_ROOT / "data" / "full" / "manifest.json"
    manifest = read_json(path, {}) or {}
    tables = [
        table
        for table in manifest.get("tables", [])
        if table.get("source_csv") not in {"open_matches.csv", "matches.csv"}
        and table.get("path") != "full/matches/part-0000.json"
    ]
    tables.insert(
        0,
        {
            "source_csv": "open_matches.csv",
            "path": "full/matches/part-0000.json",
            "partitioned_paths": parts,
            "rows": match_count,
            "columns": MATCH_COLUMNS,
            "source": "Football-Data.co.uk open CSV",
            "last_updated": TODAY,
        },
    )
    manifest["tables"] = tables
    manifest["source"] = "ARES Football public export with integrated Football-Data.co.uk open match cache"
    manifest["last_updated"] = TODAY
    write_json(path, manifest)


def update_navigation() -> None:
    path = SITE_ROOT / "data" / "navigation.json"
    nav = read_json(path, {}) or {}
    menus = nav.setdefault("menus", [])
    if not any(menu.get("id") == "matches" for menu in menus):
        menus.insert(
            4,
            {
                "id": "matches",
                "label": "Matches",
                "summary": "Open match results and league coverage from Football-Data.co.uk.",
                "sidebar": [{"label": "Open Match Data", "href": "matches/index.html"}],
                "groups": [
                    {
                        "title": "Open Match Data",
                        "items": [
                            {"label": "Match Board", "href": "matches/index.html"},
                            {"label": "League Coverage", "href": "matches/index.html#coverage"},
                            {"label": "Latest Results", "href": "matches/index.html#latest"},
                        ],
                    }
                ],
            },
        )
    write_json(path, nav)


def write_matches_page(summary: list[dict[str, Any]]) -> None:
    total_matches = sum(int(row["matches"]) for row in summary)
    total_leagues = len(summary)
    page = f"""<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>Open Match Data | ARES Football Market</title>
  <meta name=\"description\" content=\"Open football match result archive integrated from Football-Data.co.uk CSV data.\">
  <link rel=\"canonical\" href=\"https://cog-tech.github.io/ares-football-market/matches/\">
  <link rel=\"shortcut icon\" href=\"../assets/media/brand/ares-logo.png\">
  <link href=\"../assets/plugins/global/plugins.bundle.css\" rel=\"stylesheet\" type=\"text/css\">
  <link href=\"../assets/css/style.bundle.css\" rel=\"stylesheet\" type=\"text/css\">
  <link href=\"../assets/css/ares-theme.css?v=20260523-continent\" rel=\"stylesheet\" type=\"text/css\">
  <link href=\"../assets/css/ares-components.css?v=20260523-continent\" rel=\"stylesheet\" type=\"text/css\">
  <style>.soccer-main{{width:min(100%,1440px);margin:0 auto;padding:clamp(1rem,2.5vw,2rem)}}.ares-terminal-grid{{grid-template-columns:minmax(0,1fr)}}@media(max-width:900px){{.ares-table td{{min-width:8rem}}}}</style></head><body class=\"ares-shell\"><header class=\"ares-topbar\" data-ares-root=\"..\">
    <a class=\"ares-brand\" href=\"../index.html\">ARES Football Market</a>
    <nav class=\"ares-nav\" aria-label=\"Primary\">
      <a href=\"../index.html\">Home</a><a href=\"../players/index.html\">Players</a><a href=\"../rankings/ares.html\">ARES Rankings</a><a href=\"../rankings/market.html\">Market Rankings</a><a href=\"../clubs/index.html\">Clubs</a><a href=\"../leagues/index.html\">Leagues</a><a href=\"../matches/index.html\">Matches</a><a href=\"../transfers/index.html\">Transfers</a><a href=\"../continents/\">Continents</a><a href=\"../watchlist/index.html\">Watchlist</a>
    </nav>
  </header><div class=\"ares-beta-strip\"><strong>Open match data connected</strong><span>Football-Data.co.uk CSV cache integrated {TODAY}.</span></div><main class=\"soccer-main\"><div class=\"ares-page-title\"><h1>Open Match Data</h1><p>Public match result coverage from Football-Data.co.uk, integrated into the ARES Football Market data layer.</p></div><section class=\"ares-section ares-kpi-grid\"><div class=\"ares-kpi-card\"><span class=\"label\">Match Rows</span><span class=\"value\">{total_matches:,}</span><span class=\"meta\">Normalized public rows</span></div><div class=\"ares-kpi-card\"><span class=\"label\">Leagues</span><span class=\"value\">{total_leagues}</span><span class=\"meta\">Mapped open CSV sources</span></div><div class=\"ares-kpi-card\"><span class=\"label\">Cache</span><span class=\"value\">Daily</span><span class=\"meta\">One refresh per date</span></div><div class=\"ares-kpi-card\"><span class=\"label\">Source</span><span class=\"value\">Open CSV</span><span class=\"meta\">Football-Data.co.uk</span></div></section><section id=\"coverage\" class=\"ares-section ares-card\"><div class=\"ares-section-title\"><div><h2 class=\"h4\">League Coverage</h2><p>Coverage by mapped league, with season counts and date ranges.</p></div></div><input id=\"coverage-search\" class=\"ares-search mb-3\" type=\"search\" aria-label=\"Search match coverage\"><div class=\"table-responsive\"><table id=\"coverage-table\" class=\"ares-table\"><thead><tr><th>League</th><th>Country</th><th>Code</th><th>Matches</th><th>Seasons</th><th>Clubs Seen</th><th>First Date</th><th>Last Date</th><th>Source</th></tr></thead><tbody id=\"coverage-body\"></tbody></table></div></section><section id=\"latest\" class=\"ares-section ares-card\"><div class=\"ares-section-title\"><div><h2 class=\"h4\">Latest Open Match Rows</h2><p>Latest results from each mapped league. The complete archive is partitioned under <code>data/full/matches/</code>.</p></div></div><input id=\"latest-search\" class=\"ares-search mb-3\" type=\"search\" aria-label=\"Search latest matches\"><div class=\"table-responsive\"><table id=\"latest-table\" class=\"ares-table\"><thead><tr><th>Date</th><th>League</th><th>Home</th><th>Away</th><th>FT</th><th>HT</th><th>Source</th></tr></thead><tbody id=\"latest-body\"></tbody></table></div></section></main><footer class=\"ares-footer\">ARES Football Market is an independent public beta football intelligence product. <a href=\"../image-credits.html\">Image credits</a>.</footer><script src=\"../assets/plugins/global/plugins.bundle.js\"></script>
  <script src=\"../assets/js/scripts.bundle.js\"></script>
  <script src=\"../assets/js/ares-data-loader.js\"></script>
  <script src=\"../assets/js/ares-tables.js\"></script>
  <script src=\"../assets/js/soccer-pages.js\"></script>
  <script src=\"../assets/js/ares-mega-nav.js?v=20260523-continent\"></script><script>AresSoccer.initTable({{"dataPath":"../data/open_match_summary.json","tableId":"coverage-table","bodyId":"coverage-body","columns":[{{"key":"league_name","label":"League"}},{{"key":"country","label":"Country"}},{{"key":"league_code","label":"Code"}},{{"key":"matches","label":"Matches"}},{{"key":"seasons","label":"Seasons"}},{{"key":"clubs_seen","label":"Clubs Seen"}},{{"key":"first_date","label":"First Date"}},{{"key":"last_date","label":"Last Date"}},{{"key":"source","label":"Source"}}],"searchId":"coverage-search","sortKey":"matches","sortDirection":"desc"}});AresSoccer.initTable({{"dataPath":"../data/open_match_latest.json","tableId":"latest-table","bodyId":"latest-body","columns":[{{"key":"date","label":"Date"}},{{"key":"league_name","label":"League"}},{{"key":"home_team","label":"Home"}},{{"key":"away_team","label":"Away"}},{{"key":"full_time_score","label":"FT"}},{{"key":"half_time_score","label":"HT"}},{{"key":"source_confidence","label":"Source"}}],"searchId":"latest-search","sortKey":"date","sortDirection":"desc"}});</script></body></html>"""
    out = SITE_ROOT / "matches" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def make_latest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest = latest_by_league(rows)
    out = []
    for row in latest[:LATEST_LIMIT]:
        item = row.copy()
        h = item.get("full_time_home_goals")
        a = item.get("full_time_away_goals")
        hh = item.get("half_time_home_goals")
        ha = item.get("half_time_away_goals")
        item["full_time_score"] = "" if h is None or a is None else f"{h}-{a}"
        item["half_time_score"] = "" if hh is None or ha is None else f"{hh}-{ha}"
        out.append(item)
    return out


def should_skip(cache_state_path: Path, force: bool) -> bool:
    if force:
        return False
    state = read_json(cache_state_path, {}) or {}
    return state.get("last_success_date") == TODAY


def publish_if_requested(paths: list[Path], message: str) -> None:
    rel_paths = [str(path.relative_to(SITE_ROOT)) for path in paths if path.exists()]
    if not rel_paths:
        return
    status = subprocess.run(["git", "-C", str(SITE_ROOT), "status", "--short", "--", *rel_paths], text=True, capture_output=True, check=False)
    if not status.stdout.strip():
        print("No website data changes to publish.")
        return
    subprocess.run(["git", "-C", str(SITE_ROOT), "add", "--", *rel_paths], check=True)
    subprocess.run(["git", "-C", str(SITE_ROOT), "commit", "-m", message], check=True)
    subprocess.run(["git", "-C", str(SITE_ROOT), "push", "origin", "main"], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Integrate cached open match data into the ARES Football Market website.")
    ap.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--publish", action="store_true", help="Commit and push website data after integration.")
    args = ap.parse_args()

    cache_state_path = SITE_ROOT / "data" / "open_match_cache_state.json"
    if should_skip(cache_state_path, args.force):
        print(f"Open match website cache already integrated for {TODAY}. Use --force to rebuild.")
        return 0

    archive_manifest = read_json(args.archive_root / "manifest.json", {}) or {}
    csv_path = args.archive_root / "combined" / "matches_normalized.csv"
    if not csv_path.exists():
        raise SystemExit(f"Missing normalized match CSV: {csv_path}")

    rows = load_matches(csv_path)
    summary = league_summary(rows)
    parts = split_chunks(rows, SITE_ROOT / "data" / "full" / "matches")
    latest = make_latest_rows(rows)

    write_json(SITE_ROOT / "data" / "matches.json", latest, compact=True)
    write_json(SITE_ROOT / "data" / "open_match_latest.json", latest, compact=True)
    write_json(SITE_ROOT / "data" / "open_match_summary.json", summary)
    write_json(SITE_ROOT / "data" / "open_match_manifest.json", archive_manifest)
    update_data_status(len(rows), len(summary), archive_manifest)
    update_full_manifest(len(rows), parts)
    update_navigation()
    write_matches_page(summary)
    write_json(
        cache_state_path,
        {
            "last_success_date": TODAY,
            "last_success_utc": NOW_UTC,
            "archive_root": str(args.archive_root),
            "source_manifest_generated_at_utc": archive_manifest.get("generated_at_utc", ""),
            "match_rows": len(rows),
            "league_rows": len(summary),
            "full_match_parts": len(parts),
        },
    )

    touched = [
        SITE_ROOT / "README.md",
        SITE_ROOT / "assets" / "js" / "ares-mega-nav.js",
        SITE_ROOT / "scripts" / "integrate_open_match_data.py",
        SITE_ROOT / "scripts" / "run_daily_open_match_cache.ps1",
        SITE_ROOT / "data" / "matches.json",
        SITE_ROOT / "data" / "open_match_latest.json",
        SITE_ROOT / "data" / "open_match_summary.json",
        SITE_ROOT / "data" / "open_match_manifest.json",
        SITE_ROOT / "data" / "open_match_cache_state.json",
        SITE_ROOT / "data" / "data_status.json",
        SITE_ROOT / "data" / "navigation.json",
        SITE_ROOT / "data" / "full" / "manifest.json",
        SITE_ROOT / "matches" / "index.html",
        *[SITE_ROOT / "data" / part["path"] for part in parts],
    ]
    if args.publish:
        publish_if_requested(touched, f"Update open match data cache {TODAY}")

    print(f"Integrated {len(rows):,} open match rows across {len(summary)} leagues into website data.")
    print(f"Full match chunks: {len(parts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
