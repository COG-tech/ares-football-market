#!/usr/bin/env python3
"""
Build an ARES Commons input CSV from Wikidata for top football leagues.

This creates the target entity list for the Commons downloader. It uses
Wikidata and Wikimedia Commons only. It does not scrape Transfermarkt,
Google Images, ESPN, club sites, MLS pages, Getty, Reuters, AP, or social
media.

Default scope:
- 10 football markets
- top division plus the level underneath
- players with a Wikidata P18 image claim, because that gives an exact
  Commons file title for safer license verification downstream
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List
from urllib.parse import unquote, urlparse

import pandas as pd
import requests


WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"


@dataclass(frozen=True)
class LeagueTarget:
    market: str
    level: str
    league_name: str
    qid: str
    country: str
    region: str


DEFAULT_LEAGUES: List[LeagueTarget] = [
    LeagueTarget("England", "top", "Premier League", "Q9448", "England", "Europe"),
    LeagueTarget("England", "second", "EFL Championship", "Q19510", "England", "Europe"),
    LeagueTarget("Spain", "top", "La Liga", "Q324867", "Spain", "Europe"),
    LeagueTarget("Spain", "second", "LaLiga 2", "Q35615", "Spain", "Europe"),
    LeagueTarget("Germany", "top", "Bundesliga", "Q82595", "Germany", "Europe"),
    LeagueTarget("Germany", "second", "2. Bundesliga", "Q152665", "Germany", "Europe"),
    LeagueTarget("Italy", "top", "Serie A", "Q15804", "Italy", "Europe"),
    LeagueTarget("Italy", "second", "Serie B", "Q194052", "Italy", "Europe"),
    LeagueTarget("France", "top", "Ligue 1", "Q13394", "France", "Europe"),
    LeagueTarget("France", "second", "Ligue 2", "Q217374", "France", "Europe"),
    LeagueTarget("Netherlands", "top", "Eredivisie", "Q167541", "Netherlands", "Europe"),
    LeagueTarget("Netherlands", "second", "Eerste Divisie", "Q610823", "Netherlands", "Europe"),
    LeagueTarget("Portugal", "top", "Liga Portugal", "Q182994", "Portugal", "Europe"),
    LeagueTarget("Portugal", "second", "Liga Portugal 2", "Q754488", "Portugal", "Europe"),
    LeagueTarget("Brazil", "top", "Campeonato Brasileiro Serie A", "Q206813", "Brazil", "South America"),
    LeagueTarget("Brazil", "second", "Campeonato Brasileiro Serie B", "Q610175", "Brazil", "South America"),
    LeagueTarget("USA / Canada", "top", "Major League Soccer", "Q18543", "USA / Canada", "North America"),
    LeagueTarget("USA", "second", "USL Championship", "Q1362411", "USA", "North America"),
    LeagueTarget("Mexico", "top", "Liga MX", "Q764690", "Mexico", "North America"),
    LeagueTarget("Mexico", "second", "Liga de Expansion MX", "Q92292023", "Mexico", "North America"),
]


def make_user_agent(contact: str) -> str:
    contact = contact.strip() or "contact-not-provided@example.com"
    return f"ARESFootballMarketWikidataEntityBuilder/1.0 ({contact})"


def commons_title_from_url(image_url: str) -> str:
    if not image_url:
        return ""
    filename = Path(urlparse(image_url).path).name
    filename = unquote(filename).replace("_", " ").strip()
    return f"File:{filename}" if filename else ""


def qid_from_uri(uri: str) -> str:
    return uri.rstrip("/").rsplit("/", 1)[-1]


def value(binding: Dict[str, Any], key: str) -> str:
    return binding.get(key, {}).get("value", "")


def sparql_for_league(league: LeagueTarget, limit: int | None, birth_after: str) -> str:
    limit_clause = f"LIMIT {limit}" if limit else ""
    # Preferred-rank P54 statements are the least bad Wikidata signal for
    # current club without using paid/restricted roster feeds.
    return f"""
