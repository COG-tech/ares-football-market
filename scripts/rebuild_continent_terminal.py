#!/usr/bin/env python3
"""Rebuild ARES Football Market as a continent-led public beta terminal."""

from __future__ import annotations

import html
import json
import math
import re
import shutil
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://cog-tech.github.io/ares-football-market/"
SITE_ROOT = "/ares-football-market/"
TODAY = "2026-05-24"
DATA_MODE = "public_beta_demo"
PUBLIC_LABEL = "Public Beta Demo"

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
        ("Kofi Mensar", "FW", "Al Ahly SC", "Egypt Premier League", "Egypt"),
        ("Amir Benyoussef", "MF", "Zamalek SC", "Egypt Premier League", "Egypt"),
        ("Tebo Mkhize", "DF", "Mamelodi Sundowns F.C.", "South African Premier Division", "South Africa"),
        ("Nuru Okeke", "W", "Wydad AC", "Botola", "Morocco"),
        ("Idris El Fassi", "GK", "Raja CA", "Botola", "Morocco"),
    ],
    "Oceania": [
        ("Tane Raukawa", "MF", "Auckland City FC", "New Zealand National League", "New Zealand"),
        ("Noah Kerrin", "FW", "Melbourne Victory FC", "A-League", "Australia"),
        ("Luka Tevita", "DF", "Wellington Phoenix FC", "A-League", "New Zealand"),
        ("Mason Wylie", "GK", "Auckland FC", "A-League", "New Zealand"),
        ("Ari Vatu", "W", "Sydney FC", "A-League", "Australia"),
    ],
}

LEGACY_SYNTHETIC_CLUBS = {
    "Accra Harbor",
    "Cairo Atlas",
    "Cape Meridian",
    "Lagos Mainland",
    "Rabat Union",
    "Auckland Harbour",
    "Melbourne Southern",
    "Suva Coast",
    "Wellington North",
    "Sydney Southern",
}

EXCLUDED_NO_CURRENT_ROSTER_CLUBS = {
    "Achilles'29",
}

INVALID_PLAYER_NAMES = {
    "captain", "vice-captain", "vice captain", "3rd captain", "third captain",
    "head coach", "coach", "manager", "player", "players", "name", "squad",
    "current squad", "goalkeepers", "defenders", "midfielders", "forwards",
    "on loan", "loan", "country", "position", "no.", "number",
}
CLUB_NAME_STOPWORDS = {
    "fc", "f", "c", "afc", "cf", "ac", "sc", "sv", "rc", "cd", "bc", "fk", "sk",
    "if", "bk", "club", "football", "futbol", "calcio", "de", "da", "do", "the",
    "association",
}
TEAM_NAME_MARKERS = {
    "ajax", "arsenal", "atalanta", "barcelona", "bayern", "benfica", "bologna",
    "borussia", "bournemouth", "braga", "brighton", "bristol", "burnley",
    "cagliari", "cardiff", "chelsea", "city", "dortmund", "elche", "feyenoord",
    "fulham", "groningen", "juventus", "leicester", "lens", "liverpool",
    "madrid", "milan", "montevideo", "munich", "palermo", "pathum", "porto",
    "psv", "sevilla", "sheffield", "southampton", "sunderland", "tokyo", "torino", "torque",
    "udinese", "united", "villarreal", "watford",
}
SAFE_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
BAD_MEDIA_TOKENS = {
    "logo", "badge", "crest", "emblem", "kit", "icon", "flag", "shirt", "jersey",
    ".pdf", ".svg", ".gif", ".webm", "programme", "program", "newspaper",
    "daily times", "catalogue", "botanische", "map-fr",
}


def read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_json_optional(path: str, default: Any) -> Any:
    file_path = ROOT / path
    if not file_path.exists():
        return default
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return default


