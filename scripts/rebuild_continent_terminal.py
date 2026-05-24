#!/usr/bin/env python3
"""Rebuild ARES Football Market as a continent-led public beta terminal."""

from __future__ import annotations

import html
import json
import math
import re
import statistics
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://cog-tech.github.io/ares-football-market/"
SITE_ROOT = "/ares-football-market/"
TODAY = "2026-05-23"
DATA_MODE = "public_beta_demo"
PUBLIC_LABEL = "Seeded Beta"

CONTINENTS = ["Europe", "Asia", "Africa", "North America", "South America", "Oceania"]
CONFED_BY_CONTINENT = {
    "Europe": "UEFA",
    "Asia": "AFC",
    "Africa": "CAF",
    "North America": "CONCACAF",
    "South America": "CONMEBOL",
    "Oceania": "OFC",
}

COUNTRY_GEO = {
    "England": ("Europe", "Western Europe", "UEFA"),
    "Spain": ("Europe", "Southern Europe", "UEFA"),
    "Italy": ("Europe", "Southern Europe", "UEFA"),
    "Germany": ("Europe", "Western Europe", "UEFA"),
    "France": ("Europe", "Western Europe", "UEFA"),
    "Netherlands": ("Europe", "Western Europe", "UEFA"),
    "Belgium": ("Europe", "Western Europe", "UEFA"),
    "Portugal": ("Europe", "Southern Europe", "UEFA"),
    "Turkey": ("Europe", "Southern Europe", "UEFA"),
    "Scotland": ("Europe", "Northern Europe", "UEFA"),
    "Switzerland": ("Europe", "Western Europe", "UEFA"),
    "USA": ("North America", "CONCACAF", "CONCACAF"),
    "United States": ("North America", "CONCACAF", "CONCACAF"),
    "Mexico": ("North America", "CONCACAF", "CONCACAF"),
    "Canada": ("North America", "CONCACAF", "CONCACAF"),
    "CONCACAF": ("North America", "CONCACAF", "CONCACAF"),
    "Brazil": ("South America", "CONMEBOL", "CONMEBOL"),
    "Argentina": ("South America", "CONMEBOL", "CONMEBOL"),
    "Uruguay": ("South America", "CONMEBOL", "CONMEBOL"),
    "Colombia": ("South America", "CONMEBOL", "CONMEBOL"),
    "Chile": ("South America", "CONMEBOL", "CONMEBOL"),
    "Japan": ("Asia", "East Asia", "AFC"),
    "South Korea": ("Asia", "East Asia", "AFC"),
    "Saudi Arabia": ("Asia", "Middle East", "AFC"),
    "China": ("Asia", "East Asia", "AFC"),
    "India": ("Asia", "South Asia", "AFC"),
    "UAE": ("Asia", "Middle East", "AFC"),
    "Qatar": ("Asia", "Middle East", "AFC"),
    "Iran": ("Asia", "Middle East", "AFC"),
    "Uzbekistan": ("Asia", "Central Asia", "AFC"),
    "Thailand": ("Asia", "Southeast Asia", "AFC"),
    "Malaysia": ("Asia", "Southeast Asia", "AFC"),
    "Vietnam": ("Asia", "Southeast Asia", "AFC"),
    "Indonesia": ("Asia", "Southeast Asia", "AFC"),
    "Singapore": ("Asia", "Southeast Asia", "AFC"),
    "Hong Kong": ("Asia", "East Asia", "AFC"),
    "Taiwan": ("Asia", "East Asia", "AFC"),
    "AFC": ("Asia", "AFC", "AFC"),
    "Australia": ("Oceania", "Oceania", "AFC"),
    "New Zealand": ("Oceania", "Oceania", "OFC"),
    "Egypt": ("Africa", "North Africa", "CAF"),
    "Morocco": ("Africa", "North Africa", "CAF"),
    "Nigeria": ("Africa", "West Africa", "CAF"),
    "Ghana": ("Africa", "West Africa", "CAF"),
    "Kenya": ("Africa", "East Africa", "CAF"),
    "South Africa": ("Africa", "Southern Africa", "CAF"),
}

LEAGUE_COUNTRY = {
    "Premier League": "England",
    "EFL Championship": "England",
    "La Liga": "Spain",
    "LaLiga 2": "Spain",
    "Serie A": "Italy",
    "Serie B": "Italy",
    "Bundesliga": "Germany",
    "German Bundesliga": "Germany",
    "2. Bundesliga": "Germany",
    "Ligue 1": "France",
    "Ligue 2": "France",
    "Eredivisie": "Netherlands",
    "Eerste Divisie": "Netherlands",
    "Liga Portugal": "Portugal",
    "Liga Portugal 2": "Portugal",
    "Super Lig": "Turkey",
    "TFF First League": "Turkey",
    "Major League Soccer": "USA",
    "MLS Next Pro": "USA",
    "USL Championship": "USA",
    "USL League One": "USA",
    "USL League Two": "USA",
    "Liga MX": "Mexico",
    "Liga de Expansion MX": "Mexico",
    "Liga de Expansión MX": "Mexico",
    "Canadian Premier League": "Canada",
    "Campeonato Brasileiro Serie A": "Brazil",
    "Brazil Serie A": "Brazil",
    "Argentine Primera Division": "Argentina",
    "Argentine Primera": "Argentina",
    "J1 League": "Japan",
    "J2 League": "Japan",
    "J3 League": "Japan",
    "K League 1": "South Korea",
    "K League 2": "South Korea",
    "Saudi Pro League": "Saudi Arabia",
    "Chinese Super League": "China",
    "A-League": "Australia",
    "A-League Men": "Australia",
    "Indian Super League": "India",
    "South African Premier Division": "South Africa",
    "Egypt Premier League": "Egypt",
}

REQUIRED_LEAGUES = [
    ("Major League Soccer", "USA", 1), ("MLS Next Pro", "USA", 3), ("USL Championship", "USA", 2),
    ("USL League One", "USA", 3), ("USL League Two", "USA", 4), ("Liga MX", "Mexico", 1),
    ("Liga de Expansion MX", "Mexico", 2), ("Canadian Premier League", "Canada", 1),
    ("CONCACAF Champions Cup", "CONCACAF", 0), ("J1 League", "Japan", 1), ("J2 League", "Japan", 2),
    ("J3 League", "Japan", 3), ("K League 1", "South Korea", 1), ("K League 2", "South Korea", 2),
    ("Saudi Pro League", "Saudi Arabia", 1), ("Chinese Super League", "China", 1),
    ("A-League", "Australia", 1), ("Indian Super League", "India", 1), ("UAE Pro League", "UAE", 1),
    ("Qatar Stars League", "Qatar", 1), ("Persian Gulf Pro League", "Iran", 1),
    ("Uzbekistan Super League", "Uzbekistan", 1), ("Thai League 1", "Thailand", 1),
    ("Thai League 2", "Thailand", 2), ("Malaysia Super League", "Malaysia", 1),
    ("V.League 1", "Vietnam", 1), ("Indonesia Liga 1", "Indonesia", 1),
    ("Singapore Premier League", "Singapore", 1), ("Hong Kong Premier League", "Hong Kong", 1),
    ("Taiwan Football Premier League", "Taiwan", 1), ("AFC Champions League Elite", "AFC", 0),
    ("AFC Champions League Two", "AFC", 0), ("Brazil Serie A", "Brazil", 1),
    ("Argentine Primera", "Argentina", 1), ("Egypt Premier League", "Egypt", 1),
    ("South African Premier Division", "South Africa", 1), ("New Zealand National League", "New Zealand", 1),
    ("OFC Champions League", "New Zealand", 0), ("Premier League", "England", 1),
    ("La Liga", "Spain", 1), ("Serie A", "Italy", 1), ("Bundesliga", "Germany", 1),
    ("Ligue 1", "France", 1),
]

SYNTHETIC_POOLS = {
    "Africa": [
        ("Kofi Mensar", "FW", "Accra Harbor", "Ghana Premier League", "Ghana"),
        ("Amir Benyoussef", "MF", "Cairo Atlas", "Egypt Premier League", "Egypt"),
        ("Tebo Mkhize", "DF", "Cape Meridian", "South African Premier Division", "South Africa"),
        ("Nuru Okeke", "W", "Lagos Mainland", "Nigeria Premier League", "Nigeria"),
        ("Idris El Fassi", "GK", "Rabat Union", "Morocco Botola", "Morocco"),
    ],
    "Oceania": [
        ("Tane Raukawa", "MF", "Auckland Harbour", "New Zealand National League", "New Zealand"),
        ("Noah Kerrin", "FW", "Melbourne Southern", "A-League", "Australia"),
        ("Luka Tevita", "DF", "Suva Coast", "OFC Champions League", "New Zealand"),
        ("Mason Wylie", "GK", "Wellington North", "New Zealand National League", "New Zealand"),
        ("Ari Vatu", "W", "Sydney Southern", "A-League", "Australia"),
    ],
}


def read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: str, payload: str) -> None:
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8")


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-")
    return clean or "ares"


def site_url(path: str) -> str:
    return SITE_ROOT + path.lstrip("/")


def avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def geo_for(country: str, league: str = "", previous_region: str = "") -> tuple[str, str, str]:
    country = country or LEAGUE_COUNTRY.get(league, "")
    if country in COUNTRY_GEO:
        return COUNTRY_GEO[country]
    if league in LEAGUE_COUNTRY and LEAGUE_COUNTRY[league] in COUNTRY_GEO:
        return COUNTRY_GEO[LEAGUE_COUNTRY[league]]
    if previous_region in CONTINENTS:
        return previous_region, previous_region, CONFED_BY_CONTINENT[previous_region]
    return "Europe", "Western Europe", "UEFA"


def public_mode(row: dict[str, Any]) -> str:
    return DATA_MODE


def normalize_player(row: dict[str, Any]) -> dict[str, Any]:
    name = row.get("display_name") or row.get("player_name") or row.get("name") or "ARES Player"
    league = row.get("league", "")
    country = row.get("country") or LEAGUE_COUNTRY.get(league, "")
    continent, region, confederation = geo_for(country, league, row.get("region", ""))
    player_id = row.get("player_id") or f"pbp-{slug(name)}"
    player_slug = row.get("slug") or slug(name)
    club = row.get("club") or "ARES Club"
    club_id = row.get("club_id") or f"club-{slug(club)}"
    player_profile_url = site_url(f"players/profile.html?id={player_id}")
    club_profile_url = site_url(f"clubs/{club_id}/")
    league_profile_url = site_url(f"leagues/index.html?league={slug(league)}")
    row.update(
        {
            "data_mode": DATA_MODE,
            "identity_mode": row.get("identity_mode") or "wikimedia_open_photo_beta" if row.get("photo_url") else "synthetic_public_beta",
            "display_name": name,
            "player_name": name,
            "player_id": player_id,
            "slug": player_slug,
            "club": club,
            "club_id": club_id,
            "league": league,
            "league_id": row.get("league_id") or f"league-{slug(league)}",
            "country": country,
            "continent": continent,
            "region": region,
            "confederation": confederation,
            "minutes_role": row.get("minutes_role") or f"{row.get('minutes', 0)} estimated minutes / {row.get('role', 'Role review')}",
            "position_usage": row.get("position_usage") or row.get("position_label") or row.get("position", ""),
            "transfer_value_signal": row.get("transfer_value_signal") or f"{row.get('trend', 'Stable')} {row.get('trend_value', 0)}",
            "role_security": row.get("role_security") or ("High" if int(row.get("minutes", 0) or 0) >= 1900 else "Medium"),
            "durability": row.get("durability") or f"{row.get('availability_pct', 0)}% availability estimate",
            "source": row.get("source") or "ARES seeded beta",
            "score_source": row.get("score_source") or "ARES beta estimate",
            "stats_mode": row.get("stats_mode") or "ARES beta estimate; not official match statistics",
            "url": player_profile_url,
            "player_url": player_profile_url,
            "club_url": club_profile_url,
            "league_url": row.get("league_url") or league_profile_url,
        }
    )
    return row


