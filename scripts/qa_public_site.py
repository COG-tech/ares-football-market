#!/usr/bin/env python3
"""QA checks for the generated ARES Football Market static site."""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_HTML = [
    "Public Beta Demo Board rows initialize from the public beta dataset.",
    "Public Beta Demo rows are unavailable",
    "rows initialize",
    "rows unavailable",
    "rows load from file",
    "local dataset",
    "placeholder",
    "Loading open",
]

MAJOR_PAGES = [
    "index.html",
    "players/index.html",
    "rankings/ares.html",
    "rankings/market.html",
    "clubs/index.html",
    "leagues/index.html",
    "leagues/mls.html",
    "leagues/mls/index.html",
    "leagues/north-america.html",
    "transfers/index.html",
    "watchlist/index.html",
    "continents/europe/index.html",
    "continents/asia/index.html",
    "continents/africa/index.html",
    "continents/north-america/index.html",
    "continents/south-america/index.html",
    "continents/oceania/index.html",
    "image-credits.html",
]
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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_json_optional(path: str, default):
    file_path = ROOT / path
    if not file_path.exists():
        return default
    return json.loads(file_path.read_text(encoding="utf-8"))


def count_rows(html: str) -> int:
    return len(re.findall(r"<tr\b", html))


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def normalized_name(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()
    return " ".join(token for token in clean.split() if len(token) > 1 and token not in CLUB_NAME_STOPWORDS)


def blocked_name_variants(clubs: list[dict], leagues: list[dict]) -> set[str]:
    blocked: set[str] = set()
    for item in list(clubs) + list(leagues):
        for key in ("club_name", "league_name"):
            value = str(item.get(key, "")).strip()
            if value:
                blocked.add(value.lower())
                normalized = normalized_name(value)
                if normalized:
                    blocked.add(normalized)
    return blocked


def main() -> int:
    failures: list[str] = []

    for page in MAJOR_PAGES:
        path = ROOT / page
        if not path.exists():
            fail(f"Missing page: {page}", failures)
            continue
        html = read(page)
        for phrase in FORBIDDEN_HTML:
            if phrase.lower() in html.lower():
                fail(f"Forbidden public copy in {page}: {phrase}", failures)
        rows = count_rows(html)
        if rows < 2:
            fail(f"Too few table rows in {page}: {rows}", failures)
        if page != "image-credits.html" and "ares-terminal-grid" not in html:
            fail(f"Missing terminal graph layout in {page}", failures)
        if page != "image-credits.html" and "ares-kpi-grid" not in html:
            fail(f"Missing KPI card layout in {page}", failures)
        if page != "image-credits.html" and ("X-axis:" not in html or "Y-axis:" not in html or "How to read:" not in html):
            fail(f"Missing labelled graph axes/explanation in {page}", failures)
        if re.search(r'href="(?:\.\./|\.\./\.\./)?clubs/club-[^"]+/"', html):
            fail(f"Page has relative club links instead of site-root club links: {page}", failures)

    players = load_json("data/public_players.json")
    clubs = load_json("data/public_clubs.json")
    leagues = load_json("data/public_leagues.json")
    credits = load_json("data/image_credits_wikimedia.json")
    club_rosters = load_json_optional("data/club_rosters_wikipedia.json", [])
    club_honours = load_json_optional("data/club_honours.json", [])
    club_media = load_json_optional("data/club_media_wikimedia.json", [])
    club_status = load_json_optional("data/club_source_status.json", [])

    if len(club_status) < len(clubs):
        fail(f"Club source status does not cover every club: status={len(club_status)} clubs={len(clubs)}", failures)
    club_ids = {str(club.get("club_id")) for club in clubs}
    status_ids = {str(item.get("club_id")) for item in club_status}
    missing_status = sorted(club_ids - status_ids)
    if missing_status:
        fail(f"Club source status is missing final club IDs: {missing_status[:8]}", failures)
    if len(club_rosters) < len(clubs) * 5:
        fail(f"Wikipedia roster layer is too small: roster_rows={len(club_rosters)} clubs={len(clubs)}", failures)
    if len(club_honours) < 50:
        fail(f"Club honours layer is too small: honours={len(club_honours)}", failures)
    club_credit_rows = [item for item in credits if item.get("asset_type") == "club_image"]
    if club_media and len(club_credit_rows) < len(club_media):
        fail(f"Image credits do not include every club media row: club_media={len(club_media)} credit_rows={len(club_credit_rows)}", failures)
    required_media_fields = ["asset_id", "club_id", "club_name", "image_url", "creator", "license", "source_url", "attribution_text", "checked_date", "human_review_status"]
    for item in club_media:
        missing = [field for field in required_media_fields if not item.get(field)]
        if missing:
            fail(f"Club media row is missing rights fields for {item.get('club_id')}: {missing}", failures)
            break
        image_url = str(item.get("image_url") or "")
        source_url = str(item.get("source_url") or "")
        joined = f"{image_url} {source_url}".lower()
        clean_url = image_url.lower().split("?", 1)[0]
        if not clean_url.endswith(SAFE_IMAGE_EXTENSIONS) or any(token in joined for token in BAD_MEDIA_TOKENS):
            fail(f"Club media row is not a safe raster non-logo image for {item.get('club_id')}: {image_url}", failures)
            break
    required_honour_fields = ["club_id", "club_name", "competition", "honour_type", "count", "years", "level", "source_url", "checked_date"]
    for item in club_honours:
        missing = [field for field in required_honour_fields if item.get(field) in (None, "")]
        if missing:
            fail(f"Club honour row is missing normalized fields for {item.get('club_id')}: {missing}", failures)
            break
    roster_counts = {}
    for player in players:
        club_id = str(player.get("club_id") or "")
        roster_counts[club_id] = roster_counts.get(club_id, 0) + 1
    empty_roster_clubs = [club.get("club_id") for club in clubs if roster_counts.get(str(club.get("club_id")), 0) == 0]
    if empty_roster_clubs:
        fail(f"Club pages would have empty rosters: {empty_roster_clubs[:8]}", failures)
    blocked_names = blocked_name_variants(clubs, leagues)
    bad_player_names = []
    for player in players:
        name = str(player.get("player_name") or player.get("display_name") or "").strip()
        low = name.lower()
        normalized = normalized_name(name)
        words = normalized.split()
        if (
            len(name) < 3
            or low in INVALID_PLAYER_NAMES
            or normalized in INVALID_PLAYER_NAMES
            or low in blocked_names
            or normalized in blocked_names
            or (normalized.startswith("jong ") and normalized[5:] in blocked_names)
            or re.search(r"\d", name)
            or any(token in low for token in ["captain", "coach", "manager", "current squad", "on loan"])
            or (len(words) <= 4 and any(word in TEAM_NAME_MARKERS for word in words))
            or "ii" in words
        ):
            bad_player_names.append((player.get("club"), name))
    if bad_player_names:
        fail(f"Malformed roster/player names remain: {bad_player_names[:10]}", failures)

    player_html = read("players/index.html")
    player_link_ids = re.findall(r"(?:/ares-football-market/)?players/profile\.html\?id=([^\"&<]+)", player_html)
    if len(set(player_link_ids)) < 10:
        fail("Player Search has fewer than 10 distinct profile links.", failures)
    valid_player_ids = {str(player.get("player_id")) for player in players}
    missing_player_ids = [player_id for player_id in set(player_link_ids[:50]) if player_id not in valid_player_ids]
    if missing_player_ids:
        fail(f"Player links reference missing IDs: {missing_player_ids[:5]}", failures)

    profile_html = read("players/profile.html")
    if "/ares-football-market/players/profile.html?id=" in profile_html or "players/profile.html?id=" in profile_html:
        fail("Player profile template contains hard-coded self profile links.", failures)
    if "player-roster-link" not in profile_html:
        fail("Player profile is missing View club roster CTA.", failures)
    for required_profile_markup in ["ares-profile-topbar", "ares-profile-search", "ares-profile-hero", "ares-player-score-deck", "ares-player-tab-panel", "Public Beta Demo", "Club Fit"]:
        if required_profile_markup not in profile_html:
            fail(f"Player profile shell is missing: {required_profile_markup}", failures)
    if "Loading player intelligence view" in profile_html:
        fail("Player profile still contains the old loading shell copy.", failures)
    profile_views = set(re.findall(r'data-profile-view="([^"]+)"', profile_html))
    expected_views = {"overview", "stats", "market", "transfers", "rumours", "national-team", "news", "achievements", "career"}
    if profile_views != expected_views:
        fail(f"Player profile tab set is wrong: {sorted(profile_views)}", failures)
    for label in ["Profile", "Stats", "Market Value", "Transfers", "Rumours", "National Team", "News", "Achievements", "Career"]:
        if f">{label}<" not in profile_html:
            fail(f"Player profile tab label is missing: {label}", failures)
    if 'id="foot"' not in profile_html or ">Foot<" not in profile_html:
        fail("Shared player header is missing foot field.")
    soccer_js = read("assets/js/soccer-pages.js")
    for title in ["Overview", "Stats Center", "Market Value Intelligence", "Transfer Intelligence", "Rumour Intelligence", "National Team Profile", "Player News Terminal", "Achievements", "Career Intelligence"]:
        if title not in soccer_js:
            fail(f"Player tab renderer is missing title: {title}", failures)
    for overview_marker in ["ares-profile-dashboard", "ares-numbered-card", "ARES Performance Snapshot", "Market Intelligence", "Position Usage", "ARES Form Trend", "Attacker Component Grades", "Comparable Players"]:
        if overview_marker not in soccer_js:
            fail(f"Player overview screenshot module is missing: {overview_marker}", failures)
    if "X-axis:" not in soccer_js or "Y-axis:" not in soccer_js or "How to read:" not in soccer_js:
        fail("Player tab graphs are missing explicit axis labels or explanations.", failures)
    for required_graph_markup in ["ares-chart-line-labels", "ares-chart-scatter-labels", "ares-chart-seeded-note", "Seeded beta data. Live feeds are not connected."]:
        if required_graph_markup not in soccer_js:
            fail(f"Player tab graph labelling is missing: {required_graph_markup}", failures)
    css = read("assets/css/ares-components.css")
    for required_css in [".ares-player-tabs a.is-active", "rgba(247, 201, 72", ".ares-player-tabs a:hover", ".ares-profile-topbar", ".ares-profile-hero", ".ares-numbered-card", ".ares-score-card", ".ares-profile-dashboard"]:
        if required_css not in css:
            fail(f"Player tab active/hover styling is missing: {required_css}", failures)

    club_html = read("clubs/index.html")
    club_links = re.findall(r"/ares-football-market/clubs/(club-[^/\"<]+)/", club_html)
    if len(set(club_links)) < 10:
        fail("Clubs page has fewer than 10 distinct static roster links.", failures)
    valid_club_ids = {str(club.get("club_id")) for club in clubs}
    missing_club_ids = [club_id for club_id in set(club_links[:50]) if club_id not in valid_club_ids]
    if missing_club_ids:
        fail(f"Club links reference missing club pages: {missing_club_ids[:5]}", failures)

    for club_id in sorted(valid_club_ids):
        club_page = ROOT / "clubs" / club_id / "index.html"
        if not club_page.exists():
            fail(f"Missing static club roster page: clubs/{club_id}/index.html", failures)
            continue
        rows = count_rows(club_page.read_text(encoding="utf-8"))
        club_html_text = club_page.read_text(encoding="utf-8")
        if rows < 2:
            fail(f"Static club roster page has too few rows: clubs/{club_id}/index.html", failures)
        if "ares-kpi-grid" not in club_html_text or "ares-terminal-grid" not in club_html_text:
            fail(f"Static club roster page is missing terminal KPI/graph layout: clubs/{club_id}/index.html", failures)
        for required in ["Current Player Roster", "Club Honours And Trophies", "Transfer Needs", "Roster source:", "Domestic League Titles", "Domestic Cups", "Continental Honours", "Total Listed Honours", "Squad Age Curve", "U23 Pipeline", "Source And Rights Note", "Profile"]:
            if required not in club_html_text:
                fail(f"Static club roster page is missing {required}: clubs/{club_id}/index.html", failures)
        if club_html_text.count("ares-graph-card") < 4:
            fail(f"Static club roster page has fewer than four graph cards: clubs/{club_id}/index.html", failures)
        if "X-axis:" not in club_html_text or "Y-axis:" not in club_html_text or "How to read:" not in club_html_text:
            fail(f"Static club roster page is missing chart axes: clubs/{club_id}/index.html", failures)
        if "Club Honours And Trophies" in club_html_text and "Honours data pending source review" not in club_html_text and "Team honour" not in club_html_text:
            fail(f"Static club roster page has no honours rows or pending note: clubs/{club_id}/index.html", failures)
        if '<figure class="ares-club-media">' in club_html_text and club_id not in {str(item.get("club_id")) for item in club_media}:
            fail(f"Static club roster page shows club media without registry row: clubs/{club_id}/index.html", failures)

    credit_html = read("image-credits.html")
    if credits and count_rows(credit_html) < 10:
        fail("Image credits registry has data but page renders too few rows.", failures)
    if "licensed Wikimedia Commons photos are active" in read("index.html") and not credits:
        fail("Homepage claims Commons photos active without credit records.", failures)

    if failures:
        print("ARES public site QA failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("ARES public site QA passed.")
    print(f"players={len(players)} clubs={len(clubs)} credits={len(credits)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
