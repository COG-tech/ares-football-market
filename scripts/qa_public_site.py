#!/usr/bin/env python3
"""QA checks for the generated ARES Football Market static site."""

from __future__ import annotations

import json
import re
import sys
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
    "pending",
    "Loading open",
    "Public Beta Demo",
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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def count_rows(html: str) -> int:
    return len(re.findall(r"<tr\b", html))


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


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
        if re.search(r'href="(?:\.\./|\.\./\.\./)?clubs/club-[^"]+/"', html):
            fail(f"Page has relative club links instead of site-root club links: {page}", failures)

    players = load_json("data/public_players.json")
    clubs = load_json("data/public_clubs.json")
    credits = load_json("data/image_credits_wikimedia.json")

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

    club_html = read("clubs/index.html")
    club_links = re.findall(r"/ares-football-market/clubs/(club-[^/\"<]+)/", club_html)
    if len(set(club_links)) < 10:
        fail("Clubs page has fewer than 10 distinct static roster links.", failures)
    valid_club_ids = {str(club.get("club_id")) for club in clubs}
    missing_club_ids = [club_id for club_id in set(club_links[:50]) if club_id not in valid_club_ids]
    if missing_club_ids:
        fail(f"Club links reference missing club pages: {missing_club_ids[:5]}", failures)

    for club_id in list(valid_club_ids)[:10]:
        club_page = ROOT / "clubs" / club_id / "index.html"
        if not club_page.exists():
            fail(f"Missing static club roster page: clubs/{club_id}/index.html", failures)
            continue
        rows = count_rows(club_page.read_text(encoding="utf-8"))
        if rows < 2:
            fail(f"Static club roster page has too few rows: clubs/{club_id}/index.html", failures)

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