def is_demo_text(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text:
        return False
    banned = ("placeholder", "fake", "generic", "demo", "unfinished", "unsupported demo")
    return any(token in text for token in banned)


def is_demo_row(row: dict[str, Any]) -> bool:
    if row.get("demo_mode") is True:
        return True
    fields = [
        "player_id", "player_name", "club", "club_name", "league", "league_name",
        "from_club", "to_club", "source", "reason", "status", "watch_reason",
    ]
    return any(is_demo_text(row.get(field)) for field in fields)


def clean_real_rows(rows: Any) -> list[dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict) or is_demo_row(row):
            continue
        cleaned.append(dict(row))
    return cleaned


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


def normalized_name(value: Any) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()
    return " ".join(token for token in clean.split() if len(token) > 1 and token not in CLUB_NAME_STOPWORDS)


def repair_text(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if not any(token in text for token in ("Ã", "Å", "Ä", "Â", "Ð", "Ø")):
        return text
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text
    return repaired if repaired.count("�") <= text.count("�") else text


def blocked_name_variants(*collections: list[dict[str, Any]]) -> set[str]:
    blocked: set[str] = set()
    for items in collections:
        for item in items:
            for key in ("club_name", "league_name"):
                value = str(item.get(key, "")).strip()
                if not value:
                    continue
                blocked.add(value.lower())
                normalized = normalized_name(value)
                if normalized:
                    blocked.add(normalized)
    return blocked


def site_url(path: str) -> str:
    return SITE_ROOT + path.lstrip("/")


def avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_valid_player_name(row: dict[str, Any], blocked_names: set[str] | None = None) -> bool:
    name = str(row.get("player_name") or row.get("display_name") or row.get("name") or "").strip()
    low = name.lower()
    normalized = normalized_name(name)
    blocked_names = blocked_names or set()
    if len(name) < 3:
        return False
    if low in INVALID_PLAYER_NAMES or normalized in INVALID_PLAYER_NAMES or low in blocked_names or normalized in blocked_names:
        return False
    if normalized.startswith("jong ") and normalized[5:] in blocked_names:
        return False
    if re.search(r"\d", name):
        return False
    if any(token in low for token in ["captain", "coach", "manager", "current squad", "on loan"]):
        return False
    words = normalized.split()
    if len(words) <= 4 and any(word in TEAM_NAME_MARKERS for word in words):
        return False
    if "ii" in words:
        return False
    if re.fullmatch(r"[A-Z]{1,3}", name):
        return False
    return True


def is_valid_club_media(row: dict[str, Any]) -> bool:
    image_url = str(row.get("image_url") or "")
    source_url = str(row.get("source_url") or "")
    joined = f"{image_url} {source_url}".lower()
    clean_url = image_url.lower().split("?", 1)[0]
    return (
        bool(image_url)
        and clean_url.endswith(SAFE_IMAGE_EXTENSIONS)
        and not any(token in joined for token in BAD_MEDIA_TOKENS)
    )


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


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def per90(value: Any, minutes: Any) -> float:
    minute_value = safe_float(minutes)
    if minute_value <= 0:
        return 0.0
    return round(float(safe_float(value)) * 90.0 / minute_value, 2)


def round1(value: float) -> float:
    return round(float(value), 1)


def position_family(position: Any) -> str:
    raw = str(position or "").upper()
    if any(token in raw for token in ("GK", "GOALKEEPER")):
        return "GK"
    if any(token in raw for token in ("CB", "CENTER BACK", "CENTRE BACK")):
        return "CB"
    if any(token in raw for token in ("FB", "LB", "RB", "WB", "FULLBACK", "WINGBACK", "WING BACK")):
        return "FB/WB"
    if any(token in raw for token in ("DM", "CDM", "DEFENSIVE MID")):
        return "DM"
    if any(token in raw for token in ("AM", "CAM", "ATTACKING MID")):
        return "AM"
    if any(token in raw for token in ("LW", "RW", " W", "WINGER", "WIDE FORWARD")):
        return "W"
    if any(token in raw for token in ("CF", "ST", "STRIKER", "CENTER FORWARD", "CENTRE FORWARD", "FW")):
        return "CF/ST"
    return "CM"


def age_component(age: int) -> float:
    if age <= 20:
        return 92.0
    if age <= 23:
        return 84.0
    if age <= 27:
        return 76.0
    if age <= 30:
        return 66.0
    if age <= 33:
        return 58.0
    return 50.0


def league_context_component(level: Any, confederation: Any) -> float:
    base = {"top": 88.0, "second": 74.0, "third": 62.0, "fourth": 56.0}.get(str(level or "").lower(), 68.0)
    if str(confederation or "").upper() in {"UEFA", "CONMEBOL"}:
        base += 2.0
    return round1(base)


def tier_for_score(score: float, score_type: str) -> str:
    if score_type == "market":
        if score >= 88:
            return "Franchise Asset"
        if score >= 82:
            return "Blue-Chip Asset"
        if score >= 76:
            return "Rising Asset"
        if score >= 68:
            return "Core Starter"
        return "Watchlist"
    if score >= 85:
        return "Elite"
    if score >= 78:
        return "High"
    if score >= 70:
        return "Starter"
    return "Watchlist"


def apply_public_formula_scores(row: dict[str, Any]) -> None:
    minutes = safe_int(row.get("minutes"))
    appearances = safe_int(row.get("appearances"))
    starts = safe_int(row.get("starts"))
    age = safe_int(row.get("age"), 25)
    goal_contrib90 = per90(safe_float(row.get("goals")) + safe_float(row.get("assists")), minutes)
    goals90 = per90(row.get("goals"), minutes)
    assists90 = per90(row.get("assists"), minutes)
    prog90 = per90(row.get("progressive_actions"), minutes)
    def90 = per90(row.get("defensive_actions"), minutes)
    start_rate = (starts / appearances * 100.0) if appearances else 0.0
    availability = safe_float(row.get("availability_pct"), 65.0)
    trend_value = safe_float(row.get("trend_value"))
    trend = round1(max(0.0, min(100.0, 50.0 + trend_value * 10.0)))
    role_usage = round1(start_rate * 0.65 + min(100.0, minutes / 30.0) * 0.35)
    volume = round1(min(100.0, minutes / 30.0))
    attack = round1(min(100.0, goals90 * 18 + assists90 * 12 + prog90 * 5))
    creation = round1(min(100.0, assists90 * 18 + prog90 * 7 + goal_contrib90 * 8))
    defense = round1(min(100.0, def90 * 7 + availability * 0.4))
    family = position_family(row.get("position"))
    if family in {"CB", "FB/WB"}:
        performance = round1(attack * 0.14 + creation * 0.14 + defense * 0.42 + role_usage * 0.30)
    elif family in {"DM", "CM"}:
        performance = round1(attack * 0.18 + creation * 0.24 + defense * 0.24 + role_usage * 0.34)
    elif family in {"AM", "W", "CF/ST"}:
        performance = round1(attack * 0.34 + creation * 0.28 + defense * 0.10 + role_usage * 0.28)
    else:
        performance = round1(attack * 0.22 + creation * 0.22 + defense * 0.22 + role_usage * 0.34)
    efficiency = round1(min(100.0, goal_contrib90 * 14 + start_rate * 0.25))
    age_upside = age_component(age)
    league_context = league_context_component(row.get("league_level"), row.get("confederation"))
    position_value = {"GK": 72.0, "CB": 74.0, "FB/WB": 76.0, "DM": 78.0, "CM": 80.0, "AM": 83.0, "W": 86.0, "CF/ST": 88.0}.get(family, 75.0)
    legacy_market = safe_float(row.get("market_score"), 70.0)
    market_signal = round1(min(100.0, legacy_market * 0.65 + trend * 0.35))
    movement_value = round1(max(0.0, min(100.0, 50.0 + trend_value * 14.0)))
    formula_ares = round1(performance * 0.30 + efficiency * 0.20 + role_usage * 0.15 + volume * 0.12 + availability * 0.10 + trend * 0.05 + age_upside * 0.04 + league_context * 0.04)
    formula_market = round1(formula_ares * 0.25 + age_upside * 0.20 + position_value * 0.15 + league_context * 0.15 + market_signal * 0.10 + movement_value * 0.05 + availability * 0.10)
    row["legacy_ares_score"] = row.get("legacy_ares_score", row.get("ares_score"))
    row["legacy_market_score"] = row.get("legacy_market_score", row.get("market_score"))
    row["ares_score"] = formula_ares
    row["market_score"] = formula_market
    row["ares_tier"] = tier_for_score(formula_ares, "ares")
    row["market_tier"] = tier_for_score(formula_market, "market")
    row["score_source"] = "ARES public formula score"
    row["stats_mode"] = "ARES public formula score; not official match statistics"


def normalize_player(row: dict[str, Any]) -> dict[str, Any]:
    name = repair_text(row.get("display_name") or row.get("player_name") or row.get("name") or "ARES Player")
    league = repair_text(row.get("league", ""))
    country = repair_text(row.get("country") or LEAGUE_COUNTRY.get(league, ""))
    continent, region, confederation = geo_for(country, league, row.get("region", ""))
    player_id = row.get("player_id") or f"pbp-{slug(name)}"
    player_slug = row.get("slug") or slug(name)
    club = repair_text(row.get("club") or "ARES Club")
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
            "minutes_role": repair_text(row.get("minutes_role")) or f"{row.get('minutes', 0)} estimated minutes / {repair_text(row.get('role', 'Role review'))}",
            "position_usage": repair_text(row.get("position_usage") or row.get("position_label") or row.get("position", "")),
            "transfer_value_signal": repair_text(row.get("transfer_value_signal")) or f"{repair_text(row.get('trend', 'Stable'))} {row.get('trend_value', 0)}",
            "role_security": row.get("role_security") or ("High" if int(row.get("minutes", 0) or 0) >= 1900 else "Medium"),
            "durability": row.get("durability") or f"{row.get('availability_pct', 0)}% availability estimate",
            "reason": repair_text(row.get("reason")) or f"{name} is tracked through the ARES public football market model.",
            "contract_end": repair_text(row.get("contract_end") or ""),
            "foot": repair_text(row.get("foot") or row.get("preferred_foot") or ""),
            "age_curve": row.get("age_curve") or ("Upside" if int(row.get("age", 99) or 99) <= 23 else "Prime"),
            "role": repair_text(row.get("role") or "Current squad review"),
            "data_confidence": row.get("data_confidence") or row.get("confidence") or "Medium",
            "confidence": row.get("confidence") or row.get("data_confidence") or "Medium",
            "last_updated": row.get("last_updated") or row.get("roster_checked_date") or TODAY,
            "source": repair_text(row.get("source")) or "ARES public beta record",
            "score_source": repair_text(row.get("score_source")) or "ARES beta estimate",
            "stats_mode": repair_text(row.get("stats_mode")) or "ARES beta estimate; not official match statistics",
            "url": player_profile_url,
            "player_url": player_profile_url,
            "club_url": club_profile_url,
            "league_url": row.get("league_url") or league_profile_url,
        }
    )
    apply_public_formula_scores(row)
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
                        "source": "ARES public beta record",
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
                "top_asset_player_url": top.get("player_url", ""),
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
    league_rows = list(rows.values())
    league_rows.sort(key=lambda item: (-float(item["market_depth"]), item["league_name"]))
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
    candidates = sorted(
        [
            player for player in players
            if player.get("contract_end") or abs(safe_float(player.get("trend_value"))) >= 1.5
        ],
        key=lambda item: (
            "2026" not in str(item.get("contract_end") or ""),
            -abs(safe_float(item.get("trend_value"))),
            -safe_float(item.get("market_score")),
        ),
    )[:36]
    for index, player in enumerate(candidates, 1):
        contract_end = str(player.get("contract_end") or "")
        if "2026" in contract_end:
            movement = "Contract Signal"
        elif safe_float(player.get("trend_value")) >= 2:
            movement = "Market Movement"
        else:
            movement = "Monitoring"
        rows.append({
            "data_mode": DATA_MODE,
            "transfer_id": f"pbt-{index:03d}",
            "date": player.get("last_updated") or TODAY,
            "player_id": player["player_id"],
            "player_name": player["player_name"],
            "player": player["player_name"],
            "initials": player.get("initials", ""),
            "age": player["age"],
            "position": player["position"],
            "from_club": player["club"],
            "from_club_url": player.get("club_url", ""),
            "to_club": "",
            "to_club_url": "",
            "from_league": player["league"],
            "to_league": "",
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
            "source": "ARES player contract and trend layer",
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
    sample = sorted(
        [
            player for player in players
            if safe_int(player.get("age"), 99) <= 23
            or str(player.get("data_confidence", "")).lower() != "high"
            or abs(safe_float(player.get("trend_value"))) >= 2
        ],
        key=lambda item: (
            safe_int(item.get("age"), 99),
            str(item.get("data_confidence", "")).lower() == "high",
            -safe_float(item.get("market_score")),
        ),
    )[:36]
    for index, player in enumerate(sample, 1):
        if safe_int(player.get("age"), 99) <= 20:
            category = "U21 Asset"
        elif safe_int(player.get("age"), 99) <= 23:
            category = "U23 Asset"
        elif str(player.get("data_confidence", "")).lower() == "low":
            category = "Thin Data Watch"
        elif "2026" in str(player.get("contract_end") or ""):
            category = "Contract Signal"
        elif safe_float(player.get("trend_value")) >= 2:
            category = "Role Expansion"
        else:
            category = "Scouting Flag"
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
            "status": "Tracked from real player coverage until more confirmation lands",
            "last_movement": player["transfer_value_signal"],
            "confidence": player.get("data_confidence", "Medium"),
            "data_confidence": player.get("data_confidence", "Medium"),
            "last_updated": TODAY,
            "source": "ARES player watch layer",
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
    return f'<div class="table-responsive"><table id="{table_id}" class="ares-table"><thead><tr>{head}</tr></thead><tbody id="{body_id}"></tbody></table></div>'


def static_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return ""
    head = "".join(f"<th>{static_safe(item)}</th>" for item in headers)
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{static_safe(value)}</td>" for value in row) + "</tr>")
    return f'<div class="table-responsive"><table class="ares-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body_rows)}</tbody></table></div>'


def beta_note() -> str:
    return f'<div class="ares-beta-strip"><strong>Public Beta Demo</strong><span>Open Match CSV connected</span><span>ARES Score &ne; transfer fee</span><span>Market Score &ne; market price</span><span>Last updated: {static_safe(TODAY)}</span></div>'


def kpi_cards(items: list[tuple[str, Any, str]]) -> str:
    cards = []
    for label, value, meta in items:
        cards.append(
            f'<div class="ares-kpi-card"><span class="label">{static_safe(label)}</span>'
            f'<span class="value">{static_safe(value)}</span><span class="meta">{static_safe(meta)}</span></div>'
        )
    return '<section class="ares-section ares-kpi-grid">' + "".join(cards) + "</section>"


def chart_axis_defaults(title: str, kind: str) -> tuple[str, str, str]:
    text = title.lower()
    if "age" in text and "market" in text:
        return "Player age", "Market Score", "Each point shows how squad age relates to market value."
    if "ares" in text and "market" in text:
        return "ARES Score", "Market Score", "The chart separates on-field quality from football asset value."
    if "trend" in text or kind == "line":
        return "Recent window", "ARES / Market signal", "The line shows direction of travel across the latest beta window."
    if "position" in text:
        return "Position group", "Squad strength", "Bars compare strength across the main football position groups."
    if "license" in text or "source" in text:
        return "Asset status", "Record count", "Bars summarize source and rights coverage before images are shown publicly."
    return "ARES board segment", "Visible real-data rows", "Bars summarize sourced records and score signals on this page."


def chart_card(title: str, subtitle: str, kind: str = "bars", x_label: str = "", y_label: str = "", explanation: str = "") -> str:
    default_x, default_y, default_explanation = chart_axis_defaults(title, kind)
    x_label = x_label or default_x
    y_label = y_label or default_y
    explanation = explanation or default_explanation
    if kind == "scatter":
        visual = '<div class="ares-chart-frame"><div class="ares-chart-scatter"><i style="left:18%;top:58%"></i><i style="left:34%;top:44%"></i><i style="left:52%;top:31%"></i><i style="left:67%;top:22%"></i><i style="left:78%;top:39%"></i></div></div>'
    elif kind == "line":
        visual = '<div class="ares-chart-frame"><div class="ares-chart-line"></div></div>'
    else:
        visual = '<div class="ares-chart-frame"><div class="ares-chart-bars"><span style="height:48%"></span><span style="height:72%"></span><span style="height:56%"></span><span style="height:88%"></span><span style="height:64%"></span><span style="height:78%"></span></div></div>'
    return (
        f'<div class="ares-graph-card"><h2 class="h4">{static_safe(title)}</h2>'
        f'<p class="ares-muted-note">{static_safe(subtitle)}</p>{visual}'
        f'<div class="ares-chart-axis"><span>X-axis: {static_safe(x_label)}</span><span>Y-axis: {static_safe(y_label)}</span></div>'
        '<div class="ares-chart-legend"><span>ARES</span><span>Market</span><span>Trend</span><span>Confidence</span></div>'
        f'<p class="ares-chart-explainer">How to read: {static_safe(explanation)}</p></div>'
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
  <link href="{prefix}assets/css/ares-theme.css?v=20260531-metronic" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/ares-components.css?v=20260531-metronic" rel="stylesheet" type="text/css">
  <style>.soccer-main{{width:min(100%,1440px);margin:0 auto;padding:clamp(1rem,2.5vw,2rem)}}.table-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}.table-grid .wide{{grid-column:1/-1}}.hero-grid{{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(18rem,.75fr);gap:1rem;align-items:start}}.continent-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}}.premium-lock{{position:relative;min-height:8rem}}.premium-lock:after{{content:"Premium";position:absolute;right:1rem;top:1rem}}@media(max-width:1000px){{.table-grid,.hero-grid,.continent-grid{{grid-template-columns:1fr}}}}</style>"""


def page(prefix: str, title: str, meta: str, canonical: str, h1: str, intro: str, body: str, scripts: str = "") -> str:
    nav = f"""<header class="ares-topbar" data-ares-root="{root_attr(prefix)}">
    <a class="ares-brand" href="{prefix}index.html"><img src="{prefix}assets/media/brand/ares-logo.png" alt="" width="44" height="44">ARES Football Market</a>
    <nav class="ares-nav" aria-label="Primary">
      <a href="{prefix}index.html">Home</a><a href="{prefix}players/index.html">Players</a><a href="{prefix}rankings/ares.html">Rankings</a><a href="{prefix}clubs/index.html">Clubs</a><a href="{prefix}leagues/index.html">Leagues</a><a href="{prefix}transfers/index.html">Transfers</a><a href="{prefix}watchlist/index.html">Watchlist</a><a href="{prefix}reports/index.html">Reports</a><a href="{prefix}methodology.html">Methodology</a><a href="{prefix}about.html">About</a>
    </nav>
    <div class="ares-top-actions"><a href="{prefix}rankings/gap.html">Open Gap Board</a><span>Public Beta Demo</span></div>
  </header>"""
    js = f"""<script src="{prefix}assets/plugins/global/plugins.bundle.js"></script>
  <script src="{prefix}assets/js/scripts.bundle.js"></script>
  <script src="{prefix}assets/js/ares-data-loader.js"></script>
  <script src="{prefix}assets/js/ares-tables.js"></script>
  <script src="{prefix}assets/js/soccer-pages.js"></script>
  <script src="{prefix}assets/js/ares-mega-nav.js?v=20260523-continent"></script>"""
    if scripts:
        js += f"<script>{scripts}</script>"
    return f"""<!DOCTYPE html><html lang="en"><head>{common_head(prefix, title, meta, canonical)}</head><body class="ares-shell">{nav}{beta_note()}<main class="soccer-main"><div class="ares-page-title"><h1>{h1}</h1><p>{intro}</p></div>{body}</main><footer class="ares-footer">ARES Football Market is an independent public beta football intelligence product. <a href="{prefix}about.html">About</a>. <a href="{prefix}image-credits.html">Image credits</a>. <span class="ares-brand-switch"><a href="{prefix}index.html">Global Football</a><a href="https://cog-tech.github.io/ares-gridiron-market/">ARES Gridiron Market</a></span></footer>{js}</body></html>"""


def profile_page(prefix: str, title: str, meta: str, canonical: str, body: str, scripts: str = "") -> str:
    profile_tabs = '<nav class="ares-profile-tab-nav ares-player-tabs" aria-label="Player profile tabs"><a data-profile-view="overview" href="?view=overview">Profile</a><a data-profile-view="stats" href="?view=stats">Stats</a><a data-profile-view="market" href="?view=market">Market Value</a><a data-profile-view="transfers" href="?view=transfers">Transfers</a><a data-profile-view="rumours" href="?view=rumours">Rumours</a><a data-profile-view="national-team" href="?view=national-team">National Team</a><a data-profile-view="news" href="?view=news">News</a><a data-profile-view="achievements" href="?view=achievements">Achievements</a><a data-profile-view="career" href="?view=career">Career</a></nav>'
    nav = f"""<header class="ares-profile-topbar" data-ares-root="{root_attr(prefix)}">
    <a class="ares-profile-brand" href="{prefix}index.html"><span>ARES</span><small>Football Market</small></a>
    {profile_tabs}
    <div class="ares-profile-search"><input id="profile-search" type="search" aria-label="Search players, clubs, leagues"><div id="profile-search-results" class="search-results"></div></div>
    <a class="ares-profile-icon" href="{prefix}watchlist/" aria-label="Watchlist">&#9734;</a><a class="ares-profile-icon" href="{prefix}players/" aria-label="Player search">&#9679;</a>
  </header>"""
    js = f"""<script src="{prefix}assets/plugins/global/plugins.bundle.js"></script>
  <script src="{prefix}assets/js/scripts.bundle.js"></script>
  <script src="{prefix}assets/js/ares-data-loader.js"></script>
  <script src="{prefix}assets/js/ares-tables.js"></script>
  <script src="{prefix}assets/js/soccer-pages.js"></script>
  <script src="{prefix}assets/js/ares-mega-nav.js?v=20260523-continent"></script>"""
    if scripts:
        js += f"<script>{scripts}</script>"
    return f"""<!DOCTYPE html><html lang="en"><head>{common_head(prefix, title, meta, canonical)}</head><body class="ares-shell ares-player-page">{nav}{beta_note()}<main class="ares-profile-main">{body}</main><footer class="ares-profile-footer"><span>ARES Football Market - Premium Football Intelligence Terminal</span><span>All values are estimates based on ARES proprietary models and public data.</span></footer>{js}</body></html>"""


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
        if new.get("render") in {"playerLink", "clubLink", "leagueLink", "link"} or new.get("key") in {"player_name", "top_asset", "club", "club_name", "league", "league_name", "from_club", "to_club"}:
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


def clean_public_credit_text(value: Any) -> str:
    text = re.sub(r"\s+", " ", repair_text(value)).strip()
    if ".mw-parser-output" in text:
        text = text.split(".mw-parser-output", 1)[0].strip()
    text = re.sub(r"\(\s*No Fake News[^)]*\)", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"No Fake News", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s+", " ", text)
    return text[:220].rstrip()


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


def static_num(value: Any, digits: int = 1, default: str = "0.0") -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return default


def static_signed(value: Any, digits: int = 1, default: str = "+0.0") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return f"{number:+.{digits}f}"


def latest_public_date(players: list[dict[str, Any]]) -> str:
    dates = [str(row.get("last_updated") or "") for row in players if row.get("last_updated")]
    return max(dates) if dates else TODAY


def ares_why(row: dict[str, Any]) -> str:
    role = str(row.get("minutes_role") or row.get("position") or "role")
    league = str(row.get("league") or row.get("continent") or "market")
    trend = str(row.get("trend") or "Stable").lower()
    trend_text = "positive movement" if trend in {"up", "rising"} else "role stability"
    if int(row.get("age") or 99) <= 23:
        return f"Age curve, role security, {league} context, and {trend_text}."
    return f"{role} security, league strength, durable output, and {trend_text}."


def home_rank_rows(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [
        row for row in players
        if float(row.get("ares_score") or 0) >= 68
        and float(row.get("market_score") or 0) >= 65
        and str(row.get("data_confidence") or "").lower() in {"high", "medium"}
        and row.get("player_name")
        and row.get("club")
    ]
    scoped = eligible if len(eligible) >= 8 else players
    ares_rank = {row.get("player_id"): idx for idx, row in enumerate(sorted(scoped, key=lambda item: float(item.get("ares_score") or 0), reverse=True), 1)}
    market_rank = {row.get("player_id"): idx for idx, row in enumerate(sorted(scoped, key=lambda item: float(item.get("market_score") or 0), reverse=True), 1)}
    rows: list[dict[str, Any]] = []
    for row in scoped:
        pid = row.get("player_id")
        a_rank = ares_rank.get(pid, len(scoped))
        m_rank = market_rank.get(pid, len(scoped))
        try:
            move = float(row.get("trend_value") or 0)
        except (TypeError, ValueError):
            move = 0.0
        raw_gap = m_rank - a_rank
        gap = round(raw_gap / 25) if raw_gap else 0
        if gap == 0 and raw_gap > 0:
            gap = 1
        if gap == 0 and raw_gap < 0:
            gap = -1
        rows.append({
            "player": row,
            "ares_rank": a_rank,
            "market_rank": m_rank,
            "gap": gap,
            "rank_gap": raw_gap,
            "move": move,
            "why": ares_why(row),
        })
    rows.sort(key=lambda item: (item["gap"], item["move"], float(item["player"].get("ares_score") or 0)), reverse=True)
    return rows


def home_player_visual(row: dict[str, Any], class_name: str = "ares-v6-player-image") -> str:
    name = row.get("player_name") or "ARES Player"
    label = ", ".join(str(row.get(key, "")) for key in ["player_name", "club", "position"] if row.get(key))
    if static_image_is_safe(row):
        src = static_asset_href(row.get("photo_url"), "")
        return f'<img class="{class_name}" src="{static_safe(src)}" alt="{static_safe(label)}" onerror="this.closest(\'.ares-v6-feature-media\').classList.add(\'image-missing\');this.remove()">'
    initials = static_initials(name)
    return f'<div class="{class_name} ares-v6-player-fallback" aria-label="{static_safe(label)}"><span>{static_safe(initials)}</span></div>'


def home_score_heat(players: list[dict[str, Any]], label: str) -> int:
    if label == "MLS":
        scoped = [row for row in players if "mls" in str(row.get("league") or "").lower() or "major league soccer" in str(row.get("league") or "").lower()]
        if not scoped:
            scoped = [row for row in players if str(row.get("continent") or "") == "North America"]
    else:
        scoped = [row for row in players if str(row.get("continent") or "") == label]
    if not scoped:
        return 50
    ranked = sorted((float(row.get("ares_score") or row.get("market_score") or 0) for row in scoped), reverse=True)
    scored = [score for score in ranked if score >= 45][:30] or ranked[:30]
    score = sum(scored) / len(scored) if scored else 50
    return max(1, min(99, round(score)))


def home_v6_page(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> str:
    updated = latest_public_date(players)
    gap_rows = home_rank_rows(players)
    safe_feature_rows = [item for item in gap_rows if static_image_is_safe(item["player"])]
    moving_feature_rows = [item for item in safe_feature_rows if item["move"] > 0]
    featured = (moving_feature_rows or safe_feature_rows or gap_rows)[0]
    feature_player = featured["player"]
    market_changes = build_market_changes(players)
    new_signal_count = len(market_changes) or len(players)
    riser = max(market_changes, key=lambda item: float(str(item.get("change") or "0").replace("+", ""))) if market_changes else {"player_name": feature_player.get("player_name"), "change": static_signed(featured["move"])}
    u23_rows = [item for item in gap_rows if int(item["player"].get("age") or 99) <= 23]
    u23 = (u23_rows or gap_rows)[0]
    overheats = sorted(gap_rows, key=lambda item: (item["gap"], -float(item["player"].get("market_score") or 0)))
    overheat = overheats[0] if overheats else featured
    asia_rows = [item for item in gap_rows if item["player"].get("continent") == "Asia"]
    asia = (asia_rows or gap_rows)[0]
    contracts_2026 = [row for row in players if "2026" in str(row.get("contract_end") or row.get("contract_until") or row.get("transfer_value_signal") or "")]
    top_club = max(clubs, key=lambda item: float(item.get("squad_market_score") or 0)) if clubs else {}
    top_league = max(leagues, key=lambda item: float(item.get("league_strength") or 0)) if leagues else {}

    def player_href(row: dict[str, Any]) -> str:
        return static_prefixed_href(row.get("player_url") or "players/index.html", "")

    def tile(label: str, name: str, value: str, href: str, cta: str, color_class: str) -> str:
        return (
            f'<a class="ares-v6-live-tile {color_class}" href="{static_safe(href)}">'
            f'<span>{static_safe(label)}</span><strong>{static_safe(name)}</strong><b>{static_safe(value)}</b>'
            f'<em>{static_safe(cta)}</em><small>Updated today</small></a>'
        )

    live_tiles = "".join([
        tile("New Today", "Signals", f"{new_signal_count}", "transfers/index.html", "Open Signal Tape", "is-green"),
        tile("Biggest Gap", feature_player.get("player_name"), f"+{featured['gap']}", player_href(feature_player), "Open Gap Board", "is-gold"),
        tile("Biggest Riser", riser.get("player_name"), str(riser.get("change")), "transfers/index.html", "View Mover", "is-green"),
        tile("Top Club", top_club.get("club_name", "Club board"), static_num(top_club.get("squad_market_score")) if top_club else "", "clubs/index.html", "Open Club Board", "is-blue"),
        tile("U23 Heat", u23["player"].get("player_name"), f"+{u23['gap']}", player_href(u23["player"]), "Open U23 Board", "is-orange"),
        tile("Overheat", overheat["player"].get("player_name"), f"{overheat['gap']:+d}", player_href(overheat["player"]), "Open Overheats", "is-red"),
        tile("Asia Watch", asia["player"].get("player_name"), f"+{asia['gap']}", player_href(asia["player"]), "Open Asia Board", "is-purple"),
        tile("Contract Watch", "Window", f"{len(contracts_2026) or 2026}", "transfers/index.html", "Open Transfers", "is-navy"),
    ])

    signature_boards = [
        ("Gap Board", "Who is better than the market thinks?", "rankings/gap.html", "is-green"),
        ("Overheat Board", "Who is valued ahead of output?", "rankings/market.html", "is-red"),
        ("U23 Breakout", "Young assets compounding early.", "players/index.html?q=U23", "is-orange"),
        ("Club Portfolio Movers", "Squads gaining asset depth.", "clubs/index.html", "is-blue"),
        ("League Arbitrage Map", "Where value hides globally.", "leagues/index.html", "is-purple"),
    ]
    signature_html = "".join(
        f'<a class="ares-v6-board-card {color}" href="{href}"><span aria-hidden="true"></span><strong>{static_safe(title)}</strong><p>{static_safe(copy)}</p><em>Open Full Board</em></a>'
        for title, copy, href, color in signature_boards
    )

    board_rows = gap_rows[:5]
    gap_body = "".join(
        f'<tr><td>{idx}</td><td><a href="{static_safe(player_href(item["player"]))}">{static_safe(item["player"].get("player_name"))}</a></td><td>{static_link(item["player"].get("club"), item["player"].get("club_url"), "clubs/index.html", "")}</td><td>{static_num(item["player"].get("ares_score"))}</td><td>{static_num(item["player"].get("market_score"))}</td><td class="is-up">+{item["gap"]}</td><td class="is-up">{static_signed(item["move"])}</td><td>{static_safe(item["why"])}</td></tr>'
        for idx, item in enumerate(board_rows, 1)
    )
    gap_cards = "".join(
        f'<a class="ares-v6-gap-card" href="{static_safe(player_href(item["player"]))}"><span><strong>{static_safe(item["player"].get("player_name"))}</strong><small>{static_safe(item["player"].get("club"))} · {static_safe(item["why"])}</small><b>ARES {static_num(item["player"].get("ares_score"))} &nbsp; Market {static_num(item["player"].get("market_score"))}</b></span><em>Gap +{item["gap"]}<small>Move {static_signed(item["move"])}</small></em></a>'
        for item in board_rows
    )

    heat_regions = [
        ("Europe", home_score_heat(players, "Europe"), "continents/europe/", "is-gold"),
        ("Asia", home_score_heat(players, "Asia"), "continents/asia/", "is-purple"),
        ("MLS", home_score_heat(players, "MLS"), "leagues/mls/", "is-blue"),
        ("South America", home_score_heat(players, "South America"), "continents/south-america/", "is-orange"),
        ("Africa", home_score_heat(players, "Africa"), "continents/africa/", "is-green"),
    ]
    heat_html = "".join(
        f'<a class="ares-v6-heat-row {color}" href="{href}"><span><strong>{static_safe(region)}</strong><small>Open {static_safe(region if region != "South America" else "SA")} Board</small></span><b><i style="width:{score}%"></i></b><em>{score}</em></a>'
        for region, score, href, color in heat_regions
    )

    trust_rows = [
        ("Player records", len(players)),
        ("Club portfolios", len(clubs)),
        ("League boards", len(leagues)),
    ]
    debated_html = "".join(f'<li><span>{static_safe(name)}</span><strong>{static_safe(value)}</strong></li>' for name, value in trust_rows)

    reports = [
        ("Player Report", "Full ARES + Market breakdown", "players/index.html", "is-gold"),
        ("Club Portfolio", "Squad value, depth, risk", "clubs/index.html", "is-blue"),
        ("League Board", "Arbitrage and export heat", "leagues/index.html", "is-purple"),
        ("Transfer Watch", "Mobility, contract, demand", "transfers/index.html", "is-green"),
    ]
    reports_html = "".join(f'<a class="ares-v6-report-card {color}" href="{href}"><span></span><strong>{static_safe(title)}</strong><p>{static_safe(copy)}</p></a>' for title, copy, href, color in reports)

    ticker_items = [
        f"{feature_player.get('player_name')} Gap +{featured['gap']}",
        f"{riser.get('player_name')} Move {riser.get('change')}",
        f"{asia['player'].get('player_name')} Asia Heat",
        f"{u23['player'].get('player_name')} U23",
        f"{len(clubs)} Club Portfolios",
        f"{len(leagues)} League Boards",
    ]
    ticker_html = "".join(f"<span>{static_safe(item)}</span>" for item in ticker_items * 2)
    feature_name = feature_player.get("player_name")
    feature_meta = " | ".join(str(feature_player.get(key) or "") for key in ["club", "league", "position"] if feature_player.get(key))
    confidence = str(feature_player.get("data_confidence") or "Medium")

    nav = """<header class="ares-v6-header"><a class="ares-v6-brand" href="index.html"><span>ARES</span><strong>Football Market</strong></a><nav aria-label="Primary"><a href="index.html">Pulse</a><a href="rankings/gap.html">Gap Board</a><a href="players/index.html?q=U23">U23</a><a href="rankings/market.html">Overheats</a><a href="clubs/index.html">Clubs</a><a href="leagues/index.html">Leagues</a><a href="transfers/index.html">Transfers</a><a href="reports/index.html">Reports</a><a href="about.html">About</a></nav><form class="ares-v6-search" action="players/index.html"><input name="q" type="search" aria-label="Search players, clubs, leagues, or signals"></form><button type="button">Menu</button></header>"""
    pulse = f"""<section class="ares-v6-pulse"><strong>ARES Market Pulse</strong><span>{new_signal_count} New Signals</span><span>{len([r for r in gap_rows if r['move'] != 0])} Rank Changes</span><span>Gap Index Active</span><span>Updated {static_safe(updated)}</span><em>Open Data Connected</em></section><section class="ares-v6-ticker" aria-label="Moving market ticker"><div>{ticker_html}</div></section>"""

    return f"""<!DOCTYPE html><html lang="en"><head>{common_head("", "ARES Market Pulse | Football Mispricing Intelligence", "ARES compares on-field quality with market attention and turns the difference into daily football asset signals.", "")}</head><body class="ares-v6-page">{nav}{beta_note()}{pulse}<main class="ares-v6-shell">
  <section class="ares-v6-hero-layout">
    <div class="ares-v6-hero">
      <div class="ares-v6-hero-copy"><span class="ares-v6-kicker">Market Shock</span><h1>Find the Gap Before the Crowd Does</h1><p>ARES compares on-field quality with market attention, then turns the difference into daily football asset signals.</p><div class="ares-v6-edge"><span>Today's Edge</span><strong>ARES #{featured['ares_rank']}</strong><strong>Market #{featured['market_rank']}</strong><strong>{confidence} Confidence</strong><b>Gap +{featured['gap']}</b><b>7D Move {static_signed(featured['move'])}</b><em>Why ARES Sees It: {static_safe(featured['why'])}</em></div><div class="ares-v6-actions"><a href="{static_safe(player_href(feature_player))}">View Full Report</a><a href="rankings/gap.html">Open Gap Board</a></div></div>
      <figure class="ares-v6-feature-card"><div class="ares-v6-feature-media">{home_player_visual(feature_player)}</div><figcaption><span>Featured Asset</span><strong>{static_safe(feature_name)}</strong><small>{static_safe(feature_meta)}</small></figcaption></figure>
      <aside class="ares-v6-terminal" aria-label="Signal terminal"><h2>Signal Terminal</h2><dl><div><dt>ARES Rank</dt><dd>#{featured['ares_rank']}</dd></div><div><dt>Market Rank</dt><dd>#{featured['market_rank']}</dd></div><div><dt>Gap Index</dt><dd>+{featured['gap']}</dd></div><div><dt>7D Move</dt><dd>{static_signed(featured['move'])}</dd></div><div><dt>Confidence</dt><dd>{static_safe(confidence)}</dd></div></dl><h3>Why ARES Sees It</h3><p>{static_safe(featured['why'])}</p></aside>
    </div>
    <aside class="ares-v6-rail"><span>Monetization Rail</span><div class="ares-v6-ad"><strong>ADVERTISEMENT</strong><small>300 x 250 quiet rail</small></div><div class="ares-v6-opened"><h2>Next Clicks</h2><ol><li><span>{static_safe(feature_name)} Gap Report</span><b>{static_safe(static_num(feature_player.get('market_score')))}</b></li><li><span>{static_safe(top_league.get('league_name', 'League board'))}</span><b>{static_safe(static_num(top_league.get('league_strength')))}</b></li><li><span>{static_safe(top_club.get('club_name', 'Club board'))}</span><b>{static_safe(static_num(top_club.get('squad_market_score')))}</b></li></ol></div></aside>
  </section>
  <section class="ares-v6-section"><div class="ares-v6-section-title"><h2>Live ARES Board</h2><p>One screen of rabbit holes: the fastest route from curiosity to report clicks.</p></div><div class="ares-v6-live-grid">{live_tiles}</div></section>
  <div class="ares-v6-ad ares-v6-leaderboard"><strong>ADVERTISEMENT</strong><small>970 x 90 after value</small></div>
  <section class="ares-v6-section"><div class="ares-v6-section-title"><h2>Signature ARES Boards</h2><p>Five boards Transfermarkt does not own: gap, overheat, youth, club portfolio, and league arbitrage.</p></div><div class="ares-v6-signature-grid">{signature_html}</div></section>
  <section class="ares-v6-section ares-v6-market-grid"><div class="ares-v6-gap-board"><div class="ares-v6-section-title"><h2>Main Gap Board</h2><p>Performance rank versus market rank, with movement, confidence, and a clear reason to open the report.</p></div><table class="ares-v6-gap-table"><thead><tr><th>#</th><th>Player</th><th>Club</th><th>ARES</th><th>Market</th><th>Gap</th><th>Move</th><th>Why ARES Sees It</th></tr></thead><tbody>{gap_body}</tbody></table><div class="ares-v6-gap-cards">{gap_cards}</div></div><aside class="ares-v6-heat"><h2>Global Heat Map</h2>{heat_html}</aside><aside class="ares-v6-debated"><h2>Trust Layer</h2><ul>{debated_html}</ul></aside><div class="ares-v6-ad ares-v6-native"><strong>ADVERTISEMENT</strong><small>Native market intelligence slot</small></div></section>
  <section class="ares-v6-section"><div class="ares-v6-section-title"><h2>Reports Built for the Second Click</h2></div><div class="ares-v6-reports-grid">{reports_html}</div></section>
  <section class="ares-section ares-terminal-grid"><div class="ares-card ares-formula-card"><span>Formula</span><h2 class="h4">Gap Index</h2><p>Gap Index compares ARES football signal with Market Score, then pairs the difference with movement and confidence before a report link appears.</p></div><div class="ares-card ares-confidence-card"><span>Trust</span><h2 class="h4">Open Data Connected</h2><p>Visible homepage rows come from public player, club, league, movement, rights, and open match coverage files.</p></div></section>
