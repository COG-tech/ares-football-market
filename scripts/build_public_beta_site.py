from __future__ import annotations

import html
import json
import re
import shutil
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIRROR = Path(r"D:\ARES_MARKET_NETWORK\ares-soccer-market\site")
TODAY = "May 22, 2026"
ISO_TODAY = "2026-05-22"
ASSET_VERSION = "20260522-publicbeta"
SOURCE = "Seeded beta data"


def write_text(relative: str, text: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    mirror = MIRROR / relative
    if MIRROR.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(text, encoding="utf-8")


def write_json(relative: str, data) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    write_text(relative, text)


def mirror_existing(relative: str) -> None:
    mirror = MIRROR / relative
    if MIRROR.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, mirror)


def safe_id(value: str) -> str:
    return (
        value.lower()
        .replace(" / ", "-")
        .replace(" ", "-")
        .replace(".", "")
        .replace("Ã­", "i")
        .replace("Ã©", "e")
        .replace("Ã£", "a")
        .replace("'", "")
    )


def photo_fields() -> dict:
    return {
        "photo_url": "",
        "photo_source": "ARES fallback avatar",
        "photo_license_status": "branded_fallback",
        "photo_credit": "ARES public beta generated avatar",
        "photo_attribution_url": "",
        "photo_status": "fallback",
        "image_confidence": "High",
    }


