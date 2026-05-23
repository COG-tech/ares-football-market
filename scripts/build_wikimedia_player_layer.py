#!/usr/bin/env python3
"""Build the public Wikimedia player/photo layer for ARES Football Market.

Inputs are the local Commons downloader runs. Outputs are website-ready
player rows, image credits, search rows, and copied approved images.

The identity/photo fields come from Wikidata + Wikimedia Commons. The ARES
scores and soccer stat fields are deterministic public-beta estimates until
an approved live match-stat provider is connected.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUNS = [
    ROOT / "tools" / "commons_downloader" / "runs" / "top10_two_levels",
    ROOT / "tools" / "commons_downloader" / "runs" / "next10_two_levels",
]
OUT_IMAGE_DIR = ROOT / "assets" / "media" / "wikimedia" / "players"
OUT_DATA = ROOT / "data" / "public_players.json"
OUT_OPEN_COPY = ROOT / "data" / "wikimedia_players.json"
OUT_CREDITS = ROOT / "data" / "image_credits_wikimedia.json"
OUT_SEARCH = ROOT / "data" / "public_search.json"
TODAY = "2026-05-23"


LEAGUE_STRENGTH = {
    "Premier League": 0.99,
    "La Liga": 0.96,
    "Serie A": 0.93,
    "Bundesliga": 0.92,
    "Ligue 1": 0.88,
    "Super Lig": 0.78,
    "Saudi Pro League": 0.77,
    "Eredivisie": 0.76,
    "Liga Portugal": 0.75,
    "Major League Soccer": 0.72,
    "Campeonato Brasileiro Serie A": 0.72,
    "Liga MX": 0.70,
    "J1 League": 0.68,
    "K League 1": 0.65,
    "EFL Championship": 0.64,
    "LaLiga 2": 0.63,
    "2. Bundesliga": 0.62,
    "Serie B": 0.61,
    "Ligue 2": 0.59,
    "TFF First League": 0.57,
    "Eerste Divisie": 0.56,
    "Argentine Primera Division": 0.68,
    "Belgian Pro League": 0.66,
    "Scottish Premiership": 0.63,
    "Swiss Super League": 0.62,
    "A-League Men": 0.58,
    "Indian Super League": 0.54,
}


def safe_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def stable_unit(*parts: str) -> float:
    blob = "|".join(parts)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return int(digest[:10], 16) / float(16**10 - 1)


def stable_int(minimum: int, maximum: int, *parts: str) -> int:
    if maximum <= minimum:
        return minimum
    return minimum + int(round(stable_unit(*parts) * (maximum - minimum)))


def age_from_dob(dob: str) -> int:
    if not dob:
        return stable_int(19, 31, dob)
    try:
        year, month, day = [int(part) for part in dob[:10].split("-")]
        born = date(year, month, day)
        today = date(2026, 5, 23)
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except Exception:
        return stable_int(19, 31, dob)


def initials(name: str) -> str:
    return "".join(part[0] for part in name.split() if part)[:3].upper() or "AR"


def position_code(position: str) -> str:
    p = position.lower()
    if "goalkeeper" in p:
        return "GK"
    if "wing" in p and "back" not in p:
        return "W"
    if "forward" in p or "striker" in p:
        return "FW"
    if "midfielder" in p:
        return "MF"
    if "defender" in p or "back" in p:
        return "DF"
    return "FB"


def age_curve(age: int) -> tuple[str, float]:
    if age <= 20:
        return "Development", 0.84
    if age <= 23:
        return "Upside", 0.98
    if age <= 28:
        return "Prime", 1.0
    if age <= 31:
        return "Late Prime", 0.88
    if age <= 34:
        return "Veteran", 0.72
    return "Aging Risk", 0.56


def league_strength(league: str, level: str) -> float:
    base = LEAGUE_STRENGTH.get(league, 0.58)
    if level == "second":
        base -= 0.05
    return max(0.42, min(1.0, base))


def tier_from_score(score: float, market: bool = False) -> str:
    if market:
        if score >= 88:
            return "Franchise Asset"
        if score >= 82:
            return "Blue-Chip Asset"
        if score >= 76:
            return "Rising Asset"
        if score >= 69:
            return "Core Starter"
        if score >= 62:
            return "Rotation Value"
        if score >= 56:
            return "Watchlist"
        return "Risk Asset"
    if score >= 88:
        return "Elite"
    if score >= 80:
        return "High"
    if score >= 72:
        return "Starter"
    if score >= 64:
        return "Rotation"
    return "Watchlist"


def estimate_row(row: Dict[str, Any], index: int) -> Dict[str, Any]:
    player_id = safe_text(row["entity_id"])
    name = safe_text(row["entity_name"])
    league = safe_text(row["league"])
    club = safe_text(row["team"])
    level = safe_text(row.get("level"))
    pos_label = safe_text(row.get("position"))
    pos = position_code(pos_label)
    age = age_from_dob(safe_text(row.get("date_of_birth")))
    curve_label, curve_weight = age_curve(age)
    strength = league_strength(league, level)
    noise = stable_unit(player_id, name)

    ares = 58 + strength * 27 + noise * 9
    if pos == "GK":
        ares -= 1.2
    if age > 33:
        ares -= 2.0
    ares_score = round(max(54, min(94.8, ares)), 1)

    position_value = {"FW": 5.5, "W": 5.0, "MF": 3.5, "DF": 2.2, "GK": 0.8, "FB": 2.8}.get(pos, 2.8)
    market = ares_score * 0.58 + strength * 19 + curve_weight * 13 + position_value + noise * 5
    market_score = round(max(50, min(96.5, market)), 1)

    minutes = stable_int(650, 3100, player_id, league)
    if age <= 20:
        minutes = min(minutes, stable_int(650, 2100, player_id, "young"))
    if level == "second":
        minutes = min(3200, minutes + stable_int(80, 260, player_id, "second"))
    appearances = max(8, min(42, round(minutes / stable_int(72, 96, player_id, "apps"))))
    starts = max(4, min(appearances, round(minutes / stable_int(82, 105, player_id, "starts"))))
    availability = min(99, max(62, round(76 + minutes / 125 + stable_unit(player_id, "availability") * 7)))

    if pos in {"FW", "W"}:
        goals = stable_int(4, 22, player_id, "goals")
        assists = stable_int(3, 14, player_id, "assists")
        progressive_actions = stable_int(85, 260, player_id, "progression")
        defensive_actions = stable_int(22, 95, player_id, "defense")
    elif pos == "MF":
        goals = stable_int(1, 12, player_id, "goals")
        assists = stable_int(3, 16, player_id, "assists")
        progressive_actions = stable_int(130, 330, player_id, "progression")
        defensive_actions = stable_int(75, 210, player_id, "defense")
    elif pos == "DF":
        goals = stable_int(0, 6, player_id, "goals")
        assists = stable_int(0, 8, player_id, "assists")
        progressive_actions = stable_int(55, 190, player_id, "progression")
        defensive_actions = stable_int(115, 310, player_id, "defense")
    elif pos == "GK":
        goals = 0
        assists = stable_int(0, 2, player_id, "assists")
        progressive_actions = stable_int(15, 75, player_id, "progression")
        defensive_actions = stable_int(20, 85, player_id, "defense")
    else:
        goals = stable_int(0, 9, player_id, "goals")
        assists = stable_int(1, 10, player_id, "assists")
        progressive_actions = stable_int(60, 220, player_id, "progression")
        defensive_actions = stable_int(55, 190, player_id, "defense")

    trend_value = round((stable_unit(player_id, "trend") - 0.42) * 8, 1)
    trend = "Rising" if trend_value >= 1.2 else "Falling" if trend_value <= -1.2 else "Flat"
    confidence = "High" if safe_text(row.get("level")) == "top" and row.get("display_allowed") is True else "Medium"
    contract_end = str(2026 + stable_int(1, 5, player_id, "contract"))

    local_path = Path(safe_text(row["local_path"]))
    asset_name = local_path.name
    photo_asset = f"assets/media/wikimedia/players/{asset_name}"

    return {
        "data_mode": "wikimedia_open_photo_beta",
        "stats_mode": "ARES beta estimate; not official match statistics",
        "rank": index,
        "player_id": player_id,
        "player_name": name,
        "initials": initials(name),
        "age": age,
        "date_of_birth": safe_text(row.get("date_of_birth")),
        "position": pos,
        "position_label": pos_label or pos,
        "club": club,
        "league": league,
        "country": safe_text(row.get("country")),
        "region": safe_text(row.get("region")),
        "league_level": level,
        "minutes": minutes,
        "appearances": appearances,
        "starts": starts,
        "goals": goals,
        "assists": assists,
        "progressive_actions": progressive_actions,
        "defensive_actions": defensive_actions,
        "availability_pct": availability,
        "ares_score": ares_score,
        "ares_tier": tier_from_score(ares_score),
        "market_score": market_score,
        "market_tier": tier_from_score(market_score, market=True),
        "trend": trend,
        "trend_value": trend_value,
        "contract_end": contract_end,
        "age_curve": curve_label,
        "role": "Projected starter" if minutes >= 1900 else "Rotation / role player",
        "reason": f"{curve_label} {pos} profile with {league} context, {minutes} beta-estimated minutes, and licensed Commons photo coverage.",
        "data_confidence": confidence,
        "confidence": confidence,
        "last_updated": TODAY,
        "source": "Wikidata + Wikimedia Commons",
        "score_source": "ARES beta estimate",
        "url": "players/player-template.html",
        "player_url": "players/player-template.html",
        "club_url": "clubs/club-template.html",
        "league_url": "leagues/league-template.html",
        "photo_url": photo_asset,
        "photo_source": "Wikimedia Commons",
        "photo_license_status": "licensed_commons",
        "photo_credit": safe_text(row.get("creator")) or safe_text(row.get("credit")) or "Wikimedia Commons contributor",
        "photo_attribution_url": safe_text(row.get("source_url")),
        "photo_status": "available",
        "image_confidence": "High",
        "wikidata_qid": safe_text(row.get("wikidata_qid")),
        "commons_title": safe_text(row.get("commons_title")),
        "license_short_name": safe_text(row.get("license_short_name")),
        "license_url": safe_text(row.get("license_url")),
        "attribution_text": safe_text(row.get("attribution_text")),
        "rights_checked": safe_text(row.get("date_checked")),
    }


def read_run(run_dir: Path) -> pd.DataFrame:
    entities = pd.read_csv(run_dir / "entities.csv")
    registry = pd.read_csv(run_dir / "commons_output" / "metadata" / "image_rights_registry.csv")
    columns = [
        "entity_id",
        "image_status",
        "display_allowed",
        "downloaded",
        "local_path",
        "commons_title",
        "source_url",
        "creator",
        "credit",
        "license_short_name",
        "license_url",
        "attribution_text",
        "date_checked",
    ]
    merged = entities.merge(registry[columns], on=["entity_id", "commons_title"], how="left")
    return merged[(merged["display_allowed"] == True) & (merged["downloaded"] == True)].copy()


def write_json(path: Path, rows: Any) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def build_search_rows(players: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    search_rows: List[Dict[str, Any]] = []
    for player in players:
        search_rows.append(
            {
                "type": "player",
                "player_name": player["player_name"],
                "position": player["position"],
                "club": player["club"],
                "league": player["league"],
                "country": player["country"],
                "region": player["region"],
                "url": player["player_url"],
                "keywords": " ".join(
                    [
                        player["player_name"],
                        player["club"],
                        player["league"],
                        player["country"],
                        player["region"],
                        player["position"],
                        player["market_tier"],
                        player["ares_tier"],
                    ]
                ),
            }
        )
    for dataset, label_key, item_type in [
        (ROOT / "data" / "public_clubs.json", "club_name", "club"),
        (ROOT / "data" / "public_leagues.json", "league_name", "league"),
    ]:
        if not dataset.exists():
            continue
        for item in json.loads(dataset.read_text(encoding="utf-8")):
            label = item.get(label_key, "")
            search_rows.append(
                {
                    "type": item_type,
                    label_key: label,
                    "club": item.get("club_name", ""),
                    "league": item.get("league_name") or item.get("league", ""),
                    "country": item.get("country", ""),
                    "region": item.get("region", ""),
                    "url": item.get("url") or ("clubs/club-template.html" if item_type == "club" else "leagues/league-template.html"),
                    "keywords": " ".join(str(v) for v in item.values() if isinstance(v, (str, int, float))),
                }
            )
    return search_rows


def main() -> None:
    OUT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    frames = [read_run(run) for run in RUNS]
    frame = pd.concat(frames, ignore_index=True)
    frame = frame.drop_duplicates("entity_id", keep="first")

    rows: List[Dict[str, Any]] = []
    for _, record in frame.iterrows():
        src = ROOT / Path(safe_text(record["local_path"]))
        if not src.exists():
            continue
        dest = OUT_IMAGE_DIR / src.name
        shutil.copy2(src, dest)
        payload = record.to_dict()
        payload["local_path"] = str(src)
        rows.append(payload)

    players = [estimate_row(row, index + 1) for index, row in enumerate(rows)]
    players.sort(key=lambda item: item["market_score"], reverse=True)
    for index, player in enumerate(players, start=1):
        player["rank"] = index

    credits = [
        {
            "player_id": player["player_id"],
            "player_name": player["player_name"],
            "photo_url": player["photo_url"],
            "commons_title": player["commons_title"],
            "creator": player["photo_credit"],
            "license": player["license_short_name"],
            "license_url": player["license_url"],
            "source_url": player["photo_attribution_url"],
            "attribution_text": player["attribution_text"],
            "rights_checked": player["rights_checked"],
            "display_allowed": True,
        }
        for player in players
    ]

    write_json(OUT_DATA, players)
    write_json(OUT_OPEN_COPY, players)
    write_json(OUT_CREDITS, credits)
    write_json(OUT_SEARCH, build_search_rows(players))

    print(f"Players written: {len(players)}")
    print(f"Images copied: {len(list(OUT_IMAGE_DIR.glob('*')))}")
    print(f"Data: {OUT_DATA}")
    print(f"Credits: {OUT_CREDITS}")


if __name__ == "__main__":
    main()
