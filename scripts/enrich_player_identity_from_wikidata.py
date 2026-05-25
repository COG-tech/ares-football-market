#!/usr/bin/env python3
"""Enrich public player rows with Wikidata identity facts.

The public player layer already carries Wikidata QIDs for Commons-backed rows.
This script adds identity facts that should not be inferred from club country:
nationality / citizenship and height. It writes a small cache so the build
pipeline can keep those facts after future regenerations.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TODAY = date.today().isoformat()
PLAYERS_PATHS = [
    ROOT / "data" / "public_players.json",
    ROOT / "data" / "wikimedia_players.json",
]
CACHE_PATH = ROOT / "data" / "player_identity_wikidata.json"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "ARESFootballMarket/1.0 (public beta data enrichment; https://github.com/COG-tech/ares-football-market)"


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, rows: Any) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def request_entities(ids: list[str], props: str) -> dict[str, Any]:
    params = {
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": props,
        "languages": "en",
        "format": "json",
    }
    url = WIKIDATA_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == 4:
                raise
            time.sleep(1.5 + attempt)
    return {}


def claim_values(entity: dict[str, Any], prop: str) -> list[Any]:
    claims = entity.get("claims", {}).get(prop, [])
    values: list[Any] = []
    for claim in claims:
        mainsnak = claim.get("mainsnak", {})
        datavalue = mainsnak.get("datavalue", {})
        if "value" in datavalue:
            values.append(datavalue["value"])
    return values


def entity_qid(value: Any) -> str:
    if isinstance(value, dict) and value.get("entity-type") == "item":
        return "Q" + str(value.get("numeric-id"))
    return ""


def quantity_float(value: Any) -> float | None:
    if not isinstance(value, dict):
        return None
    try:
        return float(str(value.get("amount", "")).replace("+", ""))
    except ValueError:
        return None


def height_payload(entity: dict[str, Any]) -> dict[str, Any]:
    values = claim_values(entity, "P2048")
    if not values:
        return {}
    height = quantity_float(values[0])
    if not height:
        return {}
    # Wikidata footballer heights are normally metres. Guard against centimetres.
    metres = height / 100 if height > 3 else height
    return {"height": f"{metres:.2f} m", "height_cm": round(metres * 100)}


def labels_for(qids: set[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    todo = sorted(qid for qid in qids if qid)
    for batch in chunks(todo, 50):
        payload = request_entities(batch, "labels")
        for qid, entity in payload.get("entities", {}).items():
            label = entity.get("labels", {}).get("en", {}).get("value")
            if label:
                labels[qid] = label
        time.sleep(0.25)
    return labels


def build_cache(players: list[dict[str, Any]]) -> list[dict[str, Any]]:
    qids = sorted({str(row.get("wikidata_qid", "")).strip() for row in players if row.get("wikidata_qid")})
    entities: dict[str, dict[str, Any]] = {}
    referenced_country_qids: set[str] = set()

    for batch in chunks(qids, 50):
        payload = request_entities(batch, "claims|labels")
        for qid, entity in payload.get("entities", {}).items():
            if entity.get("missing"):
                continue
            entities[qid] = entity
            for prop in ("P27", "P1532"):
                for value in claim_values(entity, prop):
                    country_qid = entity_qid(value)
                    if country_qid:
                        referenced_country_qids.add(country_qid)
        time.sleep(0.35)

    country_labels = labels_for(referenced_country_qids)
    cache: list[dict[str, Any]] = []
    for qid, entity in sorted(entities.items()):
        citizenship_qids = [entity_qid(value) for value in claim_values(entity, "P27")]
        sport_country_qids = [entity_qid(value) for value in claim_values(entity, "P1532")]
        citizenship = [country_labels.get(item, "") for item in citizenship_qids if country_labels.get(item)]
        sport_country = [country_labels.get(item, "") for item in sport_country_qids if country_labels.get(item)]
        row: dict[str, Any] = {
            "wikidata_qid": qid,
            "identity_source": "Wikidata",
            "identity_source_url": f"https://www.wikidata.org/wiki/{qid}",
            "identity_checked": TODAY,
        }
        if citizenship:
            row["citizenship"] = " / ".join(dict.fromkeys(citizenship))
            row["nationality"] = row["citizenship"]
        if sport_country:
            row["sport_country"] = " / ".join(dict.fromkeys(sport_country))
            row["national_team_country"] = row["sport_country"]
            row["nationality"] = row.get("nationality") or row["sport_country"]
        row.update(height_payload(entity))
        cache.append(row)
    return cache


def apply_cache(rows: list[dict[str, Any]], cache: dict[str, dict[str, Any]]) -> int:
    updated = 0
    for row in rows:
        qid = str(row.get("wikidata_qid", "")).strip()
        facts = cache.get(qid)
        if not facts:
            continue
        for key, value in facts.items():
            if key == "wikidata_qid":
                continue
            if value not in ("", None):
                row[key] = value
        updated += 1
    return updated


def main() -> None:
    players = read_json(PLAYERS_PATHS[0], [])
    if not isinstance(players, list):
        raise SystemExit("data/public_players.json must be a list")

    cache_rows = build_cache(players)
    write_json(CACHE_PATH, cache_rows)
    cache = {row["wikidata_qid"]: row for row in cache_rows}

    for path in PLAYERS_PATHS:
        rows = read_json(path, [])
        if not isinstance(rows, list):
            continue
        updated = apply_cache(rows, cache)
        write_json(path, rows)
        print(f"{path.relative_to(ROOT)} updated rows: {updated}")
    print(f"{CACHE_PATH.relative_to(ROOT)} rows: {len(cache_rows)}")


if __name__ == "__main__":
    main()