def safe_id(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def owned_photo_fields(asset_url: str) -> dict:
    return {
        "photo_url": asset_url,
        "photo_source": "ARES owned generated public-beta image",
        "photo_license_status": "ares_owned",
        "photo_credit": "ARES public beta generated image",
        "photo_attribution_url": "",
        "photo_status": "available",
        "image_confidence": "High",
    }


def player(
    rank: int,
    name: str,
    age: int,
    position: str,
    club: str,
    league: str,
    country: str,
    region: str,
    minutes: int,
    ares: float,
    ares_tier: str,
    market: float,
    market_tier: str,
    trend: str,
    trend_value: float,
    contract_end: str,
    role: str,
    reason: str,
    confidence: str = "Medium",
) -> dict:
    player_id = f"pbp-{rank:03d}"
    row = {
        "data_mode": "public_beta_demo",
        "rank": rank,
        "player_id": player_id,
        "player_name": name,
        "initials": "".join(part[0] for part in name.split()[:3]).upper(),
        "age": age,
        "position": position,
        "club": club,
        "league": league,
        "country": country,
        "region": region,
        "minutes": minutes,
        "ares_score": ares,
        "ares_tier": ares_tier,
        "market_score": market,
        "market_tier": market_tier,
        "trend": trend,
        "trend_value": trend_value,
        "contract_end": contract_end,
        "role": role,
        "reason": reason,
        "data_confidence": confidence,
        "confidence": confidence,
        "last_updated": ISO_TODAY,
        "source": SOURCE,
        "url": "players/player-template.html",
        "player_url": "players/player-template.html",
        "club_url": "clubs/club-template.html",
        "league_url": "leagues/league-template.html",
    }
    row.update(owned_photo_fields(f"assets/media/public-beta/players/{player_id}.svg"))
    return row


players = [
    player(1, "Ari Solenne", 24, "AM", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 2810, 91.2, "Elite", 90.4, "Franchise Asset", "Rising", 3.8, "2028", "Creator starter", "Prime-age creator with heavy chance creation and stable minutes.", "High"),
    player(2, "Niko Arvellan", 21, "RW", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 2264, 86.7, "High", 92.6, "Blue-Chip Asset", "Rising", 5.1, "2029", "U22 starter", "Explosive wide role, age curve, and high-value contract window.", "Medium"),
    player(3, "Matei Corvan", 27, "DM", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 2978, 88.9, "Elite", 84.2, "Core Starter", "Flat", 0.4, "2027", "Ball-winning starter", "High role security with less age upside than younger assets.", "High"),
    player(4, "Jalen Roca", 23, "CB", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 2740, 84.1, "High", 86.8, "Rising Asset", "Rising", 2.7, "2028", "Starting center back", "Scarce profile with aerial value and improving progression.", "Medium"),
    player(5, "Elian Moreau", 19, "ST", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 1410, 78.6, "Starter", 88.5, "Rising Asset", "Rising", 6.4, "2030", "Rotation striker", "Young striker with strong usage growth and finishing signal.", "Medium"),
    player(6, "Silas Keane", 29, "GK", "Pacific Harbor FC", "Major League Soccer", "USA", "North America", 3060, 82.4, "Starter", 76.9, "Core Starter", "Flat", -0.1, "2026", "Starting goalkeeper", "Reliable shot-stopping profile with short contract horizon.", "High"),
    player(7, "Tavo Lirente", 25, "CM", "Monterra Azul", "Liga MX", "Mexico", "North America", 3012, 89.6, "Elite", 87.7, "Blue-Chip Asset", "Rising", 2.9, "2028", "Box-to-box starter", "Two-way midfielder with strong minutes, age, and league-strength balance.", "High"),
    player(8, "Rui Calder", 20, "LW", "Monterra Azul", "Liga MX", "Mexico", "North America", 1888, 82.7, "High", 90.1, "Blue-Chip Asset", "Rising", 4.8, "2029", "U23 wide starter", "Age curve and shot creation drive market signal above current ARES.", "Medium"),
    player(9, "Mica Darrow", 22, "RB", "Cascadia Union", "Major League Soccer", "Canada", "North America", 2495, 80.6, "Starter", 83.9, "Rising Asset", "Rising", 2.1, "2027", "Attacking fullback", "Progressive carries and U23 window support asset value.", "Medium"),
    player(10, "Noa Kestral", 18, "CM", "Valley Forge FC", "MLS Next Pro", "USA", "North America", 1720, 74.8, "Watchlist", 85.5, "Watchlist", "Rising", 7.2, "2029", "Development starter", "Thin-data prospect with role expansion and strong age curve.", "Low"),
    player(11, "Ren Iwasato", 24, "AM", "Tokyo Bay Verdes", "J1 League", "Japan", "Asia", 2842, 90.3, "Elite", 89.5, "Blue-Chip Asset", "Rising", 3.4, "2028", "Creator starter", "High on-ball usage, chance creation, and league-adjusted efficiency.", "High"),
    player(12, "Kaito Meren", 21, "ST", "Osaka Minato", "J2 League", "Japan", "Asia", 2311, 83.6, "High", 88.2, "Rising Asset", "Rising", 4.2, "2027", "Starting forward", "Young forward production with promotion-market upside.", "Medium"),
    player(13, "Joon Hara", 26, "CB", "Seoul Han River", "K League 1", "South Korea", "Asia", 3120, 87.4, "High", 82.8, "Core Starter", "Flat", 0.3, "2026", "Defensive leader", "Elite availability and defensive volume with shorter contract runway.", "High"),
    player(14, "Minseo Vale", 20, "RW", "Busan Tides", "K League 2", "South Korea", "Asia", 1962, 79.3, "Starter", 86.3, "Rising Asset", "Rising", 4.9, "2028", "Wide starter", "Young wide creator with second-division translation risk.", "Medium"),
    player(15, "Samir Qadir", 28, "ST", "Riyadh Horizon", "Saudi Pro League", "Saudi Arabia", "Asia", 2660, 88.1, "Elite", 83.4, "Core Starter", "Flat", 0.1, "2027", "Starting striker", "Current production is strong, but market score is moderated by age curve.", "Medium"),
    player(16, "Leandro Saye", 23, "DM", "Doha Meridian", "Qatar Stars League", "Qatar", "Asia", 2596, 84.9, "High", 85.8, "Rising Asset", "Rising", 2.0, "2028", "Deep midfielder", "Role security and scarce defensive midfield profile.", "Medium"),
    player(17, "Yun Fei Valeo", 22, "LW", "Shanghai Docklands", "Chinese Super League", "China", "Asia", 2210, 81.4, "Starter", 84.4, "Rising Asset", "Rising", 2.8, "2027", "Wide starter", "Improving direct attacking output in a visible market.", "Medium"),
    player(18, "Arman Navid", 24, "CM", "Tehran Atlas", "Persian Gulf Pro League", "Iran", "Asia", 2866, 85.7, "High", 83.1, "Core Starter", "Flat", 0.6, "2026", "Tempo midfielder", "Reliable production with limited verified movement signal.", "Medium"),
    player(19, "Luca Marrin", 19, "AM", "Melbourne Southern", "A-League", "Australia", "Oceania", 1558, 76.5, "Watchlist", 86.9, "Rising Asset", "Rising", 7.0, "2029", "U23 creator", "Young attacking midfielder with early minutes growth.", "Low"),
    player(20, "Dev Rayan", 22, "ST", "Goa Coast FC", "Indian Super League", "India", "Asia", 2440, 80.9, "Starter", 82.6, "Core Starter", "Rising", 2.3, "2027", "Starting forward", "Domestic scoring signal with rising regional visibility.", "Medium"),
    player(21, "Pran Veda", 20, "CM", "Bengal Metro", "Indian Super League", "India", "Asia", 2048, 77.8, "Watchlist", 84.9, "Rising Asset", "Rising", 5.5, "2028", "U23 midfielder", "Minutes growth and age curve drive market profile.", "Low"),
    player(22, "Chai Vannar", 24, "RB", "Bangkok Lanterns", "Thai League 1", "Thailand", "Asia", 2712, 82.8, "Starter", 81.7, "Core Starter", "Flat", 0.2, "2027", "Attacking fullback", "Availability and progressive role support stable asset value.", "Medium"),
    player(23, "Minh Caro", 23, "AM", "Hanoi Capital", "V.League 1", "Vietnam", "Asia", 2534, 83.2, "High", 84.0, "Rising Asset", "Rising", 3.0, "2028", "Creator starter", "High chance-creation share in a discovery market.", "Medium"),
    player(24, "Rafi Nural", 21, "CB", "Jakarta Crown", "Indonesia Liga 1", "Indonesia", "Asia", 2382, 79.8, "Starter", 83.3, "Rising Asset", "Rising", 3.5, "2027", "Starting center back", "Young defender with strong aerial profile and expanding minutes.", "Low"),
    player(25, "Elias Bryn", 26, "LW", "Cape Meridian", "South African Premier Division", "South Africa", "Africa", 2748, 84.2, "High", 80.8, "Core Starter", "Flat", 0.5, "2026", "Wide starter", "Strong current quality but moderate cross-market demand.", "Medium"),
    player(26, "Tiago Vesper", 22, "ST", "Rio Norte", "Brazil Serie A", "Brazil", "South America", 2126, 85.4, "High", 89.2, "Blue-Chip Asset", "Rising", 4.4, "2028", "Rotating forward", "High-value age and scarcity signal in a major export market.", "Medium"),
    player(27, "Santi Reval", 28, "CM", "Buenos Sur", "Argentine Primera", "Argentina", "South America", 2950, 86.0, "High", 81.1, "Core Starter", "Flat", -0.2, "2026", "Senior starter", "High current quality with lower age-upside profile.", "High"),
    player(28, "Milo Ostheim", 23, "GK", "Rhine Borough", "German Bundesliga", "Germany", "Europe", 3060, 83.8, "High", 84.6, "Core Starter", "Rising", 1.5, "2027", "Starting goalkeeper", "Young goalkeeper with stable first-team role.", "Medium"),
]


def club(
    rank: int,
    name: str,
    country: str,
    region: str,
    league: str,
    tier: int,
    squad: int,
    age: float,
    ares: float,
    market: float,
    u23: float,
    top_asset: str,
    weak: str,
    trend: str,
    confidence: str = "Medium",
) -> dict:
    club_id = f"pbc-{rank:03d}"
    return {
        "data_mode": "public_beta_demo",
        "rank": rank,
        "club_id": club_id,
        "club_name": name,
        "club_badge_url": f"assets/media/public-beta/clubs/{club_id}.svg",
        "badge_source": "ARES owned generated public-beta badge",
        "badge_license_status": "ares_owned",
        "country": country,
        "region": region,
        "league": league,
        "tier": tier,
        "squad_size": squad,
        "average_age": age,
        "avg_ares": ares,
        "average_ares_score": ares,
        "avg_market": market,
        "average_market_score": market,
        "u23_value": u23,
        "top_asset": top_asset,
        "weakest_unit": weak,
        "trend": trend,
        "data_confidence": confidence,
        "confidence": confidence,
        "last_updated": ISO_TODAY,
        "source": SOURCE,
        "club_url": "clubs/club-template.html",
        "league_url": "leagues/league-template.html",
    }


clubs = [
    club(1, "Pacific Harbor FC", "USA", "North America", "Major League Soccer", 1, 29, 25.8, 84.1, 86.9, 88.4, "Niko Arvellan", "Left back depth", "Rising", "High"),
    club(2, "Monterra Azul", "Mexico", "North America", "Liga MX", 1, 27, 25.1, 83.6, 85.2, 86.0, "Rui Calder", "Center back depth", "Rising", "High"),
    club(3, "Tokyo Bay Verdes", "Japan", "Asia", "J1 League", 1, 28, 25.4, 82.8, 84.3, 82.7, "Ren Iwasato", "Striker depth", "Rising", "High"),
    club(4, "Seoul Han River", "South Korea", "Asia", "K League 1", 1, 27, 26.3, 81.7, 80.8, 78.6, "Joon Hara", "U23 midfield", "Falling", "High"),
    club(5, "Riyadh Horizon", "Saudi Arabia", "Asia", "Saudi Pro League", 1, 30, 27.6, 82.2, 81.5, 73.2, "Samir Qadir", "Aging attack", "Falling", "Medium"),
    club(6, "Shanghai Docklands", "China", "Asia", "Chinese Super League", 1, 28, 26.5, 79.8, 80.6, 79.4, "Yun Fei Valeo", "Defensive midfield", "Rising", "Medium"),
    club(7, "Melbourne Southern", "Australia", "Oceania", "A-League", 1, 26, 24.6, 77.9, 81.2, 85.5, "Luca Marrin", "Goalkeeper depth", "Rising", "Medium"),
    club(8, "Goa Coast FC", "India", "Asia", "Indian Super League", 1, 27, 24.9, 78.8, 80.1, 82.0, "Dev Rayan", "Fullback depth", "Rising", "Medium"),
    club(9, "Bangkok Lanterns", "Thailand", "Asia", "Thai League 1", 1, 26, 25.7, 77.5, 78.3, 79.8, "Chai Vannar", "Finishing depth", "Falling", "Medium"),
    club(10, "Rio Norte", "Brazil", "South America", "Brazil Serie A", 1, 30, 24.3, 82.4, 85.7, 88.1, "Tiago Vesper", "Right back depth", "Rising", "Medium"),
    club(11, "Cape Meridian", "South Africa", "Africa", "South African Premier Division", 1, 28, 26.8, 78.4, 77.6, 74.9, "Elias Bryn", "U23 attack", "Falling", "Medium"),
    club(12, "Rhine Borough", "Germany", "Europe", "German Bundesliga", 1, 27, 25.9, 83.1, 84.9, 80.5, "Milo Ostheim", "Wing depth", "Falling", "Medium"),
]


required_leagues = [
    ("Major League Soccer", "USA", "North America", 1),
    ("MLS Next Pro", "USA", "North America", 3),
    ("USL Championship", "USA", "North America", 2),
    ("USL League One", "USA", "North America", 3),
    ("USL League Two", "USA", "North America", 4),
    ("Liga MX", "Mexico", "North America", 1),
    ("Liga de ExpansiÃ³n MX", "Mexico", "North America", 2),
    ("Canadian Premier League", "Canada", "North America", 1),
    ("CONCACAF Champions Cup", "CONCACAF", "North America", 0),
    ("J1 League", "Japan", "Asia", 1),
    ("J2 League", "Japan", "Asia", 2),
    ("J3 League", "Japan", "Asia", 3),
    ("K League 1", "South Korea", "Asia", 1),
    ("K League 2", "South Korea", "Asia", 2),
    ("Saudi Pro League", "Saudi Arabia", "Asia", 1),
    ("Chinese Super League", "China", "Asia", 1),
    ("A-League", "Australia", "Oceania", 1),
    ("Indian Super League", "India", "Asia", 1),
    ("UAE Pro League", "UAE", "Asia", 1),
    ("Qatar Stars League", "Qatar", "Asia", 1),
    ("Persian Gulf Pro League", "Iran", "Asia", 1),
    ("Uzbekistan Super League", "Uzbekistan", "Asia", 1),
    ("Thai League 1", "Thailand", "Asia", 1),
    ("Thai League 2", "Thailand", "Asia", 2),
    ("Malaysia Super League", "Malaysia", "Asia", 1),
    ("V.League 1", "Vietnam", "Asia", 1),
    ("Indonesia Liga 1", "Indonesia", "Asia", 1),
    ("Singapore Premier League", "Singapore", "Asia", 1),
    ("Hong Kong Premier League", "Hong Kong", "Asia", 1),
    ("Taiwan Football Premier League", "Taiwan", "Asia", 1),
    ("AFC Champions League Elite", "AFC", "Asia", 0),
    ("AFC Champions League Two", "AFC", "Asia", 0),
    ("Brazil Serie A", "Brazil", "South America", 1),
    ("Argentine Primera", "Argentina", "South America", 1),
    ("South African Premier Division", "South Africa", "Africa", 1),
    ("Egypt Premier League", "Egypt", "Africa", 1),
    ("German Bundesliga", "Germany", "Europe", 1),
    ("Atlantic Premier", "England", "Europe", 1),
]


def league_row(index: int, name: str, country: str, region: str, tier: int) -> dict:
    club_match = next((c for c in clubs if c["league"] == name), None)
    player_match = next((p for p in players if p["league"] == name), None)
    base = 72 + (index % 8) + (2 if tier == 1 else 0)
    league_id = f"pbl-{index:03d}"
    if name in {"Major League Soccer", "Liga MX", "J1 League", "K League 1", "Saudi Pro League"}:
        base += 3
    return {
        "data_mode": "public_beta_demo",
        "rank": index,
        "league_id": league_id,
        "league_name": name,
        "league_badge_url": f"assets/media/public-beta/leagues/{league_id}.svg",
        "badge_source": "ARES owned generated public-beta badge",
        "badge_license_status": "ares_owned",
        "country": country,
        "region": region,
        "tier": tier,
        "clubs": 30 if name == "Major League Soccer" else 18 if tier == 1 else 14,
        "players_tracked": 720 if name == "Major League Soccer" else max(180, 520 - index * 6),
        "avg_ares": round(base + 0.3, 1),
        "avg_market": round(base + 0.8, 1),
        "u23_share": f"{24 + (index % 12)}%",
        "top_club": club_match["club_name"] if club_match else ("Pacific Harbor FC" if name == "Major League Soccer" else "Public Beta Club"),
        "top_player": player_match["player_name"] if player_match else "Public Beta Player",
        "data_confidence": "Medium",
        "confidence": "Medium",
        "last_updated": ISO_TODAY,
        "source": SOURCE,
        "league_url": "leagues/league-template.html",
    }


leagues = [league_row(i + 1, *row) for i, row in enumerate(required_leagues)]


PALETTES = [
    ("#0B1F3A", "#F7C948", "#2D6A4F"),
    ("#102A43", "#38BDF8", "#F7C948"),
    ("#172554", "#F97316", "#FFFFFF"),
    ("#0F172A", "#A7F3D0", "#F7C948"),
    ("#111827", "#E11D48", "#F8FAFC"),
    ("#1F2937", "#22C55E", "#F7C948"),
    ("#312E81", "#FACC15", "#FFFFFF"),
    ("#064E3B", "#60A5FA", "#F7C948"),
]


def palette(index: int) -> tuple[str, str, str]:
    return PALETTES[(index - 1) % len(PALETTES)]


def esc(value: str) -> str:
    return html.escape(str(value), quote=True)


def write_svg(relative: str, svg: str) -> None:
    write_text(relative, svg.strip() + "\n")


def player_svg(row: dict) -> str:
    base, accent, third = palette(row["rank"])
    name = esc(row["player_name"])
    initials = esc(row["initials"])
    position = esc(row["position"])
    club = esc(row["club"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{name}, {position}, {club}">
  <metadata>ARES-owned generated public-beta player image. Fictional seeded data. No scraped image source.</metadata>
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{base}"/><stop offset="1" stop-color="#020617"/></linearGradient>
    <linearGradient id="a" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{accent}"/><stop offset="1" stop-color="{third}"/></linearGradient>
  </defs>
  <rect width="256" height="256" rx="34" fill="url(#g)"/>
  <circle cx="205" cy="44" r="64" fill="{accent}" opacity=".14"/>
  <path d="M38 218c9-44 42-68 90-68s81 24 90 68" fill="{accent}" opacity=".22"/>
  <circle cx="128" cy="101" r="47" fill="#F8FAFC" opacity=".95"/>
  <path d="M74 82c13-35 39-52 77-43 20 5 34 18 42 39-31-15-65-17-119 4Z" fill="{accent}"/>
  <path d="M82 146c13 18 28 27 46 27s33-9 46-27c-14 8-29 12-46 12s-32-4-46-12Z" fill="{base}" opacity=".2"/>
  <rect x="26" y="26" width="64" height="28" rx="14" fill="rgba(255,255,255,.12)" stroke="{accent}" stroke-width="2"/>
  <text x="58" y="46" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="900" fill="{accent}">{position}</text>
  <text x="128" y="214" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="42" font-weight="900" fill="{accent}">{initials}</text>
  <text x="128" y="235" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="11" font-weight="800" fill="#E5E7EB">{club[:22]}</text>
</svg>'''


def club_svg(row: dict) -> str:
    base, accent, third = palette(row["rank"])
    label = esc(row["club_name"])
    initials = esc("".join(part[0] for part in row["club_name"].split()[:3]).upper())
    league = esc(row["league"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{label} badge">
  <metadata>ARES-owned generated public-beta club badge. Fictional seeded data. No protected club mark.</metadata>
  <rect width="256" height="256" rx="34" fill="#F8FAFC"/>
  <path d="M128 20 215 56v70c0 56-35 93-87 110-52-17-87-54-87-110V56l87-36Z" fill="{base}"/>
  <path d="M128 38 196 66v58c0 42-25 72-68 88-43-16-68-46-68-88V66l68-28Z" fill="none" stroke="{accent}" stroke-width="9"/>
  <path d="M70 116h116" stroke="{third}" stroke-width="8" opacity=".8"/>
  <circle cx="128" cy="116" r="44" fill="{accent}"/>
  <text x="128" y="130" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="38" font-weight="900" fill="{base}">{initials}</text>
  <text x="128" y="184" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="850" fill="#F8FAFC">{league[:24]}</text>
</svg>'''


def league_svg(row: dict) -> str:
    base, accent, third = palette(row["rank"])
    label = esc(row["league_name"])
    region = esc(row["region"])
    initials = esc("".join(part[0] for part in row["league_name"].replace("-", " ").split()[:3]).upper())
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-label="{label} league badge">
  <metadata>ARES-owned generated public-beta league badge. Fictional seeded board art. No protected league mark.</metadata>
  <rect width="256" height="256" rx="34" fill="{base}"/>
  <circle cx="128" cy="124" r="84" fill="none" stroke="{accent}" stroke-width="12"/>
  <path d="M49 124h158M128 40c25 24 38 52 38 84s-13 60-38 84M128 40c-25 24-38 52-38 84s13 60 38 84" stroke="{third}" stroke-width="7" opacity=".9" fill="none"/>
  <circle cx="128" cy="124" r="38" fill="{accent}"/>
  <text x="128" y="137" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="900" fill="{base}">{initials}</text>
  <text x="128" y="226" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="850" fill="#E5E7EB">{region}</text>
</svg>'''


def generate_visual_assets() -> None:
    for row in players:
        write_svg(f"assets/media/public-beta/players/{row['player_id']}.svg", player_svg(row))
    for row in clubs:
        write_svg(f"assets/media/public-beta/clubs/{row['club_id']}.svg", club_svg(row))
    for row in leagues:
        write_svg(f"assets/media/public-beta/leagues/{row['league_id']}.svg", league_svg(row))


def transfer_row(idx: int, player_ref: dict, from_club: str, to_club: str, from_league: str, to_league: str, transfer_type: str, ares_impact: float, market_impact: float, confidence: str = "Medium") -> dict:
    row = {
        "data_mode": "public_beta_demo",
        "transfer_id": f"pbt-{idx:03d}",
        "date": f"2026-05-{21 - (idx % 8):02d}",
        "player_id": player_ref["player_id"],
        "player_name": player_ref["player_name"],
        "initials": player_ref["initials"],
        "age": player_ref["age"],
        "position": player_ref["position"],
        "from_club": from_club,
        "to_club": to_club,
        "from_league": from_league,
        "to_league": to_league,
        "transfer_type": transfer_type,
        "ares_impact": f"{ares_impact:+.1f}",
        "market_impact": f"{market_impact:+.1f}",
        "confidence": confidence,
        "data_confidence": confidence,
        "source": SOURCE,
        "last_updated": ISO_TODAY,
        "url": "players/player-template.html",
        "player_url": "players/player-template.html",
    }
    row.update({key: player_ref[key] for key in ["photo_url", "photo_source", "photo_license_status", "photo_credit", "photo_attribution_url", "photo_status", "image_confidence"]})
    return row


transfers = [
    transfer_row(1, players[1], "Cascadia Union", "Pacific Harbor FC", "Major League Soccer", "Major League Soccer", "U22 signing", 1.4, 3.2, "Medium"),
    transfer_row(2, players[7], "Academy Select", "Monterra Azul", "Liga de ExpansiÃ³n MX", "Liga MX", "Promotion", 1.1, 4.1, "Low"),
    transfer_row(3, players[11], "Osaka Minato", "Tokyo Bay Verdes", "J2 League", "J1 League", "Permanent", 1.8, 3.7, "Medium"),
    transfer_row(4, players[14], "Riyadh Horizon", "Doha Meridian", "Saudi Pro League", "Qatar Stars League", "Contract signal", -0.2, 0.8, "Medium"),
    transfer_row(5, players[18], "Melbourne Southern", "Valley Forge FC", "A-League", "MLS Next Pro", "Loan", 0.7, 2.5, "Low"),
    transfer_row(6, players[22], "Hanoi Capital", "Bangkok Lanterns", "V.League 1", "Thai League 1", "Free agent", 0.4, 1.6, "Medium"),
    transfer_row(7, players[25], "Rio Norte", "Monterra Azul", "Brazil Serie A", "Liga MX", "Permanent", 1.6, 2.9, "Medium"),
    transfer_row(8, players[9], "Valley Forge FC", "Pacific Harbor FC", "MLS Next Pro", "Major League Soccer", "Academy promotion", 0.9, 3.4, "Low"),
]


watchlist = []
watch_categories = [
    ("Youth Breakout", players[4], "U19 forward minutes spike"),
    ("U21 Asset", players[9], "Development starter with high age-curve value"),
    ("U23 Asset", players[13], "Wide creator entering first-team window"),
    ("Loan Watch", players[18], "Loan could unlock higher minutes"),
    ("Free Agent", players[22], "Short market window with regional demand"),
    ("Lower Division", players[11], "Promotion-market production signal"),
    ("Role Expansion", players[20], "Central midfield usage increasing"),
    ("Injury Return", players[5], "Returning starter role needs confirmation"),
    ("Contract Signal", players[14], "Contract horizon shapes market score"),
    ("Scout Flag", players[23], "Aerial profile and age curve need more data"),
]
for idx, (category, pref, reason) in enumerate(watch_categories, 1):
    row = {
        "data_mode": "public_beta_demo",
        "watch_id": f"pbw-{idx:03d}",
        "category": category,
        "player_id": pref["player_id"],
        "player_name": pref["player_name"],
        "initials": pref["initials"],
        "age": pref["age"],
        "position": pref["position"],
        "level": category,
        "club": pref["club"],
        "reason": reason,
        "status": "Tracked outside official rankings",
        "last_movement": f"{category} review",
        "confidence": pref["data_confidence"],
        "data_confidence": pref["data_confidence"],
        "last_updated": ISO_TODAY,
        "source": SOURCE,
        "url": "players/player-template.html",
        "player_url": "players/player-template.html",
    }
    row.update({key: pref[key] for key in ["photo_url", "photo_source", "photo_license_status", "photo_credit", "photo_attribution_url", "photo_status", "image_confidence"]})
    watchlist.append(row)


market_changes = []
for idx, pref in enumerate([players[1], players[4], players[7], players[10], players[18], players[20], players[23], players[25], players[5], players[26]], 1):
    old = round(pref["market_score"] - abs(pref["trend_value"]), 1)
    market_changes.append({
        "data_mode": "public_beta_demo",
        "change_id": f"pbm-{idx:03d}",
        "date": f"2026-05-{22 - idx:02d}",
        "player_name": pref["player_name"],
        "club": pref["club"],
        "league": pref["league"],
        "region": pref["region"],
        "old_market_score": old,
        "new_market_score": pref["market_score"],
        "change": f"{pref['trend_value']:+.1f}",
        "trend": "Falling" if pref["trend_value"] < 0 else pref["trend"],
        "reason": pref["reason"],
        "data_confidence": pref["data_confidence"],
        "confidence": pref["data_confidence"],
        "last_updated": ISO_TODAY,
        "source": SOURCE,
    })


def status_section(prefix: str = "") -> str:
    return f'''<section class="ares-section ares-card"><div class="d-flex justify-content-between align-items-center mb-3"><h2 class="h4 mb-0">Public Beta Status</h2><span class="ares-muted-note">Last updated: {TODAY}</span></div><div class="ares-status-terminal">
      <div class="ares-status-item"><strong>Players Tracked</strong><span>{len(players)} public beta rows</span></div><div class="ares-status-item"><strong>Clubs Tracked</strong><span>{len(clubs)} portfolio rows</span></div><div class="ares-status-item"><strong>Leagues Tracked</strong><span>{len(leagues)} market rows</span></div><div class="ares-status-item"><strong>Player Images</strong><span>Fallback avatars active</span></div><div class="ares-status-item"><strong>ARES Model</strong><span>Formula ready</span></div><div class="ares-status-item"><strong>Market Model</strong><span>Formula ready</span></div>
    </div><p class="ares-beta-note">Seeded beta data rows are fictional seeded records that show the product experience before approved live football data is connected.</p></section>'''


def head(title: str, description: str, prefix: str = "") -> str:
    return f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{description}">
  <link rel="shortcut icon" href="{prefix}assets/media/brand/ares-logo.png">
  <link href="{prefix}assets/plugins/global/plugins.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/plugins/custom/datatables/datatables.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/style.bundle.css" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/ares-theme.css?v={ASSET_VERSION}" rel="stylesheet" type="text/css">
  <link href="{prefix}assets/css/ares-components.css?v={ASSET_VERSION}" rel="stylesheet" type="text/css">
  <style>.soccer-main{{width:min(100%,1440px);margin:0 auto;padding:clamp(1rem,2.5vw,2rem)}}th button{{border:0;background:transparent;padding:0;color:inherit;font:inherit;text-transform:inherit}}.table-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}.table-grid .wide{{grid-column:1/-1}}@media(max-width:1000px){{.table-grid{{grid-template-columns:1fr}}}}.hero-grid{{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(18rem,.65fr);gap:1rem;align-items:start}}@media(max-width:1100px){{.hero-grid{{grid-template-columns:1fr}}}}</style>
</head><body class="ares-shell">'''


def nav(prefix: str = "") -> str:
    return f'''<header class="ares-topbar">
    <a class="ares-brand" href="{prefix}index.html">ARES Football Market</a>
    <nav class="ares-nav" aria-label="Primary">
      <a href="{prefix}index.html">Home</a><a href="{prefix}players/index.html">Players</a><a href="{prefix}rankings/ares.html">ARES Rankings</a><a href="{prefix}rankings/market.html">Market Rankings</a><a href="{prefix}clubs/index.html">Clubs</a><a href="{prefix}leagues/index.html">Leagues</a><a href="{prefix}transfers/index.html">Transfers</a><a href="{prefix}leagues/asia.html">Asia</a><a href="{prefix}leagues/mls.html">MLS</a><a href="{prefix}leagues/north-america.html">North America</a><a href="{prefix}watchlist/index.html">Watchlist</a><a href="{prefix}methodology.html">Methodology</a><span class="ares-brand-switch"><a href="{prefix}index.html">Global Football</a><a href="https://cog-tech.github.io/ares-gridiron-market/">Gridiron</a></span>
    </nav>
  </header>'''


def scripts(prefix: str = "", inline: str = "") -> str:
    return f'''<script src="{prefix}assets/plugins/global/plugins.bundle.js"></script>
  <script src="{prefix}assets/js/scripts.bundle.js"></script>
  <script src="{prefix}assets/js/ares-data-loader.js"></script>
  <script src="{prefix}assets/js/ares-tables.js"></script>
  <script src="{prefix}assets/js/soccer-pages.js"></script>
  <script src="{prefix}assets/js/ares-mega-nav.js?v={ASSET_VERSION}"></script>{inline}</body></html>'''


def filter_chips(labels, param="q") -> str:
    return '<div class="ares-filter-bar">' + "".join(f'<a class="ares-filter-chip" href="?{param}={label.replace(" ", "%20")}">{label}</a>' for label in labels) + "</div>"


def table_html(table_id: str, body_id: str, count_id: str, headers: list[str], empty: str = "No matching rows for this filter set. Clear filters to view the full board.") -> str:
    ths = "".join(f"<th>{h}</th>" for h in headers)
    return f'<div class="table-responsive"><table id="{table_id}" class="ares-table" data-count-id="{count_id}"><thead><tr>{ths}</tr></thead><tbody id="{body_id}"><tr><td colspan="{len(headers)}">{empty}</td></tr></tbody></table></div>'


def init_table(data_path: str, table_id: str, body_id: str, search_id: str | None, columns: list[dict], **options) -> str:
    opt = {"dataPath": data_path, "tableId": table_id, "bodyId": body_id, "columns": columns}
    if search_id:
        opt["searchId"] = search_id
    opt.update(options)
    return f"AresSoccer.initTable({json.dumps(opt, ensure_ascii=False)});"


player_cols_ares = [
    {"key": "rank"},
    {"key": "player_name", "render": "playerImage"},
    {"key": "player_name", "render": "playerLink", "pathPrefix": "../", "showAvatar": False},
    {"key": "age"},
    {"key": "position"},
    {"key": "club", "render": "clubLink", "pathPrefix": "../"},
    {"key": "league", "render": "leagueLink", "pathPrefix": "../"},
    {"key": "country"},
    {"key": "minutes"},
    {"key": "ares_score", "render": "score"},
    {"key": "ares_tier", "render": "tier"},
    {"key": "trend", "render": "trend"},
    {"key": "data_confidence", "render": "confidence"},
    {"key": "last_updated"},
    {"key": "source"},
]

player_cols_market = [
    {"key": "rank"},
    {"key": "player_name", "render": "playerImage"},
    {"key": "player_name", "render": "playerLink", "pathPrefix": "../", "showAvatar": False},
    {"key": "age"},
    {"key": "position"},
    {"key": "club", "render": "clubLink", "pathPrefix": "../"},
    {"key": "league", "render": "leagueLink", "pathPrefix": "../"},
    {"key": "country"},
    {"key": "ares_score", "render": "score"},
    {"key": "market_score", "render": "market"},
    {"key": "market_tier", "render": "tier"},
    {"key": "contract_end"},
    {"key": "trend", "render": "trend"},
    {"key": "reason"},
    {"key": "data_confidence", "render": "confidence"},
    {"key": "last_updated"},
    {"key": "source"},
]

player_cols_index = [
    {"key": "player_name", "render": "playerImage"},
    {"key": "player_name", "render": "playerLink", "pathPrefix": "../", "showAvatar": False},
    {"key": "age"},
    {"key": "position"},
    {"key": "club", "render": "clubLink", "pathPrefix": "../"},
    {"key": "league", "render": "leagueLink", "pathPrefix": "../"},
    {"key": "country"},
    {"key": "ares_score", "render": "score"},
    {"key": "market_score", "render": "market"},
    {"key": "trend", "render": "trend"},
    {"key": "data_confidence", "render": "confidence"},
    {"key": "last_updated"},
    {"key": "source"},
    {"key": "url", "render": "link", "label": "Open", "pathPrefix": "../", "fallbackUrl": "players/player-template.html"},
]

club_cols = [
    {"key": "rank"},
    {"key": "club_name", "render": "clubBadge"},
    {"key": "club_name", "render": "clubLink", "pathPrefix": "../"},
    {"key": "country"},
    {"key": "league", "render": "leagueLink", "pathPrefix": "../"},
    {"key": "region"},
    {"key": "squad_size"},
    {"key": "average_age"},
    {"key": "avg_ares", "render": "score"},
    {"key": "avg_market", "render": "market"},
    {"key": "u23_value", "render": "market"},
    {"key": "top_asset"},
    {"key": "weakest_unit"},
    {"key": "trend", "render": "trend"},
    {"key": "data_confidence", "render": "confidence"},
    {"key": "last_updated"},
]

league_cols = [
    {"key": "rank"},
    {"key": "league_name", "render": "leagueBadge"},
    {"key": "league_name", "render": "leagueLink", "pathPrefix": "../"},
    {"key": "country"},
    {"key": "region"},
    {"key": "tier"},
    {"key": "clubs"},
    {"key": "players_tracked"},
    {"key": "avg_ares", "render": "score"},
    {"key": "avg_market", "render": "market"},
    {"key": "u23_share"},
    {"key": "top_club"},
    {"key": "top_player"},
    {"key": "data_confidence", "render": "confidence"},
    {"key": "last_updated"},
    {"key": "source"},
]

transfer_cols = [
    {"key": "date"},
    {"key": "player_name", "render": "playerImage"},
    {"key": "player_name", "render": "playerLink", "pathPrefix": "../", "showAvatar": False},
    {"key": "age"},
    {"key": "position"},
    {"key": "from_club"},
    {"key": "to_club"},
    {"key": "from_league"},
    {"key": "to_league"},
    {"key": "transfer_type"},
    {"key": "ares_impact"},
    {"key": "market_impact"},
    {"key": "confidence", "render": "confidence"},
    {"key": "source"},
    {"key": "last_updated"},
]

watch_cols = [
    {"key": "player_name", "render": "playerImage"},
    {"key": "player_name", "render": "playerLink", "pathPrefix": "../", "showAvatar": False},
    {"key": "age"},
    {"key": "position"},
    {"key": "level"},
    {"key": "club"},
    {"key": "reason"},
    {"key": "status"},
    {"key": "last_movement"},
    {"key": "confidence", "render": "confidence"},
    {"key": "last_updated"},
    {"key": "source"},
]


def beta_badge() -> str:
    return '<span class="ares-beta-badge">Seeded beta data</span>'


def build_home() -> None:
    inline_parts = [
        'AresSoccer.initSearch("soccer-search", "soccer-search-results", "data/public_search.json");',
        init_table("data/public_players.json", "home-ares-table", "home-ares-body", None, [
            {"key": "player_name", "render": "playerImage"},
            {"key": "player_name", "render": "playerLink", "showAvatar": False},
            {"key": "club"},
            {"key": "ares_score", "render": "score"},
            {"key": "ares_tier", "render": "tier"},
            {"key": "source"},
        ], sortKey="ares_score", sortDirection="desc", limit=5),
        init_table("data/public_players.json", "home-market-table", "home-market-body", None, [
            {"key": "player_name", "render": "playerImage"},
            {"key": "player_name", "render": "playerLink", "showAvatar": False},
            {"key": "club"},
            {"key": "market_score", "render": "market"},
            {"key": "market_tier", "render": "tier"},
            {"key": "source"},
        ], sortKey="market_score", sortDirection="desc", limit=5),
        init_table("data/public_players.json", "home-young-table", "home-young-body", None, [
            {"key": "player_name", "render": "playerLink"},
            {"key": "age"},
            {"key": "club"},
            {"key": "market_score", "render": "market"},
            {"key": "trend", "render": "trend"},
            {"key": "source"},
        ], maxAge=23, sortKey="market_score", sortDirection="desc", limit=5),
        init_table("data/public_market_changes.json", "home-changes-table", "home-changes-body", None, [
            {"key": "player_name"},
            {"key": "club"},
            {"key": "change"},
            {"key": "reason"},
            {"key": "source"},
        ], limit=5),
        init_table("data/public_transfers.json", "home-transfer-table", "home-transfer-body", None, [
            {"key": "date"},
            {"key": "player_name", "render": "playerLink"},
            {"key": "transfer_type"},
            {"key": "to_club"},
            {"key": "market_impact"},
            {"key": "source"},
        ], limit=5),
        init_table("data/public_leagues.json", "home-asia-table", "home-asia-body", None, [
            {"key": "league_name", "render": "leagueBadge"},
            {"key": "league_name"},
            {"key": "country"},
            {"key": "avg_market", "render": "market"},
            {"key": "top_player"},
            {"key": "source"},
        ], filterKey="region", filterValue="Asia", sortKey="avg_market", sortDirection="desc", limit=5),
        init_table("data/public_players.json", "home-mls-table", "home-mls-body", None, [
            {"key": "player_name", "render": "playerLink"},
            {"key": "club"},
            {"key": "market_score", "render": "market"},
            {"key": "role"},
            {"key": "source"},
        ], filterKey="league", filterValue="Major League Soccer", sortKey="market_score", sortDirection="desc", limit=5),
        init_table("data/public_clubs.json", "home-clubs-table", "home-clubs-body", None, [
            {"key": "club_name", "render": "clubBadge"},
            {"key": "club_name"},
            {"key": "league"},
            {"key": "avg_market", "render": "market"},
            {"key": "top_asset"},
            {"key": "source"},
        ], sortKey="avg_market", sortDirection="desc", limit=5),
        init_table("data/public_leagues.json", "home-leagues-table", "home-leagues-body", None, [
            {"key": "league_name", "render": "leagueBadge"},
            {"key": "league_name"},
            {"key": "region"},
            {"key": "avg_ares", "render": "score"},
            {"key": "players_tracked"},
            {"key": "source"},
        ], sortKey="avg_ares", sortDirection="desc", limit=5),
    ]
    html = head(
        "ARES Football Market | Player Market Value, ARES Scores, Club Rankings & Transfer Intelligence",
        "ARES Football Market ranks football players, clubs, leagues, and transfer movement with seeded public-beta ARES performance scores and market asset scores.",
    ) + nav() + f'''<main class="soccer-main">
    <section class="ares-hero hero-grid"><div><h1>ARES Football Market</h1><p><strong>The football asset board.</strong></p><p>Track football players, clubs, leagues, and transfer movement through two lenses: <strong>ARES Score</strong> for on-field quality and <strong>Market Score</strong> for football asset value.</p><p>Search players, clubs, leagues, transfers, and market boards.</p><div class="hero-actions"><a href="rankings/ares.html">View ARES Rankings</a><a href="rankings/market.html">View Market Rankings</a><a href="methodology.html">How the Scores Work</a></div><div class="search-panel"><div class="ares-search"><input id="soccer-search" type="search" placeholder="Search players, clubs, leagues, transfers, and market boards."></div><div id="soccer-search-results" class="search-results"></div></div></div><div class="ares-card ares-hero-terminal"><h2 class="h4">Public Beta Terminal</h2><p>Seeded fictional rows show how ARES will work before approved live football feeds are connected.</p><p>{beta_badge()}</p></div></section>
    {status_section()}
    <section class="ares-section table-grid">
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Top ARES Players</h2>{beta_badge()}</div>{table_html("home-ares-table","home-ares-body","home-ares-count",["Image","Player","Club","ARES","Tier","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Top Market Assets</h2>{beta_badge()}</div>{table_html("home-market-table","home-market-body","home-market-count",["Image","Player","Club","Market","Tier","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Young Breakout Assets</h2>{beta_badge()}</div>{table_html("home-young-table","home-young-body","home-young-count",["Player","Age","Club","Market","Trend","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Latest Market Value Changes</h2>{beta_badge()}</div>{table_html("home-changes-table","home-changes-body","home-changes-count",["Player","Club","Change","Reason","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Latest Transfer Signals</h2>{beta_badge()}</div>{table_html("home-transfer-table","home-transfer-body","home-transfer-count",["Date","Player","Type","To","Market Impact","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Asia Market Board</h2>{beta_badge()}</div>{table_html("home-asia-table","home-asia-body","home-asia-count",["Badge","League","Country","Avg Market","Top Player","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">MLS Market Board</h2>{beta_badge()}</div>{table_html("home-mls-table","home-mls-body","home-mls-count",["Player","Club","Market","Role","Mode"])}</div>
      <div class="ares-card"><div class="section-title-row"><h2 class="h4">Club Portfolio Board</h2>{beta_badge()}</div>{table_html("home-clubs-table","home-clubs-body","home-clubs-count",["Badge","Club","League","Avg Market","Top Asset","Mode"])}</div>
      <div class="ares-card wide"><div class="section-title-row"><h2 class="h4">League Strength Board</h2>{beta_badge()}</div>{table_html("home-leagues-table","home-leagues-body","home-leagues-count",["Badge","League","Region","Avg ARES","Players","Mode"])}</div>
    </section>
    <section class="ares-section ares-card"><h2 class="h4">How ARES Works</h2><p>ARES Score measures on-field football quality. Market Score measures football asset value. Seeded beta data rows are fictional records designed to show the product surface while approved live feeds remain disconnected.</p><a href="methodology.html">Learn the difference</a></section>
  </main><footer class="ares-footer">ARES Football Market is an independent analytical database. <a href="https://cog-tech.github.io/ares-gridiron-market/">Open ARES Gridiron Market</a>.</footer>''' + scripts(inline="<script>" + "".join(inline_parts) + "</script>")
    write_text("index.html", html)


def build_rankings() -> None:
    common_warning = "Public Beta rows are seeded demonstration rows until approved live football data is connected."
    ares_inline = init_table("../data/public_players.json", "ares-table", "ares-body", "ares-search", player_cols_ares, sortKey="ares_score", sortDirection="desc")
    ares_html = head(
        "ARES Rankings | Football Player Quality Scores by Position, Club & League",
        "ARES Score ranks footballers by performance quality, role, efficiency, usage, durability, opponent context, and trend.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>ARES Player Quality Rankings</h1><p>ARES Score ranks footballers by performance quality, role, efficiency, usage, durability, opponent context, and trend.</p></div><div class="ares-demo-banner">{common_warning}</div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Country","League","Club","Position","Age band","Minimum minutes","ARES tier","Trend","Confidence","Asia","MLS"])}<input id="ares-search" class="ares-search mb-3" type="search" placeholder="Search player, club, league, position, tier, region, or trend...">{table_html("ares-table","ares-body","ares-count",["Rank","Image","Player","Age","Position","Club","League","Country","Minutes","ARES Score","ARES Tier","Trend","Data Confidence","Last Updated","Source"])}</section></main><footer class="ares-footer">Seeded beta data ARES ranking board.</footer>''' + scripts("../", "<script>" + ares_inline + "</script>")
    write_text("rankings/ares.html", ares_html)

    market_inline = init_table("../data/public_players.json", "market-table", "market-body", "market-search", player_cols_market, sortKey="market_score", sortDirection="desc")
    market_tiers = ''.join(f'<div class="ares-status-item"><strong>{name}</strong><span>{desc}</span></div>' for name, desc in [
        ("Franchise Asset", "Elite quality with long-term market durability"),
        ("Blue-Chip Asset", "High-value player with strong age and role signal"),
        ("Rising Asset", "Young or improving player with asset upside"),
        ("Core Starter", "Reliable first-team market value"),
        ("Rotation Value", "Useful squad value with role limits"),
        ("Watchlist", "Early signal or thin-data player"),
        ("Risk Asset", "Aging, injured, declining, or role-unstable profile"),
    ])
    market_html = head(
        "Football Market Rankings | Player Asset Value, Age Curve & Transfer Signal",
        "Football Market Rankings compare player asset value by ARES quality, age curve, position scarcity, role security, transfer signal, and durability.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Football Market Value Rankings</h1><p>Market Score estimates football asset value using ARES quality, age curve, position scarcity, league strength, role security, transfer signal, durability, and movement value.</p></div><div class="ares-demo-banner">Market Score is not a transfer fee. It is an analytical asset score. {common_warning}</div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Age","Position","Club","League","Contract ending","Market tier","U21","U23","Free agent","Loan","Trend","Asia","MLS"])}<input id="market-search" class="ares-search mb-3" type="search" placeholder="Search player, club, league, position, tier, region, or trend...">{table_html("market-table","market-body","market-count",["Rank","Image","Player","Age","Position","Club","League","Country","ARES Score","Market Score","Market Tier","Contract End","Trend","Reason","Confidence","Last Updated","Source"])}</section><section class="ares-section ares-card"><h2 class="h4">Market Tiers</h2><div class="ares-market-grid">{market_tiers}</div></section></main><footer class="ares-footer">Seeded beta data market ranking board.</footer>''' + scripts("../", "<script>" + market_inline + "</script>")
    write_text("rankings/market.html", market_html)


def build_players() -> None:
    inline = init_table("../data/public_players.json", "players-table", "players-body", "players-search", player_cols_index, sortKey="market_score", sortDirection="desc")
    html = head(
        "Football Player Search | ARES Scores, Market Value & Transfer Signal",
        "Search seeded public-beta football players by position, club, league, age, country, ARES quality, market score, trend, and data confidence.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Football Player Search</h1><p>Search football players by position, club, league, age, country, ARES quality, market score, trend, and data confidence.</p></div><div class="ares-demo-banner">Seeded beta data: seeded fictional players show the search and market-board experience before approved live player data is connected.</div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Player Name","Club","League","Country","Position","Age Band","U21","U23","Free Agent","Loan","Rising","Falling","High Confidence","Asia","MLS","North America"])}<input id="players-search" class="ares-search mb-3" type="search" placeholder="Search player name, club, league, country, or position...">{table_html("players-table","players-body","players-count",["Image","Player","Age","Position","Club","League","Country","ARES Score","Market Score","Trend","Confidence","Last Updated","Source","Profile"])}</section></main><footer class="ares-footer">Seeded beta data player search.</footer>''' + scripts("../", "<script>" + inline + "</script>")
    write_text("players/index.html", html)


def build_player_template() -> None:
    profile = players[0].copy()
    profile.update({"height": "5'10\"", "foot": "Right", "age_curve": "Prime", "value_tier": profile["market_tier"]})
    write_json("data/player_profile_sample.json", profile)
    html = head(
        "Player Profile | ARES Football Market",
        "Football asset profile with ARES Score, Market Score, public-beta stats, image-safe fallback avatar, and premium intelligence tabs.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><section class="ares-section profile-grid"><div class="ares-card ares-profile-card"><div id="player-photo" class="ares-profile-photo" aria-label="ARES player avatar">AR</div><span id="profile-position-badge" class="ares-position-mini">FB</span><h1 id="player-name">Player Name</h1><p class="ares-profile-club"><span id="position">Position</span> | <span id="club">Club</span> | <span id="league">League</span> | <span id="country">Country</span></p><p>Age: <strong id="age"></strong> | Contract End: <strong id="contract-end"></strong> | Role: <strong id="role"></strong></p><p>Data Confidence: <strong id="confidence"></strong> | Last Updated: <strong id="last-updated"></strong></p><p>{beta_badge()}</p><div class="ares-profile-meta"><span>Photo source: <strong id="photo-source"></strong></span><span>License: <strong id="photo-license"></strong></span><span>Credit: <strong id="photo-credit"></strong></span></div></div><div class="metric-grid"><div class="ares-stat-card"><span class="label">ARES Score</span><span id="ares-score" class="value"></span><span class="meta">Performance quality</span></div><div class="ares-stat-card"><span class="label">Market Score</span><span id="market-score" class="value"></span><span class="meta">Asset value</span></div><div class="ares-stat-card"><span class="label">Market Tier</span><span id="market-tier" class="value"></span><span class="meta">Public beta band</span></div><div class="ares-stat-card"><span class="label">Age Curve</span><span id="age-curve" class="value"></span><span class="meta">Development window</span></div><div class="ares-stat-card"><span class="label">Role</span><span id="metric-role" class="value"></span><span class="meta">Squad usage</span></div><div class="ares-stat-card"><span class="label">Trend</span><span id="trend" class="value"></span><span class="meta">Movement signal</span></div></div></section><section class="ares-section ares-card"><h2 class="h4">Public Tabs</h2><div class="ares-filter-bar"><a class="ares-filter-chip" href="#">Overview</a><a class="ares-filter-chip" href="#">Season Stats</a><a class="ares-filter-chip" href="#">Match Log</a><a class="ares-filter-chip" href="#">Minutes / Role</a><a class="ares-filter-chip" href="#">Availability</a><a class="ares-filter-chip" href="#">Position Usage</a><a class="ares-filter-chip" href="#">Comparable Players</a><a class="ares-filter-chip" href="#">Market Notes</a></div></section><section class="ares-section ares-card"><h2 class="h4">Premium Tabs</h2><div class="ares-filter-bar"><a class="ares-filter-chip" href="#">ARES Components</a><a class="ares-filter-chip" href="#">Market Breakdown</a><a class="ares-filter-chip" href="#">Age Curve</a><a class="ares-filter-chip" href="#">Transfer Value Signal</a><a class="ares-filter-chip" href="#">Team Fit</a><a class="ares-filter-chip" href="#">Risk Score</a><a class="ares-filter-chip" href="#">Movement History</a></div></section><section class="ares-section ares-card"><h2 class="h4">Why This Player Matters</h2><p id="reason">Public beta player asset explanation.</p></section><section class="ares-section ares-card"><h2 class="h4">Image Safety</h2><p>Player photos display only when a provider-supplied or properly licensed image URL exists in the player data. Otherwise ARES shows a branded avatar with initials, position, club, and region context.</p></section></main><footer class="ares-footer">Seeded beta data player profile.</footer>''' + scripts("../", '<script>AresSoccer.initProfile("../data/player_profile_sample.json",{"player-name":"player_name","position":"position","profile-position-badge":"position","club":"club","league":"league","country":"country","age":"age","contract-end":"contract_end","role":"role","metric-role":"role","confidence":"data_confidence","last-updated":"last_updated","ares-score":"ares_score","market-score":"market_score","market-tier":"market_tier","age-curve":"age_curve","trend":"trend","reason":"reason"});</script>')
    write_text("players/player-template.html", html)


