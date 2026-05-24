#!/usr/bin/env python3
"""Build Wikipedia/Wikidata club roster, media, and honours data.

This script uses public Wikipedia/Wikidata/Commons endpoints only. It avoids
club crests, badges, and logos unless a safe non-logo Commons image with
license metadata is found. Roster rows keep source URLs so generated club pages
can show where current squad data was checked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
TODAY = "2026-05-24"
DATA_MODE = "public_beta_demo"
HEADERS = {"User-Agent": "ARESFootballMarket/0.1 (public beta data build; contact: github.com/COG-tech)"}
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
    "psv", "sevilla", "sheffield", "southampton", "sunderland", "tokyo",
    "torino", "torque", "udinese", "united", "villarreal", "watford",
}
SAFE_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
BAD_MEDIA_TOKENS = {
    "logo", "badge", "crest", "emblem", "kit", "icon", "flag", "shirt", "jersey",
    ".pdf", ".svg", ".gif", ".webm", "programme", "program", "newspaper",
    "daily times", "catalogue", "botanische", "map-fr",
}
PREFERRED_MEDIA_TOKENS = {
    "stadium", "stade", "stadion", "arena", "ground", "park", "training",
    "complex", "centre", "center", "pitch", "stand", "grandstand", "tribune",
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
    "USA": ("North America", "CONCACAF", "CONCACAF"),
    "United States": ("North America", "CONCACAF", "CONCACAF"),
    "Mexico": ("North America", "CONCACAF", "CONCACAF"),
    "Canada": ("North America", "CONCACAF", "CONCACAF"),
    "Brazil": ("South America", "CONMEBOL", "CONMEBOL"),
    "Argentina": ("South America", "CONMEBOL", "CONMEBOL"),
    "Japan": ("Asia", "East Asia", "AFC"),
    "South Korea": ("Asia", "East Asia", "AFC"),
    "Saudi Arabia": ("Asia", "Middle East", "AFC"),
    "China": ("Asia", "East Asia", "AFC"),
    "India": ("Asia", "South Asia", "AFC"),
    "Australia": ("Oceania", "Oceania", "AFC"),
    "New Zealand": ("Oceania", "Oceania", "OFC"),
    "Egypt": ("Africa", "North Africa", "CAF"),
    "Morocco": ("Africa", "North Africa", "CAF"),
    "Nigeria": ("Africa", "West Africa", "CAF"),
    "Ghana": ("Africa", "West Africa", "CAF"),
    "South Africa": ("Africa", "Southern Africa", "CAF"),
}

TITLE_ALIASES = {
    "Al-Shabab Football Club": "Al Shabab Club",
    "Neom Club": "Neom SC",
    "A.S. Nancy-Lorraine": "AS Nancy Lorraine",
    "Achilles'29": "Achilles '29",
}


def read_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def read_json_optional(path: str, default: Any) -> Any:
    file_path = ROOT / path
    if not file_path.exists():
        return default
    return json.loads(file_path.read_text(encoding="utf-8"))


def write_json(path: str, payload: Any) -> None:
    out = ROOT / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", ascii_value.lower()).strip("-") or "ares"


def normalized_name(value: Any) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()
    return " ".join(token for token in clean.split() if len(token) > 1 and token not in CLUB_NAME_STOPWORDS)


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


def stable_unit(*parts: str) -> float:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:10], 16) / float(16**10 - 1)


def stable_int(minimum: int, maximum: int, *parts: str) -> int:
    return minimum + int(round(stable_unit(*parts) * (maximum - minimum)))


def clean_text(value: str) -> str:
    value = re.sub(r"\[[^\]]+\]", "", value or "")
    value = re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
    value = re.sub(r"\s*\(.*?(loan|captain|vice-captain).*?\)", "", value, flags=re.I)
    return value.strip(" *")


def is_valid_player_name(name: str, blocked_names: set[str] | None = None) -> bool:
    text = clean_text(name)
    low = text.lower()
    normalized = normalized_name(text)
    blocked_names = blocked_names or set()
    if len(text) < 3:
        return False
    if low in INVALID_PLAYER_NAMES or normalized in INVALID_PLAYER_NAMES or low in blocked_names or normalized in blocked_names:
        return False
    if normalized.startswith("jong ") and normalized[5:] in blocked_names:
        return False
    if re.search(r"\d", text):
        return False
    if any(token in low for token in ["captain", "coach", "manager", "current squad", "on loan"]):
        return False
    words = normalized.split()
    if len(words) <= 4 and any(word in TEAM_NAME_MARKERS for word in words):
        return False
    if "ii" in words:
        return False
    if re.fullmatch(r"[A-Z]{1,3}", text):
        return False
    return True


def log_text(value: str) -> str:
    return value.encode("ascii", "replace").decode("ascii")


def position_code(value: str) -> str:
    text = (value or "").lower()
    if "goalkeeper" in text or text == "gk":
        return "GK"
    if "forward" in text or "striker" in text or text in {"fw", "cf", "st"}:
        return "FW"
    if "wing" in text:
        return "W"
    if "midfielder" in text or text in {"mf", "cm", "dm", "am"}:
        return "MF"
    if "defender" in text or "back" in text or text in {"df", "cb", "lb", "rb"}:
        return "DF"
    return "FB"


def geo_for(country: str, club: dict[str, Any]) -> tuple[str, str, str]:
    return COUNTRY_GEO.get(country or "", (club.get("continent", "Europe"), club.get("region", "Europe"), club.get("confederation", "UEFA")))


def api_get(endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    for attempt in range(6):
        response = requests.get(endpoint, params={**params, "format": "json"}, headers=HEADERS, timeout=30)
        if response.status_code in {429, 503}:
            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after and retry_after.isdigit() else min(45.0, 4.0 * (attempt + 1))
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json()
    response.raise_for_status()
    return response.json()


def wiki_get(params: dict[str, Any]) -> dict[str, Any]:
    return api_get(WIKI_API, params)


def commons_get(params: dict[str, Any]) -> dict[str, Any]:
    return api_get(COMMONS_API, params)


def search_wikipedia_title(club: dict[str, Any]) -> str:
    candidates = [
        f'{club["club_name"]} football club',
        f'{club["club_name"]} football',
        f'{club["club_name"]} {club.get("league", "")}',
        club["club_name"],
    ]
    for query in candidates:
        data = wiki_get({"action": "query", "list": "search", "srsearch": query, "srlimit": 5})
        results = data.get("query", {}).get("search", [])
        if not results:
            continue
        for result in results:
            title = result.get("title", "")
            low = title.lower()
            if "football" in low or "(football" in low:
                return title
        for result in results:
            title = result.get("title", "")
            low = title.lower()
            if any(token in low for token in ["f.c.", "fc", "football", "soccer", "cf", "calcio", "club"]):
                return title
        return results[0].get("title", "")
    return ""


def parse_page(title: str) -> tuple[str, str]:
    data = wiki_get({"action": "parse", "page": title, "prop": "text", "redirects": 1})
    parsed = data.get("parse", {})
    html = parsed.get("text", {}).get("*", "")
    source_url = f"https://en.wikipedia.org/wiki/{quote(parsed.get('title', title).replace(' ', '_'))}"
    return html, source_url


def table_headers(table: Any) -> list[str]:
    first = table.find("tr")
    if not first:
        return []
    cells = first.find_all(["th", "td"])
    return [clean_text(cell.get_text(" ")) for cell in cells]


def extract_player_name(cell: Any) -> str:
    links = [a for a in cell.find_all("a") if a.get_text(strip=True) and not (a.get("href") or "").startswith("/wiki/File:")]
    if links:
        return clean_text(links[-1].get_text(" "))
    return clean_text(cell.get_text(" "))


def parse_age(value: str, fallback_key: str) -> int:
    text = value or ""
    match = re.search(r"age\s*(\d{2})", text, re.I) or re.search(r"\((\d{2})\)", text)
    if match:
        return int(match.group(1))
    return stable_int(18, 34, fallback_key, "age")


def roster_from_html(html: str, club: dict[str, Any], source_url: str, blocked_names: set[str] | None = None) -> tuple[list[dict[str, Any]], str]:
    soup = BeautifulSoup(html, "lxml")
    best_rows: list[dict[str, Any]] = []
    best_reason = "no squad table found"
    for table in soup.select("table"):
        headers = [h.lower() for h in table_headers(table)]
        if not headers or not any("player" in h or "name" in h for h in headers):
            continue
        if not any("pos" in h or "position" in h for h in headers):
            continue
        raw_rows = []
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            values = {headers[i] if i < len(headers) else f"col_{i}": cells[i] for i in range(len(cells))}
            player_cell = next((cell for key, cell in values.items() if "player" in key or "name" in key), None)
            pos_cell = next((cell for key, cell in values.items() if "pos" in key or "position" in key), None)
            if not player_cell:
                continue
            name = extract_player_name(player_cell)
            if not is_valid_player_name(name, blocked_names):
                continue
            position = position_code(clean_text(pos_cell.get_text(" ")) if pos_cell else "")
            nation_cell = next((cell for key, cell in values.items() if "nation" in key or "nationality" in key), None)
            age_cell = next((cell for key, cell in values.items() if "age" in key or "birth" in key or "date" in key), None)
            country = clean_text(nation_cell.get_text(" ")) if nation_cell else club.get("country", "")
            age = parse_age(clean_text(age_cell.get_text(" ")) if age_cell else "", name)
            continent, region, confed = geo_for(club.get("country", ""), club)
            player_id = f"wiki-{club['club_id']}-{slug(name)}"
            raw_rows.append({
                "data_mode": DATA_MODE,
                "player_id": player_id,
                "slug": slug(name),
                "display_name": name,
                "player_name": name,
                "age": age,
                "position": position,
                "club_id": club["club_id"],
                "club": club["club_name"],
                "league_id": club.get("league_id") or f"league-{slug(club.get('league', ''))}",
                "league": club.get("league", ""),
                "country": club.get("country", ""),
                "nationality": country,
                "continent": continent,
                "region": region,
                "confederation": confed,
                "minutes_role": f"{stable_int(650, 3100, player_id)} estimated minutes / current squad",
                "position_usage": f"{position} primary role",
                "ares_score": round(66 + stable_unit(player_id, "ares") * 24, 1),
                "market_score": round(64 + stable_unit(player_id, "market") * 27, 1),
                "ares_tier": "High" if stable_unit(player_id, "ares-tier") > 0.65 else "Starter",
                "market_tier": "Rising Asset" if age <= 23 else "Core Starter",
                "trend": "Rising" if stable_unit(player_id, "trend") > 0.55 else "Stable",
                "transfer_value_signal": "Roster watch",
                "role_security": "Current squad listed",
                "durability": "Source review",
                "data_confidence": "Medium",
                "confidence": "Medium",
                "source": "Wikipedia current squad table",
                "source_url": source_url,
                "roster_checked_date": TODAY,
                "identity_mode": "wikipedia_roster_current_squad",
                "photo_license_status": "ares_owned",
                "photo_source": "ARES fallback avatar",
                "photo_credit": "ARES fallback avatar",
                "photo_status": "fallback",
                "club_url": f"/ares-football-market/clubs/{club['club_id']}/",
                "player_url": f"/ares-football-market/players/profile.html?id={player_id}",
                "league_url": f"/ares-football-market/leagues/index.html?league={slug(club.get('league', ''))}",
                "last_updated": TODAY,
                "contract_end": "Source review",
                "role": "Current squad",
                "age_curve": "Upside" if age <= 23 else ("Prime" if age <= 29 else "Veteran"),
                "reason": "Current club roster row parsed from Wikipedia.",
            })
        if len(raw_rows) > len(best_rows):
            best_rows = raw_rows
            best_reason = "current squad table parsed"
    return best_rows, best_reason


def media_text(*values: str) -> str:
    return " ".join(str(value or "").lower() for value in values)


def bad_file_title(title: str) -> bool:
    low = media_text(title)
    return any(token in low for token in BAD_MEDIA_TOKENS)


def safe_media_url(url: str) -> bool:
    low = media_text(url).split("?", 1)[0]
    return low.endswith(SAFE_IMAGE_EXTENSIONS) and not any(token in low for token in BAD_MEDIA_TOKENS)


def media_title_score(title: str) -> int:
    low = media_text(title)
    return sum(1 for token in PREFERRED_MEDIA_TOKENS if token in low)


def media_record_from_file(title: str, club: dict[str, Any], source_url: str) -> dict[str, Any] | None:
    if bad_file_title(title):
        return None
    try:
        data = commons_get({"action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|extmetadata"})
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        license_name = clean_text(meta.get("LicenseShortName", {}).get("value", ""))
        usage_terms = clean_text(meta.get("UsageTerms", {}).get("value", ""))
        if not license_name or re.search(r"fair use|non-free|trademark|copyrighted", f"{license_name} {usage_terms}", re.I):
            return None
        creator = clean_text(BeautifulSoup(meta.get("Artist", {}).get("value", ""), "lxml").get_text(" ")) or "Wikimedia Commons contributor"
        image_url = info.get("url", "")
        desc_url = info.get("descriptionurl") or source_url
        if not safe_media_url(image_url) or bad_file_title(f"{title} {desc_url}"):
            return None
        return {
            "asset_id": f"club-media-{club['club_id']}",
            "club_id": club["club_id"],
            "club_name": club["club_name"],
            "display_name": club["club_name"],
            "player_name": club["club_name"],
            "image_url": image_url,
            "creator": creator,
            "license": license_name or usage_terms,
            "source_url": desc_url,
            "attribution_text": f"{club['club_name']} image | Creator: {creator} | Source: {desc_url} | License: {license_name or usage_terms}",
            "checked_date": TODAY,
            "rights_checked": TODAY,
            "human_review_status": "non-logo Commons image metadata captured",
            "commercial_allowed": True,
            "data_mode": DATA_MODE,
            "asset_type": "club_image",
        }
    except Exception:
        return None


def media_record_from_titles(titles: list[str], club: dict[str, Any], source_url: str) -> dict[str, Any] | None:
    filtered: list[str] = []
    for title in titles:
        if title and title not in filtered and not bad_file_title(title):
            filtered.append(title)
    if not filtered:
        return None
    try:
        data = commons_get({"action": "query", "titles": "|".join(filtered[:20]), "prop": "imageinfo", "iiprop": "url|extmetadata"})
    except Exception:
        return None
    pages = data.get("query", {}).get("pages", {})
    ordered_pages = sorted(
        pages.values(),
        key=lambda page: (
            -media_title_score(page.get("title", "")),
            filtered.index(page.get("title", filtered[0])) if page.get("title") in filtered else 999,
        ),
    )
    for page in ordered_pages:
        title = page.get("title", "")
        if bad_file_title(title):
            continue
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        license_name = clean_text(meta.get("LicenseShortName", {}).get("value", ""))
        usage_terms = clean_text(meta.get("UsageTerms", {}).get("value", ""))
        if not license_name or re.search(r"fair use|non-free|trademark|copyrighted", f"{license_name} {usage_terms}", re.I):
            continue
        creator = clean_text(BeautifulSoup(meta.get("Artist", {}).get("value", ""), "lxml").get_text(" ")) or "Wikimedia Commons contributor"
        image_url = info.get("url", "")
        desc_url = info.get("descriptionurl") or source_url
        if not safe_media_url(image_url) or bad_file_title(f"{title} {desc_url}"):
            continue
        return {
            "asset_id": f"club-media-{club['club_id']}",
            "club_id": club["club_id"],
            "club_name": club["club_name"],
            "display_name": club["club_name"],
            "player_name": club["club_name"],
            "image_url": image_url,
            "creator": creator,
            "license": license_name or usage_terms,
            "source_url": desc_url,
            "attribution_text": f"{club['club_name']} image | Creator: {creator} | Source: {desc_url} | License: {license_name or usage_terms}",
            "checked_date": TODAY,
            "rights_checked": TODAY,
            "human_review_status": "non-logo Commons image metadata captured",
            "commercial_allowed": True,
            "data_mode": DATA_MODE,
            "asset_type": "club_image",
        }
    return None


def commons_search_titles(query: str) -> list[str]:
    data = commons_get({"action": "query", "list": "search", "srnamespace": 6, "srsearch": query, "srlimit": 10})
    return [item.get("title", "") for item in data.get("query", {}).get("search", []) if item.get("title")]


def first_safe_club_media(html: str, club: dict[str, Any], source_url: str) -> dict[str, Any] | None:
    soup = BeautifulSoup(html, "lxml")
    files: list[str] = []
    for img in soup.select(".infobox a.image, .infobox-image a.image, a.image"):
        href = img.get("href") or ""
        if "/wiki/File:" not in href:
            continue
        title = "File:" + unquote(href.split("/wiki/File:", 1)[1]).replace("_", " ")
        if not bad_file_title(title):
            files.append(title)
    files = sorted(files, key=lambda title: -media_title_score(title))
    preferred_files = [title for title in files if media_title_score(title) > 0]
    record = media_record_from_titles(preferred_files[:10], club, source_url)
    if record:
        return record
    for query in [f'{club["club_name"]} stadium', f'{club["club_name"]} football ground']:
        record = media_record_from_titles(commons_search_titles(query), club, source_url)
        if record:
            return record
    return None


def honours_from_html(html: str, club: dict[str, Any], source_url: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    heading = None
    for candidate in soup.find_all(["h2", "h3", "span"]):
        text = clean_text(candidate.get_text(" "))
        ident = candidate.get("id", "")
        if re.search(r"honou?rs|trophies|achievements", f"{text} {ident}", re.I):
            heading = candidate
            break
    if not heading:
        return []
    node = heading.parent if heading.name == "span" and heading.parent else heading
    rows: list[dict[str, Any]] = []
    current = node
    while current:
        current = current.find_next()
        if not current:
            break
        if current.name == "h2" and current is not node:
            break
        if current.name not in {"li", "tr"}:
            continue
        text = clean_text(current.get_text(" "))
        if len(text) < 5 or len(text) > 240:
            continue
        if re.search(r"source|updated|reference", text, re.I):
            continue
        competition = re.split(r"[:\u2013\u2014-]", text, maxsplit=1)[0].strip()
        years = re.findall(r"(?:19|20)\d{2}", text)
        rows.append({
            "honour_id": f"honour-{club['club_id']}-{len(rows)+1:02d}",
            "club_id": club["club_id"],
            "club_name": club["club_name"],
            "competition": competition[:90],
            "honour_type": "Team honour",
            "count": max(1, len(set(years))),
            "years": sorted(set(years))[:30],
            "level": "Domestic/continental source listing",
            "source_text": text,
            "source_url": source_url,
            "checked_date": TODAY,
            "data_mode": DATA_MODE,
        })
        if len(rows) >= 30:
            break
    return rows


def merge_players(existing: list[dict[str, Any]], roster_rows: list[dict[str, Any]], blocked_names: set[str] | None = None) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in existing:
        if not is_valid_player_name(str(row.get("player_name") or row.get("display_name") or ""), blocked_names):
            continue
        by_key[(slug(row.get("player_name") or row.get("display_name", "")), row.get("club_id", ""))] = row
    for row in roster_rows:
        key = (slug(row["player_name"]), row["club_id"])
        if key in by_key:
            by_key[key].update({
                "club_roster_source": "Wikipedia current squad table",
                "club_roster_source_url": row["source_url"],
                "roster_checked_date": TODAY,
                "role_security": by_key[key].get("role_security") or row["role_security"],
            })
        else:
            by_key[key] = row
    return list(by_key.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Limit clubs for smoke testing. Default: all clubs.")
    parser.add_argument("--club", action="append", default=[], help="Only process a club name, slug, or club_id. Repeatable.")
    parser.add_argument("--sleep", type=float, default=0.8)
    args = parser.parse_args()

    clubs = read_json("data/public_clubs.json")
    existing_players = read_json("data/public_players.json")
    if args.club:
        requested = {slug(item) for item in args.club}
        clubs = [
            club for club in clubs
            if slug(club.get("club_id", "")) in requested
            or slug(club.get("club_name", "")) in requested
            or slug(club.get("club_name", "").replace(" F.C.", "").replace(" FC", "")) in requested
        ]
    if args.limit:
        clubs = clubs[:args.limit]
    blocked_names = blocked_name_variants(
        read_json_optional("data/public_clubs.json", []),
        read_json_optional("data/public_leagues.json", []),
    )

    all_rosters: list[dict[str, Any]] = []
    honours: list[dict[str, Any]] = []
    media: list[dict[str, Any]] = []
    statuses: list[dict[str, Any]] = []

    for index, club in enumerate(clubs, 1):
        title = ""
        source_url = ""
        roster_rows: list[dict[str, Any]] = []
        honour_rows: list[dict[str, Any]] = []
        media_row = None
        status = "not_checked"
        reason = ""
        try:
            title = TITLE_ALIASES.get(club["club_name"], club["club_name"])
            try:
                html, source_url = parse_page(title)
            except Exception:
                title = search_wikipedia_title(club)
                html, source_url = parse_page(title) if title else ("", "")
            if not html:
                reason = "no Wikipedia search result"
            else:
                roster_rows, reason = roster_from_html(html, club, source_url, blocked_names)
                honour_rows = honours_from_html(html, club, source_url)
                media_row = first_safe_club_media(html, club, source_url)
                if not roster_rows:
                    alt_title = search_wikipedia_title(club)
                    if alt_title and alt_title != title:
                        alt_html, alt_source_url = parse_page(alt_title)
                        alt_roster_rows, alt_reason = roster_from_html(alt_html, club, alt_source_url, blocked_names)
                        if len(alt_roster_rows) > len(roster_rows):
                            title = alt_title
                            source_url = alt_source_url
                            roster_rows = alt_roster_rows
                            reason = alt_reason
                            honour_rows = honours_from_html(alt_html, club, alt_source_url)
                            media_row = first_safe_club_media(alt_html, club, alt_source_url)
                status = "checked"
        except Exception as exc:
            status = "error"
            reason = str(exc)[:180]
        all_rosters.extend(roster_rows)
        honours.extend(honour_rows)
        if media_row:
            media.append(media_row)
        statuses.append({
            "club_id": club["club_id"],
            "club_name": club["club_name"],
            "wikipedia_title": title,
            "source_url": source_url,
            "status": status,
            "roster_rows": len(roster_rows),
            "honours_rows": len(honour_rows),
            "club_media_rows": 1 if media_row else 0,
            "reason": reason,
            "checked_date": TODAY,
        })
        print(log_text(f"{index}/{len(clubs)} {club['club_name']}: roster={len(roster_rows)} honours={len(honour_rows)} media={1 if media_row else 0} {reason}"), flush=True)
        time.sleep(args.sleep)

    if args.club:
        selected_ids = {club["club_id"] for club in clubs}
        existing_rosters = [row for row in read_json_optional("data/club_rosters_wikipedia.json", []) if row.get("club_id") not in selected_ids]
        existing_honours = [row for row in read_json_optional("data/club_honours.json", []) if row.get("club_id") not in selected_ids]
        existing_media = [row for row in read_json_optional("data/club_media_wikimedia.json", []) if row.get("club_id") not in selected_ids]
        existing_status = [row for row in read_json_optional("data/club_source_status.json", []) if row.get("club_id") not in selected_ids]
        all_rosters = existing_rosters + all_rosters
        honours = existing_honours + honours
        media = existing_media + media
        statuses = existing_status + statuses

    merged_players = merge_players(existing_players, all_rosters, blocked_names)
    write_json("data/public_players.json", merged_players)
    write_json("data/club_rosters_wikipedia.json", all_rosters)
    write_json("data/club_honours.json", honours)
    write_json("data/club_media_wikimedia.json", media)
    write_json("data/club_source_status.json", statuses)
    print(log_text(f"clubs_checked={len(statuses)} roster_rows={len(all_rosters)} honours={len(honours)} club_media={len(media)} players={len(merged_players)}"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