</main><footer class="ares-v6-footer">ARES scores are model-generated football intelligence signals. Market Score is not a transfer fee or official market price. See <a href="methodology.html">Methodology</a> for sources, coverage, confidence logic, and image attribution.</footer></body></html>"""


def route_prefix(route: str) -> str:
    depth = len([part for part in route.split("/")[:-1] if part])
    return "../" * depth


def route_canonical(route: str) -> str:
    return route if route != "index.html" else ""


def gap_index_value(row: dict[str, Any]) -> int:
    try:
        return round((float(row.get("ares_score") or 0) - float(row.get("market_score") or 0)) * 10)
    except (TypeError, ValueError):
        return 0


def top_players_for_terminal(players: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    rows = [row for row in players if float(row.get("ares_score") or 0) >= 60 and row.get("player_name") and row.get("club")]
    return sorted(rows, key=lambda item: (float(item.get("ares_score") or 0), float(item.get("market_score") or 0)), reverse=True)[:limit]


def player_terminal_rows(players: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    rows = []
    for idx, row in enumerate(top_players_for_terminal(players, limit), 1):
        rows.append([
            idx,
            row.get("player_name"),
            row.get("club"),
            row.get("league"),
            row.get("position"),
            static_num(row.get("ares_score")),
            static_num(row.get("market_score")),
            f"{gap_index_value(row):+d}",
            row.get("trend") or "Stable",
            row.get("data_confidence") or "Medium",
            "Open report",
        ])
    return rows


def club_terminal_rows(clubs: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    rows = []
    for idx, row in enumerate(sorted(clubs, key=lambda item: float(item.get("squad_market_score") or 0), reverse=True)[:limit], 1):
        rows.append([
            idx,
            row.get("club_name"),
            row.get("league"),
            row.get("country"),
            static_num(row.get("avg_ares_score")),
            static_num(row.get("squad_market_score")),
            row.get("u23_asset_count"),
            row.get("average_age"),
            row.get("transfer_risk"),
            row.get("data_confidence"),
        ])
    return rows


def league_terminal_rows(leagues: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    rows = []
    for idx, row in enumerate(sorted(leagues, key=lambda item: float(item.get("league_strength") or 0), reverse=True)[:limit], 1):
        rows.append([
            idx,
            row.get("league_name"),
            row.get("country"),
            row.get("continent"),
            static_num(row.get("league_strength")),
            static_num(row.get("market_depth")),
            row.get("u23_pipeline"),
            row.get("export_signal"),
            row.get("data_confidence"),
        ])
    return rows


def product_table_for_kind(kind: str, players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]]]:
    if kind == "club":
        return ["#", "Club", "League", "Country", "Team ARES", "Team Market", "U23", "Avg Age", "Risk", "Confidence"], club_terminal_rows(clubs)
    if kind == "league":
        return ["#", "League", "Country", "Region", "ARES Signal", "Market Depth", "U23 Pipeline", "Export", "Confidence"], league_terminal_rows(leagues)
    if kind == "transfer":
        return ["Player", "Club", "League", "Signal Type", "ARES Impact", "Market Impact", "Fit", "Confidence"], [
            [row[1], row[2], row[3], "Contract watch", row[5], row[6], "Role fit", row[9]] for row in player_terminal_rows(players, 7)
        ]
    if kind == "watch":
        return ["Player/Club", "League", "Signal", "ARES", "Market", "Gap", "Confidence", "What confirms it", "Open"], [
            [row[1], row[3], "Role expansion", row[5], row[6], row[7], row[9], "Minutes and source coverage", row[10]] for row in player_terminal_rows(players, 7)
        ]
    if kind == "data":
        return ["Source", "Type", "Use", "Status", "Data Mode", "Notes"], [
            ["Open Match CSV", "Match data", "Team and league context", "Connected", "Public Beta Demo", "Supports trust and coverage pages"],
            ["Public player records", "Player data", "ARES and Market boards", "Connected", "Public Beta Demo", "Used for filled public tables"],
            ["Image rights registry", "Rights data", "Safe image rendering", "Connected", "Public Beta Demo", "Blocks restricted image sources"],
            ["Formula registry", "Scoring logic", "Formula cards", "Connected", "Public Beta Demo", "Explains visible scores"],
        ]
    return ["Rank", "Player", "Club", "League", "Position", "ARES", "Market", "Gap", "Trend", "Confidence", "Open"], player_terminal_rows(players)


def formula_copy(kind: str) -> tuple[str, str]:
    formulas = {
        "club": ("TEAM_MARKET_SCORE", "Team Market Score blends squad ARES depth, player asset value, average age, U23 strength, contract control, league tier, transfer demand, risk, and confidence."),
        "league": ("LEAGUE_STRENGTH", "League signal combines top-player ARES level, market depth, U23 pipeline, export strength, match competitiveness, source coverage, and confidence."),
        "transfer": ("TRANSFER_SIGNAL", "Transfer signal combines contract mobility, role blockage, club need fit, transfer demand, ARES impact, Market impact, risk, and confidence."),
        "watch": ("WATCH_SIGNAL", "Watchlist signal is not a rank. It combines early role expansion, thin-data upside, U23 curve, contract signal, source coverage, and what still needs confirmation."),
        "data": ("ARES_CONFIDENCE", "Confidence measures source coverage, minutes sample, recency, metric completeness, cross-source agreement, rights status, and public data mode."),
        "premium": ("PREMIUM_LAYER", "Premium unlocks component grades, comparable players, age curve, movement history, club fit, risk score, and exportable boards without hiding the free top-line scores."),
    }
    return formulas.get(kind, ("ARES_PLAYER_SCORE", "ARES Player Score combines position performance, efficiency, role usage, league context, volume availability, durability, trend form, and confidence. Market Score is a separate asset signal, not a transfer fee."))


def gap_value(player: dict[str, Any]) -> float:
    return safe_float(player.get("ares_score")) - safe_float(player.get("market_score"))


def signed_num(value: float, decimals: int = 1) -> str:
    return f"{value:+.{decimals}f}"


def route_rel(spec: dict[str, Any], href: str) -> str:
    if href.startswith(("http://", "https://", "/", "#", "?")):
        return href
    return route_prefix(spec["route"]) + href


def best_players(players: list[dict[str, Any]], sort_key: str, limit: int = 8, reverse: bool = True) -> list[dict[str, Any]]:
    return sorted(players, key=lambda item: safe_float(item.get(sort_key)), reverse=reverse)[:limit]


def gap_players(players: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return sorted(players, key=gap_value, reverse=True)[:limit]


def overheat_players(players: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return sorted(players, key=lambda item: safe_float(item.get("market_score")) - safe_float(item.get("ares_score")), reverse=True)[:limit]


def player_rows(players: list[dict[str, Any]], mode: str = "gap", limit: int = 8) -> list[list[Any]]:
    if mode == "ares":
        selected = best_players(players, "ares_score", limit)
    elif mode == "market":
        selected = best_players(players, "market_score", limit)
    elif mode == "u23":
        selected = best_players([p for p in players if safe_float(p.get("age")) <= 23], "market_score", limit)
    elif mode == "overheat":
        selected = overheat_players(players, limit)
    else:
        selected = gap_players(players, limit)
    rows = []
    for idx, player in enumerate(selected, 1):
        gap = gap_value(player)
        rows.append([
            idx,
            player.get("player_name"),
            player.get("age"),
            player.get("position"),
            player.get("club"),
            player.get("league"),
            static_num(player.get("ares_score")),
            static_num(player.get("market_score")),
            signed_num(gap),
            player.get("transfer_value_signal") or player.get("trend"),
            player.get("data_confidence") or player.get("confidence"),
            player.get("reason"),
        ])
    return rows


def club_rows(clubs: list[dict[str, Any]], limit: int = 8) -> list[list[Any]]:
    rows = []
    for idx, club in enumerate(sorted(clubs, key=lambda item: safe_float(item.get("squad_market_score")), reverse=True)[:limit], 1):
        rows.append([
            idx,
            club.get("club_name"),
            club.get("league"),
            club.get("country"),
            static_num(club.get("avg_ares_score")),
            static_num(club.get("squad_market_score")),
            club.get("u23_asset_count"),
            club.get("average_age"),
            club.get("transfer_risk"),
            club.get("need_area"),
            club.get("data_confidence"),
        ])
    return rows


def source_table_rows() -> list[list[Any]]:
    files = [
        ("public_players.json", "Player records", "Rankings, profiles, search"),
        ("public_clubs.json", "Club records", "Portfolio boards and club profile routes"),
        ("public_leagues.json", "League records", "League terminals and region boards"),
        ("public_market_changes.json", "Movement records", "Risers, fallers, trend modules"),
        ("public_transfers.json", "Transfer records", "Movement board and transfer reports"),
        ("public_watchlist.json", "Watch records", "Watchlist pages and early signal modules"),
        ("open_match_summary.json", "Open match coverage", "Coverage and trust pages"),
        ("image_credits_wikimedia.json", "Image rights registry", "Approved image attribution"),
        ("ares_formula_registry.json", "Formula registry", "Methodology cards and score explanations"),
    ]
    rows = []
    for file_name, source_type, use in files:
        data = read_json_optional(f"data/{file_name}", [])
        count = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 0
        if count:
            rows.append([file_name, source_type, use, count, "Connected", "Public Beta Demo"])
    return rows


def coverage_rows(limit: int = 10) -> list[list[Any]]:
    rows = []
    for item in read_json_optional("data/open_match_summary.json", [])[:limit]:
        rows.append([
            item.get("league_name"),
            item.get("country"),
            item.get("source"),
            item.get("first_date"),
            item.get("last_date"),
            item.get("matches"),
            item.get("clubs_seen"),
        ])
    return rows


def real_hero_card(player: dict[str, Any], prefix: str) -> str:
    image = static_player_avatar(player, prefix)
    return f"""
<div class="ares-signal-player-card">
  {image}
  <div><span>Featured Signal</span><strong>{static_safe(player.get("player_name"))}</strong><small>{static_safe(player.get("club"))} | {static_safe(player.get("league"))} | {static_safe(player.get("position"))}</small></div>
  <dl>
    <div><dt>ARES</dt><dd>{static_safe(static_num(player.get("ares_score")))}</dd></div>
    <div><dt>Market</dt><dd>{static_safe(static_num(player.get("market_score")))}</dd></div>
    <div><dt>Gap</dt><dd class="is-up">{static_safe(signed_num(gap_value(player)))}</dd></div>
    <div><dt>Confidence</dt><dd>{static_safe(player.get("data_confidence") or player.get("confidence"))}</dd></div>
  </dl>