def build_clubs() -> None:
    inline = init_table("../data/public_clubs.json", "clubs-table", "clubs-body", "clubs-search", club_cols, sortKey="avg_market", sortDirection="desc")
    section_scripts = [
        init_table("../data/public_clubs.json", "clubs-most-table", "clubs-most-body", None, [{"key":"club_name","render":"clubBadge"},{"key":"club_name"},{"key":"league"},{"key":"avg_market","render":"market"},{"key":"top_asset"},{"key":"source"}], sortKey="avg_market", sortDirection="desc", limit=5),
        init_table("../data/public_clubs.json", "clubs-young-table", "clubs-young-body", None, [{"key":"club_name","render":"clubBadge"},{"key":"club_name"},{"key":"average_age"},{"key":"u23_value","render":"market"},{"key":"top_asset"},{"key":"source"}], sortKey="u23_value", sortDirection="desc", limit=5),
        init_table("../data/public_clubs.json", "clubs-u23-table", "clubs-u23-body", None, [{"key":"club_name","render":"clubBadge"},{"key":"club_name"},{"key":"region"},{"key":"u23_value","render":"market"},{"key":"top_asset"},{"key":"source"}], sortKey="u23_value", sortDirection="desc", limit=5),
        init_table("../data/public_clubs.json", "clubs-aging-table", "clubs-aging-body", None, [{"key":"club_name"},{"key":"average_age"},{"key":"weakest_unit"},{"key":"trend","render":"trend"},{"key":"source"}], sortKey="average_age", sortDirection="desc", limit=5),
        init_table("../data/public_clubs.json", "clubs-rising-table", "clubs-rising-body", None, [{"key":"club_name"},{"key":"region"},{"key":"avg_ares","render":"score"},{"key":"trend","render":"trend"},{"key":"source"}], filterKey="trend", filterValue="Rising", limit=5),
        init_table("../data/public_clubs.json", "clubs-falling-table", "clubs-falling-body", None, [{"key":"club_name"},{"key":"region"},{"key":"weakest_unit"},{"key":"trend","render":"trend"},{"key":"source"}], filterKey="trend", filterValue="Falling", limit=5),
    ]
    html = head(
        "Club Market Rankings | Squad Value, U23 Assets & Transfer Risk",
        "Compare public-beta clubs by squad quality, market value, age curve, U23 assets, transfer movement, and roster strength.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Club Market Rankings</h1><p>Compare clubs by squad quality, market value, age curve, U23 assets, transfer movement, and roster strength.</p></div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Region","Country","League","Tier","U23 Strength","High ARES","High Market","Rising Clubs","Falling Clubs"])}<input id="clubs-search" class="ares-search mb-3" type="search" placeholder="Search club, league, country, region, or trend...">{table_html("clubs-table","clubs-body","clubs-count",["Rank","Badge","Club","Country","League","Region","Squad Size","Average Age","Avg ARES","Avg Market","U23 Value","Top Asset","Weakest Unit","Trend","Confidence","Last Updated"])}</section><section class="ares-section table-grid"><div class="ares-card"><div class="section-title-row"><h2 class="h4">Most Valuable Clubs</h2>{beta_badge()}</div>{table_html("clubs-most-table","clubs-most-body","clubs-most-count",["Badge","Club","League","Avg Market","Top Asset","Mode"])}</div><div class="ares-card"><div class="section-title-row"><h2 class="h4">Youngest High-Value Squads</h2>{beta_badge()}</div>{table_html("clubs-young-table","clubs-young-body","clubs-young-count",["Badge","Club","Average Age","U23 Value","Top Asset","Mode"])}</div><div class="ares-card"><div class="section-title-row"><h2 class="h4">U23 Value Leaders</h2>{beta_badge()}</div>{table_html("clubs-u23-table","clubs-u23-body","clubs-u23-count",["Badge","Club","Region","U23 Value","Top Asset","Mode"])}</div><div class="ares-card"><div class="section-title-row"><h2 class="h4">Aging Risk Clubs</h2>{beta_badge()}</div>{table_html("clubs-aging-table","clubs-aging-body","clubs-aging-count",["Club","Average Age","Weakest Unit","Trend","Mode"])}</div><div class="ares-card"><div class="section-title-row"><h2 class="h4">Rising Clubs</h2>{beta_badge()}</div>{table_html("clubs-rising-table","clubs-rising-body","clubs-rising-count",["Club","Region","Avg ARES","Trend","Mode"])}</div><div class="ares-card"><div class="section-title-row"><h2 class="h4">Falling Clubs</h2>{beta_badge()}</div>{table_html("clubs-falling-table","clubs-falling-body","clubs-falling-count",["Club","Region","Weakest Unit","Trend","Mode"])}</div></section></main><footer class="ares-footer">Seeded beta data club board.</footer>''' + scripts("../", "<script>" + inline + "".join(section_scripts) + "</script>")
    write_text("clubs/index.html", html)


def build_club_template() -> None:
    club_profile = clubs[0].copy()
    write_json("data/club_profile_sample.json", club_profile)
    html = head("Club Portfolio | ARES Football Market", "ARES club portfolio with squad quality, market value, U23 assets, transfer movement, contract risk, and squad depth.", "../") + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Club Portfolio</h1><p>Clubs are treated as football asset portfolios: squad quality, market value, age curve, U23 value, transfer risk, and depth.</p></div><section class="ares-section ares-card"><h2 class="h4">Club Market Snapshot</h2><div class="ares-status-terminal"><div class="ares-status-item"><strong>Club</strong><span>{clubs[0]["club_name"]}</span></div><div class="ares-status-item"><strong>League</strong><span>{clubs[0]["league"]}</span></div><div class="ares-status-item"><strong>Squad Quality</strong><span>{clubs[0]["avg_ares"]}</span></div><div class="ares-status-item"><strong>Squad Market Value</strong><span>{clubs[0]["avg_market"]}</span></div><div class="ares-status-item"><strong>Average Age</strong><span>{clubs[0]["average_age"]}</span></div><div class="ares-status-item"><strong>U23 Value</strong><span>{clubs[0]["u23_value"]}</span></div></div><p>{beta_badge()}</p></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Top 5 by ARES</h2>{table_html("club-ares-table","club-ares-body","club-ares-count",["Player","Position","ARES","Role","Mode"])}</div><div class="ares-card"><h2 class="h4">Top 5 by Market</h2>{table_html("club-market-table","club-market-body","club-market-count",["Player","Age","Market","Tier","Mode"])}</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>{table_html("club-u23-table","club-u23-body","club-u23-count",["Player","Age","Market","Reason","Mode"])}</div><div class="ares-card"><h2 class="h4">Recent Transfers</h2>{table_html("club-transfer-table","club-transfer-body","club-transfer-count",["Date","Player","Type","Impact","Mode"])}</div></section><section class="ares-section ares-card"><h2 class="h4">Weakest Position Groups</h2><p>Left back depth, backup striker minutes, and U23 defensive midfield are the current public-beta risk notes.</p></section><section class="ares-section ares-card"><h2 class="h4">Contract Risk</h2><p>Shorter contract windows are flagged separately from performance quality so Market Score does not pretend to be salary or fee data.</p></section><section class="ares-section ares-card"><h2 class="h4">Squad Depth</h2><p>ARES evaluates depth by role security, age curve, positional scarcity, and public-beta confidence.</p></section><section class="ares-section ares-card"><h2 class="h4">Source Notes</h2><p>Seeded beta data rows are fictional seeded records. No restricted feeds or scraped club imagery are used.</p></section></main><footer class="ares-footer">Seeded beta data club portfolio.</footer>''' + scripts("../", "<script>" +
        init_table("../data/public_players.json", "club-ares-table", "club-ares-body", None, [{"key":"player_name"},{"key":"position"},{"key":"ares_score","render":"score"},{"key":"role"},{"key":"source"}], filterKey="club", filterValue="Pacific Harbor FC", sortKey="ares_score", sortDirection="desc", limit=5) +
        init_table("../data/public_players.json", "club-market-table", "club-market-body", None, [{"key":"player_name"},{"key":"age"},{"key":"market_score","render":"market"},{"key":"market_tier","render":"tier"},{"key":"source"}], filterKey="club", filterValue="Pacific Harbor FC", sortKey="market_score", sortDirection="desc", limit=5) +
        init_table("../data/public_players.json", "club-u23-table", "club-u23-body", None, [{"key":"player_name"},{"key":"age"},{"key":"market_score","render":"market"},{"key":"reason"},{"key":"source"}], filterKey="club", filterValue="Pacific Harbor FC", maxAge=23, sortKey="market_score", sortDirection="desc", limit=5) +
        init_table("../data/public_transfers.json", "club-transfer-table", "club-transfer-body", None, [{"key":"date"},{"key":"player_name"},{"key":"transfer_type"},{"key":"market_impact"},{"key":"source"}], limit=5) +
        "</script>")
    write_text("clubs/club-template.html", html)