def add_synthetic_players(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = defaultdict(int)
    for player in players:
        counts[player["continent"]] += 1
    next_rank = len(players) + 1
    for continent in CONTINENTS:
        needed = max(0, 20 - counts[continent])
        if not needed:
            continue
        pool = SYNTHETIC_POOLS.get(continent) or [
            (f"{continent} Beta Asset", "MF", f"{continent} Portfolio FC", f"{continent} Market League", continent)
        ]
        for index in range(needed):
            base = pool[index % len(pool)]
            name = f"{base[0]} {index // len(pool) + 1}" if index >= len(pool) else base[0]
            age = 18 + (index * 3) % 14
            country = base[4]
            cont, region, confed = geo_for(country, base[3], continent)
            market_score = round(76 + (index % 9) * 1.4 + (5 if age <= 23 else 0), 1)
            ares_score = round(73 + (index % 8) * 1.3, 1)
            players.append(
                normalize_player(
                    {
                        "rank": next_rank,
                        "player_id": f"pbp-{slug(continent)}-{index + 1:02d}",
                        "player_name": name,
                        "initials": "".join(part[0] for part in name.split())[:3].upper(),
                        "age": age,
                        "position": base[1],
                        "club": base[2],
                        "league": base[3],
                        "country": country,
                        "continent": cont,
                        "region": region,
                        "confederation": confed,
                        "minutes": 900 + index * 73,
                        "appearances": 12 + index % 18,
                        "starts": 8 + index % 16,
                        "goals": index % 11,
                        "assists": (index * 2) % 9,
                        "availability_pct": 82 + index % 14,
                        "ares_score": ares_score,
                        "ares_tier": "High" if ares_score >= 80 else "Starter",
                        "market_score": market_score,
                        "market_tier": "Rising Asset" if age <= 23 else "Core Starter",
                        "trend": "Rising" if index % 3 else "Flat",
                        "trend_value": round(0.8 + index % 5, 1),
                        "contract_end": str(2027 + index % 4),
                        "age_curve": "Upside" if age <= 23 else "Prime",
                        "role": "Public beta role review",
                        "reason": f"{cont} public-beta asset row showing ARES continent market structure.",
                        "data_confidence": "Medium",
                        "confidence": "Medium",
                        "last_updated": TODAY,
                        "source": "ARES seeded beta",
                        "photo_url": "",
                        "photo_source": "ARES fallback avatar",
                        "photo_license_status": "ares_owned",
                        "photo_credit": "ARES branded fallback avatar",
                        "photo_attribution_url": "",
                        "photo_status": "fallback",
                        "image_confidence": "High",
                    }
                )
            )
            next_rank += 1
    players.sort(key=lambda item: float(item.get("market_score", 0)), reverse=True)
    for index, player in enumerate(players, 1):
        player["rank"] = index
    return players


def build_clubs(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for player in players:
        groups[(player["club"], player["league"])].append(player)
    rows = []
    for (club, league), members in groups.items():
        top = max(members, key=lambda item: float(item.get("market_score", 0)))
        avg_age = avg([float(item.get("age", 0)) for item in members])
        avg_ares = avg([float(item.get("ares_score", 0)) for item in members])
        avg_market = avg([float(item.get("market_score", 0)) for item in members])
        u23_assets = [item for item in members if int(item.get("age", 99)) <= 23]
        rows.append(
            {
                "data_mode": DATA_MODE,
                "club_id": f"club-{slug(club)}",
                "club_name": club,
                "league_id": top["league_id"],
                "league": league,
                "country": top["country"],
                "continent": top["continent"],
                "region": top["region"],
                "confederation": top["confederation"],
                "tier": 1,
                "squad_size": max(len(members), 18),
                "average_age": avg_age,
                "avg_ares": avg_ares,
                "avg_market": avg_market,
                "squad_market_score": avg_market,
                "avg_ares_score": avg_ares,
                "u23_value": avg([float(item.get("market_score", 0)) for item in u23_assets]) if u23_assets else round(avg_market - 3.5, 1),
                "u23_asset_count": len(u23_assets),
                "top_asset": top["player_name"],
                "weakest_unit": "Depth risk review",
                "need_area": "Role security and U23 depth",
                "transfer_risk": "Medium" if avg_age > 28 else "Low",
                "trend": "Rising" if avg_market >= 82 else "Stable",
                "market_trend": "Rising" if avg_market >= 82 else "Stable",
                "data_confidence": "High" if len(members) >= 3 else "Medium",
                "confidence": "High" if len(members) >= 3 else "Medium",
                "last_updated": TODAY,
                "source": "ARES derived from public beta player layer",
                "club_url": site_url(f"clubs/club-{slug(club)}/"),
                "league_url": site_url(f"leagues/index.html?league={slug(league)}"),
                "club_badge_url": "",
            }
        )
    rows.sort(key=lambda item: item["avg_market"], reverse=True)
    for index, row in enumerate(rows, 1):
        row["rank"] = index
    return rows


def build_leagues(players: list[dict[str, Any]], clubs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    player_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    club_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for player in players:
        player_groups[player["league"]].append(player)
    for club in clubs:
        club_groups[club["league"]].append(club)
    rows: dict[str, dict[str, Any]] = {}
    for league, members in player_groups.items():
      top_player = max(members, key=lambda item: float(item.get("market_score", 0)))
      league_clubs = club_groups.get(league, [])
      top_club = max(league_clubs, key=lambda item: float(item.get("avg_market", 0)))["club_name"] if league_clubs else top_player["club"]
      rows[league] = {
          "data_mode": DATA_MODE,
          "league_id": top_player["league_id"],
          "league_name": league,
          "country": top_player["country"],
          "continent": top_player["continent"],
          "region": top_player["region"],
          "confederation": top_player["confederation"],
          "tier": 1,
          "clubs": max(len(league_clubs), 8),
          "players_tracked": len(members),
          "avg_ares": avg([float(item.get("ares_score", 0)) for item in members]),
          "avg_market": avg([float(item.get("market_score", 0)) for item in members]),
          "league_strength": avg([float(item.get("ares_score", 0)) for item in members]),
          "market_depth": avg([float(item.get("market_score", 0)) for item in members]),
          "u23_share": f"{round(len([item for item in members if int(item.get('age', 99)) <= 23]) / len(members) * 100)}%",
          "u23_pipeline": "High" if any(int(item.get("age", 99)) <= 21 for item in members) else "Medium",
          "export_signal": "Rising" if top_player["market_score"] >= 82 else "Stable",
          "top_club": top_club,
          "top_player": top_player["player_name"],
          "data_confidence": "High" if len(members) >= 8 else "Medium",
          "confidence": "High" if len(members) >= 8 else "Medium",
          "last_updated": TODAY,
          "source": "ARES public beta league model",
          "league_url": site_url(f"leagues/index.html?league={slug(league)}"),
          "league_badge_url": "",
      }
    for league, country, tier in REQUIRED_LEAGUES:
        if league in rows:
            continue
        continent, region, confed = geo_for(country, league)
        rows[league] = {
            "data_mode": DATA_MODE,
            "league_id": f"league-{slug(league)}",
            "league_name": league,
            "country": country,
            "continent": continent,
            "region": region,
            "confederation": confed,
            "tier": tier,
            "clubs": 14 if tier != 0 else 24,
            "players_tracked": 0,
            "avg_ares": 72.0 + (len(rows) % 14),
            "avg_market": 72.5 + (len(rows) % 14),
            "league_strength": 72.0 + (len(rows) % 14),
            "market_depth": 72.5 + (len(rows) % 14),
            "u23_share": f"{24 + len(rows) % 12}%",
            "u23_pipeline": "Staged",
            "export_signal": "Public beta watch",
            "top_club": "ARES Club",
            "top_player": "ARES Prospect",
            "data_confidence": "Medium",
            "confidence": "Medium",
            "last_updated": TODAY,
            "source": "ARES seeded beta",
            "league_url": site_url(f"leagues/index.html?league={slug(league)}"),
            "league_badge_url": "",
        }
    league_rows = list(rows.values())
    league_rows.sort(key=lambda item: (item["continent"], -float(item["avg_market"])))
    for index, row in enumerate(league_rows, 1):
        row["rank"] = index
    return league_rows


def build_market_changes(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chosen: list[dict[str, Any]] = []
    for continent in CONTINENTS:
        pool = [p for p in players if p["continent"] == continent]
        rising = sorted([p for p in pool if float(p.get("trend_value", 0)) >= 0], key=lambda item: float(item.get("trend_value", 0)), reverse=True)[:3]
        falling = sorted([p for p in pool if float(p.get("trend_value", 0)) < 0], key=lambda item: float(item.get("trend_value", 0)))[:3]
        filler = [p for p in sorted(pool, key=lambda item: abs(float(item.get("trend_value", 0))), reverse=True) if p not in rising and p not in falling]
        chosen.extend((rising + falling + filler)[:6])
    rows = []
    for index, player in enumerate(chosen, 1):
        value = float(player.get("trend_value", 0))
        rows.append({
            "data_mode": DATA_MODE,
            "change_id": f"mc-{index:03d}",
            "player_id": player["player_id"],
            "player_name": player["player_name"],
            "club": player["club"],
            "club_url": player.get("club_url", ""),
            "league": player["league"],
            "country": player["country"],
            "continent": player["continent"],
            "region": player["region"],
            "confederation": player["confederation"],
            "change": f"{value:+.1f}",
            "trend": "Rising" if value >= 0 else "Falling",
            "reason": player["reason"],
            "source": "ARES public beta movement estimate",
            "last_updated": TODAY,
        })
    return rows


def build_transfers(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    sample = []
    for continent in CONTINENTS:
        sample.extend([p for p in players if p["continent"] == continent][:5])
    movement_types = ["Contract Signal", "Loan Watch", "Permanent Signal", "Free Agent Watch", "Academy Promotion"]
    for index, player in enumerate(sample[:36], 1):
        movement = movement_types[index % len(movement_types)]
        rows.append({
            "data_mode": DATA_MODE,
            "transfer_id": f"pbt-{index:03d}",
            "date": f"2026-05-{(index % 23) + 1:02d}",
            "player_id": player["player_id"],
            "player_name": player["player_name"],
            "player": player["player_name"],
            "initials": player.get("initials", ""),
            "age": player["age"],
            "position": player["position"],
            "from_club": player["club"],
            "from_club_url": player.get("club_url", ""),
            "to_club": "Market fit review",
            "to_club_url": "",
            "from_league": player["league"],
            "to_league": player["league"],
            "country": player["country"],
            "continent": player["continent"],
            "region": player["region"],
            "confederation": player["confederation"],
            "movement_type": movement,
            "transfer_type": movement,
            "ares_impact": f"{(float(player.get('trend_value', 0)) / 3):+.1f}",
            "market_impact": f"{float(player.get('trend_value', 0)):+.1f}",
            "confidence": player.get("data_confidence", "Medium"),
            "data_confidence": player.get("data_confidence", "Medium"),
            "reason": player["reason"],
            "source": "ARES seeded beta",
            "last_updated": TODAY,
            "slug": player.get("slug", slug(player["player_name"])),
            "player_url": player["player_url"],
            "url": player["player_url"],
            "photo_url": player.get("photo_url", ""),
            "photo_source": player.get("photo_source", "ARES fallback avatar"),
            "photo_license_status": player.get("photo_license_status", "ares_owned"),
            "photo_credit": player.get("photo_credit", ""),
            "photo_attribution_url": player.get("photo_attribution_url", ""),
            "photo_status": player.get("photo_status", "fallback"),
            "image_confidence": player.get("image_confidence", "Medium"),
        })
    return rows


def build_watchlist(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    sample: list[dict[str, Any]] = []
    for continent in CONTINENTS:
        sample.extend(sorted([p for p in players if p["continent"] == continent], key=lambda item: (int(item.get("age", 99)), -float(item.get("market_score", 0))))[:6])
    categories = ["Youth Breakout", "U21 Asset", "U23 Asset", "Loan Watch", "Role Expansion", "Contract Signal", "Scouting Flag", "Thin Data Watch"]
    for index, player in enumerate(sample[:36], 1):
        category = categories[index % len(categories)]
        rows.append({
            "data_mode": DATA_MODE,
            "watchlist_id": f"pbw-{index:03d}",
            "watch_id": f"pbw-{index:03d}",
            "category": category,
            "player_id": player["player_id"],
            "player_name": player["player_name"],
            "player": player["player_name"],
            "initials": player.get("initials", ""),
            "age": player["age"],
            "position": player["position"],
            "level": category,
            "club": player["club"],
            "club_url": player.get("club_url", ""),
            "league": player["league"],
            "country": player["country"],
            "continent": player["continent"],
            "region": player["region"],
            "confederation": player["confederation"],
            "watch_reason": category,
            "reason": player["reason"],
            "ares_signal": player["ares_tier"],
            "market_signal": player["market_tier"],
            "risk": "Medium" if player["data_confidence"] == "Medium" else "Low",
            "status": "Tracked outside official rankings until confidence improves",
            "last_movement": player["transfer_value_signal"],
            "confidence": player.get("data_confidence", "Medium"),
            "data_confidence": player.get("data_confidence", "Medium"),
            "last_updated": TODAY,
            "source": "ARES seeded beta",
            "slug": player.get("slug", slug(player["player_name"])),
            "player_url": player["player_url"],
            "url": player["player_url"],
            "photo_url": player.get("photo_url", ""),
            "photo_source": player.get("photo_source", "ARES fallback avatar"),
            "photo_license_status": player.get("photo_license_status", "ares_owned"),
            "photo_credit": player.get("photo_credit", ""),
            "photo_attribution_url": player.get("photo_attribution_url", ""),
            "photo_status": player.get("photo_status", "fallback"),
            "image_confidence": player.get("image_confidence", "Medium"),
        })
    return rows


def build_search(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for player in players:
        rows.append({
            "type": "player",
            "player_name": player["player_name"],
            "position": player["position"],
            "club": player["club"],
            "league": player["league"],
            "country": player["country"],
            "continent": player["continent"],
            "region": player["region"],
            "confederation": player["confederation"],
            "url": player["player_url"],
            "keywords": " ".join(str(player.get(key, "")) for key in ["player_name", "club", "league", "country", "continent", "region", "confederation", "position", "market_tier", "ares_tier"]),
        })
    for club in clubs:
        rows.append({
            "type": "club",
            "club_name": club["club_name"],
            "league": club["league"],
            "country": club["country"],
            "continent": club["continent"],
            "region": club["region"],
            "confederation": club["confederation"],
            "url": club["club_url"],
            "keywords": " ".join(str(v) for v in club.values() if isinstance(v, (str, int, float))),
        })
    for league in leagues:
        rows.append({
            "type": "league",
            "league": league["league_name"],
            "country": league["country"],
            "continent": league["continent"],
            "region": league["region"],
            "confederation": league["confederation"],
            "url": league["league_url"],
            "keywords": " ".join(str(v) for v in league.values() if isinstance(v, (str, int, float))),
        })
    for continent in CONTINENTS:
        rows.append({"type": "continent", "league": f"{continent} Market Board", "continent": continent, "url": f"continents/{slug(continent)}/", "keywords": continent})
    return rows


def table(table_id: str, headers: list[str]) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body_id = table_id.replace("-table", "-body")
    empty = f'<tr><td colspan="{len(headers)}">No matching rows for this filter set. Clear filters to view the full board.</td></tr>'
    return f'<div class="table-responsive"><table id="{table_id}" class="ares-table"><thead><tr>{head}</tr></thead><tbody id="{body_id}">{empty}</tbody></table></div>'


def beta_note() -> str:
    return '<div class="ares-beta-strip"><strong>Seeded beta data</strong><span>Live feeds are not connected.</span></div>'


def kpi_cards(items: list[tuple[str, Any, str]]) -> str:
    cards = []
    for label, value, meta in items:
        cards.append(
            f'<div class="ares-kpi-card"><span class="label">{static_safe(label)}</span>'
            f'<span class="value">{static_safe(value)}</span><span class="meta">{static_safe(meta)}</span></div>'
        )
    return '<section class="ares-section ares-kpi-grid">' + "".join(cards) + "</section>"


def chart_card(title: str, subtitle: str, kind: str = "bars") -> str:
    if kind == "scatter":
        visual = '<div class="ares-chart-frame"><div class="ares-chart-scatter"><i style="left:18%;top:58%"></i><i style="left:34%;top:44%"></i><i style="left:52%;top:31%"></i><i style="left:67%;top:22%"></i><i style="left:78%;top:39%"></i></div></div>'
    elif kind == "line":
        visual = '<div class="ares-chart-frame"><div class="ares-chart-line"></div></div>'
    else:
        visual = '<div class="ares-chart-frame"><div class="ares-chart-bars"><span style="height:48%"></span><span style="height:72%"></span><span style="height:56%"></span><span style="height:88%"></span><span style="height:64%"></span><span style="height:78%"></span></div></div>'
    return (
        f'<div class="ares-graph-card"><h2 class="h4">{static_safe(title)}</h2>'
        f'<p class="ares-muted-note">{static_safe(subtitle)}</p>{visual}'
        '<div class="ares-chart-legend"><span>ARES</span><span>Market</span><span>Trend</span><span>Confidence</span></div></div>'
    )


def terminal_table_card(title: str, description: str, table_id: str, headers: list[str], href: str = "") -> str:
    link = f'<a class="ares-view-link" href="{static_safe(href)}">View full board</a>' if href else ""
    return (
        '<div class="ares-card">'
        f'<div class="ares-section-title"><div><h2 class="h4">{static_safe(title)}</h2><p>{static_safe(description)}</p></div>{link}</div>'
        f'{table(table_id, headers)}</div>'
    )


def terminal_pair(table_html: str, chart_title: str, chart_subtitle: str, kind: str = "bars") -> str:
    return f'<section class="ares-section ares-terminal-grid">{table_html}{chart_card(chart_title, chart_subtitle, kind)}</section>'


def href_for_home_board(table_id: str) -> str:
    if "ares" in table_id:
        return "rankings/ares.html"
    if "market" in table_id or "young" in table_id:
        return "rankings/market.html"
    if "transfer" in table_id or "changes" in table_id:
        return "transfers/index.html"
    if "clubs" in table_id:
        return "clubs/index.html"
    if "leagues" in table_id:
        return "leagues/index.html"
    for continent in CONTINENTS:
        if slug(continent) in table_id:
            return f"continents/{slug(continent)}/"
    return ""


def script_init(configs: list[dict[str, Any]]) -> str:
    chunks = []
    for config in configs:
        cleaned = dict(config)
        cleaned["columns"] = [column for column in cleaned.get("columns", []) if column.get("key") != "data_mode"]
        chunks.append(f"AresSoccer.initTable({json.dumps(cleaned, ensure_ascii=False)});")
    return "".join(chunks)


def root_attr(prefix: str) -> str:
    return "." if prefix == "" else prefix.rstrip("/")


def common_head(prefix: str, title: str, meta: str, canonical: str) -> str:
    return f"""<meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{meta}">
  <link rel="canonical" href="{BASE_URL}{canonical}">
  <link rel="shortcut icon" href="{prefix}assets/media/brand/ares-logo.png">
  <link href="{prefix}assets/plugins/global/plugins.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/plugins/custom/datatables/datatables.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/style.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/ares-theme.css?v=20260523-continent" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/ares-components.css?v=20260523-continent" rel="stylesheet" type="text/css">
  <style>.soccer-main{{width:min(100%,1440px);margin:0 auto;padding:clamp(1rem,2.5vw,2rem)}}.table-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}.table-grid .wide{{grid-column:1/-1}}.hero-grid{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(18rem,.75fr);gap:1rem;align-items:start}}.continent-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}.premium-lock{{position:relative;min-height:8rem}}.premium-lock:after{{content:"Premium";position:absolute;right:1rem;top:1rem}}@media(max-width:1000px){{.table-grid,.hero-grid,.continent-grid{{grid-template-columns:1fr}}}}</style>"""


def page(prefix: str, title: str, meta: str, canonical: str, h1: str, intro: str, body: str, scripts: str = "") -> str:
    nav = f"""<header class="ares-topbar" data-ares-root="{root_attr(prefix)}">
    <a class="ares-brand" href="{prefix}index.html">ARES Football Market</a>
    <nav class="ares-nav" aria-label="Primary">
      <a href="{prefix}index.html">Home</a><a href="{prefix}players/index.html">Players</a><a href="{prefix}rankings/ares.html">ARES Rankings</a><a href="{prefix}rankings/market.html">Market Rankings</a><a href="{prefix}clubs/index.html">Clubs</a><a href="{prefix}leagues/index.html">Leagues</a><a href="{prefix}transfers/index.html">Transfers</a><a href="{prefix}continents/">Continents</a><a href="{prefix}watchlist/index.html">Watchlist</a><a href="{prefix}methodology.html">Methodology</a><a href="{prefix}image-credits.html">Image Credits</a>
    </nav>
  </header>"""
    js = f"""<script src="{prefix}assets/plugins/global/plugins.bundle.js"></script>
  <script src="{prefix}assets/js/scripts.bundle.js"></script>
  <script src="{prefix}assets/js/ares-data-loader.js"></script>
  <script src="{prefix}assets/js/ares-tables.js"></script>
  <script src="{prefix}assets/js/soccer-pages.js"></script>
  <script src="{prefix}assets/js/ares-mega-nav.js?v=20260523-continent"></script>"""
    if scripts:
        js += f"<script>{scripts}</script>"
    return f"""<!DOCTYPE html><html lang="en"><head>{common_head(prefix, title, meta, canonical)}</head><body class="ares-shell">{nav}{beta_note()}<main class="soccer-main"><div class="ares-page-title"><h1>{h1}</h1><p>{intro}</p></div>{body}</main><footer class="ares-footer">ARES Football Market is an independent public beta football intelligence product. <a href="{prefix}image-credits.html">Image credits</a>. <span class="ares-brand-switch"><a href="{prefix}index.html">Global Football</a><a href="https://cog-tech.github.io/ares-gridiron-market/">ARES Gridiron Market</a></span></footer>{js}</body></html>"""


PLAYER_COLS = [
    {"key": "player_name", "label": "Image", "render": "playerImage"},
    {"key": "player_name", "label": "Player", "render": "playerLink", "showAvatar": False},
    {"key": "age", "label": "Age"},
    {"key": "position", "label": "Position"},
    {"key": "club", "label": "Club", "render": "clubLink"},
    {"key": "league", "label": "League", "render": "leagueLink"},
    {"key": "country", "label": "Country"},
    {"key": "continent", "label": "Continent"},
    {"key": "minutes_role", "label": "Minutes / Role"},
    {"key": "ares_score", "label": "ARES Score", "render": "score"},
    {"key": "market_score", "label": "Market Score", "render": "market"},
    {"key": "market_tier", "label": "Tier", "render": "tier"},
    {"key": "trend", "label": "Trend", "render": "trend"},
    {"key": "data_confidence", "label": "Confidence", "render": "confidence"},
    {"key": "data_mode", "label": "Mode", "render": "mode"},
]


def with_prefix(cols: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    out = []
    for col in cols:
        new = dict(col)
        if new.get("render") in {"playerLink", "clubLink", "leagueLink", "link"} or new.get("key") in {"club", "club_name", "from_club", "to_club"}:
            new["pathPrefix"] = prefix
        out.append(new)
    return out


def build_navigation() -> dict[str, Any]:
    return {
        "brand": "ARES Football Market",
        "menus": [
            {"id": "players", "label": "Players", "summary": "Search player assets by continent, region, club, role, and score.", "sidebar": [{"label": "All Players", "href": "players/index.html"}], "groups": [{"title": "Players", "items": [{"label": "All Players", "href": "players/index.html"}, {"label": "U23 Assets", "href": "players/index.html?q=U23"}, {"label": "Rising Players", "href": "players/index.html?trend=Rising"}]}]},
            {"id": "rankings", "label": "Rankings", "summary": "ARES quality and Market asset value boards.", "sidebar": [{"label": "ARES Rankings", "href": "rankings/ares.html"}, {"label": "Market Rankings", "href": "rankings/market.html"}], "groups": [{"title": "Rankings", "items": [{"label": "ARES Rankings", "href": "rankings/ares.html"}, {"label": "Market Rankings", "href": "rankings/market.html"}, {"label": "U23 Assets", "href": "rankings/market.html?q=U23"}, {"label": "Risers and Fallers", "href": "transfers/index.html"}]}]},
            {"id": "continents", "label": "Continents", "summary": "World to continent market boards.", "sidebar": [{"label": "World Map", "href": "continents/"}], "groups": [{"title": "Continents", "items": [{"label": c, "href": f"continents/{slug(c)}/"} for c in CONTINENTS]}]},
            {"id": "leagues", "label": "Leagues", "summary": "League strength, market depth, U23 pipeline, and transfer signal.", "sidebar": [{"label": "All Leagues", "href": "leagues/index.html"}], "groups": [{"title": "Featured Leagues", "items": [{"label": "MLS", "href": "leagues/mls/"}, {"label": "Liga MX", "href": "leagues/index.html?league=Liga%20MX"}, {"label": "J1 League", "href": "leagues/index.html?league=J1%20League"}, {"label": "K League", "href": "leagues/index.html?league=K%20League"}, {"label": "Saudi Pro League", "href": "leagues/index.html?league=Saudi%20Pro%20League"}, {"label": "A-League", "href": "leagues/index.html?league=A-League"}]}]},
            {"id": "clubs", "label": "Clubs", "summary": "Club portfolios, squad market scores, age curves, and need areas.", "sidebar": [{"label": "Club Boards", "href": "clubs/index.html"}], "groups": [{"title": "Clubs", "items": [{"label": "Club Portfolio Board", "href": "clubs/index.html"}, {"label": "U23 Value Leaders", "href": "clubs/index.html?q=U23"}, {"label": "Transfer Risk", "href": "clubs/index.html?q=Risk"}]}]},
            {"id": "transfers", "label": "Transfers", "summary": "Market movement tape across transfers, loans, contracts, and watch signals.", "sidebar": [{"label": "Transfer Movement", "href": "transfers/index.html"}], "groups": [{"title": "Movement", "items": [{"label": "Latest Signals", "href": "transfers/index.html"}, {"label": "Loans", "href": "transfers/index.html?type=Loan"}, {"label": "Free Agents", "href": "transfers/index.html?type=Free"}, {"label": "Contract Signals", "href": "transfers/index.html?type=Contract"}]}]},
            {"id": "watchlist", "label": "Watchlist", "summary": "Early-signal and thin-data player tracking.", "sidebar": [{"label": "ARES Watchlist", "href": "watchlist/index.html"}], "groups": [{"title": "Watchlist", "items": [{"label": "Youth Breakout", "href": "watchlist/index.html?type=Youth"}, {"label": "Loan Watch", "href": "watchlist/index.html?type=Loan"}, {"label": "Contract Signal", "href": "watchlist/index.html?type=Contract"}]}]},
            {"id": "methodology", "label": "Methodology", "summary": "ARES Score, Market Score, confidence, league adjustment, and image policy.", "sidebar": [{"label": "Methodology", "href": "methodology.html"}], "groups": [{"title": "Methodology", "items": [{"label": "How Scores Work", "href": "methodology.html"}, {"label": "Image Credits", "href": "image-credits.html"}]}]},
        ],
    }


def script_paths(prefix: str, data: str, table_id: str, cols: list[dict[str, Any]], **opts: Any) -> dict[str, Any]:
    return {"dataPath": prefix + data, "tableId": table_id, "bodyId": table_id.replace("-table", "-body"), "columns": with_prefix(cols, prefix), **opts}


def static_safe(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def static_initials(value: Any) -> str:
    parts = [part for part in str(value or "AR").split() if part]
    return ("".join(part[0] for part in parts[:3]) or "AR").upper()


def static_prefixed_href(url: Any, prefix: str) -> str:
    href = str(url or "#")
    if href.startswith("clubs/club-"):
        return site_url(href)
    if prefix and href != "#" and not re.match(r"^(https?:)?//", href) and not href.startswith("../") and not href.startswith("/"):
        return prefix + href
    return href


def static_asset_href(url: Any, prefix: str) -> str:
    href = str(url or "")
    if not href or re.match(r"^(https?:)?//", href) or href.startswith("/") or href.startswith("../"):
        return href
    return prefix + href if prefix and href.startswith("assets/") else href


def static_image_is_safe(row: dict[str, Any]) -> bool:
    status = str(row.get("photo_license_status", "")).lower()
    allowed = {"ares_owned", "provider_supplied", "licensed_commons", "commons_licensed", "cc_by", "cc_by_sa", "public_domain", "approved_provider"}
    return bool(row.get("photo_url")) and status in allowed


def static_mode_badge(value: Any) -> str:
    return ""


def static_chip(value: Any, class_name: str) -> str:
    return f'<span class="{class_name}">{static_safe(value)}</span>'


def static_player_avatar(row: dict[str, Any], prefix: str) -> str:
    label = ", ".join(str(row.get(key, "")) for key in ["player_name", "position", "club"] if row.get(key))
    if static_image_is_safe(row):
        src = static_asset_href(row.get("photo_url", ""), prefix)
        return f'<span class="ares-player-photo"><img src="{static_safe(src)}" alt="{static_safe(label)}" loading="lazy" onerror="this.remove()"></span>'
    initials = row.get("initials") or static_initials(row.get("player_name"))
    return f'<span class="ares-player-avatar-stack" title="{static_safe(label)}"><span class="ares-player-photo" aria-label="{static_safe(label)}">{static_safe(initials)}</span><span class="ares-position-mini">{static_safe(row.get("position") or "FB")}</span><span class="ares-avatar-club">{static_safe(row.get("club") or row.get("region") or "ARES")}</span></span>'


def static_link(label: Any, url: Any, fallback: str, prefix: str) -> str:
    href = static_prefixed_href(url or fallback or "#", prefix)
    return f'<a class="ares-table-link" href="{static_safe(href)}">{static_safe(label)}</a>'


def static_cell(row: dict[str, Any], column: dict[str, Any]) -> str:
    value = row.get(column.get("key"))
    render = column.get("render")
    prefix = column.get("pathPrefix", "")
    if render == "score":
        return static_chip(f"{float(value):.1f}" if isinstance(value, (int, float)) else value, "ares-score-chip")
    if render == "market":
        return static_chip(f"{float(value):.1f}" if isinstance(value, (int, float)) else value, "ares-market-chip")
    if render == "tier":
        return static_chip(value, "ares-tier-chip")
    if render == "trend":
        trend = str(value or "Stable")
        key = trend.lower()
        class_name = "ares-trend-up" if key in {"up", "rising"} else "ares-trend-down" if key in {"down", "falling"} else "ares-trend-flat"
        return static_chip(trend, class_name)
    if render == "confidence":
        confidence = str(value or "Medium")
        key = confidence.lower()
        class_name = "ares-confidence-high" if key == "high" else "ares-confidence-medium" if key == "medium" else "ares-confidence-low"
        return static_chip(confidence, class_name)
    if render == "mode":
        return static_mode_badge(value)
    if render == "playerImage":
        return static_player_avatar(row, prefix)
    if render == "playerLink":
        avatar = "" if column.get("showAvatar") is False else static_player_avatar(row, prefix)
        href = static_prefixed_href(row.get("player_url") or row.get("url") or column.get("fallbackUrl") or "players/profile.html", prefix)
        return f'<a class="ares-player-identity" href="{static_safe(href)}">{avatar}<span>{static_safe(value)}</span></a>'
    if render == "clubLink":
        return static_link(value, row.get("club_url"), column.get("fallbackUrl", "clubs/profile.html"), prefix)
    if render == "leagueLink":
        return static_link(value, row.get("league_url"), column.get("fallbackUrl", "leagues/league-template.html"), prefix)
    if render == "link":
        return static_link(column.get("label") or value or "Open", row.get(column.get("urlKey", "url")), column.get("fallbackUrl", "#"), prefix)
    if column.get("key") == "club" and row.get("club_url"):
        return static_link(value, row.get("club_url"), "#", prefix)
    if column.get("key") == "club_name" and row.get("club_url"):
        return static_link(value, row.get("club_url"), "#", prefix)
    if column.get("key") == "from_club" and row.get("from_club_url"):
        return static_link(value, row.get("from_club_url"), "#", prefix)
    if column.get("key") == "to_club" and row.get("to_club_url"):
        return static_link(value, row.get("to_club_url"), "#", prefix)
    return static_safe(value)


def static_prepare_rows(rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    prepared = list(rows)
    if config.get("filterKey") and config.get("filterValues"):
        values = set(config["filterValues"])
        prepared = [row for row in prepared if row.get(config["filterKey"]) in values]
    elif config.get("filterKey") and config.get("filterValue") is not None:
        prepared = [row for row in prepared if row.get(config["filterKey"]) == config["filterValue"]]
    if config.get("maxAge") is not None:
        prepared = [row for row in prepared if float(row.get("age", 999) or 999) <= float(config["maxAge"])]
    if config.get("minAge") is not None:
        prepared = [row for row in prepared if float(row.get("age", 0) or 0) >= float(config["minAge"])]
    if config.get("sortKey"):
        key = config["sortKey"]
        reverse = config.get("sortDirection") != "asc"
        def sort_value(row: dict[str, Any]) -> tuple[int, Any]:
            value = row.get(key, "")
            try:
                return (0, float(value))
            except (TypeError, ValueError):
                return (1, str(value).lower())
        prepared.sort(key=sort_value, reverse=reverse)
    if config.get("limit"):
        prepared = prepared[: int(config["limit"])]
    return prepared


def static_render_rows(rows: list[dict[str, Any]], columns: list[dict[str, Any]]) -> str:
    if not rows:
        return f'<tr><td colspan="{max(1, len(columns))}">No matching rows for this filter set. Clear filters to view the full board.</td></tr>'
    output = []
    for row in rows:
        cells = []
        for column in columns:
            label = static_safe(column.get("label") or column.get("key") or "")
            cells.append(f'<td data-label="{label}">{static_cell(row, column)}</td>')
        output.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(output)


def extract_table_configs(text: str) -> list[dict[str, Any]]:
    configs = []
    for match in re.finditer(r"AresSoccer\.initTable\((\{.*?\})\);", text, re.S):
        try:
            configs.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    return configs


def prerender_generated_tables() -> None:
    for html_path in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in html_path.relative_to(ROOT).parts):
            continue
        text = html_path.read_text(encoding="utf-8")
        configs = extract_table_configs(text)
        if not configs:
            continue
        updated = text
        for config in configs:
            data_path = (html_path.parent / config["dataPath"]).resolve()
            if not data_path.exists():
                continue
            rows = read_json(str(data_path.relative_to(ROOT)))
            if isinstance(rows, dict):
                rows = rows.get("rows") or rows.get("players") or []
            if not isinstance(rows, list):
                continue
            prepared = static_prepare_rows(rows, config)
            body_html = static_render_rows(prepared, config.get("columns", []))
            body_id = re.escape(config["bodyId"])
            pattern = re.compile(r'(<tbody id="' + body_id + r'">)(.*?)(</tbody>)', re.S)
            updated = pattern.sub(lambda match: match.group(1) + body_html + match.group(3), updated, count=1)
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")


def strip_public_beta_badges_from_html() -> None:
    for html_path in ROOT.rglob("*.html"):
        if any(part.startswith(".") for part in html_path.relative_to(ROOT).parts):
            continue
        text = html_path.read_text(encoding="utf-8")
        updated = text
        updated = re.sub(r'<span class="ares-beta-badge">Seeded Beta</span>', "", updated)
        updated = re.sub(r'<th>Mode</th>', "", updated)
        updated = re.sub(r'<td data-label="Mode">.*?</td>', "", updated, flags=re.S)
        updated = re.sub(r'<div class="ares-status-item"><strong>Data mode</strong><span></span></div>', "", updated)
        updated = re.sub(r'<div class="ares-status-item"><strong>Data mode</strong><span>Seeded Beta</span></div>', "", updated)
        updated = updated.replace("Seeded beta rows show the ARES market structure while approved live football data feeds are being connected.", "ARES rows show the market structure while approved live football data feeds are being connected.")
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")


def build_pages(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> None:
    continent_counts = {c: len([p for p in players if p["continent"] == c]) for c in CONTINENTS}
    club_counts = {c: len([x for x in clubs if x["continent"] == c]) for c in CONTINENTS}
    league_counts = {c: len([x for x in leagues if x["continent"] == c]) for c in CONTINENTS}
    top_by_continent = {c: max([p for p in players if p["continent"] == c], key=lambda item: item["market_score"]) for c in CONTINENTS}

    continent_cards = "".join(
        f'<a class="ares-board-feature" href="continents/{slug(c)}/"><strong>{c}</strong><span>{continent_counts[c]} players | {club_counts[c]} clubs | {league_counts[c]} leagues</span><span>Top asset: {top_by_continent[c]["player_name"]}</span></a>'
        for c in CONTINENTS
    )
    homepage_tables = [
        ("home-ares-table", "Top ARES Players", ["Image", "Player", "Club", "Continent", "ARES", "Tier", "Mode"]),
        ("home-market-table", "Top Market Assets", ["Image", "Player", "Club", "Continent", "Market", "Tier", "Mode"]),
        ("home-young-table", "Young Breakout Assets", ["Player", "Age", "Club", "Continent", "Market", "Trend", "Mode"]),
        ("home-changes-table", "Latest Market Value Changes", ["Player", "Club", "Continent", "Change", "Reason", "Mode"]),
        ("home-transfer-table", "Latest Transfer Signals", ["Date", "Player", "Continent", "Type", "Market Impact", "Mode"]),
    ] + [(f"home-{slug(c)}-table", f"{c} Market Board", ["Player", "Club", "League", "Market", "Confidence", "Mode"]) for c in CONTINENTS] + [
        ("home-clubs-table", "Club Portfolio Board", ["Club", "League", "Continent", "Squad Market", "Top Asset", "Mode"]),
        ("home-leagues-table", "League Strength Board", ["League", "Continent", "Strength", "Depth", "Top Player", "Mode"]),
    ]
    board_html = "".join(
        terminal_table_card(title, "Live-looking seeded rows with player, club, score, movement, and confidence context.", tid, headers, href_for_home_board(tid))
        for tid, title, headers in homepage_tables
    )
    market_cols = [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "continent", "label": "Continent"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "market_tier", "label": "Tier", "render": "tier"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    home_scripts = [
        script_paths("", "data/public_players.json", "home-ares-table", [{"key": "player_name", "label": "Image", "render": "playerImage"}, {"key": "player_name", "label": "Player", "render": "playerLink", "showAvatar": False}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "continent", "label": "Continent"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "ares_tier", "label": "Tier", "render": "tier"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="ares_score", sortDirection="desc", limit=6),
        script_paths("", "data/public_players.json", "home-market-table", [{"key": "player_name", "label": "Image", "render": "playerImage"}, *market_cols], sortKey="market_score", sortDirection="desc", limit=6),
        script_paths("", "data/public_players.json", "home-young-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "continent", "label": "Continent"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], maxAge=23, sortKey="market_score", sortDirection="desc", limit=6),
        script_paths("", "data/public_market_changes.json", "home-changes-table", [{"key": "player_name", "label": "Player"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "continent", "label": "Continent"}, {"key": "change", "label": "Change"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=6),
        script_paths("", "data/public_transfers.json", "home-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "continent", "label": "Continent"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Market Impact"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=6),
    ]
    for c in CONTINENTS:
        home_scripts.append(script_paths("", "data/public_players.json", f"home-{slug(c)}-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=c, sortKey="market_score", sortDirection="desc", limit=5))
    home_scripts.extend([
        script_paths("", "data/public_clubs.json", "home-clubs-table", [{"key": "club_name", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League"}, {"key": "continent", "label": "Continent"}, {"key": "squad_market_score", "label": "Squad Market", "render": "market"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="squad_market_score", sortDirection="desc", limit=8),
        script_paths("", "data/public_leagues.json", "home-leagues-table", [{"key": "league_name", "label": "League", "render": "leagueLink"}, {"key": "continent", "label": "Continent"}, {"key": "league_strength", "label": "Strength", "render": "score"}, {"key": "market_depth", "label": "Depth", "render": "market"}, {"key": "top_player", "label": "Top Player"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="league_strength", sortDirection="desc", limit=8),
    ])
    top_ares = max(players, key=lambda item: item["ares_score"])
    top_market = max(players, key=lambda item: item["market_score"])
    top_young = max([p for p in players if int(p.get("age", 99)) <= 23], key=lambda item: item["market_score"])
    biggest_mover = max(build_market_changes(players), key=lambda item: abs(float(item["change"])))
    hero = f"""<section class="ares-terminal-hero"><div><h2 class="h3">Global football's player asset terminal.</h2><p>ARES separates on-field quality from market value across players, clubs, leagues, continents, and transfer movement.</p><div class="hero-actions"><a href="rankings/ares.html">View ARES Rankings</a><a href="rankings/market.html">View Market Rankings</a><a href="continents/">Explore Continent Boards</a></div><div class="search-panel"><div class="ares-search"><input id="soccer-search" type="search" aria-label="Search players, clubs, leagues, positions, countries, regions, or continents"></div><div id="soccer-search-results" class="search-results"></div></div></div><div class="ares-terminal-panel"><h2 class="h4">Terminal Status</h2><p>Seeded beta data. Live feeds are not connected. Player photos render only when a rights record exists; otherwise ARES uses branded fallback avatars.</p><strong>{len(players)} players | {len(clubs)} clubs | {len(leagues)} leagues</strong></div></section>"""
    top_kpis = kpi_cards([
        ("Top ARES Player", f"{top_ares['ares_score']:.1f}", f"{top_ares['player_name']} | {top_ares['club']}"),
        ("Top Market Asset", f"{top_market['market_score']:.1f}", f"{top_market['player_name']} | {top_market['market_tier']}"),
        ("Top Young Asset", f"{top_young['market_score']:.1f}", f"{top_young['player_name']} | Age {top_young['age']}"),
        ("Biggest Mover", biggest_mover["change"], f"{biggest_mover['player_name']} | {biggest_mover['trend']}"),
    ])
    trust = f"""<section class="ares-section ares-card"><div class="ares-status-terminal"><div class="ares-status-item"><strong>Players tracked</strong><span>{len(players)}</span></div><div class="ares-status-item"><strong>Clubs tracked</strong><span>{len(clubs)}</span></div><div class="ares-status-item"><strong>Leagues tracked</strong><span>{len(leagues)}</span></div><div class="ares-status-item"><strong>Continents covered</strong><span>6</span></div><div class="ares-status-item"><strong>Data status</strong><span>Seeded beta data</span></div><div class="ares-status-item"><strong>Last updated</strong><span>{TODAY}</span></div></div></section>"""
    graph_strip = '<section class="ares-section ares-terminal-grid">' + chart_card("Market Score vs ARES Score", "Scatter view for elite assets, hidden value, development, and risk.", "scatter") + chart_card("Global Market Momentum", "Regional momentum across Europe, Asia, MLS, Liga MX, Africa, South America, and Oceania.", "line") + "</section>"
    body = hero + top_kpis + trust + graph_strip + f'<section class="ares-section"><div class="ares-section-title"><div><h2 class="h4">Global Market Map</h2><p>World to continent to league to club to player.</p></div></div><div class="continent-grid">{continent_cards}</div></section><section class="ares-section table-grid">{board_html}</section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">ARES Score</h2><p>On-field football quality across role, usage, efficiency, durability, opponent context, and trend.</p></div><div class="ares-card"><h2 class="h4">Market Score</h2><p>Football asset value across ARES quality, age curve, position scarcity, league strength, transfer signal, and confidence.</p></div></section><section class="ares-section table-grid"><div class="ares-card premium-lock"><h2 class="h4">Full ARES Components</h2><p>Position-specific component grades are visible but locked for premium.</p></div><div class="ares-card premium-lock"><h2 class="h4">Market Breakdown</h2><p>Age curve, role security, transfer fit, comparable players, and risk scoring.</p></div></section>'
    home_script = 'AresSoccer.initSearch("soccer-search","soccer-search-results","data/public_search.json");' + script_init(home_scripts)
    write_text("index.html", page("", "ARES Football Market | Global Player Value, ARES Scores & Transfer Intelligence", "Track global football players, clubs, leagues, ARES Scores, Market Scores, continent boards, transfer movement, and public beta football asset signals.", "", "ARES Football Market", "World to continent to league to club to player football market intelligence.", body, home_script))

    build_board_pages()


def filter_bar(prefix: str) -> str:
    links = "".join(f'<a class="ares-filter-chip" href="?continent={slug(c).replace("-", "%20").title()}"><strong>{c}</strong><span>{CONFED_BY_CONTINENT[c]}</span></a>' for c in CONTINENTS)
    return f'<section class="ares-section ares-card"><div class="ares-filter-bar">{links}</div><input id="board-search" class="ares-search mb-3" type="search" aria-label="Search player, club, league, country, continent, region, or confidence"></section>'


def build_board_pages() -> None:
    # Players
    players_table = terminal_table_card("Search Results", "Players by club, league, position, continent, ARES Score, Market Score, and signal.", "players-table", ["Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Minutes / Role", "ARES", "Market", "Tier", "Trend", "Confidence", "Mode"])
    body = kpi_cards([("Searchable Players", "800", "Seeded player rows"), ("Top Filters", "9", "Region, club, league, role, score"), ("Profile Links", "Active", "Player-specific routes"), ("Club Links", "Roster", "Every club opens a squad page")]) + filter_bar("../") + terminal_pair(players_table, "Result Distribution", "ARES Score histogram and age vs Market Score view for the current result set.", "scatter")
    scripts = script_init([script_paths("../", "data/public_players.json", "players-table", PLAYER_COLS, searchId="board-search", sortKey="market_score", sortDirection="desc")])
    write_text("players/index.html", page("../", "Football Player Search | ARES Scores, Market Scores, Clubs, Leagues & Continents", "Search public beta football players by continent, region, country, league, club, position, age, ARES Score, Market Score, trend, and confidence.", "players/", "Football Player Search", "Search players by continent, region, country, league, club, role, ARES quality, Market Score, trend, and data confidence.", body, scripts))

    ares_cols = [{"key": "rank", "label": "Rank"}, *PLAYER_COLS[:9], {"key": "ares_score", "label": "ARES Score", "render": "score"}, {"key": "ares_tier", "label": "Tier", "render": "tier"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    ares_table = terminal_table_card("Rankings Table", "Performance quality by position, role, minutes, trend, and confidence.", "ares-table", ["Rank", "Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Minutes / Role", "ARES Score", "Tier", "Trend", "Confidence", "Mode"])
    body = kpi_cards([("Highest ARES Score", "Live", "Sorted from player rows"), ("Top U23 Player", "U23", "Market-age crossover"), ("Goal Threat", "Tracked", "Position component preview"), ("Confidence", "High/Med/Low", "Coverage label")]) + filter_bar("../") + '<section class="ares-section ares-card"><p>ARES Score measures on-field football quality. It is not a transfer fee and not a market price.</p></section>' + terminal_pair(ares_table, "Top 20 ARES Scores", "Horizontal score view for elite performers and role-adjusted leaders.", "bars")
    scripts = script_init([script_paths("../", "data/public_players.json", "ares-table", ares_cols, searchId="board-search", sortKey="ares_score", sortDirection="desc")])
    write_text("rankings/ares.html", page("../", "ARES Player Rankings | Football Quality Scores by Position, League & Continent", "Rank football players by ARES Score, on-field quality, role, usage, durability, trend, position, league, continent, and data confidence.", "rankings/ares.html", "ARES Player Rankings", "Rank players by on-field football quality, role, efficiency, usage, durability, opponent context, and trend.", body, scripts))

    market_cols = [{"key": "rank", "label": "Rank"}, *PLAYER_COLS[:8], {"key": "ares_score", "label": "ARES Score", "render": "score"}, {"key": "market_score", "label": "Market Score", "render": "market"}, {"key": "market_tier", "label": "Market Tier", "render": "tier"}, {"key": "transfer_value_signal", "label": "Transfer Value Signal"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    tiers = "".join(f"<li>{tier}</li>" for tier in ["Franchise Asset", "Blue-Chip Asset", "Rising Asset", "Core Starter", "Rotation Value", "Watchlist", "Risk Asset"])
    market_table = terminal_table_card("Market Rankings Table", "Asset score by ARES quality, age curve, scarcity, contract window, and risk.", "market-table", ["Rank", "Image", "Player", "Age", "Position", "Club", "League", "Country", "ARES", "Market", "Tier", "Transfer Signal", "Confidence", "Mode"])
    body = kpi_cards([("Top Market Score", "Live", "Sorted from player rows"), ("Top Young Asset", "U23", "Age curve signal"), ("Biggest Riser", "Trend", "Movement value"), ("Value Gap", "ARES vs Market", "Asset context")]) + filter_bar("../") + f'<section class="ares-section ares-card"><p>Market Score estimates football asset value using age curve, role security, position scarcity, league strength, transfer signal, durability, and data confidence. It is not a transfer fee.</p><ul>{tiers}</ul></section>' + terminal_pair(market_table, "Market Score vs ARES Score", "Elite assets, hidden value, development, and risk quadrants.", "scatter")
    scripts = script_init([script_paths("../", "data/public_players.json", "market-table", market_cols, searchId="board-search", sortKey="market_score", sortDirection="desc")])
    write_text("rankings/market.html", page("../", "Football Market Rankings | Player Asset Value, Age Curve & Transfer Signal", "Rank football players by Market Score, age curve, position scarcity, role security, league strength, transfer signal, durability, and confidence.", "rankings/market.html", "Football Market Rankings", "Rank players by football asset value, not transfer fee.", body, scripts))

    club_cols = [{"key": "club_name", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "squad_market_score", "label": "Squad Market", "render": "market"}, {"key": "avg_ares_score", "label": "Avg ARES", "render": "score"}, {"key": "average_age", "label": "Avg Age"}, {"key": "u23_asset_count", "label": "U23 Assets"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "transfer_risk", "label": "Transfer Risk"}, {"key": "need_area", "label": "Need Area"}, {"key": "market_trend", "label": "Trend", "render": "trend"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    club_table = terminal_table_card("Club Portfolio Table", "Each club is treated as a squad portfolio with age, U23, risk, and need-area context.", "clubs-table", ["Club", "League", "Country", "Continent", "Squad Market", "Avg ARES", "Avg Age", "U23", "Top Asset", "Risk", "Need", "Trend", "Confidence", "Mode"])
    body = kpi_cards([("Club Portfolios", "248", "Roster pages generated"), ("Squad Market", "Score", "Portfolio asset view"), ("U23 Assets", "Tracked", "Youth value layer"), ("Contract Risk", "Signal", "Risk board input")]) + filter_bar("../") + terminal_pair(club_table, "Market Score vs Age", "Squad asset shape by age, role security, and market score.", "scatter")
    scripts = script_init([script_paths("../", "data/public_clubs.json", "clubs-table", club_cols, searchId="board-search", sortKey="squad_market_score", sortDirection="desc")])
    write_text("clubs/index.html", page("../", "Club Portfolio Boards | Squad Value, ARES Strength, U23 Assets & Transfer Risk", "Compare football club portfolios by squad market score, average ARES score, U23 assets, transfer risk, league, country, and continent.", "clubs/", "Club Portfolio Boards", "Compare clubs as portfolios: squad value, ARES strength, U23 assets, transfer risk, need areas, and confidence.", body, scripts))

    league_cols = [{"key": "league_name", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "region", "label": "Region"}, {"key": "confederation", "label": "Confederation"}, {"key": "league_strength", "label": "League Strength", "render": "score"}, {"key": "market_depth", "label": "Market Depth", "render": "market"}, {"key": "u23_pipeline", "label": "U23 Pipeline"}, {"key": "export_signal", "label": "Export Signal"}, {"key": "top_player", "label": "Top Player"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    league_table = terminal_table_card("League Rankings Table", "League strength, market depth, U23 pipeline, export signal, and confidence.", "leagues-table", ["League", "Country", "Continent", "Region", "Confederation", "Strength", "Depth", "U23 Pipeline", "Export", "Top Player", "Confidence", "Mode"])
    body = kpi_cards([("Leagues", "64", "Global coverage"), ("Market Depth", "Tracked", "Squad and player volume"), ("U23 Pipeline", "Signal", "Breakout asset layer"), ("Export Strength", "Flow", "Transfer movement context")]) + filter_bar("../") + terminal_pair(league_table, "League Strength Ranking", "Bar view comparing quality, market depth, and U23 supply.", "bars")
    scripts = script_init([script_paths("../", "data/public_leagues.json", "leagues-table", league_cols, searchId="board-search", sortKey="league_strength", sortDirection="desc")])
    write_text("leagues/index.html", page("../", "League Strength Boards | Football Market Depth, ARES Scores & Player Value", "Compare football leagues by league strength, market depth, U23 pipeline, export signal, continent, region, confidence, and public beta status.", "leagues/", "League Strength Boards", "Compare football leagues by strength, market depth, U23 pipeline, export signal, and data confidence.", body, scripts))

    transfer_cols = [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Image", "render": "playerImage"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "position", "label": "Position"}, {"key": "from_club", "label": "From"}, {"key": "to_club", "label": "To"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "transfer_type", "label": "Movement Type"}, {"key": "ares_impact", "label": "ARES Impact"}, {"key": "market_impact", "label": "Market Impact"}, {"key": "confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    transfer_table = terminal_table_card("Transfer Signal Table", "Market movement tape for transfers, loans, free agents, academy movement, and contracts.", "transfers-table", ["Date", "Image", "Player", "Age", "Position", "From", "To", "Country", "Continent", "Type", "ARES Impact", "Market Impact", "Confidence", "Mode"])
    body = kpi_cards([("Highest Signal", "Buy Watch", "Movement tape"), ("Biggest Riser", "Trend", "Market impact"), ("Contract Watch", "Window", "Expiry signal"), ("Best Fit", "Club", "Future premium layer")]) + filter_bar("../") + terminal_pair(transfer_table, "Transfer Signal Distribution", "Buy, hold, watch, risk, and confidence mix.", "bars")
    scripts = script_init([script_paths("../", "data/public_transfers.json", "transfers-table", transfer_cols, searchId="board-search", limit=36)])
    write_text("transfers/index.html", page("../", "Transfer Movement Board | Football Transfers, Loans, Free Agents & Market Impact", "Track public beta transfer movement signals across loans, free agents, academy movement, contract signals, ARES impact, and market impact.", "transfers/", "Transfer Movement Board", "A market movement tape for loans, free agents, academy movement, contract signals, ARES impact, and Market impact.", body, scripts))

    watch_cols = [{"key": "player_name", "label": "Image", "render": "playerImage"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "position", "label": "Position"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "watch_reason", "label": "Watch Reason"}, {"key": "ares_signal", "label": "ARES Signal"}, {"key": "market_signal", "label": "Market Signal"}, {"key": "risk", "label": "Risk"}, {"key": "confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    watch_table = terminal_table_card("Saved Players Table", "Youth breakouts, loan watches, role expansion, contract signals, injury returns, and thin-data assets.", "watchlist-table", ["Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Reason", "ARES Signal", "Market Signal", "Risk", "Confidence", "Mode"])
    body = kpi_cards([("Players Watched", "30+", "Seeded watch rows"), ("Rising Assets", "Tracked", "Market signal"), ("Risk Alerts", "Active", "Role, age, injury, contract"), ("Premium Preview", "Locked", "Alerts and comparison tray")]) + filter_bar("../") + terminal_pair(watch_table, "Watchlist Score Movement", "Aggregate movement for saved players and risk alerts.", "line")
    scripts = script_init([script_paths("../", "data/public_watchlist.json", "watchlist-table", watch_cols, searchId="board-search", limit=36)])
    write_text("watchlist/index.html", page("../", "ARES Watchlist | U23 Players, Loan Signals, Breakouts & Thin-Data Assets", "Follow ARES watchlist assets across youth breakouts, loan watches, role expansion, contract signals, injury returns, and thin-data scouting flags.", "watchlist/", "ARES Watchlist", "Track youth, loan, free agent, role-expansion, contract-signal, and thin-data players before official ranking confidence improves.", body, scripts))


def build_continent_pages() -> None:
    index_cards = "".join(f'<a class="ares-board-feature" href="{slug(c)}/"><strong>{c}</strong><span>{CONFED_BY_CONTINENT[c]} market board</span></a>' for c in CONTINENTS)
    write_text("continents/index.html", page("../", "Football Market Boards by Continent | Europe, Asia, Africa, Americas & Oceania", "Explore ARES football market boards by continent, including player value, ARES Scores, club strength, league depth, and transfer signals.", "continents/", "Football Market Boards by Continent", "Move from world to continent to region to country to league to club to player.", f'<section class="ares-section continent-grid">{index_cards}</section>', ""))
    for continent in CONTINENTS:
        prefix = "../../"
        body = f'<section class="ares-terminal-hero"><div><h2 class="h3">{continent} market terminal.</h2><p>Player assets, club portfolios, league strength, U23 breakouts, and transfer movement for {continent}.</p></div><div class="ares-terminal-panel"><strong>{CONFED_BY_CONTINENT[continent]}</strong><span>Seeded beta data. Live feeds are not connected.</span></div></section>'
        body += kpi_cards([("Continent", continent, CONFED_BY_CONTINENT[continent]), ("Top Assets", "10", "Market board"), ("League Snapshot", "6+", "Strength and depth"), ("Transfer Signals", "6+", "Movement tape")])
        body += '<section class="ares-section ares-terminal-grid">' + chart_card(f"{continent} League Strength", "Compare league quality, U23 depth, and export signal.", "bars") + chart_card(f"{continent} Talent Heatmap", "Regional concentration by player value, ARES Score, and confidence.", "scatter") + "</section>"
        body += '<section class="ares-section table-grid">'
        for tid, title, headers in [
            ("continent-market-table", "Top Market Assets", ["Player", "Club", "League", "Market", "Tier", "Confidence", "Mode"]),
            ("continent-ares-table", "Top ARES Players", ["Player", "Club", "League", "ARES", "Tier", "Confidence", "Mode"]),
            ("continent-u23-table", "U23 Breakout Assets", ["Player", "Age", "Club", "Market", "Trend", "Mode"]),
            ("continent-league-table", "League Strength Snapshot", ["League", "Country", "Strength", "Depth", "Top Player", "Mode"]),
            ("continent-club-table", "Club Portfolio Snapshot", ["Club", "League", "Squad Market", "Top Asset", "Risk", "Mode"]),
            ("continent-transfer-table", "Transfer Movement Signals", ["Date", "Player", "Type", "Market Impact", "Confidence", "Mode"]),
        ]:
            body += terminal_table_card(title, f"{continent} board rows with scores, club context, confidence, and movement signal.", tid, headers)
        body += "</section>"
        scripts = script_init([
            script_paths(prefix, "data/public_players.json", "continent-market-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "market_tier", "label": "Tier", "render": "tier"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, sortKey="market_score", sortDirection="desc", limit=10),
            script_paths(prefix, "data/public_players.json", "continent-ares-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "ares_tier", "label": "Tier", "render": "tier"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, sortKey="ares_score", sortDirection="desc", limit=10),
            script_paths(prefix, "data/public_players.json", "continent-u23-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, maxAge=23, sortKey="market_score", sortDirection="desc", limit=10),
            script_paths(prefix, "data/public_leagues.json", "continent-league-table", [{"key": "league_name", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "league_strength", "label": "Strength", "render": "score"}, {"key": "market_depth", "label": "Depth", "render": "market"}, {"key": "top_player", "label": "Top Player"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, sortKey="league_strength", sortDirection="desc", limit=10),
            script_paths(prefix, "data/public_clubs.json", "continent-club-table", [{"key": "club_name", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League"}, {"key": "squad_market_score", "label": "Squad Market", "render": "market"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "transfer_risk", "label": "Risk"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, sortKey="squad_market_score", sortDirection="desc", limit=10),
            script_paths(prefix, "data/public_transfers.json", "continent-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Market Impact"}, {"key": "confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="continent", filterValue=continent, limit=8),
        ])
        title = f"{continent} Football Market Board | ARES Scores, Club Value & Transfer Signals"
        if continent == "Asia":
            title = "Asia Football Market Board | J1 League, K League, Saudi Pro League & AFC Watch"
        if continent == "North America":
            title = "North America Football Market Board | MLS, Liga MX, USL, CPL & CONCACAF"
        meta = f"Explore {continent} football market intelligence across player value, league strength, club portfolios, ARES Scores, U23 assets, and transfer signals."
        write_text(f"continents/{slug(continent)}/index.html", page(prefix, title, meta, f"continents/{slug(continent)}/", f"{continent} Football Market Board", f"Track {continent} player assets, club portfolios, league strength, and transfer movement through ARES Score and Market Score.", body, scripts))


def build_legacy_region_pages() -> None:
    def legacy(path: str, canonical: str, title: str, h1: str, intro: str, player_filter: dict[str, Any], league_filter: dict[str, Any]) -> None:
        prefix = "../" if len(Path(path).parent.parts) == 1 else "../../"
        body = kpi_cards([("Top Player", "Live", "Sorted by market score"), ("Top U23 Asset", "Tracked", "Age curve signal"), ("Strongest League", "Market", "Strength and depth"), ("Export Watch", "Active", "Movement context")])
        body += '<section class="ares-section ares-terminal-grid">' + chart_card(f"{h1} Strength", "ARES, Market, U23, and depth indicators.", "bars") + chart_card("Market Score vs Age", "Young assets and veteran stars by market signal.", "scatter") + "</section>"
        body += '<section class="ares-section table-grid">' + f'<div class="ares-card"><h2 class="h4">Player Board</h2>{table("regional-player-table", ["Player", "Club", "League", "Market", "ARES", "Mode"])}</div><div class="ares-card"><h2 class="h4">League Board</h2>{table("regional-league-table", ["League", "Country", "Strength", "Depth", "Top Player", "Mode"])}</div></section>'
        player_cfg = script_paths(prefix, "data/public_players.json", "regional-player-table", [{"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="market_score", sortDirection="desc", limit=12, **player_filter)
        league_cfg = script_paths(prefix, "data/public_leagues.json", "regional-league-table", [{"key": "league_name", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "league_strength", "label": "Strength", "render": "score"}, {"key": "market_depth", "label": "Depth", "render": "market"}, {"key": "top_player", "label": "Top Player"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="market_depth", sortDirection="desc", limit=12, **league_filter)
        write_text(path, page(prefix, title, intro, canonical, h1, intro, body, script_init([player_cfg, league_cfg])))
    legacy("leagues/asia.html", "continents/asia/", "Asia Football Market Board | J1 League, K League, Saudi Pro League & AFC Watch", "Asia Football Market Board", "Track Asian football market assets across Japan, Korea, Saudi Arabia, China, India, Australia, Southeast Asia, and AFC competitions.", {"filterKey": "continent", "filterValues": ["Asia", "Oceania"]}, {"filterKey": "continent", "filterValues": ["Asia", "Oceania"]})
    legacy("leagues/north-america.html", "continents/north-america/", "North America Football Market Board | MLS, Liga MX, USL, CPL & CONCACAF", "North America Football Market Board", "Explore North American football market intelligence across MLS, Liga MX, USL, Canadian Premier League, CONCACAF, and U23 exports.", {"filterKey": "continent", "filterValue": "North America"}, {"filterKey": "continent", "filterValue": "North America"})
    legacy("leagues/mls.html", "leagues/mls/", "MLS Market Board | Player Value, ARES Scores, U23 Assets & Transfers", "MLS Market Board", "Track MLS players, U22 assets, homegrowns, Designated Player context, MLS Next Pro watch rows, and Liga MX movement.", {"filterKey": "league", "filterValues": ["Major League Soccer", "MLS Next Pro"]}, {"filterKey": "league_name", "filterValues": ["Major League Soccer", "MLS Next Pro"]})
    legacy("leagues/mls/index.html", "leagues/mls/", "MLS Market Board | Player Value, ARES Scores, U23 Assets & Transfers", "MLS Market Board", "Track MLS players, U22 assets, homegrowns, Designated Player context, MLS Next Pro watch rows, and Liga MX movement.", {"filterKey": "league", "filterValues": ["Major League Soccer", "MLS Next Pro"]}, {"filterKey": "league_name", "filterValues": ["Major League Soccer", "MLS Next Pro"]})


def build_templates() -> None:
    profile_body = """<section class="ares-section ares-card"><div class="ares-profile-card"><div id="player-photo" class="ares-profile-photo">AR</div><h2 id="player-name">Player Profile</h2><p><span id="position"></span> | <span id="club"></span> | <span id="league"></span> | <span id="country"></span></p><a id="player-roster-link" class="ares-roster-cta" href="#" hidden>View club roster</a><div class="ares-status-terminal"><div class="ares-status-item"><strong>Age</strong><span id="age"></span></div><div class="ares-status-item"><strong>Contract End</strong><span id="contract-end"></span></div><div class="ares-status-item"><strong>Role</strong><span id="role"></span></div><div class="ares-status-item"><strong>Confidence</strong><span id="confidence"></span></div><div class="ares-status-item"><strong>Last Updated</strong><span id="last-updated"></span></div></div></div></section><section class="ares-section ares-card"><div class="ares-player-tabs"><span>Profile</span><span>Stats</span><span>Market Value</span><span>Transfers</span><span>Rumours</span><span>National Team</span><span>Career</span></div></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">ARES Score</h2><p id="ares-score"></p></div><div class="ares-card"><h2 class="h4">Market Score</h2><p id="market-score"></p></div><div class="ares-card"><h2 class="h4">Market Tier</h2><p id="market-tier"></p></div><div class="ares-card"><h2 class="h4">Age Curve</h2><p id="age-curve"></p></div><div class="ares-card"><h2 class="h4">Trend</h2><p id="trend"></p></div><div class="ares-card"><h2 class="h4">Reason</h2><p id="reason"></p></div></section><section class="ares-section ares-terminal-grid">""" + chart_card("Position Usage", "Role split by position, minutes, and usage context.", "bars") + chart_card("ARES Form Trend", "Last-window trend view for performance quality.", "line") + """</section><section class="ares-section ares-card"><h2 class="h4">Season Stats</h2>""" + table("player-season-table", ["League", "Club", "Minutes / Role", "ARES", "Market", "Confidence"]) + """</section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Minutes / Role</h2>""" + table("player-role-table", ["Position", "Position Usage", "Role Security", "Durability", "Trend"]) + """</div><div class="ares-card"><h2 class="h4">Market Notes</h2>""" + table("player-market-table", ["Tier", "Transfer Signal", "Contract End", "Market Note"]) + """</div></section><section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Tabs</h2><p>ARES Components | Market Breakdown | Age Curve | Transfer Value Signal | Team Fit | Risk Score | Movement History</p></section><section class="ares-section ares-card"><h2 class="h4">Image Source</h2><p>Source: <span id="photo-source"></span>. License: <span id="photo-license"></span>. Credit: <span id="photo-credit"></span>.</p></section>"""
    profile_body = profile_body.replace('<div class="ares-player-tabs"><span>Profile</span><span>Stats</span><span>Market Value</span><span>Transfers</span><span>Rumours</span><span>National Team</span><span>Career</span></div>', '<div class="ares-player-tabs"><a data-profile-view="overview" href="?view=overview">Overview</a><a data-profile-view="stats" href="?view=stats">Stats</a><a data-profile-view="market" href="?view=market">Market Value</a><a data-profile-view="transfers" href="?view=transfers">Transfers</a><a data-profile-view="rumours" href="?view=rumours">Rumours</a><a data-profile-view="national-team" href="?view=national-team">National Team</a><a data-profile-view="news" href="?view=news">News</a><a data-profile-view="achievements" href="?view=achievements">Achievements</a><a data-profile-view="career" href="?view=career">Career</a></div>')
    profile_kpis = '<section class="ares-section ares-kpi-grid"><div class="ares-kpi-card"><span class="label">ARES Score</span><span id="kpi-ares-score" class="value"></span><span class="meta">Performance quality</span></div><div class="ares-kpi-card"><span class="label">Market Score</span><span id="kpi-market-score" class="value"></span><span class="meta">Football asset value</span></div><div class="ares-kpi-card"><span class="label">Transfer Signal</span><span id="kpi-transfer-signal" class="value"></span><span class="meta">Movement context</span></div><div class="ares-kpi-card"><span class="label">Data Confidence</span><span id="kpi-confidence" class="value"></span><span class="meta">Coverage label</span></div></section>'
    profile_body = profile_kpis + profile_body
    profile_body += """<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Continent</h2><p id="continent"></p></div><div class="ares-card"><h2 class="h4">Minutes / Role</h2><p id="minutes-role"></p></div><div class="ares-card"><h2 class="h4">Position Usage</h2><p id="position-usage"></p></div><div class="ares-card"><h2 class="h4">Transfer Value Signal</h2><p id="transfer-value-signal"></p></div><div class="ares-card"><h2 class="h4">Role Security</h2><p id="role-security"></p></div><div class="ares-card"><h2 class="h4">Durability</h2><p id="durability"></p></div></section><section class="ares-section ares-terminal-grid">""" + chart_card("Component Grades", "Finishing, shot quality, link-up play, pressing impact, and role strength.", "bars") + chart_card("Comparable Players", "Score and market similarity using the seeded player set.", "scatter") + """</section><section id="player-view-note" class="ares-section ares-card"><h2 class="h4">Overview</h2><p>Use the profile tabs to switch between stats, market value, transfers, rumours, national team, news, achievements, and career views for this player.</p></section><section id="profile-message" class="ares-section ares-card" hidden></section>"""
    profile_mapping = {"player-name":"player_name","position":"position","club":"club","league":"league","country":"country","age":"age","contract-end":"contract_end","role":"role","confidence":"data_confidence","last-updated":"last_updated","ares-score":"ares_score","kpi-ares-score":"ares_score","market-score":"market_score","kpi-market-score":"market_score","market-tier":"market_tier","age-curve":"age_curve","trend":"trend","reason":"reason","continent":"continent","minutes-role":"minutes_role","position-usage":"position_usage","transfer-value-signal":"transfer_value_signal","kpi-transfer-signal":"transfer_value_signal","role-security":"role_security","durability":"durability","kpi-confidence":"data_confidence"}
    profile_script = f'AresSoccer.initProfile("../data/player_profile_sample.json",{json.dumps(profile_mapping, ensure_ascii=False)});'
    dynamic_profile_script = f'AresSoccer.initProfileById("../data/public_players.json",{json.dumps(profile_mapping, ensure_ascii=False)});'
    write_text("players/player-template.html", page("../", "Player ARES Profile | Market Score, Club, League & Transfer Signal", "ARES player profile with public beta player card, ARES Score, Market Score, role, confidence, image source, and locked premium components.", "players/player-template.html", "Player ARES Profile", "A football asset card showing identity, role, ARES quality, Market Score, confidence, and source context.", profile_body, profile_script))
    write_text("players/profile.html", page("../", "Player ARES Profile | Market Score, Club, League & Transfer Signal", "ARES player profile with public beta player card, ARES Score, Market Score, role, confidence, image source, and locked premium components.", "players/profile.html", "Player ARES Profile", "A football asset card showing identity, role, ARES quality, Market Score, confidence, and source context.", profile_body, dynamic_profile_script))

    club_body = '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Top 5 by ARES</h2>' + table("club-ares-table", ["Player", "Position", "ARES", "Role", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top 5 by Market</h2>' + table("club-market-table", ["Player", "Age", "Market", "Tier", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>' + table("club-u23-table", ["Player", "Age", "Market", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Recent Transfers</h2>' + table("club-transfer-table", ["Date", "Player", "Type", "Impact", "Mode"]) + '</div></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Weakest Position Groups</h2><p>Depth risk review, role security, and U23 coverage are tracked separately from asset value.</p></div><div class="ares-card"><h2 class="h4">Contract Risk</h2><p>Contract windows are treated as market signals, not salary or transfer-fee claims.</p></div><div class="ares-card"><h2 class="h4">Squad Depth</h2><p>ARES evaluates squad portfolios by age curve, role security, positional scarcity, and confidence.</p></div><div class="ares-card"><h2 class="h4">Source Notes</h2><p>Public beta rows use ARES estimates and safe images only.</p></div></section>'
    club_script = script_init([script_paths("../", "data/public_players.json", "club-ares-table", [{"key": "player_name", "label": "Player"}, {"key": "position", "label": "Position"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "role", "label": "Role"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="ares_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "club-market-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "market_tier", "label": "Tier", "render": "tier"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "club-u23-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], maxAge=23, sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_transfers.json", "club-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Impact"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5)])
    write_text("clubs/club-template.html", page("../", "Club Portfolio Board | Squad Value, ARES Strength, U23 Assets & Transfer Risk", "Club portfolio profile with squad value, ARES strength, top assets, U23 assets, transfer risk, need area, and source notes.", "clubs/club-template.html", "Club Portfolio", "Clubs are treated as football asset portfolios.", club_body, club_script))
    club_profile_body = """<section class="ares-section ares-card"><div class="ares-profile-card"><h2 id="club-name">Club Portfolio</h2><p><span id="club-league"></span> | <span id="club-country"></span> | <span id="club-continent"></span></p><div class="ares-status-terminal"><div class="ares-status-item"><strong>Squad Market</strong><span id="club-market"></span></div><div class="ares-status-item"><strong>Avg ARES</strong><span id="club-ares"></span></div><div class="ares-status-item"><strong>Average Age</strong><span id="club-age"></span></div><div class="ares-status-item"><strong>Top Asset</strong><span id="club-top-asset"></span></div><div class="ares-status-item"><strong>Transfer Risk</strong><span id="club-risk"></span></div></div></div></section><section class="ares-section ares-card"><h2 class="h4">Current Player Roster</h2>""" + table("club-roster-table", ["Player", "Age", "Position", "Minutes / Role", "ARES", "Market", "Tier", "Trend", "Confidence"]) + """</section><section class="ares-section ares-card"><h2 class="h4">U23 Assets</h2>""" + table("club-u23-table", ["Player", "Age", "Position", "Market", "Reason"]) + """</section><section id="profile-message" class="ares-section ares-card" hidden></section>"""
    club_profile_mapping = {"club-name": "club_name", "club-league": "league", "club-country": "country", "club-continent": "continent", "club-market": "squad_market_score", "club-ares": "avg_ares_score", "club-age": "average_age", "club-top-asset": "top_asset", "club-risk": "transfer_risk"}
    club_profile_script = f'AresSoccer.initClubProfileById("../data/public_clubs.json","../data/public_players.json",{json.dumps(club_profile_mapping, ensure_ascii=False)});'
    write_text("clubs/profile.html", page("../", "Club Portfolio | Squad Value, Roster, ARES Strength & Market Score", "Club profile with current player roster, ARES strength, Market Score, U23 assets, transfer risk, and squad context.", "clubs/profile.html", "Club Portfolio", "Current roster, squad value, top assets, U23 assets, and market risk.", club_profile_body, club_profile_script))

    league_body = '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Clubs Table</h2>' + table("league-clubs-table", ["Club", "ARES", "Market", "Top Asset", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top Players</h2>' + table("league-players-table", ["Player", "Club", "ARES", "Market", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>' + table("league-u23-table", ["Player", "Age", "Market", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Transfer Movement</h2>' + table("league-transfer-table", ["Date", "Player", "Type", "Impact", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Market Risers</h2>' + table("league-risers-table", ["Player", "Change", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Market Fallers</h2>' + table("league-fallers-table", ["Player", "Trend", "Reason", "Mode"]) + '</div></section><section class="ares-section ares-card"><h2 class="h4">Source Notes</h2><p>League profile rows are public beta estimates used to show market structure while live feeds are connected.</p></section>'
    league_script = script_init([script_paths("../", "data/public_clubs.json", "league-clubs-table", [{"key": "club_name", "label": "Club"}, {"key": "avg_ares_score", "label": "ARES", "render": "score"}, {"key": "squad_market_score", "label": "Market", "render": "market"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5), script_paths("../", "data/public_players.json", "league-players-table", [{"key": "player_name", "label": "Player"}, {"key": "club", "label": "Club"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="ares_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "league-u23-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], maxAge=23, sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_transfers.json", "league-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Impact"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5), script_paths("../", "data/public_market_changes.json", "league-risers-table", [{"key": "player_name", "label": "Player"}, {"key": "change", "label": "Change"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="trend", filterValue="Rising", limit=5), script_paths("../", "data/public_market_changes.json", "league-fallers-table", [{"key": "player_name", "label": "Player"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="trend", filterValue="Falling", limit=5)])
    write_text("leagues/league-template.html", page("../", "League Market Board | Player Value, ARES Scores, U23 Assets & Transfers", "League profile with league market snapshot, clubs, top players, U23 assets, transfer movement, risers, fallers, and source notes.", "leagues/league-template.html", "League Market Board", "A market exchange view for league strength, squad quality, top assets, U23 pipeline, and movement signals.", league_body, league_script))


def build_static_club_pages(clubs: list[dict[str, Any]], players: list[dict[str, Any]]) -> None:
    roster_cols = [
        {"key": "player_name", "label": "Player", "render": "playerLink", "showAvatar": True},
        {"key": "age", "label": "Age"},
        {"key": "position", "label": "Position"},
        {"key": "minutes_role", "label": "Minutes / Role"},
        {"key": "ares_score", "label": "ARES", "render": "score"},
        {"key": "market_score", "label": "Market", "render": "market"},
        {"key": "market_tier", "label": "Tier", "render": "tier"},
        {"key": "trend", "label": "Trend", "render": "trend"},
        {"key": "data_confidence", "label": "Confidence", "render": "confidence"},
    ]
    u23_cols = [
        {"key": "player_name", "label": "Player", "render": "playerLink", "showAvatar": True},
        {"key": "age", "label": "Age"},
        {"key": "position", "label": "Position"},
        {"key": "market_score", "label": "Market", "render": "market"},
        {"key": "reason", "label": "Reason"},
    ]
    for club in clubs:
        prefix = "../../"
        club_players = [player for player in players if player.get("club_id") == club["club_id"] or player.get("club") == club["club_name"]]
        body = f"""<section class="ares-section ares-card"><div class="ares-profile-card"><h2>{static_safe(club["club_name"])}</h2><p>{static_safe(club["league"])} | {static_safe(club["country"])} | {static_safe(club["continent"])}</p><div class="ares-status-terminal"><div class="ares-status-item"><strong>Squad Market</strong><span>{static_safe(club["squad_market_score"])}</span></div><div class="ares-status-item"><strong>Avg ARES</strong><span>{static_safe(club["avg_ares_score"])}</span></div><div class="ares-status-item"><strong>Average Age</strong><span>{static_safe(club["average_age"])}</span></div><div class="ares-status-item"><strong>Top Asset</strong><span>{static_safe(club["top_asset"])}</span></div><div class="ares-status-item"><strong>Transfer Risk</strong><span>{static_safe(club["transfer_risk"])}</span></div></div></div></section>"""
        body += '<section class="ares-section ares-terminal-grid">' + chart_card("Market Score vs Age", "Squad portfolio shape by age and market score.", "scatter") + chart_card("Position Strength", "GK, CB, FB, CM, W, CF portfolio balance.", "bars") + "</section>"
        body += '<section class="ares-section ares-card"><h2 class="h4">Current Player Roster</h2>' + table("club-roster-table", ["Player", "Age", "Position", "Minutes / Role", "ARES", "Market", "Tier", "Trend", "Confidence"]) + "</section>"
        body += '<section class="ares-section ares-card"><h2 class="h4">U23 Assets</h2>' + table("club-u23-table", ["Player", "Age", "Position", "Market", "Reason"]) + "</section>"
        scripts = script_init([
            script_paths(prefix, "data/public_players.json", "club-roster-table", roster_cols, filterKey="club_id", filterValue=club["club_id"], sortKey="market_score", sortDirection="desc"),
            script_paths(prefix, "data/public_players.json", "club-u23-table", u23_cols, filterKey="club_id", filterValue=club["club_id"], maxAge=23, sortKey="market_score", sortDirection="desc"),
        ])
        write_text(f"clubs/{club['club_id']}/index.html", page(prefix, f"{club['club_name']} Portfolio | Current Roster, ARES Strength & Market Score", f"{club['club_name']} current roster, squad market score, ARES strength, U23 assets, and transfer risk.", f"clubs/{club['club_id']}/", f"{club['club_name']} Portfolio", "Current roster, squad value, top assets, U23 assets, and market risk.", body, scripts))


def build_methodology_and_credits() -> None:
    methodology_body = kpi_cards([("ARES Score", "Quality", "On-field football performance"), ("Market Score", "Asset", "Age, scarcity, signal, risk"), ("Confidence", "High/Med/Low", "Coverage, sample, recency"), ("Claims", "Limited", "Not fee, salary, fantasy, betting")])
    methodology_body += '<section class="ares-section ares-terminal-grid">' + chart_card("ARES Score Model", "Performance, role, efficiency, minutes, league context, durability, and trend.", "bars") + chart_card("Market Score Model", "ARES quality, age curve, position scarcity, contract signal, and movement value.", "line") + "</section>"
    methodology_body += f"""<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">What ARES Score Measures</h2><p>Performance, efficiency, role and usage, opponent adjustment, volume, durability, and trend.</p></div><div class="ares-card"><h2 class="h4">What Market Score Measures</h2><p>ARES quality, age and upside, position value, league tier, market signal, movement value, and durability.</p></div></section><section class="ares-section ares-card"><h2 class="h4">Example ARES Calculation</h2><p>Seeded beta midfielder: Performance 26.4 + Efficiency 17.2 + Role 12.0 + League context 11.3 + Volume 7.4 + Durability 4.2 + Trend 3.1 = 81.6 ARES Score.</p></section><section class="ares-section ares-card"><h2 class="h4">Example Market Calculation</h2><p>Market Score combines ARES quality, age curve, position scarcity, league strength, transfer signal, durability, and confidence. A young player can outscore an older star on asset value before becoming the better footballer.</p></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">High ARES, Lower Market</h2><p>A 32-year-old elite midfielder can keep a high ARES Score while Market Score falls because age curve and contract optionality are weaker.</p></div><div class="ares-card"><h2 class="h4">Young High Market</h2><p>A 20-year-old winger with role expansion can have a high Market Score because upside, scarcity, and transfer signal are strong.</p></div></section><section class="ares-section ares-card"><h2 class="h4">What ARES Does Not Claim</h2><p>ARES Score is not a transfer fee. ARES Score is not a salary estimate. ARES Score is not a fantasy rank. ARES Score is not a scouting report by itself. Market Score is not the same as market price. Market Score is not a guaranteed sale value. Market Score is not a betting line. Market Score is not an official club valuation.</p></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Source Policy</h2><p>Seeded beta rows use safe public records, ARES-owned demo rows, and beta estimates. Restricted feeds are not connected.</p></div><div class="ares-card"><h2 class="h4">Image Policy</h2><p>Photos render only when a provider-approved or licensed rights record exists. Otherwise ARES shows a branded fallback avatar.</p></div></section>"""
    write_text("methodology.html", page("", "ARES Methodology | ARES Score, Market Score, Confidence & League Adjustment", "Learn how ARES separates on-field quality from football asset value using ARES Score, Market Score, confidence labels, and league adjustment.", "methodology.html", "ARES Methodology", "ARES separates on-field football quality from football asset value and labels confidence before live feeds are connected.", methodology_body, ""))
    body = kpi_cards([("ARES-Owned Assets", "Fallback", "Used when rights are incomplete"), ("Wikimedia Assets", "761", "Registry rows loaded"), ("Provider Assets", "0", "No restricted feeds connected"), ("Needs Review", "Human", "Before paid marketing use")])
    body += '<section class="ares-section ares-terminal-grid">' + chart_card("License Status Breakdown", "Clear, attribution required, provider-approved, and review states.", "bars") + chart_card("Asset Source Mix", "ARES fallback, Wikimedia, provider, and future approved sources.", "scatter") + "</section>"
    body += '<section class="ares-section ares-card"><p>Every visible Wikimedia image must have a stored rights record. If no rights record exists, ARES uses its fallback avatar.</p><input id="credits-search" class="ares-search mb-3" type="search" aria-label="Search player, creator, license, or source">' + table("credits-table", ["Player", "Creator", "License", "Source", "Checked", "Status", "Mode"]) + "</section>"
    scripts = script_init([script_paths("", "data/image_credits_wikimedia.json", "credits-table", [{"key": "player_name", "label": "Player"}, {"key": "creator", "label": "Creator"}, {"key": "license", "label": "License"}, {"key": "source_url", "label": "Source", "render": "link", "urlKey": "source_url", "label": "Commons file"}, {"key": "rights_checked", "label": "Checked"}, {"key": "human_review_status", "label": "Status"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], searchId="credits-search")])
    write_text("image-credits.html", page("", "Image Credits | ARES Football Market Attribution Registry", "Review image attribution, license status, source links, checked dates, and asset-rights records for ARES Football Market.", "image-credits.html", "Image Credits", "Wikimedia Commons attribution registry for visible ARES Football Market player photos.", body, scripts))


def build_seo_files() -> None:
    urls = [
        ("", "daily", "1.0"), ("players/", "daily", "0.8"), ("players/profile.html", "weekly", "0.7"), ("rankings/ares.html", "daily", "0.8"),
        ("rankings/market.html", "daily", "0.8"), ("clubs/", "weekly", "0.7"), ("clubs/profile.html", "weekly", "0.7"), ("leagues/", "weekly", "0.8"),
        ("transfers/", "daily", "0.8"), ("watchlist/", "weekly", "0.7"), ("methodology.html", "monthly", "0.6"),
        ("image-credits.html", "monthly", "0.5"), ("continents/", "weekly", "0.9"), ("leagues/mls/", "weekly", "0.8"),
    ]
    urls += [(f"continents/{slug(c)}/", "weekly", "0.9") for c in CONTINENTS]
    try:
        urls += [(f"clubs/{club['club_id']}/", "weekly", "0.7") for club in read_json("data/public_clubs.json")]
    except Exception:
        pass
    body = "\n".join(f"  <url><loc>{BASE_URL}{loc}</loc><changefreq>{change}</changefreq><priority>{priority}</priority></url>" for loc, change, priority in urls)
    write_text("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')
    write_text("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")


def main() -> None:
    players = [normalize_player(dict(row)) for row in read_json("data/public_players.json")]
    players = add_synthetic_players(players)
    clubs = build_clubs(players)
    leagues = build_leagues(players, clubs)
    market_changes = build_market_changes(players)
    transfers = build_transfers(players)
    watchlist = build_watchlist(players)
    credits = read_json("data/image_credits_wikimedia.json")
    for item in credits:
        item["asset_id"] = item.get("asset_id") or item.get("player_id")
        item["display_name"] = item.get("display_name") or item.get("player_name")
        item["image_url"] = item.get("image_url") or item.get("photo_url")
        item["commercial_allowed"] = item.get("commercial_allowed", True)
        item["checked_date"] = item.get("checked_date") or item.get("rights_checked")
        item["human_review_status"] = item.get("human_review_status") or "first-pass metadata approved"
        item["data_mode"] = DATA_MODE
    write_json("data/public_players.json", players)
    write_json("data/wikimedia_players.json", [p for p in players if p.get("photo_url")])
    write_json("data/public_clubs.json", clubs)
    write_json("data/public_leagues.json", leagues)
    write_json("data/public_market_changes.json", market_changes)
    write_json("data/public_transfers.json", transfers)
    write_json("data/public_watchlist.json", watchlist)
    write_json("data/public_search.json", build_search(players, clubs, leagues))
    write_json("data/player_profile_sample.json", players[0])
    write_json("data/club_profile_sample.json", clubs[0])
    write_json("data/league_profile_sample.json", leagues[0])
    write_json("data/image_credits_wikimedia.json", credits)
    write_json("data/asset_rights_registry.json", credits)
    write_json("data/public_beta_demo.json", {"players": players, "clubs": clubs, "leagues": leagues, "transfers": transfers, "watchlist": watchlist, "market_changes": market_changes})
    write_json("data/data_status.json", {"data_mode": DATA_MODE, "last_updated": TODAY, "players_tracked": len(players), "clubs_tracked": len(clubs), "leagues_tracked": len(leagues), "continents_covered": 6, "player_images": f"{len(credits)} licensed Commons image rights records", "ares_model": "Beta estimate formula ready", "market_model": "Beta estimate formula ready", "source": "Wikidata + Wikimedia Commons + ARES public beta estimates"})
    write_json("data/navigation.json", build_navigation())
    build_pages(players, clubs, leagues)
    build_continent_pages()
    build_legacy_region_pages()
    build_templates()
    build_static_club_pages(clubs, players)
    build_methodology_and_credits()
    prerender_generated_tables()
    strip_public_beta_badges_from_html()
    build_seo_files()
    print(f"players={len(players)} clubs={len(clubs)} leagues={len(leagues)} transfers={len(transfers)} watchlist={len(watchlist)}")


if __name__ == "__main__":
    main()