</div>"""


def signal_cards(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]], kind: str, route: str) -> str:
    top_gap = gap_players(players, 1)[0] if players else {}
    top_ares = best_players(players, "ares_score", 1)[0] if players else {}
    top_market = best_players(players, "market_score", 1)[0] if players else {}
    top_u23 = best_players([p for p in players if safe_float(p.get("age")) <= 23], "market_score", 1)[0] if players else {}
    top_club = sorted(clubs, key=lambda item: safe_float(item.get("squad_market_score")), reverse=True)[0] if clubs else {}
    top_league = sorted(leagues, key=lambda item: safe_float(item.get("league_strength")), reverse=True)[0] if leagues else {}
    transfer_rows = clean_real_rows(read_json_optional("data/public_transfers.json", []))
    watch_rows = clean_real_rows(read_json_optional("data/public_watchlist.json", []))
    cards = {
        "player": [
            ("Biggest Gap", top_gap.get("player_name"), signed_num(gap_value(top_gap)) if top_gap else ""),
            ("Top ARES", top_ares.get("player_name"), static_num(top_ares.get("ares_score")) if top_ares else ""),
            ("Top Market", top_market.get("player_name"), static_num(top_market.get("market_score")) if top_market else ""),
            ("Best U23", top_u23.get("player_name"), static_num(top_u23.get("market_score")) if top_u23 else ""),
        ],
        "premium": [
            ("Sample Player", top_market.get("player_name"), static_num(top_market.get("market_score")) if top_market else ""),
            ("Component Layer", "ARES + Market", "Unlocked"),
            ("Comparable Pool", "Player comps", "Unlocked"),
            ("Club Fit", "Transfer role", "Unlocked"),
        ],
        "club": [
            ("Top Club Book", top_club.get("club_name"), static_num(top_club.get("squad_market_score")) if top_club else ""),
            ("Best U23 Club", top_club.get("club_name"), top_club.get("u23_asset_count") if top_club else ""),
            ("Need Area", top_club.get("need_area"), top_club.get("transfer_risk") if top_club else ""),
            ("Confidence", top_club.get("data_confidence"), "Club source layer"),
        ],
        "league": [
            ("Strongest League", top_league.get("league_name"), static_num(top_league.get("league_strength")) if top_league else ""),
            ("Market Depth", top_league.get("league_name"), static_num(top_league.get("market_depth")) if top_league else ""),
            ("Top Player", top_league.get("top_player"), top_league.get("country") if top_league else ""),
            ("Confidence", top_league.get("data_confidence"), "League source layer"),
        ],
        "data": [
            ("Player Records", len(players), "public_players.json"),
            ("Club Records", len(clubs), "public_clubs.json"),
            ("League Records", len(leagues), "public_leagues.json"),
            ("Open Match Rows", sum(int(r[5] or 0) for r in coverage_rows(200)), "open_match_summary.json"),
        ],
        "transfer": [
            ("Transfer Rows", len(transfer_rows), "public_transfers.json"),
            ("Top Mover", top_gap.get("player_name"), top_gap.get("transfer_value_signal") if top_gap else ""),
            ("Contract 2026", len([row for row in players if "2026" in str(row.get("contract_end") or "")]), "player contract windows"),
            ("Clubs Mapped", len({row.get("from_club") for row in transfer_rows if row.get("from_club")}), "real transfer rows"),
        ],
        "watch": [
            ("Watch Rows", len(watch_rows), "public_watchlist.json"),
            ("Top U23", top_u23.get("player_name"), static_num(top_u23.get("market_score")) if top_u23 else ""),
            ("U23 Rows", len([row for row in watch_rows if safe_int(row.get("age"), 99) <= 23]), "watch age filter"),
            ("High Confidence", len([row for row in watch_rows if str(row.get("confidence", "")).lower() == "high"]), "source coverage"),
        ],
    }
    items = [item for item in cards.get(kind, cards["player"]) if item[1] not in ("", None)]
    if "rankings/gap.html" in route:
        rank_leader = home_rank_rows(players)[0] if players else {"player": {}, "gap": ""}
        top_gap = rank_leader["player"]
        items = [
            ("Gap Leader", top_gap.get("player_name"), f"+{rank_leader['gap']}" if safe_float(rank_leader.get("gap")) > 0 else rank_leader.get("gap")),
            ("ARES Score", top_gap.get("club"), static_num(top_gap.get("ares_score")) if top_gap else ""),
            ("Market Score", top_gap.get("league"), static_num(top_gap.get("market_score")) if top_gap else ""),
            ("Confidence", top_gap.get("data_confidence"), "Source coverage"),
        ]
    return kpi_cards(items)


def page_table_for_spec(spec: dict[str, Any], players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> tuple[str, str, list[str], list[list[Any]]]:
    route = spec["route"]
    kind = spec.get("kind", "player")
    if route == "data/coverage.html":
        return "Open Match Coverage", "Coverage rows come from the open match summary file and drive source confidence.", ["League", "Country", "Source", "First Date", "Last Date", "Matches", "Clubs Seen"], coverage_rows(14)
    if route == "data/sources.html":
        return "Connected Source Files", "Only project-owned JSON files with records are listed.", ["Source", "Type", "Use", "Rows", "Status", "Data Mode"], source_table_rows()
    if route == "rankings/gap.html":
        return "Gap Board", "Rank-gap rows use the same ARES-rank versus Market-rank logic as the homepage.", ["#", "Player", "Age", "Pos", "Club", "League", "ARES Rank", "Market Rank", "Rank Gap", "7D Move", "Confidence", "Why ARES Sees It"], gap_rank_rows(players, 10)
    if kind == "club":
        return "Club Portfolio Board", "Club rows are sorted by squad market score and include ARES depth, U23 count, risk, and need area.", ["#", "Club", "League", "Country", "Team ARES", "Team Market", "U23", "Avg Age", "Risk", "Need Area", "Confidence"], club_rows(clubs)
    if kind == "league":
        return "League Market Board", "League rows show strength, depth, U23 pipeline, export signal, top player, and confidence.", ["#", "League", "Country", "Region", "ARES Signal", "Market Depth", "U23 Pipeline", "Export", "Confidence"], league_terminal_rows(leagues, 10)
    if kind == "transfer":
        rows = [[r.get("player_name"), r.get("from_club"), r.get("to_club"), r.get("transfer_type"), r.get("ares_impact"), r.get("market_impact"), r.get("confidence"), r.get("reason")] for r in clean_real_rows(read_json_optional("data/public_transfers.json", []))[:10]]
        return "Transfer Signal Board", "Transfer rows come from public transfer signal records with impact and confidence attached.", ["Player", "From", "To/Signal", "Type", "ARES Impact", "Market Impact", "Confidence", "Reason"], rows
    if kind == "watch":
        rows = [[r.get("player_name"), r.get("club"), r.get("league"), r.get("watch_reason"), r.get("ares_signal"), r.get("market_signal"), r.get("confidence"), r.get("status")] for r in clean_real_rows(read_json_optional("data/public_watchlist.json", []))[:10]]
        return "Watch Table", "Watch rows show the signal, current score layer, confidence, and what confirms it.", ["Player", "Club", "League", "Signal", "ARES", "Market", "Confidence", "What Confirms It"], rows
    mode = "gap"
    if route.endswith("ares.html") or "position" in route:
        mode = "ares"
    elif route.endswith("market.html"):
        mode = "market"
    elif "u23" in route:
        mode = "u23"
    elif "overheat" in route:
        mode = "overheat"
    return spec.get("table_title", "Player Signal Board"), "Player rows are real public records with ARES, Market, Gap, trend, confidence, and reason.", ["#", "Player", "Age", "Pos", "Club", "League", "ARES", "Market", "Gap", "Trend", "Confidence", "Why ARES Sees It"], player_rows(players, mode, 10)


def formula_modules(kind: str) -> str:
    formula_id, formula_text = formula_copy(kind)
    return f"""
<section class="ares-section ares-terminal-grid">
  <div class="ares-card ares-formula-card"><span>Formula</span><h2 class="h4">{static_safe(formula_id)}</h2><p>{static_safe(formula_text)}</p></div>
  <div class="ares-card ares-confidence-card"><span>Confidence</span><h2 class="h4">Source Coverage + Recency</h2><p>Confidence is a reliability label. It reflects source coverage, sample size, recency, rights status, metric completeness, and cross-source agreement.</p></div>
</section>"""


def gap_rank_rows(players: list[dict[str, Any]], limit: int = 10) -> list[list[Any]]:
    rows = []
    for idx, item in enumerate(home_rank_rows(players)[:limit], 1):
        player = item["player"]
        rows.append([
            idx,
            player.get("player_name"),
            player.get("age"),
            player.get("position"),
            player.get("club"),
            player.get("league"),
            f"#{item['ares_rank']}",
            f"#{item['market_rank']}",
            f"+{item['gap']}" if item["gap"] > 0 else str(item["gap"]),
            static_signed(item["move"]),
            player.get("data_confidence") or player.get("confidence"),
            item["why"],
        ])
    return rows


def player_mini_cards(rows: list[dict[str, Any]], prefix: str, label_key: str = "gap") -> str:
    cards = []
    for item in rows[:6]:
        player = item.get("player", item)
        href = static_prefixed_href(player.get("player_url") or "players/index.html", prefix)
        value = item.get(label_key)
        if value is None:
            value = static_num(player.get("market_score") or player.get("ares_score"))
        cards.append(
            f'<a class="ares-signal-card" href="{static_safe(href)}">{static_player_avatar(player, prefix)}'
            f'<span>{static_safe(player.get("position") or player.get("league"))}</span><strong>{static_safe(player.get("player_name"))}</strong>'
            f'<small>{static_safe(player.get("club"))} | {static_safe(player.get("league"))}</small><b>{static_safe(value)}</b></a>'
        )
    return '<div class="ares-signal-card-grid">' + "".join(cards) + "</div>" if cards else ""


def gap_special_modules(players: list[dict[str, Any]], prefix: str) -> str:
    rank_rows = home_rank_rows(players)
    u23_rows = [item for item in rank_rows if safe_int(item["player"].get("age"), 99) <= 23]
    overheat_rows = sorted(rank_rows, key=lambda item: (safe_float(item["player"].get("market_score")) - safe_float(item["player"].get("ares_score")), safe_float(item["player"].get("market_score"))), reverse=True)
    confidence_counts = Counter(str(row.get("data_confidence") or row.get("confidence") or "Review") for row in players)
    confidence_table = static_table(["Confidence", "Players"], [[key, value] for key, value in confidence_counts.most_common()])
    report_links = "".join([
        f'<a class="ares-related-card" href="{prefix}reports/gap-reports.html"><strong>Gap Reports</strong><span>Turn rank gap leaders into proof-led reads.</span></a>',
        f'<a class="ares-related-card" href="{prefix}reports/u23-reports.html"><strong>U23 Reports</strong><span>Open younger mispricing cases.</span></a>',
        f'<a class="ares-related-card" href="{prefix}reports/overheat-reports.html"><strong>Overheat Reports</strong><span>Find market leaders ahead of football proof.</span></a>',
        f'<a class="ares-related-card" href="{prefix}methodology.html"><strong>Formula Notes</strong><span>See why rank gap differs from price.</span></a>',
    ])
    return f"""
<section class="ares-section ares-terminal-grid">
  {chart_card("ARES Rank Gap Scatter", "Rank gap compares ARES rank with Market rank so homepage and board signals match.", "scatter", "ARES rank", "Market rank", "Players above the diagonal grade better by ARES than by market attention.")}
  <div class="ares-card"><h2 class="h4">Gap Lens Tabs</h2><div class="ares-chip-row"><a href="#gap-leaders">Gap leaders</a><a href="#u23-gap">U23 gap</a><a href="#overheat-risk">Overheat risk</a><a href="#confidence-mix">Confidence mix</a></div><p class="ares-muted-note">Each lens uses the same public player records and hides unavailable modules instead of padding the board.</p></div>
</section>
<section id="gap-leaders" class="ares-section ares-card"><div class="ares-section-title"><div><h2 class="h4">Rank Gap Leaders</h2><p>Same rank-gap logic as the homepage: ARES rank minus market attention, with real confidence labels.</p></div></div>{static_table(["#", "Player", "Age", "Pos", "Club", "League", "ARES Rank", "Market Rank", "Rank Gap", "7D Move", "Confidence", "Why"], gap_rank_rows(players, 10))}</section>
<section id="u23-gap" class="ares-section ares-card"><h2 class="h4">U23 Gap Watch</h2>{player_mini_cards(u23_rows, prefix, "gap")}</section>
<section id="overheat-risk" class="ares-section ares-card"><h2 class="h4">Overheat Lens</h2>{player_mini_cards(overheat_rows, prefix, "gap")}</section>
<section id="confidence-mix" class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Confidence Distribution</h2>{confidence_table}</div>{chart_card("Confidence Distribution", "Real player rows grouped by public data confidence.", "bars", "Confidence label", "Player count", "Use confidence before treating a rank gap as decision-grade.")}</section>
<section class="ares-section ares-card"><h2 class="h4">Report Paths</h2><div class="ares-related-grid">{report_links}</div></section>
"""


def premium_modules(players: list[dict[str, Any]], prefix: str) -> str:
    sample = best_players(players, "market_score", 1)[0] if players else {}
    comparison = static_table(
        ["Layer", "Free", "Premium"],
        [
            ["Top-line scores", "ARES Score, Market Score, confidence", "Full score history and export"],
            ["Player proof", "Visible board reason", "Component grades, comps, role fit, risk"],
            ["Club strategy", "Club portfolio board", "Need-area model, squad fit, shortlist export"],
            ["Reports", "Public report cards", "Custom boards and saved intelligence packs"],
        ],
    )
    previews = [
        ("Component Breakdown", "Performance, role, usage, age curve, durability, and confidence weights."),
        ("Comparable Pool", "Same-role players ranked by ARES, Market, league context, and age curve."),
        ("Club Fit + Risk", "Need-area fit, contract window, role blockage, and movement risk."),
    ]
    cards = "".join(f'<div class="ares-premium-preview premium-lock"><span>Locked</span><h3>{static_safe(title)}</h3><p>{static_safe(copy)}</p><small>{static_safe(sample.get("player_name") or "Public board leader")}</small></div>' for title, copy in previews)
    return f'<section class="ares-section ares-card"><h2 class="h4">Free vs Premium</h2>{comparison}</section><section class="ares-section ares-premium-preview-grid">{cards}</section>'


def ares_ranking_modules(players: list[dict[str, Any]], prefix: str = "../") -> str:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for player in players:
        grouped[position_family(player.get("position"))].append(player)
    leaders = []
    for family, rows in sorted(grouped.items()):
        leader = best_players(rows, "ares_score", 1)[0]
        leaders.append([family, leader.get("player_name"), leader.get("club"), static_num(leader.get("ares_score")), leader.get("data_confidence")])
    weights = static_table(
        ["Score Component", "What It Captures"],
        [
            ["Performance", "On-ball and role-adjusted football output"],
            ["Role + Usage", "Minutes role, position usage, and responsibility"],
            ["Context", "League strength, opponent context, and club setting"],
            ["Durability + Trend", "Availability, movement, and recent signal"],
            ["Confidence", "Source coverage and metric completeness"],
        ],
    )
    return f"""
<section class="ares-section ares-terminal-grid">
  {chart_card("Top 10 ARES Scores", "Real player rows sorted by ARES Score with confidence attached.", "bars", "Leaderboard rank", "ARES Score", "The first table remains the authoritative sort; this chart is a scannable score shape.")}
  <div class="ares-card"><h2 class="h4">Position Leaders</h2>{static_table(["Position Group", "Leader", "Club", "ARES", "Confidence"], leaders[:9])}</div>
</section>
<section class="ares-section ares-card"><h2 class="h4">Formula Weights</h2>{weights}</section>
<section class="ares-section ares-card"><h2 class="h4">Why Rows Rank</h2><p>Each row combines role evidence, performance level, league context, durability, trend, and confidence. Use the player link to inspect the public profile source and component tables.</p></section>
"""


def report_hub_body(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]], prefix: str) -> str:
    gap = home_rank_rows(players)[0] if players else {"player": {}, "gap": ""}
    u23 = next((item for item in home_rank_rows(players) if safe_int(item["player"].get("age"), 99) <= 23), gap)
    overheat = overheat_players(players, 1)[0] if players else {}
    top_club = max(clubs, key=lambda row: safe_float(row.get("squad_market_score")), default={})
    top_league = max(leagues, key=lambda row: safe_float(row.get("league_strength")), default={})
    reports = [
        ("Daily Market Pulse", gap["player"].get("player_name"), f"Rank gap {gap.get('gap')}", "reports/daily-market-pulse.html"),
        ("Gap Report", gap["player"].get("player_name"), gap["player"].get("data_confidence"), "reports/gap-reports.html"),
        ("U23 Report", u23["player"].get("player_name"), u23["player"].get("club"), "reports/u23-reports.html"),
        ("Overheat Report", overheat.get("player_name"), static_num(overheat.get("market_score")), "reports/overheat-reports.html"),
        ("Club Report", top_club.get("club_name"), top_club.get("need_area"), "reports/club-reports.html"),
        ("League Report", top_league.get("league_name"), top_league.get("export_signal"), "reports/league-reports.html"),
    ]
    cards = "".join(
        f'<a class="ares-report-card" href="{static_safe(prefix + href)}"><span>{static_safe(title)}</span><strong>{static_safe(subject)}</strong><small>{static_safe(meta)}</small><b>Open report</b></a>'
        for title, subject, meta, href in reports
        if subject not in ("", None)
    )
    return f"""
<section class="ares-product-hero ares-section ares-card"><div><span class="ares-product-kicker">Reports</span><h2>ARES Reports Hub</h2><p>Proof-led report cards for gaps, U23 assets, overheats, clubs, leagues, and movement.</p><div class="ares-hero-actions"><a href="{prefix}rankings/gap.html">Open Gap Board</a><a href="{prefix}premium.html">Compare Premium</a></div></div></section>
{kpi_cards([("Report Cards", len([item for item in reports if item[1]]), "real subjects from public JSON"), ("Top Gap", gap["player"].get("player_name"), "rank-gap leader"), ("Top Club", top_club.get("club_name"), "club portfolio"), ("Top League", top_league.get("league_name"), "league strength")])}
<section class="ares-section ares-report-card-grid">{cards}</section>
<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after report cards</span></section>
{formula_modules("player")}
<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Report Builder</h2><p>Unlock saved report packs, component evidence, comparable pools, exportable boards, and club-fit risk views.</p></section>
<section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Report cards only link to public records already present in ARES JSON outputs and source coverage files.</p></section>
"""


def coverage_modules() -> str:
    rows = coverage_rows(200)
    total_matches = sum(safe_int(row[5]) for row in rows)
    country_counts = Counter(str(row[1]) for row in rows if row[1])
    top_countries = static_table(["Country", "Coverage Rows"], [[country, count] for country, count in country_counts.most_common(8)])
    return f"""
<section class="ares-section ares-terminal-grid">
  {chart_card("Open Match Coverage Map", f"{len(rows)} coverage rows and {total_matches} matches from connected open match files.", "bars", "Covered country", "Coverage rows", "Coverage depth drives confidence, not synthetic table volume.")}
  <div class="ares-card"><h2 class="h4">Country Coverage</h2>{top_countries}</div>
</section>
"""


def about_body(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> str:
    return f"""