def build_leagues() -> None:
    inline = init_table("../data/public_leagues.json", "leagues-table", "leagues-body", "leagues-search", league_cols, sortKey="avg_market", sortDirection="desc")
    html = head(
        "Global Football League Rankings | Asia, MLS & Market Strength",
        "Compare football leagues by player quality, market value, U23 depth, transfer movement, league strength, and data confidence.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Global Football League Rankings</h1><p>Compare football leagues by player quality, market value, U23 depth, transfer movement, league strength, and data confidence.</p></div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Global","Europe","Asia","North America","South America","Africa","Oceania","MLS","AFC","CONCACAF"], "region")}<input id="leagues-search" class="ares-search mb-3" type="search" placeholder="Search league, country, region, tier, AFC, CONCACAF, or provider...">{table_html("leagues-table","leagues-body","leagues-count",["Rank","Badge","League","Country","Region","Tier","Clubs","Players Tracked","Avg ARES","Avg Market","U23 Share","Top Club","Top Player","Data Confidence","Last Updated","Source"])}</section></main><footer class="ares-footer">Seeded beta data global league board.</footer>''' + scripts("../", "<script>" + inline + "</script>")
    write_text("leagues/index.html", html)


def regional_page(filename: str, title: str, description: str, sections: list[str], region_values: list[str] | None = None, league_values: list[str] | None = None, player_filter: dict | None = None) -> None:
    prefix = "../"
    filter_opts = {}
    if region_values:
        filter_opts = {"filterKey": "region", "filterValues": region_values}
    if league_values:
        filter_opts = {"filterKey": "league_name", "filterValues": league_values}
    league_init = init_table("../data/public_leagues.json", "regional-league-table", "regional-league-body", "regional-league-search", league_cols, sortKey="avg_market", sortDirection="desc", **filter_opts)
    player_opts = player_filter or {}
    player_init = init_table("../data/public_players.json", "regional-player-table", "regional-player-body", None, [
        {"key":"player_name","render":"playerImage"},
        {"key":"player_name","render":"playerLink","pathPrefix":"../","showAvatar":False},
        {"key":"club"},
        {"key":"league"},
        {"key":"market_score","render":"market"},
        {"key":"ares_score","render":"score"},
        {"key":"source"},
    ], sortKey="market_score", sortDirection="desc", limit=8, **player_opts)
    section_cards = "".join(f'<div class="ares-status-item"><strong>{s}</strong><span>Seeded board active</span></div>' for s in sections)
    html = head(f"{title} | ARES Football Market", description, prefix) + nav(prefix) + f'''<main class="soccer-main"><div class="ares-page-title"><h1>{title}</h1><p>{description}</p></div><section class="ares-section ares-card"><div class="ares-status-grid">{section_cards}</div><p>{beta_badge()}</p></section><section class="ares-section ares-card"><h2 class="h4">Seeded Player Board</h2>{table_html("regional-player-table","regional-player-body","regional-player-count",["Image","Player","Club","League","Market","ARES","Mode"])}</section><section class="ares-section ares-card"><h2 class="h4">Seeded League Board</h2><input id="regional-league-search" class="ares-search mb-3" type="search" placeholder="Search league, country, region, or provider...">{table_html("regional-league-table","regional-league-body","regional-league-count",["Rank","Badge","League","Country","Region","Tier","Clubs","Players Tracked","Avg ARES","Avg Market","U23 Share","Top Club","Top Player","Data Confidence","Last Updated","Source"])}</section></main><footer class="ares-footer">{title} Seeded beta data.</footer>''' + scripts(prefix, "<script>" + player_init + league_init + "</script>")
    write_text(filename, html)


def build_regional_pages() -> None:
    regional_page(
        "leagues/asia.html",
        "Asia Market Board",
        "Track J1 League, K League, Saudi Pro League, Chinese Super League, A-League, Indian Super League, ASEAN leagues, and AFC competitions.",
        ["Top Asian Market Assets", "Top Asian ARES Players", "Top U23 Asian Assets", "J1 League Board", "K League Board", "Saudi Pro League Board", "ASEAN Watchlist", "AFC Competition Board", "Rising Markets", "Data Confidence by League"],
        region_values=["Asia", "Oceania"],
        player_filter={"filterKey": "region", "filterValues": ["Asia", "Oceania"]},
    )
    regional_page(
        "leagues/mls.html",
        "MLS Market Board",
        "Track MLS players, U22 assets, homegrowns, aging stars, Designated Players, MLS Next Pro, and Liga MX movement.",
        ["Top MLS ARES Players", "Top MLS Market Assets", "Best U22 Assets", "Best Homegrown Players", "Aging Star Risk Board", "MLS Next Pro Watchlist", "Liga MX / MLS Movement Board", "Designated Player Board", "Data Confidence by Club"],
        league_values=["Major League Soccer", "MLS Next Pro"],
        player_filter={"filterKey": "league", "filterValues": ["Major League Soccer", "MLS Next Pro"]},
    )
    regional_page(
        "leagues/north-america.html",
        "North America Market Board",
        "Track MLS, Liga MX, USL, Canadian Premier League, CONCACAF, cross-border movement, and U23 market assets.",
        ["MLS Board", "Liga MX Board", "USL Board", "Canadian Premier League Board", "CONCACAF Board", "Cross-Border Movement", "U23 Market Assets"],
        region_values=["North America"],
        player_filter={"filterKey": "region", "filterValue": "North America"},
    )


def build_league_template() -> None:
    write_json("data/league_profile_sample.json", leagues[0])
    html = head("League Market Profile | ARES Football Market", "ARES league profile with market snapshot, clubs table, top players, U23 assets, transfer movement, risers, fallers, and source notes.", "../") + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>League Market Profile</h1><p>A league page should feel like a market exchange: quality, value, U23 depth, transfers, and movement.</p></div><section class="ares-section ares-card"><h2 class="h4">League Market Snapshot</h2><div class="ares-status-terminal"><div class="ares-status-item"><strong>League</strong><span>{leagues[0]["league_name"]}</span></div><div class="ares-status-item"><strong>Country</strong><span>{leagues[0]["country"]}</span></div><div class="ares-status-item"><strong>Region</strong><span>{leagues[0]["region"]}</span></div><div class="ares-status-item"><strong>Clubs</strong><span>{leagues[0]["clubs"]}</span></div><div class="ares-status-item"><strong>Avg ARES</strong><span>{leagues[0]["avg_ares"]}</span></div><div class="ares-status-item"><strong>Avg Market</strong><span>{leagues[0]["avg_market"]}</span></div></div><p>{beta_badge()}</p></section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Clubs Table</h2>{table_html("league-clubs-table","league-clubs-body","league-clubs-count",["Club","Avg ARES","Avg Market","Top Asset","Mode"])}</div><div class="ares-card"><h2 class="h4">Top Players</h2>{table_html("league-players-table","league-players-body","league-players-count",["Player","Club","ARES","Market","Mode"])}</div><div class="ares-card"><h2 class="h4">Top U23 Assets</h2>{table_html("league-u23-table","league-u23-body","league-u23-count",["Player","Age","Market","Reason","Mode"])}</div><div class="ares-card"><h2 class="h4">Transfer Movement</h2>{table_html("league-transfer-table","league-transfer-body","league-transfer-count",["Date","Player","Type","Market Impact","Mode"])}</div><div class="ares-card"><h2 class="h4">Market Risers</h2>{table_html("league-risers-table","league-risers-body","league-risers-count",["Player","Change","Reason","Mode"])}</div><div class="ares-card"><h2 class="h4">Market Fallers</h2>{table_html("league-fallers-table","league-fallers-body","league-fallers-count",["Player","Trend","Reason","Mode"])}</div></section><section class="ares-section ares-card"><h2 class="h4">Source Notes</h2><p>Seeded beta data rows are fictional seeded records. Live player, club, transfer, and match data will replace these rows only after approved data sources are connected.</p></section></main><footer class="ares-footer">Seeded beta data league profile.</footer>''' + scripts("../", "<script>" +
        init_table("../data/public_clubs.json", "league-clubs-table", "league-clubs-body", None, [{"key":"club_name"},{"key":"avg_ares","render":"score"},{"key":"avg_market","render":"market"},{"key":"top_asset"},{"key":"source"}], limit=5) +
        init_table("../data/public_players.json", "league-players-table", "league-players-body", None, [{"key":"player_name"},{"key":"club"},{"key":"ares_score","render":"score"},{"key":"market_score","render":"market"},{"key":"source"}], limit=5, sortKey="ares_score", sortDirection="desc") +
        init_table("../data/public_players.json", "league-u23-table", "league-u23-body", None, [{"key":"player_name"},{"key":"age"},{"key":"market_score","render":"market"},{"key":"reason"},{"key":"source"}], maxAge=23, limit=5, sortKey="market_score", sortDirection="desc") +
        init_table("../data/public_transfers.json", "league-transfer-table", "league-transfer-body", None, [{"key":"date"},{"key":"player_name"},{"key":"transfer_type"},{"key":"market_impact"},{"key":"source"}], limit=5) +
        init_table("../data/public_market_changes.json", "league-risers-table", "league-risers-body", None, [{"key":"player_name"},{"key":"change"},{"key":"reason"},{"key":"source"}], limit=5) +
        init_table("../data/public_players.json", "league-fallers-table", "league-fallers-body", None, [{"key":"player_name"},{"key":"trend","render":"trend"},{"key":"reason"},{"key":"source"}], sortKey="trend_value", sortDirection="asc", limit=5) +
        "</script>")
    write_text("leagues/league-template.html", html)