SELECT DISTINCT ?player ?playerLabel ?clubLabel ?image ?dob ?positionLabel WHERE {{
  VALUES ?league {{ wd:{league.qid} }}
  ?club wdt:P118 ?league.
  ?player wdt:P106 wd:Q937857.
  ?player p:P54 ?membership.
  ?membership ps:P54 ?club.
  ?membership wikibase:rank wikibase:PreferredRank.
  ?player wdt:P18 ?image.
  OPTIONAL {{ ?player wdt:P569 ?dob. }}
  FILTER(!BOUND(?dob) || ?dob >= "{birth_after}"^^xsd:dateTime)
  OPTIONAL {{ ?player wdt:P413 ?position. }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
ORDER BY ?clubLabel ?playerLabel
{limit_clause}
""".strip()


def fetch_league_rows(session: requests.Session, league: LeagueTarget, limit: int | None, birth_after: str, sleep_seconds: float) -> List[Dict[str, str]]:
    time.sleep(sleep_seconds)
    response = session.get(
        WIKIDATA_SPARQL,
        params={"query": sparql_for_league(league, limit, birth_after), "format": "json"},
        timeout=90,
    )
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "10"))
        time.sleep(retry_after)
        response = session.get(
            WIKIDATA_SPARQL,
            params={"query": sparql_for_league(league, limit, birth_after), "format": "json"},
            timeout=90,
        )
    response.raise_for_status()

    rows: List[Dict[str, str]] = []
    for binding in response.json().get("results", {}).get("bindings", []):
        qid = qid_from_uri(value(binding, "player"))
        image_url = value(binding, "image")
        rows.append(
            {
                "entity_id": f"soc_{qid.lower()}",
                "entity_name": value(binding, "playerLabel"),
                "sport": "soccer",
                "league": league.league_name,
                "team": value(binding, "clubLabel"),
                "commons_title": commons_title_from_url(image_url),
                "wikidata_qid": qid,
                "league_qid": league.qid,
                "market": league.market,
                "level": league.level,
                "country": league.country,
                "region": league.region,
                "position": value(binding, "positionLabel"),
                "date_of_birth": value(binding, "dob")[:10],
                "wikidata_image_url": image_url,
                "data_mode": "wikimedia_open_data",
            }
        )
    return rows


def unique_rows(rows: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    final: List[Dict[str, str]] = []
    for row in rows:
        key = row["entity_id"]
        if key in seen:
            continue
        seen.add(key)
        final.append(row)
    return final


def write_league_manifest(path: Path, leagues: List[LeagueTarget]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["market", "level", "league_name", "qid", "country", "region"])
        writer.writeheader()
        for league in leagues:
            writer.writerow(
                {
                    "market": league.market,
                    "level": league.level,
                    "league_name": league.league_name,
                    "qid": league.qid,
                    "country": league.country,
                    "region": league.region,
                }
            )


def run(args: argparse.Namespace) -> None:
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": make_user_agent(args.contact), "Accept": "application/sparql-results+json"})

    limit = None if args.no_limit else args.players_per_league
    all_rows: List[Dict[str, str]] = []
    summary_rows: List[Dict[str, Any]] = []

    for league in DEFAULT_LEAGUES:
        try:
            rows = fetch_league_rows(session, league, limit, args.birth_after, args.sleep_seconds)
            all_rows.extend(rows)
            summary_rows.append(
                {
                    "league": league.league_name,
                    "level": league.level,
                    "country": league.country,
                    "region": league.region,
                    "rows": len(rows),
                    "status": "ok",
                }
            )
            print(f"{league.league_name}: {len(rows)} players with Commons image claims")
        except Exception as exc:
            summary_rows.append(
                {
                    "league": league.league_name,
                    "level": league.level,
                    "country": league.country,
                    "region": league.region,
                    "rows": 0,
                    "status": f"error:{exc}",
                }
            )
            print(f"{league.league_name}: error: {exc}")

    rows = unique_rows([row for row in all_rows if row.get("commons_title")])
    frame = pd.DataFrame(rows)
    frame.to_csv(output_path, index=False, encoding="utf-8-sig")

    summary_path = output_path.with_name(f"{output_path.stem}_summary.csv")
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False, encoding="utf-8-sig")

    manifest_path = output_path.with_name("top10_two_level_league_manifest.csv")
    write_league_manifest(manifest_path, DEFAULT_LEAGUES)

    print("Done.")
    print(f"Entity CSV: {output_path}")
    print(f"Unique players with exact Commons titles: {len(frame)}")
    print(f"Summary CSV: {summary_path}")
    print(f"League manifest: {manifest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build ARES Commons entity CSV from Wikidata top league targets.")
    parser.add_argument("--output", default="ares_top10_two_levels_entities.csv", help="Output CSV for ares_commons_image_downloader.py.")
    parser.add_argument("--contact", required=True, help="Contact email or URL for Wikimedia/Wikidata User-Agent.")
    parser.add_argument("--players-per-league", type=int, default=100, help="Max players per league. Ignored with --no-limit.")
    parser.add_argument("--no-limit", action="store_true", help="Do not cap players per league. This can be slow and may timeout.")
    parser.add_argument("--birth-after", default="1983-01-01", help="Filter out older/historical players by date of birth.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Delay between Wikidata requests.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