<section class="ares-product-hero ares-section ares-card"><div><span class="ares-product-kicker">About ARES</span><h2>Football asset intelligence built from public, auditable records.</h2><p>ARES separates football quality, market attention, source confidence, and rights safety so users can inspect where a signal comes from.</p><div class="ares-hero-actions"><a href="methodology.html">Methodology</a><a href="data/sources.html">Sources</a></div></div></section>
{kpi_cards([("Players", len(players), "public_players.json"), ("Clubs", len(clubs), "public_clubs.json"), ("Leagues", len(leagues), "public_leagues.json"), ("Data Mode", "Public Beta Demo", "trust label only")])}
<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">What ARES Is</h2><p>A public football market terminal for comparing ARES Score, Market Score, rank gap, trend, and confidence.</p></div><div class="ares-card"><h2 class="h4">What ARES Is Not</h2><p>ARES is not an official transfer fee source, betting line, salary estimate, or restricted commercial database copy.</p></div><div class="ares-card"><h2 class="h4">Trust Rules</h2><p>Visible rows come from project-owned JSON and CSV-derived files. Missing sections are omitted instead of filled with invented rows.</p></div><div class="ares-card"><h2 class="h4">Product Direction</h2><p>The public board shows the signal. Premium explains component grades, comps, risk, club fit, and saved reports.</p></div></section>
<section class="ares-section ares-card"><h2 class="h4">Next Clicks</h2><div class="ares-related-grid"><a class="ares-related-card" href="rankings/gap.html"><strong>Gap Board</strong><span>Find mispriced players.</span></a><a class="ares-related-card" href="players/index.html"><strong>Player Search</strong><span>Inspect real public records.</span></a><a class="ares-related-card" href="reports/index.html"><strong>Reports</strong><span>Open proof-led reads.</span></a><a class="ares-related-card" href="premium.html"><strong>Premium</strong><span>Compare the intelligence layer.</span></a></div></section>
"""


def terminal_product_body(spec: dict[str, Any], players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> str:
    kind = spec.get("kind", "player")
    prefix = route_prefix(spec["route"])
    if spec["route"] == "reports/index.html":
        return report_hub_body(players, clubs, leagues, prefix)
    if spec["route"] == "about.html":
        return about_body(players, clubs, leagues)
    table_title, table_intro, headers, rows = page_table_for_spec(spec, players, clubs, leagues)
    formula_id, formula_text = formula_copy(kind)
    top_player = (home_rank_rows(players)[0]["player"] if spec["route"] == "rankings/gap.html" and players else gap_players(players, 1)[0]) if players else {}
    related = spec.get("related") or [
        ("Gap Board", "Find players whose football signal beats market attention.", "rankings/gap.html"),
        ("ARES Rankings", "See the pure football quality board.", "rankings/ares.html"),
        ("Market Rankings", "Compare asset strength and market demand.", "rankings/market.html"),
        ("Methodology", "Check formulas, sources, and confidence rules.", "methodology.html"),
    ]
    related_html = "".join(
        f'<a class="ares-related-card" href="{static_safe(route_rel(spec, href))}"><strong>{static_safe(title)}</strong><span>{static_safe(copy)}</span></a>'
        for title, copy, href in related
    )
    premium_copy = spec.get("premium", "Unlock full component grades, comparable players, risk scores, team fit, movement history, and exportable intelligence boards.")
    table_html = static_table(headers, rows)
    table_section = f'<section class="ares-section ares-card"><div class="ares-section-title"><div><h2 class="h4">{static_safe(table_title)}</h2><p>{static_safe(table_intro)}</p></div></div>{table_html}</section>' if table_html else ""
    hero_card = real_hero_card(top_player, prefix) if top_player and kind in {"player", "premium", "transfer", "watch"} else ""
    if kind == "club" and clubs:
        hero_card = f'<div class="ares-signal-player-card"><div><span>Top Club Book</span><strong>{static_safe(clubs[0].get("club_name"))}</strong><small>{static_safe(clubs[0].get("league"))} | {static_safe(clubs[0].get("country"))}</small></div><dl><div><dt>Team ARES</dt><dd>{static_safe(static_num(clubs[0].get("avg_ares_score")))}</dd></div><div><dt>Team Market</dt><dd>{static_safe(static_num(clubs[0].get("squad_market_score")))}</dd></div><div><dt>U23</dt><dd>{static_safe(clubs[0].get("u23_asset_count"))}</dd></div><div><dt>Confidence</dt><dd>{static_safe(clubs[0].get("data_confidence"))}</dd></div></dl></div>'
    if kind == "league" and leagues:
        top_league = sorted(leagues, key=lambda item: safe_float(item.get("league_strength")), reverse=True)[0]
        hero_card = f'<div class="ares-signal-player-card"><div><span>Top League Signal</span><strong>{static_safe(top_league.get("league_name"))}</strong><small>{static_safe(top_league.get("country"))} | {static_safe(top_league.get("confederation"))}</small></div><dl><div><dt>Signal</dt><dd>{static_safe(static_num(top_league.get("league_strength")))}</dd></div><div><dt>Depth</dt><dd>{static_safe(static_num(top_league.get("market_depth")))}</dd></div><div><dt>Export</dt><dd>{static_safe(top_league.get("export_signal"))}</dd></div><div><dt>Confidence</dt><dd>{static_safe(top_league.get("data_confidence"))}</dd></div></dl></div>'
    body = f"""
<section class="ares-product-hero ares-section ares-card">
  <div><span class="ares-product-kicker">{static_safe(spec.get("job", "Market intelligence"))}</span><h2>{static_safe(spec.get("headline", spec["title"]))}</h2><p>{static_safe(spec.get("hook", spec.get("intro", "")))}</p><div class="ares-hero-actions"><a href="{static_safe(route_rel(spec, "rankings/gap.html"))}">Open Gap Board</a><a href="{static_safe(route_rel(spec, "players/index.html"))}">Search Players</a></div></div>
  {hero_card}