def build_transfers() -> None:
    inline = init_table("../data/public_transfers.json", "transfers-table", "transfers-body", "transfers-search", transfer_cols, limit=20)
    section_scripts = [
        init_table("../data/public_transfers.json", "latest-transfer-table", "latest-transfer-body", None, [{"key":"date"},{"key":"player_name"},{"key":"transfer_type"},{"key":"market_impact"},{"key":"source"}], limit=5),
        init_table("../data/public_transfers.json", "loan-transfer-table", "loan-transfer-body", None, [{"key":"player_name"},{"key":"from_club"},{"key":"to_club"},{"key":"market_impact"},{"key":"source"}], filterKey="transfer_type", filterValue="Loan", limit=5),
        init_table("../data/public_transfers.json", "free-agent-transfer-table", "free-agent-transfer-body", None, [{"key":"player_name"},{"key":"from_club"},{"key":"to_club"},{"key":"market_impact"},{"key":"source"}], filterKey="transfer_type", filterValue="Free agent", limit=5),
        init_table("../data/public_transfers.json", "contract-transfer-table", "contract-transfer-body", None, [{"key":"player_name"},{"key":"transfer_type"},{"key":"ares_impact"},{"key":"market_impact"},{"key":"source"}], filterKey="transfer_type", filterValue="Contract signal", limit=5),
        init_table("../data/public_market_changes.json", "market-riser-table", "market-riser-body", None, [{"key":"player_name"},{"key":"club"},{"key":"change"},{"key":"reason"},{"key":"source"}], filterKey="trend", filterValue="Rising", limit=5),
        init_table("../data/public_market_changes.json", "market-faller-table", "market-faller-body", None, [{"key":"player_name"},{"key":"club"},{"key":"change"},{"key":"reason"},{"key":"source"}], filterKey="trend", filterValue="Falling", sortKey="change", sortDirection="asc", limit=5),
        init_table("../data/public_transfers.json", "academy-transfer-table", "academy-transfer-body", None, [{"key":"player_name"},{"key":"from_club"},{"key":"to_club"},{"key":"market_impact"},{"key":"source"}], filterKey="transfer_type", filterValue="Academy promotion", limit=5),
    ]
    html = head(
        "Football Transfers | Loans, Free Agents & Market Impact",
        "Track seeded public-beta permanent transfers, loans, free agents, academy promotions, contract signals, and market impact.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>Football Transfers</h1><p>Track permanent transfers, loans, free agents, academy promotions, contract signals, and market impact.</p></div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Permanent","Loan","Free Agent","Academy","Contract Signal","Market Riser","Market Faller","High Confidence"], "type")}<input id="transfers-search" class="ares-search mb-3" type="search" placeholder="Search player, club, league, movement type, or confidence...">{table_html("transfers-table","transfers-body","transfers-count",["Date","Image","Player","Age","Position","From Club","To Club","From League","To League","Transfer Type","ARES Impact","Market Impact","Confidence","Source","Last Updated"])}</section><section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Latest Transfers</h2>{table_html("latest-transfer-table","latest-transfer-body","latest-transfer-count",["Date","Player","Type","Market Impact","Mode"])}</div><div class="ares-card"><h2 class="h4">Loans</h2>{table_html("loan-transfer-table","loan-transfer-body","loan-transfer-count",["Player","From","To","Market Impact","Mode"])}</div><div class="ares-card"><h2 class="h4">Free Agents</h2>{table_html("free-agent-transfer-table","free-agent-transfer-body","free-agent-transfer-count",["Player","From","To","Market Impact","Mode"])}</div><div class="ares-card"><h2 class="h4">Contract Signals</h2>{table_html("contract-transfer-table","contract-transfer-body","contract-transfer-count",["Player","Type","ARES Impact","Market Impact","Mode"])}</div><div class="ares-card"><h2 class="h4">Market Risers</h2>{table_html("market-riser-table","market-riser-body","market-riser-count",["Player","Club","Change","Reason","Mode"])}</div><div class="ares-card"><h2 class="h4">Market Fallers</h2>{table_html("market-faller-table","market-faller-body","market-faller-count",["Player","Club","Change","Reason","Mode"])}</div><div class="ares-card"><h2 class="h4">Academy Promotions</h2>{table_html("academy-transfer-table","academy-transfer-body","academy-transfer-count",["Player","From","To","Market Impact","Mode"])}</div></section><section class="ares-section ares-card"><h2 class="h4">Impact Definitions</h2><p><strong>ARES Impact</strong> means how the move changes projected on-field role and quality. <strong>Market Impact</strong> means how the move changes asset value through age, league, club, role, and demand.</p></section></main><footer class="ares-footer">Seeded beta data transfer movement board.</footer>''' + scripts("../", "<script>" + inline + "".join(section_scripts) + "</script>")
    write_text("transfers/index.html", html)


def build_watchlist() -> None:
    inline = init_table("../data/public_watchlist.json", "watchlist-table", "watchlist-body", "watchlist-search", watch_cols, limit=20)
    html = head(
        "ARES Watchlist | Youth, Loan, Free Agent & Thin-Data Players",
        "Track youth, loan, free agent, lower-division, and thin-data players before they qualify for official ARES or Market rankings.",
        "../",
    ) + nav("../") + f'''<main class="soccer-main"><div class="ares-page-title"><h1>ARES Watchlist</h1><p>Track youth, loan, free agent, lower-division, and thin-data players before they qualify for official ARES or Market rankings.</p></div><div class="ares-demo-banner">Demo rows show early-signal tracking. Players remain outside official rankings until data confidence improves.</div>{status_section("../")}<section class="ares-section ares-card">{filter_chips(["Youth Breakout","U21 Asset","U23 Asset","Loan Watch","Free Agent","Lower Division","Role Expansion","Injury Return","Contract Signal","Scout Flag"], "type")}<input id="watchlist-search" class="ares-search mb-3" type="search" placeholder="Search player, club, level, reason, category, or confidence...">{table_html("watchlist-table","watchlist-body","watchlist-count",["Image","Player","Age","Position","Level","Club","Reason","Status","Last Movement","Confidence","Last Updated","Source"])}</section></main><footer class="ares-footer">Seeded beta data watchlist board.</footer>''' + scripts("../", "<script>" + inline + "</script>")
    write_text("watchlist/index.html", html)


def build_methodology() -> None:
    html = head(
        "How ARES Score and Market Score Work",
        "ARES Football Market explains ARES Score, Market Score, position-specific components, confidence labels, source policy, image policy, and public-beta examples.",
    ) + nav() + f'''<main class="soccer-main"><div class="ares-page-title"><h1>How ARES Score and Market Score Work</h1><p>ARES Football Market separates on-field football quality from football asset value.</p></div><section class="ares-section ares-card"><h2>Methodology Status</h2><p>The scoring framework is defined. Seeded beta data rows are fictional examples. Live model outputs depend on connected player, club, league, transfer, and availability data.</p></section><section class="ares-section ares-card"><h2>What ARES Score Measures</h2><p>ARES Score measures on-field football quality through performance, efficiency, role and usage, opponent adjustment, volume, durability, and trend.</p></section><section class="ares-section ares-card"><h2>What Market Score Measures</h2><p>Market Score measures football asset value through ARES quality, age and upside, position value, league tier, market signal, movement value, and durability.</p></section><section class="ares-section ares-card"><h2>ARES Score Formula</h2><p class="formula">Football ARES Score =\\n0.30 * Performance\\n+ 0.20 * Efficiency\\n+ 0.15 * Role / Usage\\n+ 0.15 * Opponent Adjustment\\n+ 0.10 * Volume\\n+ 0.05 * Durability\\n+ 0.05 * Trend</p></section><section class="ares-section ares-card"><h2>Market Score Formula</h2><p class="formula">Football Market Score =\\n0.25 * ARES Score\\n+ 0.20 * Age / Upside\\n+ 0.20 * Position Value\\n+ 0.15 * League Tier\\n+ 0.10 * Market Signal\\n+ 0.05 * Movement Value\\n+ 0.05 * Durability</p></section><section class="ares-section ares-card"><h2>Example ARES Score Calculation</h2><p>A public-beta attacking midfielder with Performance 91, Efficiency 88, Role 94, Opponent Context 84, Volume 90, Durability 86, and Trend 92 grades near 89.7 after weighting.</p></section><section class="ares-section ares-card"><h2>Example Market Score Calculation</h2><p>A 21-year-old wide forward with ARES 86.7, strong age upside, scarce role, stable minutes, and rising movement signal can carry a Market Score above 92 even before becoming the top ARES player.</p></section><section class="ares-section ares-card"><h2>High ARES, Lower Market Example</h2><p>A 29-year-old goalkeeper can have strong current ARES quality but a lower Market Score because age curve, contract horizon, and position liquidity reduce long-term asset value.</p></section><section class="ares-section ares-card"><h2>Young Player, High Market Example</h2><p>A 19-year-old rotation striker can have a lower current ARES Score but a high Market Score if minutes are rising, role scarcity is strong, and the age curve suggests upside.</p></section><section class="ares-section ares-card"><h2>Position-Specific Components</h2><div class="ares-module-grid"><div><h3>Forward Module</h3><p>Non-penalty goals, xG, shots, shot quality, touches in box, pressing actions, dribbles, off-ball runs, durability, and league adjustment.</p></div><div><h3>Midfielder Module</h3><p>Progressive passes, carries, chance creation, ball retention, defensive actions, press resistance, duels, minutes load, and league adjustment.</p></div><div><h3>Defender Module</h3><p>Tackles, interceptions, aerial duels, clearances, ball progression, error rate, defensive line role, availability, and league adjustment.</p></div><div><h3>Goalkeeper Module</h3><p>Save percentage, goals prevented, cross claims, distribution, sweeper actions, error rate, minutes, and league adjustment.</p></div></div></section><section class="ares-section ares-card"><h2>Confidence Label Guide</h2><div class="ares-status-grid"><div class="ares-status-item"><strong>High</strong><span>Stable seeded fields or future provider-backed rows with broad coverage</span></div><div class="ares-status-item"><strong>Medium</strong><span>Good identity and usage signal, but some component fields need stronger coverage</span></div><div class="ares-status-item"><strong>Low</strong><span>Thin-data, youth, lower-division, or watchlist-only profile</span></div></div></section><section class="ares-section ares-card"><h2>League Strength Adjustment</h2><p>League strength is designed to prevent equal raw production from being treated the same across unequal competitions. Live outputs require connected league and player data.</p></section><section class="ares-section ares-card"><h2>Age Curve Logic</h2><p>Age curve logic rewards upside windows, prime-year stability, and role durability while flagging aging, injury, and role-decline risk.</p></section><section class="ares-section ares-card"><h2>Transfer Signal Logic</h2><p>Transfer signal logic tracks movement type, sending club, receiving club, league change, role opportunity, scarcity, and market impact.</p></section><section class="ares-section ares-card"><h2>What ARES Does Not Claim</h2><p>ARES Score is not a transfer fee.<br>ARES Score is not a salary estimate.<br>ARES Score is not a fantasy rank.<br>ARES Score is not a scouting report by itself.<br>Market Score is not the same as market price.<br>Market Score is not a guaranteed sale value.<br>Market Score is not a betting line.<br>Market Score is not an official club valuation.</p></section><section class="ares-section ares-card"><h2>Source Policy</h2><p>ARES does not claim to be official league data, does not replace scouting, does not claim to know assignments perfectly, and does not use restricted commercial scraping.</p></section><section class="ares-section ares-card"><h2>Image Policy</h2><p>Player images must come from provider-supplied URLs, properly licensed Wikimedia Commons pages, TheSportsDB artwork, or the ARES fallback avatar. Do not scrape Transfermarkt, Google Images, club websites, agency previews, or social media.</p></section></main><footer class="ares-footer">ARES methodology framework with public-beta examples.</footer>''' + scripts()
    write_text("methodology.html", html)


def build_search() -> list[dict]:
    rows = []
    for p in players:
        rows.append({
            "type": "Player",
            "player_name": p["player_name"],
            "position": p["position"],
            "club": p["club"],
            "league": p["league"],
            "country": p["country"],
            "region": p["region"],
            "keywords": f"{p['market_tier']} {p['ares_tier']} {p['role']} {p['source']}",
            "url": "players/player-template.html",
        })
    for c in clubs:
        rows.append({"type": "Club", "club_name": c["club_name"], "league": c["league"], "country": c["country"], "region": c["region"], "keywords": c["top_asset"], "url": "clubs/club-template.html"})
    for l in leagues:
        rows.append({"type": "League", "league": l["league_name"], "country": l["country"], "region": l["region"], "keywords": f"{l['top_club']} {l['top_player']} {l['source']}", "url": "leagues/league-template.html"})
    rows.extend([
        {"type": "Board", "league": "Asia Market Board", "region": "Asia", "keywords": "J1 K League Saudi AFC ASEAN", "url": "leagues/asia.html"},
        {"type": "Board", "league": "MLS Market Board", "region": "North America", "keywords": "Major League Soccer U22 MLS Next Pro", "url": "leagues/mls.html"},
        {"type": "Board", "league": "North America Market Board", "region": "North America", "keywords": "MLS Liga MX USL CONCACAF", "url": "leagues/north-america.html"},
    ])
    return rows


def update_assets() -> None:
    # Patch the table renderer for safe image handling and separate image/player columns.
    tables_path = ROOT / "assets/js/ares-tables.js"
    text = tables_path.read_text(encoding="utf-8")
    text = text.replace(
        '  function renderPlayerAvatar(row) {\n    const label = row.player_name || row.name || "ARES player";\n    const alt = data.safeText([label, row.position, row.club].filter(Boolean).join(", "));\n    // Image safety rule: only render provider-supplied or licensed image URLs already present in data.\n    // Do not scrape Transfermarkt, Google Images, club sites, agency previews, or social media.\n    if (row.photo_url) return \'<span class="ares-player-photo"><img src="\' + data.safeText(row.photo_url) + \'" alt="\' + alt + \'" loading="lazy"></span>\';\n    return \'<span class="ares-player-avatar-stack"><span class="ares-player-photo" aria-label="\' + alt + \'">\' + data.safeText(initials(label)) + \'</span><span class="ares-position-mini">\' + data.safeText(row.position || "FB") + "</span></span>";\n  }\n\n  function renderPlayerIdentity(label, row, column) {\n    const href = prefixedHref(row.player_url || row.url || column.fallbackUrl || "players/player-template.html", column.pathPrefix);\n    return \'<a class="ares-player-identity" href="\' + data.safeText(href) + \'">\' + renderPlayerAvatar(row) + \'<span>\' + data.safeText(label) + "</span></a>";\n  }\n',
        '''  function imageIsSafe(row) {
    const status = String(row.photo_license_status || "").toLowerCase();
    return Boolean(row.photo_url) && ["provider_supplied", "licensed_commons", "commons_licensed", "cc_by", "cc_by_sa", "public_domain", "approved_provider"].includes(status);
  }

  function renderPlayerAvatar(row) {
    const label = row.player_name || row.name || "ARES player";
    const alt = data.safeText([label, row.position, row.club].filter(Boolean).join(", "));
    // Image safety rule: only render provider-supplied or licensed image URLs already present in data.
    // Do not scrape Transfermarkt, Google Images, club sites, agency previews, or social media.
    if (imageIsSafe(row)) return '<span class="ares-player-photo"><img src="' + data.safeText(row.photo_url) + '" alt="' + alt + '" loading="lazy" onerror="this.remove()"></span>';
    return '<span class="ares-player-avatar-stack" title="' + alt + '"><span class="ares-player-photo" aria-label="' + alt + '">' + data.safeText(row.initials || initials(label)) + '</span><span class="ares-position-mini">' + data.safeText(row.position || "FB") + '</span><span class="ares-avatar-club">' + data.safeText(row.club || row.region || "ARES") + "</span></span>";
  }

  function renderPlayerIdentity(label, row, column) {
    const href = prefixedHref(row.player_url || row.url || column.fallbackUrl || "players/player-template.html", column.pathPrefix);
    const avatar = column.showAvatar === false ? "" : renderPlayerAvatar(row);
    return '<a class="ares-player-identity" href="' + data.safeText(href) + '">' + avatar + '<span>' + data.safeText(label) + "</span></a>";
  }