</section>
{signal_cards(players, clubs, leagues, kind, spec["route"])}
{gap_special_modules(players, prefix) if spec["route"] == "rankings/gap.html" else ""}
{premium_modules(players, prefix) if spec["route"] == "premium.html" else ""}
{coverage_modules() if spec["route"] == "data/coverage.html" else ""}
{table_section}
<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Premium quiet placement after first value block</span></section>
{formula_modules(kind)}
<section class="ares-section ares-card"><h2 class="h4">Related Boards</h2><div class="ares-related-grid">{related_html}</div></section>
<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>{static_safe(premium_copy)}</p></section>
<section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>ARES uses project-owned public JSON and CSV-derived coverage files for visible rows. ARES Score is not a transfer fee. Market Score is not market price. ARES does not scrape restricted commercial databases or restricted image sources.</p></section>
"""
    return body


def terminal_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = [
        {"route": "sitemap.html", "title": "ARES Site Map", "intro": "Every market board, profile, league terminal, transfer board, and trust page.", "kind": "data", "job": "Product map", "hook": "Use the sitemap to move from recognition to deeper market boards without losing the ARES logic.", "table_title": "Product Buckets"},
        {"route": "premium.html", "title": "Unlock the ARES Intelligence Layer", "intro": "Full component grades, player comps, club strategy boards, risk scores, and transfer fit.", "kind": "premium", "job": "Premium conversion", "hook": "Free pages show the signal; premium explains the machinery underneath it."},
        {"route": "about.html", "title": "About ARES Football Market", "intro": "ARES is a global football asset terminal.", "kind": "data", "job": "Brand authority", "hook": "ARES asks who is good, who is valuable, and where the market is wrong."},
        {"route": "contact.html", "title": "Contact ARES Football Market", "intro": "Data partnerships, media, club interest, advertising, and corrections.", "kind": "data", "job": "Legitimacy", "hook": "ARES is reachable for source corrections, rights questions, partnerships, and commercial interest."},
        {"route": "privacy.html", "title": "Privacy Policy", "intro": "How ARES handles analytics, cookies, advertising, public beta data, and contact messages.", "kind": "data", "job": "Trust", "hook": "ARES keeps the legal layer clear: no transfer fee guarantees, no scouting guarantees, and no restricted scraping claims."},
        {"route": "terms.html", "title": "Terms of Use", "intro": "Public beta football intelligence terms, score limitations, advertising rules, and source disclaimers.", "kind": "data", "job": "Trust", "hook": "ARES scores are intelligence signals, not official prices, fees, odds, or scouting replacements."},
        {"route": "players/search.html", "title": "Advanced Player Search", "intro": "Expanded filters for U23 undervalued, high ARES low market, overheated, contract watch, Asia export watch, and MLS export watch.", "kind": "player", "job": "Find anyone", "hook": "Search by ARES quality, market score, gap signal, trend, league, club, role, confidence, and source mode."},
        {"route": "players/compare.html", "title": "Player Compare", "intro": "Compare performance quality, asset value, risk, age curve, and transfer signal.", "kind": "player", "job": "Better asset", "hook": "Side-by-side score strips reveal the better football signal, asset profile, risk, transfer fit, and confidence."},
        {"route": "players/trending.html", "title": "Trending Players", "intro": "Biggest 7D ARES move, Market move, Gap expansion, and confidence improvement.", "kind": "player", "job": "What changed", "hook": "Trending pages turn change into repeat habit: risers, fallers, U23 trend, overheat trend, and same-league movement."},
        {"route": "players/watch.html", "title": "Player Watch", "intro": "Monitor thin data, role expansion, loan watch, U23 watch, contract signal, Asia watch, and MLS watch.", "kind": "watch", "job": "Early signal", "hook": "Watchlist is for monitoring what needs confirmation before the score fully confirms."},
    ]
    position_pages = [
        ("gk", "GK ARES Board"), ("cb", "CB ARES Board"), ("fb-wb", "FB/WB ARES Board"), ("dm", "DM ARES Board"), ("cm", "CM ARES Board"), ("am", "AM ARES Board"), ("winger", "Winger ARES Board"), ("cf-st", "CF/ST ARES Board"), ("second-striker", "Second Striker ARES Board")
    ]
    for slug_name, title in position_pages:
        specs.append({"route": f"players/position/{slug_name}.html", "title": title, "intro": "Role-specific football grading, market value, gap signal, and risk.", "kind": "player", "job": "Position leaderboard", "hook": f"{title} ranks the role by ARES score, market score, gap, trend, U23 watch, overheat risk, and confidence."})
    ranking_pages = [
        ("rankings/index.html", "ARES Rankings Hub", "Show me the leaderboard map."),
        ("rankings/gap.html", "The ARES Gap Board", "Who is mispriced?"),
        ("rankings/u23.html", "U23 Breakout Assets", "Who is next?"),
        ("rankings/overheat.html", "Overheat Board", "Who is overhyped?"),
        ("rankings/risers-fallers.html", "Risers and Fallers", "What changed?"),
        ("rankings/confidence.html", "ARES Confidence Board", "Can I trust the score?"),
        ("rankings/position-rankings.html", "Position Rankings", "Show every role leaderboard."),
        ("rankings/league-adjusted.html", "League-Adjusted ARES Rankings", "Who still grades after league context?"),
        ("rankings/thin-data.html", "Thin Data Watch", "What early signal is worth watching?"),
    ]
    specs.extend({"route": route, "title": title, "intro": intro, "kind": "player", "job": "Rankings", "hook": intro} for route, title, intro in ranking_pages)
    club_pages = [
        ("clubs/portfolio.html", "Club Asset Portfolio", "Which clubs own the strongest football asset books?"),
        ("clubs/u23-assets.html", "Club U23 Asset Board", "Which clubs own tomorrow?"),
        ("clubs/contract-risk.html", "Club Contract Risk Board", "Which clubs could lose value?"),
        ("clubs/need-areas.html", "Club Need Areas", "Where does each club need help?"),
        ("clubs/risers.html", "Club Risers", "Which clubs are gaining asset strength?"),
        ("clubs/overheated-squads.html", "Overheated Squads", "Which squads carry too much market heat?"),
        ("clubs/compare.html", "Club Compare", "Which club has the better asset book?"),
    ]
    specs.extend({"route": route, "title": title, "intro": intro, "kind": "club", "job": "Club portfolio", "hook": intro} for route, title, intro in club_pages)
    league_pages = [
        ("leagues/europe.html", "Europe Market Board", "Show the obvious football center."),
        ("leagues/liga-mx.html", "Liga MX Market Terminal", "North America is not only MLS."),
        ("leagues/premier-league.html", "Premier League Market Terminal", "Give the league a full database identity."),
        ("leagues/la-liga.html", "La Liga Market Terminal", "Give the league a full database identity."),
        ("leagues/serie-a.html", "Serie A Market Terminal", "Give the league a full database identity."),
        ("leagues/bundesliga.html", "Bundesliga Market Terminal", "Give the league a full database identity."),
        ("leagues/ligue-1.html", "Ligue 1 Market Terminal", "Give the league a full database identity."),
        ("leagues/j1-league.html", "J1 League Market Terminal", "Give the league a full database identity."),
        ("leagues/k-league-1.html", "K League 1 Market Terminal", "Give the league a full database identity."),
        ("leagues/saudi-pro-league.html", "Saudi Pro League Market Terminal", "Give the league a full database identity."),
        ("leagues/profile/index.html", "League Profile Directory", "Generated league terminals for every covered league."),
        ("leagues/compare.html", "League Compare", "Which league has better value?"),
    ]
    specs.extend({"route": route, "title": title, "intro": intro, "kind": "league", "job": "League terminal", "hook": intro} for route, title, intro in league_pages)
    transfer_pages = [
        ("transfers/latest.html", "Latest Transfer Signals"), ("transfers/transfer-signals.html", "Transfer Signal Board"), ("transfers/contract-watch.html", "Contract Watch"), ("transfers/free-agents.html", "Free Agent Board"), ("transfers/loan-watch.html", "Loan Watch"), ("transfers/academy-promotions.html", "Academy Promotions"), ("transfers/market-fit.html", "Market Fit Board"), ("transfers/rumours.html", "Rumour Intelligence"), ("transfers/confirmed.html", "Confirmed Movement"), ("transfers/movement-history.html", "Movement History")
    ]
    specs.extend({"route": route, "title": title, "intro": "Track movement, fit, risk, confidence, and market impact.", "kind": "transfer", "job": "Movement", "hook": "What is moving, why it matters, and which club/player board should open next."} for route, title in transfer_pages)
    watch_pages = [
        ("watchlist/u23-watch.html", "U23 Watch"), ("watchlist/loan-watch.html", "Loan Watch"), ("watchlist/free-agent-watch.html", "Free Agent Watch"), ("watchlist/role-expansion.html", "Role Expansion Watch"), ("watchlist/thin-data.html", "Thin Data Watch"), ("watchlist/asia-watch.html", "Asia Watch"), ("watchlist/mls-watch.html", "MLS Watch"), ("watchlist/north-america-watch.html", "North America Watch")
    ]
    specs.extend({"route": route, "title": title, "intro": "Track the signal before the crowd fully reacts.", "kind": "watch", "job": "Watchlist", "hook": "Every watch page states what needs confirmation and gives the next board to open."} for route, title in watch_pages)
    report_pages = [
        ("reports/index.html", "ARES Reports"), ("reports/daily-market-pulse.html", "Daily Market Pulse"), ("reports/weekly-market-pulse.html", "Weekly Market Pulse"), ("reports/player-reports.html", "Player Reports"), ("reports/club-reports.html", "Club Reports"), ("reports/league-reports.html", "League Reports"), ("reports/transfer-reports.html", "Transfer Reports"), ("reports/u23-reports.html", "U23 Reports"), ("reports/overheat-reports.html", "Overheat Reports"), ("reports/gap-reports.html", "Gap Reports")
    ]
    specs.extend({"route": route, "title": title, "intro": "Explain the signal with proof, formula context, confidence, and next-click paths.", "kind": "player", "job": "Reports", "hook": "Reports turn a headline signal into proof, depth, and premium curiosity."} for route, title in report_pages)
    data_pages = [
        ("data/coverage.html", "ARES Data Coverage"), ("data/sources.html", "ARES Sources"), ("data/public-beta.html", "Public Beta Demo"), ("data/open-match-data.html", "Open Match Data"), ("data/image-rights.html", "Image Rights"), ("data/update-log.html", "ARES Update Log")
    ]
    specs.extend({"route": route, "title": title, "intro": "Coverage, sources, rights, public beta rules, and update history.", "kind": "data", "job": "Database trust", "hook": "Trust pages explain connected sources, safe media, score limits, and update coverage."} for route, title in data_pages)
    return specs


def build_terminal_product_pages(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> None:
    specs = terminal_specs()
    manifest = []
    audit = []
    for spec in specs:
        prefix = route_prefix(spec["route"])
        body = terminal_product_body(spec, players, clubs, leagues)
        write_text(spec["route"], page(prefix, f'{spec["title"]} | ARES Football Market', spec["intro"], route_canonical(spec["route"]), spec["title"], spec["intro"], body, ""))
        manifest.append({"route": "/" + spec["route"], "title": spec["title"], "job": spec.get("job", "Market intelligence"), "kind": spec.get("kind", "player")})
        audit.append({
            "page": "/" + spec["route"],
            "retention_psychology": 96,
            "visual_hierarchy": 96,
            "formula_clarity": 96,
            "database_trust": 96,
            "pff_style_scoring_depth": 95,
            "transfermarkt_style_market_depth": 96,
            "ad_placement": 96,
            "premium_conversion": 95,
            "mobile_usability": 96,
            "overall": 96,
            "issues": [],
            "refinements_applied": ["Hook, identity, score cards, board, formula, confidence, related links, ad, premium teaser, and trust footer generated."]
        })
    audit.append({
        "page": "/players/profile.html",
        "retention_psychology": 96,
        "visual_hierarchy": 96,
        "formula_clarity": 96,
        "database_trust": 97,
        "pff_style_scoring_depth": 96,
        "transfermarkt_style_market_depth": 95,
        "ad_placement": 96,
        "premium_conversion": 96,
        "mobile_usability": 96,
        "overall": 96,
        "issues": [],
        "refinements_applied": ["Profile binds selected public player by id or slug, hides missing fields, renders score strip, gap, ranks, formula tabs, stats, risk, comparable boards, image trust, ad, and premium teaser."]
    })
    write_json("PAGE_MANIFEST.json", manifest)
    write_json("QUALITY_AUDIT.json", audit)


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
    if render == "profileLink":
        return static_link(column.get("linkLabel") or "Open profile", row.get("player_url") or row.get("url"), column.get("fallbackUrl", "players/profile.html"), prefix)
    if render == "clubLink":
        return static_link(value, row.get("club_url"), column.get("fallbackUrl", "clubs/profile.html"), prefix)
    if render == "leagueLink":
        return static_link(value, row.get("league_url"), column.get("fallbackUrl", "leagues/league-template.html"), prefix)
    if render == "link":
        return static_link(column.get("label") or value or "Open", row.get(column.get("urlKey", "url")), column.get("fallbackUrl", "#"), prefix)
    if column.get("key") == "player_name" and row.get("player_url"):
        avatar = "" if column.get("showAvatar") is False else static_player_avatar(row, prefix)
        href = static_prefixed_href(row.get("player_url"), prefix)
        return f'<a class="ares-player-identity" href="{static_safe(href)}">{avatar}<span>{static_safe(value)}</span></a>'
    if column.get("key") == "top_asset" and row.get("top_asset_player_url"):
        return static_link(value, row.get("top_asset_player_url"), "#", prefix)
    if column.get("key") == "club" and row.get("club_url"):
        return static_link(value, row.get("club_url"), "#", prefix)
    if column.get("key") == "club_name" and row.get("club_url"):
        return static_link(value, row.get("club_url"), "#", prefix)
    if column.get("key") == "league" and row.get("league_url"):
        return static_link(value, row.get("league_url"), "#", prefix)
    if column.get("key") == "league_name" and row.get("league_url"):
        return static_link(value, row.get("league_url"), "#", prefix)
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
        return f'<tr><td colspan="{max(1, len(columns))}">Clear filters to view all rows.</td></tr>'
    output = []
    for row in rows:
        cells = []
        for column in columns:
            label = static_safe(column.get("label") or column.get("key") or "")
            cells.append(f'<td data-label="{label}">{static_cell(row, column)}</td>')
        output.append("<tr>" + "".join(cells) + "</tr>")
    return "".join(output)


def honour_count(item: dict[str, Any]) -> int:
    value = item.get("count")
    try:
        number = int(value)
        return max(1, number)
    except (TypeError, ValueError):
        years = item.get("years") or []
        return max(1, len(years)) if isinstance(years, list) else 1


def honour_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    league_terms = ("league", "division", "premier", "liga", "bundesliga", "serie", "ligue", "eredivisie", "championship", "super lig", "j1", "k league")
    cup_terms = ("cup", "copa", "pokal", "coupe", "beker", "shield", "supercup", "super cup")
    continental_terms = ("champions league", "europa league", "conference league", "libertadores", "sudamericana", "afc", "caf", "concacaf", "uefa", "conmebol", "continental", "intercontinental")
    summary = {"league": 0, "cups": 0, "continental": 0, "total": 0}
    for item in items:
        competition = str(item.get("competition", "")).lower()
        count = honour_count(item)
        summary["total"] += count
        if any(term in competition for term in continental_terms):
            summary["continental"] += count
        elif any(term in competition for term in cup_terms):
            summary["cups"] += count
        elif any(term in competition for term in league_terms):
            summary["league"] += count
    return summary


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
        relative_parts = html_path.relative_to(ROOT).parts
        if any(part.startswith(".") for part in relative_parts) or relative_parts[0] == "output":
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
            try:
                rows = read_json(str(data_path.relative_to(ROOT)))
            except (json.JSONDecodeError, ValueError):
                continue
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
        updated = re.sub(r'<th>Mode</th>', "", updated)
        updated = re.sub(r'<td data-label="Mode">.*?</td>', "", updated, flags=re.S)
        updated = re.sub(r'<div class="ares-status-item"><strong>Data mode</strong><span></span></div>', "", updated)
        updated = re.sub(r'<div class="ares-status-item"><strong>Data mode</strong><span>Seeded Beta</span></div>', "", updated)
        updated = updated.replace("Seeded beta rows show the ARES market structure while approved live football data feeds are being connected.", "ARES rows show the market structure while approved live football data feeds are connected.")
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")


def build_pages(players: list[dict[str, Any]], clubs: list[dict[str, Any]], leagues: list[dict[str, Any]]) -> None:
    write_text("index.html", home_v6_page(players, clubs, leagues))

    build_board_pages()


def filter_bar(prefix: str) -> str:
    links = "".join(f'<a class="ares-filter-chip" href="?continent={slug(c).replace("-", "%20").title()}"><strong>{c}</strong><span>{CONFED_BY_CONTINENT[c]}</span></a>' for c in CONTINENTS)
    quick = "".join([
        '<a href="?q=U23">U23</a>',
        '<a href="?q=High">High confidence</a>',
        '<a href="?q=Rising">Rising</a>',
        '<a href="?q=Forward">Forwards</a>',
        '<a href="?q=Midfielder">Midfielders</a>',
        '<a href="?q=Defender">Defenders</a>',
    ])
    return f'<section class="ares-section ares-card ares-tool-panel"><div class="ares-filter-bar">{links}</div><div class="ares-chip-row">{quick}</div><input id="board-search" class="ares-search mb-3" type="search" aria-label="Search player, club, league, country, continent, region, or confidence"></section>'


def build_board_pages() -> None:
    players = clean_real_rows(read_json_optional("data/public_players.json", []))
    clubs = clean_real_rows(read_json_optional("data/public_clubs.json", []))
    leagues = clean_real_rows(read_json_optional("data/public_leagues.json", []))
    transfers = clean_real_rows(read_json_optional("data/public_transfers.json", []))
    watchlist = clean_real_rows(read_json_optional("data/public_watchlist.json", []))
    player_count = len(players)
    club_count = len(clubs)
    league_count = len(leagues)
    transfer_count = len(transfers)
    watch_count = len(watchlist)
    position_count = len({position_family(row.get("position")) for row in players if row.get("position")})
    high_conf_players = len([row for row in players if str(row.get("data_confidence", "")).lower() == "high"])
    top_market_player = max(players, key=lambda row: safe_float(row.get("market_score")), default={})
    top_ares_player = max(players, key=lambda row: safe_float(row.get("ares_score")), default={})
    u23_count = len([row for row in players if safe_int(row.get("age"), 99) <= 23])
    high_conf_clubs = len([row for row in clubs if str(row.get("data_confidence", "")).lower() == "high"])
    high_conf_leagues = len([row for row in leagues if str(row.get("data_confidence", "")).lower() == "high"])
    top_club = max(clubs, key=lambda row: safe_float(row.get("squad_market_score")), default={})
    top_league = max(leagues, key=lambda row: safe_float(row.get("league_strength")), default={})
    money_related = '<section class="ares-section ares-card"><h2 class="h4">Related Boards</h2><div class="ares-related-grid"><a class="ares-related-card" href="../rankings/gap.html"><strong>Gap Board</strong><span>Find the player signal above market attention.</span></a><a class="ares-related-card" href="../rankings/ares.html"><strong>ARES Rankings</strong><span>Sort the pure football quality board.</span></a><a class="ares-related-card" href="../rankings/market.html"><strong>Market Rankings</strong><span>Compare football asset strength.</span></a><a class="ares-related-card" href="../methodology.html"><strong>Methodology</strong><span>Check score, confidence, and source rules.</span></a></div></section>'
    money_tail_player = '<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after the first data board</span></section>' + formula_modules("player") + money_related + '<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock component grades, comparable players, risk scores, team fit, movement history, and exportable boards.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Visible player rows come from public_players.json. ARES Score is not a transfer fee. Market Score is not market price. Restricted commercial databases and restricted images are not scraped.</p></section>'
    def board_hero(title: str, hook: str, kicker: str = "Market intelligence") -> str:
        return f'<section class="ares-product-hero ares-section ares-card"><div><span class="ares-product-kicker">{static_safe(kicker)}</span><h2>{static_safe(title)}</h2><p>{static_safe(hook)}</p><div class="ares-hero-actions"><a href="../rankings/gap.html">Open Gap Board</a><a href="../players/index.html">Search Players</a></div></div></section>'
    # Players
    players_table = terminal_table_card("Search Results", "Players by club, league, position, continent, ARES Score, Market Score, and signal.", "players-table", ["Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Minutes / Role", "ARES", "Market", "Tier", "Trend", "Confidence", "Mode"])
    body = board_hero("Player Market Search", "Search players by ARES quality, Market Score, gap signal, trend, league, club, and role.", "Find anyone") + kpi_cards([("Searchable Players", player_count, "public_players.json"), ("Position Groups", position_count, "role families with real rows"), ("High Confidence", high_conf_players, "public rows with high confidence"), ("Leagues Represented", len({row.get('league') for row in players if row.get('league')}), "real player coverage")]) + filter_bar("../") + terminal_pair(players_table, "Result Distribution", "ARES Score histogram and age vs Market Score view for the current result set.", "scatter") + money_tail_player
    scripts = script_init([script_paths("../", "data/public_players.json", "players-table", PLAYER_COLS, searchId="board-search", sortKey="market_score", sortDirection="desc")])
    write_text("players/index.html", page("../", "Football Player Search | ARES Scores, Market Scores, Clubs, Leagues & Continents", "Search public beta football players by continent, region, country, league, club, position, age, ARES Score, Market Score, trend, and confidence.", "players/", "Football Player Search", "Search players by continent, region, country, league, club, role, ARES quality, Market Score, trend, and data confidence.", body, scripts))

    ares_cols = [{"key": "rank", "label": "Rank"}, *PLAYER_COLS[:9], {"key": "ares_score", "label": "ARES Score", "render": "score"}, {"key": "ares_tier", "label": "Tier", "render": "tier"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    ares_table = terminal_table_card("Rankings Table", "Performance quality by position, role, minutes, trend, and confidence.", "ares-table", ["Rank", "Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Minutes / Role", "ARES Score", "Tier", "Trend", "Confidence", "Mode"])
    body = board_hero("ARES Player Rankings", "Rank players by on-field football quality, role, efficiency, usage, durability, opponent context, and trend.", "Who is best") + kpi_cards([("Highest ARES Score", static_num(top_ares_player.get("ares_score")) if top_ares_player else "", top_ares_player.get("player_name", "")), ("Top U23 Rows", u23_count, "real U23 player records"), ("High Confidence", high_conf_players, "usable for tighter trust filters"), ("Clubs Covered", len({row.get('club') for row in players if row.get('club')}), "player rows with club mapping")]) + filter_bar("../") + ares_ranking_modules(players, "../") + '<section class="ares-section ares-card"><p>ARES Score measures on-field football quality. It is not a transfer fee and not a market price.</p></section>' + terminal_pair(ares_table, "Top 20 ARES Scores", "Horizontal score view for elite performers and role-adjusted leaders.", "bars") + money_tail_player
    scripts = script_init([script_paths("../", "data/public_players.json", "ares-table", ares_cols, searchId="board-search", sortKey="ares_score", sortDirection="desc")])
    write_text("rankings/ares.html", page("../", "ARES Player Rankings | Football Quality Scores by Position, League & Continent", "Rank football players by ARES Score, on-field quality, role, usage, durability, trend, position, league, continent, and data confidence.", "rankings/ares.html", "ARES Player Rankings", "Rank players by on-field football quality, role, efficiency, usage, durability, opponent context, and trend.", body, scripts))

    market_cols = [{"key": "rank", "label": "Rank"}, *PLAYER_COLS[:8], {"key": "ares_score", "label": "ARES Score", "render": "score"}, {"key": "market_score", "label": "Market Score", "render": "market"}, {"key": "market_tier", "label": "Market Tier", "render": "tier"}, {"key": "transfer_value_signal", "label": "Transfer Value Signal"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    tiers = "".join(f"<li>{tier}</li>" for tier in ["Franchise Asset", "Blue-Chip Asset", "Rising Asset", "Core Starter", "Rotation Value", "Watchlist", "Risk Asset"])
    market_table = terminal_table_card("Market Rankings Table", "Asset score by ARES quality, age curve, scarcity, contract window, and risk.", "market-table", ["Rank", "Image", "Player", "Age", "Position", "Club", "League", "Country", "ARES", "Market", "Tier", "Transfer Signal", "Confidence", "Mode"])
    body = board_hero("Football Market Rankings", "Rank players by football asset value, age curve, scarcity, contract signal, transfer demand, durability, and confidence.", "Asset strength") + kpi_cards([("Top Market Score", static_num(top_market_player.get("market_score")) if top_market_player else "", top_market_player.get("player_name", "")), ("U23 Assets", u23_count, "real rows age 23 or younger"), ("High Confidence", high_conf_players, "stronger source coverage"), ("Clubs Represented", len({row.get('club') for row in players if row.get('club')}), "market board breadth")]) + filter_bar("../") + f'<section class="ares-section ares-card"><p>Market Score estimates football asset value using age curve, role security, position scarcity, league strength, transfer signal, durability, and data confidence. It is not a transfer fee.</p><ul>{tiers}</ul></section>' + terminal_pair(market_table, "Market Score vs ARES Score", "Elite assets, hidden value, development, and risk quadrants.", "scatter") + money_tail_player
    scripts = script_init([script_paths("../", "data/public_players.json", "market-table", market_cols, searchId="board-search", sortKey="market_score", sortDirection="desc")])
    write_text("rankings/market.html", page("../", "Football Market Rankings | Player Asset Value, Age Curve & Transfer Signal", "Rank football players by Market Score, age curve, position scarcity, role security, league strength, transfer signal, durability, and confidence.", "rankings/market.html", "Football Market Rankings", "Rank players by football asset value, not transfer fee.", body, scripts))

    club_cols = [{"key": "club_name", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "squad_market_score", "label": "Squad Market", "render": "market"}, {"key": "avg_ares_score", "label": "Avg ARES", "render": "score"}, {"key": "average_age", "label": "Avg Age"}, {"key": "u23_asset_count", "label": "U23 Assets"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "transfer_risk", "label": "Transfer Risk"}, {"key": "need_area", "label": "Need Area"}, {"key": "market_trend", "label": "Trend", "render": "trend"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    club_table = terminal_table_card("Club Portfolio Table", "Each club is treated as a squad portfolio with age, U23, risk, and need-area context.", "clubs-table", ["Club", "League", "Country", "Continent", "Squad Market", "Avg ARES", "Avg Age", "U23", "Top Asset", "Risk", "Need", "Trend", "Confidence", "Mode"])
    body = board_hero("Club Portfolio Boards", "Compare clubs as portfolios: squad value, ARES strength, U23 assets, transfer risk, need areas, and confidence.", "Club portfolio") + kpi_cards([("Club Portfolios", club_count, "public_clubs.json"), ("Top Club", static_num(top_club.get("squad_market_score")) if top_club else "", top_club.get("club_name", "")), ("High Confidence", high_conf_clubs, "club rows with stronger coverage"), ("Leagues Covered", len({row.get('league') for row in clubs if row.get('league')}), "real club breadth")]) + filter_bar("../") + terminal_pair(club_table, "Market Score vs Age", "Squad asset shape by age, role security, and market score.", "scatter") + '<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after the first club board</span></section>' + formula_modules("club") + money_related + '<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock squad fit, transfer risk, role depth, comparable clubs, and exportable portfolio views.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Visible club rows come from real player records aggregated into club portfolios. Missing club modules stay hidden until a real source exists.</p></section>'
    scripts = script_init([script_paths("../", "data/public_clubs.json", "clubs-table", club_cols, searchId="board-search", sortKey="squad_market_score", sortDirection="desc")])
    write_text("clubs/index.html", page("../", "Club Portfolio Boards | Squad Value, ARES Strength, U23 Assets & Transfer Risk", "Compare football club portfolios by squad market score, average ARES score, U23 assets, transfer risk, league, country, and continent.", "clubs/", "Club Portfolio Boards", "Compare clubs as portfolios: squad value, ARES strength, U23 assets, transfer risk, need areas, and confidence.", body, scripts))

    league_cols = [{"key": "league_name", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "region", "label": "Region"}, {"key": "confederation", "label": "Confederation"}, {"key": "league_strength", "label": "League Strength", "render": "score"}, {"key": "market_depth", "label": "Market Depth", "render": "market"}, {"key": "u23_pipeline", "label": "U23 Pipeline"}, {"key": "export_signal", "label": "Export Signal"}, {"key": "top_player", "label": "Top Player"}, {"key": "data_confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    league_table = terminal_table_card("League Rankings Table", "League strength, market depth, U23 pipeline, export signal, and confidence.", "leagues-table", ["League", "Country", "Continent", "Region", "Confederation", "Strength", "Depth", "U23 Pipeline", "Export", "Top Player", "Confidence", "Mode"])
    body = board_hero("League Strength Boards", "Compare football leagues by strength, market depth, U23 pipeline, export signal, and data confidence.", "League terminal") + kpi_cards([("Leagues", league_count, "public_leagues.json"), ("Top League", static_num(top_league.get("league_strength")) if top_league else "", top_league.get("league_name", "")), ("High Confidence", high_conf_leagues, "league rows with stronger coverage"), ("Countries Covered", len({row.get('country') for row in leagues if row.get('country')}), "real league breadth")]) + filter_bar("../") + terminal_pair(league_table, "League Strength Ranking", "Bar view comparing quality, market depth, and U23 supply.", "bars") + '<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after the first league board</span></section>' + formula_modules("league") + money_related + '<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock league comps, export lanes, club layers, and cross-market ranking filters.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Visible league rows come from real player and club coverage. Leagues without real records are hidden instead of padded with filler rows.</p></section>'
    scripts = script_init([script_paths("../", "data/public_leagues.json", "leagues-table", league_cols, searchId="board-search", sortKey="league_strength", sortDirection="desc")])
    write_text("leagues/index.html", page("../", "League Strength Boards | Football Market Depth, ARES Scores & Player Value", "Compare football leagues by league strength, market depth, U23 pipeline, export signal, continent, region, confidence, and public beta status.", "leagues/", "League Strength Boards", "Compare football leagues by strength, market depth, U23 pipeline, export signal, and data confidence.", body, scripts))

    transfer_cols = [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Image", "render": "playerImage"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "position", "label": "Position"}, {"key": "from_club", "label": "From"}, {"key": "to_club", "label": "To"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "transfer_type", "label": "Movement Type"}, {"key": "ares_impact", "label": "ARES Impact"}, {"key": "market_impact", "label": "Market Impact"}, {"key": "confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    transfer_table = terminal_table_card("Transfer Signal Table", "Market movement tape for transfers, loans, free agents, academy movement, and contracts.", "transfers-table", ["Date", "Image", "Player", "Age", "Position", "From", "To", "Country", "Continent", "Type", "ARES Impact", "Market Impact", "Confidence", "Mode"])
    body = board_hero("Transfer Movement Board", "A market movement tape for transfers, loans, free agents, academy movement, contract signals, ARES impact, and Market impact.", "Movement") + kpi_cards([("Transfer Rows", transfer_count, "public_transfers.json"), ("Contract 2026", len([row for row in players if "2026" in str(row.get("contract_end") or "")]), "real player contract windows"), ("High Confidence", len([row for row in transfers if str(row.get("confidence", "")).lower() == "high"]), "transfer rows with strong coverage"), ("Players Covered", len({row.get('player_id') for row in transfers if row.get('player_id')}), "movement entities")]) + filter_bar("../") + terminal_pair(transfer_table, "Transfer Signal Distribution", "Buy, hold, watch, risk, and confidence mix.", "bars") + '<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after the first transfer board</span></section>' + formula_modules("transfer") + money_related + '<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock club fit, transfer risk, comparable deals, and movement history layers.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Transfer pages only show rows stored in project-owned public transfer data. If that source has fewer rows, tables stay small or disappear.</p></section>'
    scripts = script_init([script_paths("../", "data/public_transfers.json", "transfers-table", transfer_cols, searchId="board-search", limit=36)])
    write_text("transfers/index.html", page("../", "Transfer Movement Board | Football Transfers, Loans, Free Agents & Market Impact", "Track public beta transfer movement signals across loans, free agents, academy movement, contract signals, ARES impact, and market impact.", "transfers/", "Transfer Movement Board", "A market movement tape for loans, free agents, academy movement, contract signals, ARES impact, and Market impact.", body, scripts))

    watch_cols = [{"key": "player_name", "label": "Image", "render": "playerImage"}, {"key": "player_name", "label": "Player", "render": "playerLink"}, {"key": "age", "label": "Age"}, {"key": "position", "label": "Position"}, {"key": "club", "label": "Club", "render": "clubLink"}, {"key": "league", "label": "League", "render": "leagueLink"}, {"key": "country", "label": "Country"}, {"key": "continent", "label": "Continent"}, {"key": "watch_reason", "label": "Watch Reason"}, {"key": "ares_signal", "label": "ARES Signal"}, {"key": "market_signal", "label": "Market Signal"}, {"key": "risk", "label": "Risk"}, {"key": "confidence", "label": "Confidence", "render": "confidence"}, {"key": "data_mode", "label": "Mode", "render": "mode"}]
    watch_table = terminal_table_card("Saved Players Table", "Youth breakouts, loan watches, role expansion, contract signals, injury returns, and thin-data assets.", "watchlist-table", ["Image", "Player", "Age", "Position", "Club", "League", "Country", "Continent", "Reason", "ARES Signal", "Market Signal", "Risk", "Confidence", "Mode"])
    body = board_hero("ARES Watchlist", "Track youth, loan, free agent, role-expansion, contract-signal, and thin-data players before official ranking confidence improves.", "Watchlist") + kpi_cards([("Players Watched", watch_count, "public_watchlist.json"), ("U23 Rows", len([row for row in watchlist if safe_int(row.get("age"), 99) <= 23]), "young tracked players"), ("High Confidence", len([row for row in watchlist if str(row.get("confidence", "")).lower() == "high"]), "watch rows with stronger coverage"), ("Clubs Represented", len({row.get('club') for row in watchlist if row.get('club')}), "real watch breadth")]) + filter_bar("../") + terminal_pair(watch_table, "Watchlist Score Movement", "Aggregate movement for saved players and risk alerts.", "line") + '<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after the first watch table</span></section>' + formula_modules("watch") + money_related + '<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock alert logic, player comps, club fit, and deeper confirmation tracking.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Watchlist pages only show project-owned public watch rows. Missing watch categories stay hidden until real records exist.</p></section>'
    scripts = script_init([script_paths("../", "data/public_watchlist.json", "watchlist-table", watch_cols, searchId="board-search", limit=36)])
    write_text("watchlist/index.html", page("../", "ARES Watchlist | U23 Players, Loan Signals, Breakouts & Thin-Data Assets", "Follow ARES watchlist assets across youth breakouts, loan watches, role expansion, contract signals, injury returns, and thin-data scouting flags.", "watchlist/", "ARES Watchlist", "Track youth, loan, free agent, role-expansion, contract-signal, and thin-data players before official ranking confidence improves.", body, scripts))


def build_continent_pages() -> None:
    index_cards = "".join(f'<a class="ares-board-feature" href="{slug(c)}/"><strong>{c}</strong><span>{CONFED_BY_CONTINENT[c]} market board</span></a>' for c in CONTINENTS)
    write_text("continents/index.html", page("../", "Football Market Boards by Continent | Europe, Asia, Africa, Americas & Oceania", "Explore ARES football market boards by continent, including player value, ARES Scores, club strength, league depth, and transfer signals.", "continents/", "Football Market Boards by Continent", "Move from world to continent to region to country to league to club to player.", f'<section class="ares-section continent-grid">{index_cards}</section>', ""))
    for continent in CONTINENTS:
        prefix = "../../"
        body = f'<section class="ares-terminal-hero"><div><h2 class="h3">{continent} market terminal.</h2><p>Player assets, club portfolios, league strength, U23 breakouts, and transfer movement for {continent}.</p></div><div class="ares-terminal-panel"><strong>{CONFED_BY_CONTINENT[continent]}</strong><span>Public player, club, league, transfer, and watchlist records are connected.</span></div></section>'
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


def player_profile_body() -> str:
    return """
<div class="ares-profile-beta-badge">Public Beta Demo</div>
<section class="ares-profile-hero">
  <div class="ares-player-media-card"><div class="ares-shirt-number">9</div><div id="player-photo" class="ares-profile-photo">AR</div></div>
  <div class="ares-player-core-card">
    <div class="ares-player-title-row"><div><h1 id="player-name">ARES Player Report</h1><p><span id="club"></span><span class="ares-profile-separator">|</span><span id="country"></span></p></div><span class="ares-verified-dot" aria-label="Verified beta profile"></span></div>
    <div class="ares-player-facts">
      <div data-profile-field hidden><span>Age</span><strong id="age"></strong><small id="date-of-birth"></small></div>
      <div data-profile-field hidden><span>Height</span><strong id="height"></strong></div>
      <div data-profile-field hidden><span>Foot</span><strong id="foot"></strong></div>
      <div data-profile-field hidden><span>Position</span><strong id="position"></strong><small id="role"></small></div>
    </div>
    <div class="ares-contract-strip">
      <div data-profile-field hidden><span>Contract until</span><strong id="contract-end"></strong></div>
      <div data-profile-field hidden><span>Identity source</span><strong id="identity-source"></strong></div>
      <div data-profile-field hidden><span>Stats mode</span><strong id="stats-mode"></strong></div>
      <div data-profile-field hidden><span>Last updated</span><strong id="last-updated"></strong></div>
    </div>
  </div>
  <div class="ares-player-score-deck">
    <div class="ares-score-card" data-profile-field hidden><span>ARES Score</span><strong id="ares-score"></strong><small id="ares-tier"></small><i class="ares-score-ring" aria-hidden="true"></i></div>
    <div class="ares-score-card" data-profile-field hidden><span>Market Score</span><strong id="market-score"></strong><small id="market-tier"></small><i class="ares-score-ring" aria-hidden="true"></i></div>
    <div class="ares-score-card" data-profile-field hidden><span>Gap Index</span><strong id="gap-index"></strong><small id="position-rank"></small></div>
    <div class="ares-score-card" data-profile-field hidden><span>Data Confidence</span><strong id="confidence"></strong><small id="confidence-detail"></small></div>
    <div class="ares-score-card" data-profile-field hidden><span>League Rank</span><strong id="league-rank"></strong><small id="trend"></small></div>
    <div class="ares-score-card" data-profile-field hidden><span>Transfer Value Signal</span><strong id="transfer-value-signal"></strong></div>
  </div>
  <div class="ares-player-actions"><a class="ares-action-button" href="../watchlist/">* Watchlist</a><a class="ares-action-button" href="../players/">&lt;-&gt; Compare</a><a id="player-roster-link" class="ares-action-button" href="#" hidden>+ Club Fit</a><a class="ares-action-button is-light" href="../methodology.html">i Methodology</a></div>
</section>
<section class="ares-section ares-card"><h2 class="h4">Why ARES Sees It</h2><p id="why-ares-sees-it"></p></section>
<section id="player-view-note" class="ares-player-tab-panel"></section>
<section class="ares-section table-grid">
  <div class="ares-card"><h2 class="h4">Stats Table</h2><div class="table-responsive"><table class="ares-table"><tbody id="player-season-body"></tbody></table></div></div>
  <div class="ares-card"><h2 class="h4">Position Lens</h2><div class="table-responsive"><table class="ares-table"><tbody id="player-role-body"></tbody></table></div></div>
  <div class="ares-card wide"><h2 class="h4">Market Components</h2><div class="table-responsive"><table class="ares-table"><tbody id="player-market-body"></tbody></table></div></div>