''',
    )
    tables_path.write_text(text, encoding="utf-8")
    mirror_existing("assets/js/ares-tables.js")

    soccer_path = ROOT / "assets/js/soccer-pages.js"
    text = soccer_path.read_text(encoding="utf-8")
    text = text.replace(
        '''  function initTable(options) {
    const data = window.AresData;
    const tables = window.AresTables;
    data.loadJson(options.dataPath)
      .then(function (rows) {
        tables.renderTable(options.bodyId, rows, options.columns);
        tables.makeTableSortable(options.tableId);
''',
        '''  function prepareRows(rows, options) {
    let prepared = Array.isArray(rows) ? rows.slice() : [];
    if (options.filterKey && options.filterValues) {
      prepared = prepared.filter(function (row) { return options.filterValues.includes(row[options.filterKey]); });
    } else if (options.filterKey && options.filterValue) {
      prepared = prepared.filter(function (row) { return row[options.filterKey] === options.filterValue; });
    }
    if (options.maxAge !== undefined) {
      prepared = prepared.filter(function (row) { return Number(row.age) <= Number(options.maxAge); });
    }
    if (options.minAge !== undefined) {
      prepared = prepared.filter(function (row) { return Number(row.age) >= Number(options.minAge); });
    }
    if (options.sortKey) {
      const factor = options.sortDirection === "asc" ? 1 : -1;
      prepared.sort(function (left, right) {
        const leftValue = left[options.sortKey];
        const rightValue = right[options.sortKey];
        const leftNumber = Number(leftValue);
        const rightNumber = Number(rightValue);
        if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) return (leftNumber - rightNumber) * factor;
        return String(leftValue || "").localeCompare(String(rightValue || "")) * factor;
      });
    }
    if (options.limit) prepared = prepared.slice(0, Number(options.limit));
    return prepared;
  }

  function initTable(options) {
    const data = window.AresData;
    const tables = window.AresTables;
    data.loadJson(options.dataPath)
      .then(function (rows) {
        tables.renderTable(options.bodyId, prepareRows(rows, options), options.columns);
        tables.makeTableSortable(options.tableId);
''',
    )
    text = text.replace(
        '''  function fillPlayerImage(record) {
    const container = document.getElementById("player-photo");
    if (!container) return;
    const label = [record.player_name, record.position, record.club].filter(Boolean).join(", ");
    if (record.photo_url) {
      container.innerHTML = '<img src="' + window.AresData.safeText(record.photo_url) + '" alt="' + window.AresData.safeText(label) + '" loading="lazy">';
    } else {
      container.textContent = initials(record.player_name);
      container.setAttribute("aria-label", label);
    }
    fillText("photo-source", record.photo_source || "ARES fallback");
    fillText("photo-license", record.photo_license_status || "branded_fallback");
    fillText("photo-credit", record.photo_credit || "ARES branded fallback avatar");
  }
''',
        '''  function imageIsSafe(record) {
    const status = String(record.photo_license_status || "").toLowerCase();
    return Boolean(record.photo_url) && ["provider_supplied", "licensed_commons", "commons_licensed", "cc_by", "cc_by_sa", "public_domain", "approved_provider"].includes(status);
  }

  function fillPlayerImage(record) {
    const container = document.getElementById("player-photo");
    if (!container) return;
    const label = [record.player_name, record.position, record.club].filter(Boolean).join(", ");
    if (imageIsSafe(record)) {
      container.innerHTML = '<img src="' + window.AresData.safeText(record.photo_url) + '" alt="' + window.AresData.safeText(label) + '" loading="lazy" onerror="this.remove()">';
    } else {
      container.innerHTML = '<span>' + window.AresData.safeText(record.initials || initials(record.player_name)) + '</span><small>' + window.AresData.safeText(record.position || "") + '</small>';
      container.setAttribute("aria-label", label);
    }
    fillText("photo-source", record.photo_source || "ARES fallback");
    fillText("photo-license", record.photo_license_status || "branded_fallback");
    fillText("photo-credit", record.photo_credit || "ARES branded fallback avatar");
  }
''',
    )
    soccer_path.write_text(text, encoding="utf-8")
    mirror_existing("assets/js/soccer-pages.js")

    css_path = ROOT / "assets/css/ares-components.css"
    css = css_path.read_text(encoding="utf-8")
    additions = """

.ares-beta-note {
  margin: 0.85rem 0 0;
  color: var(--ares-muted);
  font-size: 0.875rem;
}

.ares-beta-badge {
  display: inline-flex;
  align-items: center;
  min-height: 1.45rem;
  padding: 0.18rem 0.5rem;
  color: var(--ares-navy);
  background: rgba(247, 201, 72, 0.24);
  border: 1px solid rgba(247, 201, 72, 0.72);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0;
  text-transform: uppercase;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.section-title-row h2 {
  margin: 0;
}

.ares-hero-terminal {
  align-self: stretch;
  background: rgba(255, 255, 255, 0.96);
}

.ares-avatar-club {
  max-width: 5.5rem;
  color: var(--ares-muted);
  font-size: 0.62rem;
  font-weight: 800;
  line-height: 1.1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ares-player-identity {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.ares-profile-photo {
  display: grid;
  gap: 0.15rem;
  align-content: center;
  justify-items: center;
}

.ares-profile-photo small {
  color: var(--ares-gold);
  font-size: 0.72rem;
  font-weight: 900;
}
"""
    if ".ares-beta-badge" not in css:
        css += additions
    css_path.write_text(css, encoding="utf-8")
    mirror_existing("assets/css/ares-components.css")


def build_supporting_json() -> None:
    write_json("data/public_players.json", players)
    write_json("data/public_clubs.json", clubs)
    write_json("data/public_leagues.json", leagues)
    write_json("data/public_transfers.json", transfers)
    write_json("data/public_watchlist.json", watchlist)
    write_json("data/public_market_changes.json", market_changes)
    write_json("data/public_search.json", build_search())
    write_json("data/data_status.json", {
        "data_mode": "public_beta_demo",
        "last_updated": ISO_TODAY,
        "players_tracked": len(players),
        "clubs_tracked": len(clubs),
        "leagues_tracked": len(leagues),
        "player_images": "Fallback avatars active",
        "ares_model": "Formula ready",
        "market_model": "Formula ready",
        "source": SOURCE,
    })


def main() -> None:
    generate_visual_assets()
    build_supporting_json()
    update_assets()
    build_home()
    build_rankings()
    build_players()
    build_player_template()
    build_clubs()
    build_club_template()
    build_leagues()
    build_regional_pages()
    build_league_template()
    build_transfers()
    build_watchlist()
    build_methodology()
    print("public beta site generated")


if __name__ == "__main__":
    main()