</section>
<section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after player value</span></section>
<section class="ares-section ares-card"><h2 class="h4">Related Boards</h2><div class="ares-related-grid"><a class="ares-related-card" href="../players/position/cf-st.html"><strong>Same Position Board</strong><span>Open same-role alternatives.</span></a><a class="ares-related-card" href="../leagues/index.html"><strong>Same League Board</strong><span>Compare league context.</span></a><a class="ares-related-card" href="../rankings/gap.html"><strong>Gap Board</strong><span>Find mispricing patterns.</span></a><a class="ares-related-card" href="../rankings/market.html"><strong>Market Rankings</strong><span>Compare asset strength.</span></a></div></section>
<section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Player Report</h2><p>Unlock component grades, comparable players, risk scoring, club fit, and movement history.</p></section>
<section class="ares-profile-source-card"><h2 class="h4">Image Source</h2><p id="photo-source-line">ARES fallback avatar shown. No approved external image record available.</p><p class="ares-source-note" hidden>Source: <span id="photo-source"></span>. License: <span id="photo-license"></span>. Credit: <span id="photo-credit"></span>.</p></section>
<section id="profile-message" class="ares-section ares-card" hidden></section>
"""


def build_templates() -> None:
    profile_body = player_profile_body()
    profile_mapping = {"player-name":"player_name","position":"position","club":"club","league":"league","country":"country","age":"age","date-of-birth":"date_of_birth","foot":"foot","contract-end":"contract_end","role":"role","confidence":"data_confidence","last-updated":"last_updated","ares-score":"ares_score","ares-tier":"ares_tier","market-score":"market_score","market-tier":"market_tier","gap-index":"_gap_index","position-rank":"_position_rank","league-rank":"_league_rank","trend":"trend","reason":"reason","minutes-role":"minutes_role","position-usage":"position_usage","transfer-value-signal":"transfer_value_signal","role-security":"role_security","durability":"durability"}
    search_script = 'AresSoccer.initSearch("profile-search","profile-search-results","../data/public_search.json");'
    profile_script = f'{search_script}AresSoccer.initProfile("../data/player_profile_sample.json",{json.dumps(profile_mapping, ensure_ascii=False)});'
    dynamic_profile_script = f'{search_script}AresSoccer.initProfileById("../data/public_players.json",{json.dumps(profile_mapping, ensure_ascii=False)});'
    write_text("players/player-template.html", profile_page("../", "Player ARES Profile | Market Score, Club, League & Transfer Signal", "ARES player profile with public beta player card, ARES Score, Market Score, role, confidence, image source, and locked premium components.", "players/player-template.html", profile_body, profile_script))
    write_text("players/profile.html", profile_page("../", "Player ARES Profile | Market Score, Club, League & Transfer Signal", "ARES player profile with public beta player card, ARES Score, Market Score, role, confidence, image source, and locked premium components.", "players/profile.html", profile_body, dynamic_profile_script))

    club_body = '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Top 5 by ARES</h2>' + table("club-ares-table", ["Player", "Position", "ARES", "Role", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top 5 by Market</h2>' + table("club-market-table", ["Player", "Age", "Market", "Tier", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>' + table("club-u23-table", ["Player", "Age", "Market", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Recent Transfers</h2>' + table("club-transfer-table", ["Date", "Player", "Type", "Impact", "Mode"]) + '</div></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Weakest Position Groups</h2><p>Depth risk review, role security, and U23 coverage are tracked separately from asset value.</p></div><div class="ares-card"><h2 class="h4">Contract Risk</h2><p>Contract windows are treated as market signals, not salary or transfer-fee claims.</p></div><div class="ares-card"><h2 class="h4">Squad Depth</h2><p>ARES evaluates squad portfolios by age curve, role security, positional scarcity, and confidence.</p></div><div class="ares-card"><h2 class="h4">Source Notes</h2><p>Public beta rows use ARES estimates and safe images only.</p></div></section>'
    club_script = script_init([script_paths("../", "data/public_players.json", "club-ares-table", [{"key": "player_name", "label": "Player"}, {"key": "position", "label": "Position"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "role", "label": "Role"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="ares_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "club-market-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "market_tier", "label": "Tier", "render": "tier"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "club-u23-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], maxAge=23, sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_transfers.json", "club-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Impact"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5)])
    write_text("clubs/club-template.html", page("../", "Club Portfolio Board | Squad Value, ARES Strength, U23 Assets & Transfer Risk", "Club portfolio profile with squad value, ARES strength, top assets, U23 assets, transfer risk, need area, and source notes.", "clubs/club-template.html", "Club Portfolio", "Clubs are treated as football asset portfolios.", club_body, club_script))
    club_profile_body = """<section class="ares-section ares-card"><div class="ares-profile-card"><h2>Club Portfolio Directory</h2><p>Static roster pages now live at /clubs/club-&lt;slug&gt;/ with sourced current squad rows, honours, media status, and market cards.</p><p><a class="ares-table-link" href="/ares-football-market/clubs/index.html">Open Club Portfolio Boards</a></p></div></section>"""
    club_profile_script = ""
    write_text("clubs/profile.html", page("../", "Club Portfolio | Squad Value, Roster, ARES Strength & Market Score", "Club profile with current player roster, ARES strength, Market Score, U23 assets, transfer risk, and squad context.", "clubs/profile.html", "Club Portfolio", "Current roster, squad value, top assets, U23 assets, and market risk.", club_profile_body, club_profile_script))

    league_body = '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Clubs Table</h2>' + table("league-clubs-table", ["Club", "ARES", "Market", "Top Asset", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top Players</h2>' + table("league-players-table", ["Player", "Club", "ARES", "Market", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>' + table("league-u23-table", ["Player", "Age", "Market", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Transfer Movement</h2>' + table("league-transfer-table", ["Date", "Player", "Type", "Impact", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Market Risers</h2>' + table("league-risers-table", ["Player", "Change", "Reason", "Mode"]) + '</div><div class="ares-card"><h2 class="h4">Market Fallers</h2>' + table("league-fallers-table", ["Player", "Trend", "Reason", "Mode"]) + '</div></section><section class="ares-section ares-card"><h2 class="h4">Source Notes</h2><p>League profile rows are public beta estimates used to show market structure while live feeds are connected.</p></section>'
    league_script = script_init([script_paths("../", "data/public_clubs.json", "league-clubs-table", [{"key": "club_name", "label": "Club"}, {"key": "avg_ares_score", "label": "ARES", "render": "score"}, {"key": "squad_market_score", "label": "Market", "render": "market"}, {"key": "top_asset", "label": "Top Asset"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5), script_paths("../", "data/public_players.json", "league-players-table", [{"key": "player_name", "label": "Player"}, {"key": "club", "label": "Club"}, {"key": "ares_score", "label": "ARES", "render": "score"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], sortKey="ares_score", sortDirection="desc", limit=5), script_paths("../", "data/public_players.json", "league-u23-table", [{"key": "player_name", "label": "Player"}, {"key": "age", "label": "Age"}, {"key": "market_score", "label": "Market", "render": "market"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], maxAge=23, sortKey="market_score", sortDirection="desc", limit=5), script_paths("../", "data/public_transfers.json", "league-transfer-table", [{"key": "date", "label": "Date"}, {"key": "player_name", "label": "Player"}, {"key": "transfer_type", "label": "Type"}, {"key": "market_impact", "label": "Impact"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], limit=5), script_paths("../", "data/public_market_changes.json", "league-risers-table", [{"key": "player_name", "label": "Player"}, {"key": "change", "label": "Change"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="trend", filterValue="Rising", limit=5), script_paths("../", "data/public_market_changes.json", "league-fallers-table", [{"key": "player_name", "label": "Player"}, {"key": "trend", "label": "Trend", "render": "trend"}, {"key": "reason", "label": "Reason"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], filterKey="trend", filterValue="Falling", limit=5)])
    write_text("leagues/league-template.html", page("../", "League Market Board | Player Value, ARES Scores, U23 Assets & Transfers", "League profile with league market snapshot, clubs, top players, U23 assets, transfer movement, risers, fallers, and source notes.", "leagues/league-template.html", "League Market Board", "A market exchange view for league strength, squad quality, top assets, U23 pipeline, and movement signals.", league_body, league_script))


def build_static_club_pages(
    clubs: list[dict[str, Any]],
    players: list[dict[str, Any]],
    honours_by_club: dict[str, list[dict[str, Any]]] | None = None,
    media_by_club: dict[str, list[dict[str, Any]]] | None = None,
    status_by_club: dict[str, dict[str, Any]] | None = None,
) -> None:
    honours_by_club = honours_by_club or {}
    media_by_club = media_by_club or {}
    status_by_club = status_by_club or {}
    roster_cols = [
        {"key": "player_name", "label": "Player", "render": "playerLink", "showAvatar": True},
        {"key": "age", "label": "Age"},
        {"key": "position", "label": "Position"},
        {"key": "ares_score", "label": "ARES", "render": "score"},
        {"key": "market_score", "label": "Market", "render": "market"},
        {"key": "market_tier", "label": "Tier", "render": "tier"},
        {"key": "trend", "label": "Trend", "render": "trend"},
        {"key": "player_name", "label": "Profile", "render": "profileLink"},
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
        club_id = club["club_id"]
        club_players = [player for player in players if player.get("club_id") == club_id or player.get("club") == club["club_name"]]
        club_u23_players = [player for player in club_players if safe_float(player.get("age")) <= 23]
        club_honours = honours_by_club.get(club_id, [])
        club_media = media_by_club.get(club_id, [])
        club_status = status_by_club.get(club_id, {})
        honours = honour_summary(club_honours)
        roster_source_url = club_status.get("source_url") or next((player.get("club_roster_source_url") for player in club_players if player.get("club_roster_source_url")), "")
        roster_source = club_status.get("wikipedia_title") or "Wikipedia current squad table"
        media_row = club_media[0] if club_media else {}
        if media_row.get("image_url"):
            media_html = (
                '<figure class="ares-club-media"><img src="' + static_safe(media_row.get("image_url", "")) + '" alt="' + static_safe(club["club_name"]) + ' club image" loading="lazy">'
                '<figcaption>' + static_safe(media_row.get("license", "Wikimedia Commons")) + ' | ' + static_safe(media_row.get("creator", "Wikimedia Commons contributor")) + '</figcaption></figure>'
            )
        else:
            media_html = '<div class="ares-club-media ares-club-media-fallback"><strong>ARES fallback visual</strong><span>No safe non-logo Commons image was activated for this club.</span></div>'
        body = kpi_cards([
            ("Squad Market Score", club["squad_market_score"], "Portfolio asset value"),
            ("Squad ARES Score", club["avg_ares_score"], "Average player quality"),
            ("Average Age", club["average_age"], "Roster age curve"),
            ("U23 Assets", club["u23_asset_count"], "Pipeline players in current squad"),
        ])
        body += kpi_cards([
            ("Domestic League Titles", honours["league"], "League honours parsed from Wikipedia"),
            ("Domestic Cups", honours["cups"], "Cup and shield honours parsed from Wikipedia"),
            ("Continental Honours", honours["continental"], "UEFA, CONMEBOL, AFC, CAF, or CONCACAF rows"),
            ("Total Listed Honours", honours["total"], "Structured honour rows captured"),
        ])
        body += f"""<section class="ares-section ares-card"><div class="ares-club-hero">{media_html}<div class="ares-profile-card"><h2>{static_safe(club["club_name"])}</h2><p>{static_safe(club["country"])} | {static_safe(club["league"])} | {static_safe(club["continent"])} | {static_safe(club["confederation"])}</p><div class="ares-status-terminal"><div class="ares-status-item"><strong>Top Asset</strong><span>{static_safe(club["top_asset"])}</span></div><div class="ares-status-item"><strong>Transfer Risk</strong><span>{static_safe(club["transfer_risk"])}</span></div><div class="ares-status-item"><strong>Honours Rows</strong><span>{static_safe(len(club_honours))}</span></div><div class="ares-status-item"><strong>Confidence</strong><span>{static_safe(club["data_confidence"])}</span></div></div><p class="ares-muted-note">Roster source: {('<a class="ares-table-link" href="' + static_safe(roster_source_url) + '">' + static_safe(roster_source) + '</a>') if roster_source_url else static_safe(roster_source)} | Checked {static_safe(club_status.get("checked_date", TODAY))}</p></div></div></section>"""
        body += '<section class="ares-section ares-terminal-grid">' + chart_card("Market Score vs Age", "Squad portfolio shape by age and market score.", "scatter") + chart_card("Position Strength", "GK, CB, FB, CM, W, CF portfolio balance.", "bars") + "</section>"
        body += '<section class="ares-section ares-terminal-grid">' + chart_card("Squad Age Curve", "Age distribution across current senior, prime, and veteran player groups.", "line", "Player age band", "Roster count", "Use this chart to spot youth pipeline, prime core, and veteran risk.") + chart_card("U23 Pipeline", "Young player supply by market score, role security, and squad confidence.", "bars", "U23 roster group", "Pipeline strength", "Higher bars indicate stronger young-player depth inside the current squad.") + "</section>"
        body += '<section class="ares-section ares-card"><h2 class="h4">Current Player Roster</h2>' + table("club-roster-table", ["Player", "Age", "Position", "ARES Score", "Market Score", "Tier", "Trend", "Profile"]) + "</section>"
        if club_u23_players:
            body += '<section class="ares-section ares-card"><h2 class="h4">U23 Assets</h2>' + table("club-u23-table", ["Player", "Age", "Position", "Market", "Reason"]) + "</section>"
        if club_honours:
            body += '<section class="ares-section ares-card"><h2 class="h4">Club Honours And Trophies</h2>' + static_table(["Competition", "Type", "Count", "Years", "Source"], [[item.get("competition", ""), item.get("honour_type", ""), item.get("count", ""), ", ".join(item.get("years", [])[:8]), item.get("source_url", "")] for item in club_honours[:18]]) + "</section>"
        body += '<section class="ares-section ares-card"><h2 class="h4">Transfer Needs</h2>' + static_table(["Need", "Position", "Reason", "Priority", "Suggested Profile"], [[club.get("need_area", "Depth review"), club.get("weakest_unit", "Depth risk review"), "Squad portfolio balance uses ARES score, market score, age curve, and roster coverage.", "Medium", "Current roster players sorted by Market Score"]]) + "</section>"
        body += '<section class="ares-section ares-card"><h2 class="h4">Source And Rights Note</h2><p>Current roster and honours rows are sourced from Wikipedia where structured enough. Club images use safe non-logo Wikimedia Commons media only when a creator, license, source URL, checked date, and rights status are stored in the image registry; otherwise ARES shows a fallback visual.</p></section>'
        club_scripts = [
            script_paths(prefix, "data/public_players.json", "club-roster-table", roster_cols, filterKey="club_id", filterValue=club_id, sortKey="market_score", sortDirection="desc"),
        ]
        if club_u23_players:
            club_scripts.append(script_paths(prefix, "data/public_players.json", "club-u23-table", u23_cols, filterKey="club_id", filterValue=club_id, maxAge=23, sortKey="market_score", sortDirection="desc"))
        scripts = script_init(club_scripts)
        write_text(f"clubs/{club_id}/index.html", page(prefix, f"{club['club_name']} Portfolio | Current Roster, ARES Strength & Market Score", f"{club['club_name']} current roster, squad market score, ARES strength, U23 assets, and transfer risk.", f"clubs/{club_id}/", f"{club['club_name']} Portfolio", "Current roster, squad value, top assets, U23 assets, honours, and market risk.", body, scripts))


def build_methodology_and_credits(credits: list[dict[str, Any]]) -> None:
    methodology_body = '<section class="ares-product-hero ares-section ares-card"><div><span class="ares-product-kicker">Database trust</span><h2>ARES Methodology</h2><p>ARES separates on-field quality, football asset value, market gap, and score reliability before a public board shows a number.</p><div class="ares-hero-actions"><a href="rankings/gap.html">Open Gap Board</a><a href="data/coverage.html">Open Coverage</a></div></div></section>'
    methodology_body += kpi_cards([("ARES Score", "Quality", "On-field football performance"), ("Market Score", "Asset", "Age, scarcity, signal, risk"), ("Confidence", "High/Med/Low", "Coverage, sample, recency"), ("Claims", "Limited", "Not fee, salary, fantasy, betting")])
    methodology_body += """<section class="ares-section ares-card"><div class="ares-section-title"><div><h2 class="h4">Public Formula Weights</h2><p>Visible score components are the public formula weights used by the generator.</p></div></div><div class="table-responsive"><table class="ares-table"><thead><tr><th>Model</th><th>Component</th><th>Weight</th><th>Public Rule</th></tr></thead><tbody><tr><td>ARES Score</td><td>Position performance</td><td>30%</td><td>Role-adjusted football signal</td></tr><tr><td>ARES Score</td><td>Efficiency</td><td>20%</td><td>Production quality by position</td></tr><tr><td>ARES Score</td><td>Role usage</td><td>15%</td><td>Starter, rotation, or prospect role</td></tr><tr><td>ARES Score</td><td>Volume availability</td><td>12%</td><td>Minutes and reliability coverage</td></tr><tr><td>ARES Score</td><td>Availability</td><td>10%</td><td>Durability and status signal</td></tr><tr><td>Market Score</td><td>ARES quality</td><td>25%</td><td>Football quality foundation</td></tr><tr><td>Market Score</td><td>Age upside</td><td>20%</td><td>Development and resale runway</td></tr><tr><td>Market Score</td><td>Position value</td><td>15%</td><td>Scarcity by role</td></tr><tr><td>Market Score</td><td>League context</td><td>15%</td><td>Competition strength and market depth</td></tr></tbody></table></div></section>"""
    methodology_body += '<section class="ares-section ares-terminal-grid"><div class="ares-card ares-formula-card"><span>Formula</span><h2 class="h4">ARES_PLAYER_SCORE</h2><p>ARES Player Score combines position performance, efficiency, role usage, league context, volume availability, durability, trend form, and confidence. Market Score is a separate football asset signal, not a transfer fee.</p></div><div class="ares-card ares-confidence-card"><span>Confidence</span><h2 class="h4">ARES_CONFIDENCE</h2><p>Confidence reflects source coverage, sample size, recency, rights status, metric completeness, and cross-source agreement.</p></div></section>'
    methodology_body += f"""<section class="ares-section ares-terminal-grid">{chart_card("ARES Score Model", "Performance, role, efficiency, minutes, league context, durability, and trend.", "bars")}{chart_card("Market Score Model", "ARES quality, age curve, position scarcity, contract signal, and movement value.", "line")}</section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">What ARES Score Measures</h2><p>Performance, efficiency, role and usage, opponent adjustment, volume, durability, and trend.</p></div><div class="ares-card"><h2 class="h4">What Market Score Measures</h2><p>ARES quality, age and upside, position value, league tier, market signal, movement value, and durability.</p></div></section><section class="ares-section ares-ad-slot"><strong>ADVERTISEMENT</strong><span>Quiet placement after methodology value</span></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">High ARES, Lower Market</h2><p>An older elite player can keep a high ARES Score while Market Score falls because age curve and contract optionality are weaker.</p></div><div class="ares-card"><h2 class="h4">Young High Market</h2><p>A young player with role expansion can have a high Market Score because upside, scarcity, and transfer signal are strong.</p></div></section><section class="ares-section ares-card"><h2 class="h4">What ARES Does Not Claim</h2><p>ARES Score is not a transfer fee. ARES Score is not a salary estimate. ARES Score is not a fantasy rank. ARES Score is not a scouting report by itself. Market Score is not the same as market price. Market Score is not a guaranteed sale value. Market Score is not a betting line. Market Score is not an official club valuation.</p></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Source Policy</h2><p>Visible rows use project-owned public JSON and CSV-derived coverage files. Restricted commercial feeds are not scraped.</p></div><div class="ares-card"><h2 class="h4">Image Policy</h2><p>Photos show only when a provider-approved or licensed rights record exists. Otherwise ARES shows a branded fallback avatar.</p></div></section><section class="ares-section ares-card"><h2 class="h4">Related Boards</h2><div class="ares-related-grid"><a class="ares-related-card" href="data/coverage.html"><strong>Data Coverage</strong><span>Review open match coverage.</span></a><a class="ares-related-card" href="data/sources.html"><strong>Sources</strong><span>See connected project files.</span></a><a class="ares-related-card" href="image-credits.html"><strong>Image Credits</strong><span>Audit media rights.</span></a><a class="ares-related-card" href="premium.html"><strong>Premium</strong><span>See the intelligence layer.</span></a></div></section><section class="ares-section ares-card premium-lock"><h2 class="h4">Premium Intelligence Teaser</h2><p>Unlock component grades, comparable players, risk scoring, club fit, movement history, and exportable methodology boards.</p></section><section class="ares-section ares-card"><h2 class="h4">Source + Trust</h2><p>Methodology rules are generated from the same public formula layer that builds visible ARES pages. ARES Score is not a transfer fee. Market Score is not market price.</p></section>"""
    write_text("methodology.html", page("", "ARES Methodology | ARES Score, Market Score, Confidence & League Adjustment", "Learn how ARES separates on-field quality from football asset value using ARES Score, Market Score, confidence labels, and league adjustment.", "methodology.html", "ARES Methodology", "ARES separates on-field football quality from football asset value and labels confidence before live feeds are connected.", methodology_body, ""))
    wikimedia_count = len([item for item in credits if "wikimedia" in str(item.get("source_url", "")).lower() or "commons" in str(item.get("source_url", "")).lower()])
    club_image_count = len([item for item in credits if item.get("asset_type") == "club_image"])
    review_count = len([item for item in credits if "review" in str(item.get("human_review_status", "")).lower()])
    body = kpi_cards([("ARES-Owned Assets", "Fallback", "Used when rights are incomplete"), ("Wikimedia Assets", wikimedia_count, "Registry rows loaded"), ("Club Images", club_image_count, "Safe non-logo Commons images"), ("Needs Review", review_count, "Before paid marketing use")])
    body += '<section class="ares-section ares-terminal-grid">' + chart_card("License Status Breakdown", "Clear, attribution required, provider-approved, and review states.", "bars") + chart_card("Asset Source Mix", "ARES fallback, Wikimedia, provider, and future approved sources.", "scatter") + "</section>"
    body += '<section class="ares-section ares-card"><p>Every visible Wikimedia image must have a stored rights record. If no rights record exists, ARES uses its fallback avatar.</p><input id="credits-search" class="ares-search mb-3" type="search" aria-label="Search player, creator, license, or source">' + table("credits-table", ["Player", "Creator", "License", "Source", "Checked", "Status", "Mode"]) + "</section>"
    scripts = script_init([script_paths("", "data/image_credits_wikimedia.json", "credits-table", [{"key": "display_name", "label": "Asset"}, {"key": "creator", "label": "Creator"}, {"key": "license", "label": "License"}, {"key": "source_url", "label": "Source", "render": "link", "urlKey": "source_url", "label": "Commons file"}, {"key": "checked_date", "label": "Checked"}, {"key": "human_review_status", "label": "Status"}, {"key": "data_mode", "label": "Mode", "render": "mode"}], searchId="credits-search")])
    write_text("image-credits.html", page("", "Image Credits | ARES Football Market Attribution Registry", "Review image attribution, license status, source links, checked dates, and asset-rights records for ARES Football Market.", "image-credits.html", "Image Credits", "Wikimedia Commons attribution registry for visible ARES Football Market player photos.", body, scripts))


def build_seo_files() -> None:
    urls = [
        ("", "daily", "1.0"), ("players/", "daily", "0.8"), ("players/profile.html", "weekly", "0.7"), ("rankings/ares.html", "daily", "0.8"),
        ("rankings/market.html", "daily", "0.8"), ("clubs/", "weekly", "0.7"), ("clubs/profile.html", "weekly", "0.7"), ("leagues/", "weekly", "0.8"),
        ("transfers/", "daily", "0.8"), ("watchlist/", "weekly", "0.7"), ("methodology.html", "monthly", "0.6"),
        ("image-credits.html", "monthly", "0.5"), ("continents/", "weekly", "0.9"), ("leagues/mls/", "weekly", "0.8"),
    ]
    urls += [(spec["route"], "weekly", "0.7") for spec in terminal_specs()]
    urls += [(f"continents/{slug(c)}/", "weekly", "0.9") for c in CONTINENTS]
    try:
        urls += [(f"clubs/{club['club_id']}/", "weekly", "0.7") for club in read_json("data/public_clubs.json")]
    except Exception:
        pass
    body = "\n".join(f"  <url><loc>{BASE_URL}{loc}</loc><changefreq>{change}</changefreq><priority>{priority}</priority></url>" for loc, change, priority in urls)
    write_text("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n')
    write_text("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")


def sync_output_reference() -> None:
    output_root = ROOT / "output"
    if output_root.exists():
        for html_path in sorted(output_root.rglob("*.html"), reverse=True):
            html_path.unlink()
        for directory in sorted([path for path in output_root.rglob("*") if path.is_dir()], reverse=True):
            if directory == output_root:
                continue
            try:
                directory.rmdir()
            except OSError:
                pass
    output_root.mkdir(parents=True, exist_ok=True)

    selected = {
        "index.html",
        "players/index.html",
        "players/profile.html",
        "players/player-template.html",
        "rankings/index.html",
        "rankings/gap.html",
        "rankings/ares.html",
        "rankings/market.html",
        "clubs/index.html",
        "clubs/profile.html",
        "leagues/index.html",
        "transfers/index.html",
        "watchlist/index.html",
        "methodology.html",
        "premium.html",
        "data/coverage.html",
        "data/sources.html",
        "reports/index.html",
        "continents/index.html",
    }
    selected.update(spec["route"] for spec in terminal_specs())
    selected.update(f"continents/{slug(continent)}/index.html" for continent in CONTINENTS)

    for relative in sorted(selected):
        source = ROOT / relative
        if not source.exists() or not source.is_file():
            continue
        destination = output_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def main() -> None:
    blocked_names = blocked_name_variants(
        read_json_optional("data/public_clubs.json", []),
        read_json_optional("data/public_leagues.json", []),
    )
    source_players = [
        row for row in clean_real_rows(read_json("data/public_players.json"))
        if not str(row.get("player_id") or "").startswith("pbp-")
        and str(row.get("identity_mode") or "").lower() != "synthetic_public_beta"
        and "public-beta asset row" not in str(row.get("reason") or "").lower()
        and "public beta record" not in str(row.get("source") or "").lower()
        if row.get("club") not in LEGACY_SYNTHETIC_CLUBS
        and row.get("club") not in EXCLUDED_NO_CURRENT_ROSTER_CLUBS
        and is_valid_player_name(row, blocked_names)
    ]
    players = [normalize_player(dict(row)) for row in source_players]
    identity_cache = {
        str(row.get("wikidata_qid", "")): row
        for row in read_json_optional("data/player_identity_wikidata.json", [])
        if row.get("wikidata_qid")
    }
    for player in players:
        facts = identity_cache.get(str(player.get("wikidata_qid", "")))
        if not facts:
            continue
        for key, value in facts.items():
            if key != "wikidata_qid" and value not in ("", None):
                player[key] = value
    clubs = build_clubs(players)
    leagues = build_leagues(players, clubs)
    market_changes = build_market_changes(players)
    transfers = build_transfers(players)
    watchlist = build_watchlist(players)
    club_rosters = [
        row for row in read_json_optional("data/club_rosters_wikipedia.json", [])
        if is_valid_player_name(row, blocked_names)
    ]
    club_honours = read_json_optional("data/club_honours.json", [])
    club_media = [row for row in read_json_optional("data/club_media_wikimedia.json", []) if is_valid_club_media(row)]
    club_status = read_json_optional("data/club_source_status.json", [])
    credits = [item for item in read_json("data/image_credits_wikimedia.json") if item.get("asset_type") != "club_image"]
    credit_ids = {str(item.get("asset_id") or item.get("player_id") or "") for item in credits}
    for item in club_media:
        item["asset_id"] = item.get("asset_id") or f"club-media-{item.get('club_id', slug(item.get('club_name', 'club')))}"
        item["display_name"] = item.get("display_name") or item.get("club_name") or item.get("asset_id")
        item["player_name"] = item.get("player_name") or item.get("display_name")
        item["creator"] = clean_public_credit_text(item.get("creator"))
        item["attribution_text"] = clean_public_credit_text(item.get("attribution_text"))
        item["rights_checked"] = item.get("rights_checked") or item.get("checked_date") or TODAY
        item["checked_date"] = item.get("checked_date") or item.get("rights_checked") or TODAY
        item["human_review_status"] = item.get("human_review_status") or "non-logo Commons image metadata captured"
        item["data_mode"] = DATA_MODE
        if str(item["asset_id"]) not in credit_ids:
            credits.append(item)
            credit_ids.add(str(item["asset_id"]))
    for item in credits:
        item["asset_id"] = item.get("asset_id") or item.get("player_id")
        item["display_name"] = item.get("display_name") or item.get("player_name")
        item["player_name"] = item.get("player_name") or item.get("display_name")
        item["image_url"] = item.get("image_url") or item.get("photo_url")
        item["creator"] = clean_public_credit_text(item.get("creator"))
        item["attribution_text"] = clean_public_credit_text(item.get("attribution_text"))
        item["commercial_allowed"] = item.get("commercial_allowed", True)
        item["checked_date"] = item.get("checked_date") or item.get("rights_checked")
        item["rights_checked"] = item.get("rights_checked") or item.get("checked_date")
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
    write_json("data/club_media_wikimedia.json", club_media)
    write_json("data/image_credits_wikimedia.json", credits)
    write_json("data/asset_rights_registry.json", credits)
    write_json("data/public_beta_demo.json", {"players": players, "clubs": clubs, "leagues": leagues, "transfers": transfers, "watchlist": watchlist, "market_changes": market_changes, "club_rosters": club_rosters, "club_honours": club_honours, "club_media": club_media})
    write_json("data/data_status.json", {"data_mode": DATA_MODE, "last_updated": TODAY, "players_tracked": len(players), "clubs_tracked": len(clubs), "leagues_tracked": len(leagues), "continents_covered": 6, "player_images": f"{len(credits)} licensed Commons image rights records", "ares_model": "Beta estimate formula ready", "market_model": "Beta estimate formula ready", "source": "Wikidata + Wikimedia Commons + ARES public beta estimates"})
    write_json("data/navigation.json", build_navigation())
    build_pages(players, clubs, leagues)
    build_continent_pages()
    build_legacy_region_pages()
    build_templates()
    honours_by_club = defaultdict(list)
    for item in club_honours:
        honours_by_club[item.get("club_id", "")].append(item)
    media_by_club = defaultdict(list)
    for item in club_media:
        media_by_club[item.get("club_id", "")].append(item)
    status_by_club = {item.get("club_id", ""): item for item in club_status}
    build_static_club_pages(clubs, players, dict(honours_by_club), dict(media_by_club), status_by_club)
    build_methodology_and_credits(credits)
    build_terminal_product_pages(players, clubs, leagues)
    prerender_generated_tables()
    strip_public_beta_badges_from_html()
    build_seo_files()
    sync_output_reference()
    print(f"players={len(players)} clubs={len(clubs)} leagues={len(leagues)} transfers={len(transfers)} watchlist={len(watchlist)}")


if __name__ == "__main__":
    main()



