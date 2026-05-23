#!/usr/bin/env python3
"""
ARES Wikimedia Commons Image Downloader

Purpose:
- Search Wikimedia Commons for football / gridiron images by entity name.
- Download only files whose metadata appears compatible with commercial reuse.
- Save image files plus a rights/attribution registry for ARES.
- Never scrape Google, Transfermarkt, ESPN, club sites, NFL, MLS, Getty, AP, Reuters, or social media.

Input CSV required columns:
    entity_id,entity_name,sport,league,team

Optional columns:
    commons_title,wikidata_qid

If `commons_title` is present, the tool checks that exact Wikimedia
Commons file before doing any text search. This is preferred for scale
because Wikidata P18 image claims point to known Commons files.

Install:
    pip install requests pandas python-slugify tqdm

Run:
    python ares_commons_image_downloader.py --input ares_entities_sample.csv --output ares_commons_output --contact you@example.com --max-results 5
"""

from __future__ import annotations

import argparse
import html
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

import pandas as pd
import requests
from slugify import slugify
from tqdm import tqdm


COMMONS_API = "https://commons.wikimedia.org/w/api.php"

ALLOW_LICENSE_HINTS = [
    "cc0",
    "public domain",
    "pd",
    "cc by",
    "cc-by",
    "cc by-sa",
    "cc-by-sa",
]

BLOCK_LICENSE_HINTS = [
    "noncommercial",
    "non-commercial",
    "cc by-nc",
    "cc-by-nc",
    "-nc",
    "no derivatives",
    "noderivatives",
    "cc by-nd",
    "cc-by-nd",
    "-nd",
    "all rights reserved",
]

IMAGE_MIME_ALLOW = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/svg+xml",
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        value = value.get("value", "")
    text = html.unescape(str(value))
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_get_ext(ext: Dict[str, Any], key: str) -> str:
    return clean_text(ext.get(key, {}).get("value", ""))


def license_is_allowed(license_short: str, usage_terms: str, license_url: str) -> Tuple[bool, str]:
    blob = f"{license_short} {usage_terms} {license_url}".lower()
    for bad in BLOCK_LICENSE_HINTS:
        if bad in blob:
            return False, f"blocked_license_hint:{bad}"
    if not blob.strip():
        return False, "missing_license_metadata"
    for good in ALLOW_LICENSE_HINTS:
        if good in blob:
            return True, f"allowed_license_hint:{good}"
    return False, "license_not_on_allowlist"


def make_user_agent(contact: str) -> str:
    contact = contact.strip() or "contact-not-provided@example.com"
    return f"ARESFootballMarketCommonsDownloader/1.0 ({contact})"


@dataclass
class ImageRecord:
    entity_id: str
    entity_name: str
    sport: str
    league: str
    team: str
    image_status: str
    display_allowed: bool
    downloaded: bool
    local_path: str
    commons_title: str
    source_url: str
    file_url: str
    thumb_url: str
    mime: str
    width: int
    height: int
    creator: str
    credit: str
    license_short_name: str
    license_url: str
    usage_terms: str
    attribution_required: bool
    commercial_use_allowed: bool
    paid_site_display_allowed: bool
    cropping_allowed: str
    attribution_text: str
    date_checked: str
    notes: str


def commons_request(session: requests.Session, params: Dict[str, Any], sleep_seconds: float) -> Dict[str, Any]:
    time.sleep(sleep_seconds)
    response = session.get(COMMONS_API, params=params, timeout=30)
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", "10"))
        time.sleep(retry_after)
        response = session.get(COMMONS_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_commons(session: requests.Session, query: str, max_results: int, thumb_width: int, sleep_seconds: float) -> List[Dict[str, Any]]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": max_results,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": thumb_width,
    }
    data = commons_request(session, params, sleep_seconds)
    pages = data.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        ext = info.get("extmetadata", {})
        results.append(
            {
                "title": page.get("title", ""),
                "pageid": page.get("pageid", ""),
                "fullurl": info.get("descriptionurl", ""),
                "file_url": info.get("url", ""),
                "thumb_url": info.get("thumburl", ""),
                "mime": info.get("mime", ""),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "artist": safe_get_ext(ext, "Artist"),
                "credit": safe_get_ext(ext, "Credit"),
                "license_short": safe_get_ext(ext, "LicenseShortName"),
                "license_url": safe_get_ext(ext, "LicenseUrl"),
                "usage_terms": safe_get_ext(ext, "UsageTerms"),
                "object_name": safe_get_ext(ext, "ObjectName"),
                "image_description": safe_get_ext(ext, "ImageDescription"),
                "restrictions": safe_get_ext(ext, "Restrictions"),
            }
        )
    return results


def normalize_commons_title(title: str) -> str:
    title = clean_text(title).strip()
    if not title:
        return ""
    title = unquote(title)
    title = title.replace("_", " ")
    if not title.lower().startswith("file:"):
        title = f"File:{title}"
    return title


def get_commons_file(session: requests.Session, title: str, thumb_width: int, sleep_seconds: float) -> List[Dict[str, Any]]:
    title = normalize_commons_title(title)
    if not title:
        return []
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "imageinfo",
        "iiprop": "url|mime|size|extmetadata",
        "iiurlwidth": thumb_width,
    }
    data = commons_request(session, params, sleep_seconds)
    pages = data.get("query", {}).get("pages", {})
    results = []
    for page in pages.values():
        if "missing" in page:
            continue
        info_list = page.get("imageinfo", [])
        if not info_list:
            continue
        info = info_list[0]
        ext = info.get("extmetadata", {})
        results.append(
            {
                "title": page.get("title", title),
                "pageid": page.get("pageid", ""),
                "fullurl": info.get("descriptionurl", ""),
                "file_url": info.get("url", ""),
                "thumb_url": info.get("thumburl", ""),
                "mime": info.get("mime", ""),
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "artist": safe_get_ext(ext, "Artist"),
                "credit": safe_get_ext(ext, "Credit"),
                "license_short": safe_get_ext(ext, "LicenseShortName"),
                "license_url": safe_get_ext(ext, "LicenseUrl"),
                "usage_terms": safe_get_ext(ext, "UsageTerms"),
                "object_name": safe_get_ext(ext, "ObjectName"),
                "image_description": safe_get_ext(ext, "ImageDescription"),
                "restrictions": safe_get_ext(ext, "Restrictions"),
            }
        )
    return results


def build_queries(entity_name: str, sport: str, league: str, team: str) -> List[str]:
    name = entity_name.strip()
    sport_l = sport.strip().lower()
    league = league.strip()
    team = team.strip()
    if sport_l in {"soccer", "football", "association football"}:
        queries = [f'"{name}" association football', f'"{name}" footballer', f'"{name}" soccer']
    elif sport_l in {"gridiron", "american football", "nfl", "college football"}:
        queries = [f'"{name}" American football', f'"{name}" NFL', f'"{name}" football player']
    else:
        queries = [f'"{name}" {sport}']
    if team:
        queries.insert(0, f'"{name}" "{team}"')
    if league:
        queries.insert(0, f'"{name}" "{league}"')
    seen = set()
    return [query for query in queries if not (query in seen or seen.add(query))]


def choose_candidate(candidates: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    rejected = []
    for candidate in candidates:
        mime = candidate.get("mime", "")
        if mime not in IMAGE_MIME_ALLOW:
            candidate["reject_reason"] = f"unsupported_mime:{mime}"
            rejected.append(candidate)
            continue
        allowed, reason = license_is_allowed(candidate.get("license_short", ""), candidate.get("usage_terms", ""), candidate.get("license_url", ""))
        if not allowed:
            candidate["reject_reason"] = reason
            rejected.append(candidate)
            continue
        restrictions = candidate.get("restrictions", "").lower()
        if restrictions and restrictions not in {"none", "no restrictions"}:
            candidate["reject_reason"] = f"has_restrictions_metadata:{restrictions[:80]}"
            rejected.append(candidate)
            continue
        candidate["accept_reason"] = reason
        return candidate, rejected
    return None, rejected


def download_file(session: requests.Session, url: str, out_path: Path, sleep_seconds: float) -> bool:
    if not url:
        return False
    time.sleep(sleep_seconds)
    with session.get(url, stream=True, timeout=60) as response:
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "10"))
            time.sleep(retry_after)
            response = session.get(url, stream=True, timeout=60)
        response.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    handle.write(chunk)
    return True


def extension_from_mime(mime: str, url: str) -> str:
    if mime == "image/jpeg":
        return ".jpg"
    if mime == "image/png":
        return ".png"
    if mime == "image/webp":
        return ".webp"
    if mime == "image/tiff":
        return ".tif"
    if mime == "image/svg+xml":
        return ".svg"
    suffix = Path(url.split("?")[0]).suffix.lower()
    return suffix if suffix else ".img"


def attribution_text(candidate: Dict[str, Any]) -> str:
    title = candidate.get("object_name") or candidate.get("title", "").replace("File:", "")
    creator = candidate.get("artist") or candidate.get("credit") or "Unknown creator"
    source = candidate.get("fullurl", "")
    license_short = candidate.get("license_short", "")
    license_url = candidate.get("license_url", "")
    license_text = f"{license_short} ({license_url})" if license_url else license_short
    return " | ".join([f'Image: "{title}"', f"Creator: {creator}", f"Source: {source}", f"License: {license_text}"])


def pending_record(entity_id: str, entity_name: str, sport: str, league: str, team: str, date_checked: str) -> ImageRecord:
    return ImageRecord(
        entity_id=entity_id,
        entity_name=entity_name,
        sport=sport,
        league=league,
        team=team,
        image_status="rights_pending",
        display_allowed=False,
        downloaded=False,
        local_path="",
        commons_title="",
        source_url="",
        file_url="",
        thumb_url="",
        mime="",
        width=0,
        height=0,
        creator="",
        credit="",
        license_short_name="",
        license_url="",
        usage_terms="",
        attribution_required=False,
        commercial_use_allowed=False,
        paid_site_display_allowed=False,
        cropping_allowed="unknown",
        attribution_text="",
        date_checked=date_checked,
        notes="No acceptable Wikimedia Commons image found by conservative license filter.",
    )


def run(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    output_dir = Path(args.output)
    image_dir = output_dir / "images"
    metadata_dir = output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    frame = pd.read_csv(input_path)
    required = {"entity_id", "entity_name", "sport", "league", "team"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Input CSV missing required columns: {sorted(missing)}")

    session = requests.Session()
    session.headers.update({"User-Agent": make_user_agent(args.contact)})

    records: List[ImageRecord] = []
    rejected_rows: List[Dict[str, Any]] = []
    log_rows: List[Dict[str, Any]] = []

    for row in tqdm(frame.to_dict("records"), desc="ARES Commons image search"):
        entity_id = str(row.get("entity_id", "")).strip()
        entity_name = str(row.get("entity_name", "")).strip()
        sport = str(row.get("sport", "")).strip()
        league = str(row.get("league", "")).strip()
        team = str(row.get("team", "")).strip()
        commons_title = str(row.get("commons_title", "")).strip()
        accepted = None

        if commons_title:
            try:
                candidates = get_commons_file(session, commons_title, args.thumb_width, args.sleep_seconds)
                candidate, rejected = choose_candidate(candidates)
                for rejected_candidate in rejected:
                    rejected_candidate.update({"entity_id": entity_id, "entity_name": entity_name, "sport": sport, "league": league, "team": team, "query": f"exact:{normalize_commons_title(commons_title)}"})
                rejected_rows.extend(rejected)
                if candidate:
                    accepted = candidate
                    accepted["query"] = f"exact:{normalize_commons_title(commons_title)}"
            except Exception as exc:
                log_rows.append({"entity_id": entity_id, "entity_name": entity_name, "status": "exact_file_error", "query": f"exact:{commons_title}", "error": str(exc)})

        if not accepted and args.exact_only:
            records.append(pending_record(entity_id, entity_name, sport, league, team, args.date_checked))
            continue

        for query in ([] if accepted else build_queries(entity_name, sport, league, team)):
            try:
                candidates = search_commons(session, query, args.max_results, args.thumb_width, args.sleep_seconds)
                candidate, rejected = choose_candidate(candidates)
                for rejected_candidate in rejected:
                    rejected_candidate.update({"entity_id": entity_id, "entity_name": entity_name, "sport": sport, "league": league, "team": team, "query": query})
                rejected_rows.extend(rejected)
                if candidate:
                    accepted = candidate
                    accepted["query"] = query
                    break
            except Exception as exc:
                log_rows.append({"entity_id": entity_id, "entity_name": entity_name, "status": "search_error", "query": query, "error": str(exc)})

        if not accepted:
            records.append(pending_record(entity_id, entity_name, sport, league, team, args.date_checked))
            continue

        ext = extension_from_mime(accepted.get("mime", ""), accepted.get("file_url", ""))
        local_path = image_dir / f"{slugify(entity_id)}__{slugify(entity_name)}__commons{ext}"
        downloaded = False
        try:
            download_url = accepted.get("thumb_url") or accepted.get("file_url")
            downloaded = download_file(session, download_url, local_path, args.sleep_seconds)
            log_rows.append({"entity_id": entity_id, "entity_name": entity_name, "status": "downloaded", "query": accepted.get("query", ""), "commons_title": accepted.get("title", ""), "local_path": str(local_path)})
        except Exception as exc:
            log_rows.append({"entity_id": entity_id, "entity_name": entity_name, "status": "download_error", "query": accepted.get("query", ""), "commons_title": accepted.get("title", ""), "error": str(exc)})

        license_blob = f"{accepted.get('license_short', '')} {accepted.get('usage_terms', '')} {accepted.get('license_url', '')}".lower()
        share_alike = "by-sa" in license_blob or "sharealike" in license_blob or "share alike" in license_blob

        records.append(
            ImageRecord(
                entity_id=entity_id,
                entity_name=entity_name,
                sport=sport,
                league=league,
                team=team,
                image_status="wikimedia_verified",
                display_allowed=downloaded,
                downloaded=downloaded,
                local_path=str(local_path) if downloaded else "",
                commons_title=accepted.get("title", ""),
                source_url=accepted.get("fullurl", ""),
                file_url=accepted.get("file_url", ""),
                thumb_url=accepted.get("thumb_url", ""),
                mime=accepted.get("mime", ""),
                width=int(accepted.get("width") or 0),
                height=int(accepted.get("height") or 0),
                creator=accepted.get("artist", ""),
                credit=accepted.get("credit", ""),
                license_short_name=accepted.get("license_short", ""),
                license_url=accepted.get("license_url", ""),
                usage_terms=accepted.get("usage_terms", ""),
                attribution_required=("cc0" not in license_blob and "public domain" not in license_blob),
                commercial_use_allowed=True,
                paid_site_display_allowed=True,
                cropping_allowed="check_license; CC BY-SA may trigger share-alike if modified" if share_alike else "likely_allowed_but_verify",
                attribution_text=attribution_text(accepted),
                date_checked=args.date_checked,
                notes="Conservative metadata pass. Human review still recommended before using in paid marketing.",
            )
        )

    registry = pd.DataFrame([asdict(record) for record in records])
    registry.to_csv(metadata_dir / "image_rights_registry.csv", index=False, encoding="utf-8-sig")
    (metadata_dir / "image_rights_registry.json").write_text(json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rejected_rows).to_csv(metadata_dir / "rejected_candidates.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(log_rows).to_csv(metadata_dir / "download_log.csv", index=False, encoding="utf-8-sig")

    print("Done.")
    print(f"Images: {image_dir}")
    print(f"Registry CSV: {metadata_dir / 'image_rights_registry.csv'}")
    print(f"Registry JSON: {metadata_dir / 'image_rights_registry.json'}")
    print(f"Rejected candidates: {metadata_dir / 'rejected_candidates.csv'}")
    print(f"Log: {metadata_dir / 'download_log.csv'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARES Wikimedia Commons image downloader.")
    parser.add_argument("--input", required=True, help="Input CSV with entity_id, entity_name, sport, league, team.")
    parser.add_argument("--output", default="ares_commons_output", help="Output folder.")
    parser.add_argument("--contact", required=True, help="Contact email or URL for Wikimedia User-Agent.")
    parser.add_argument("--max-results", type=int, default=5, help="Max Commons candidates per query.")
    parser.add_argument("--thumb-width", type=int, default=800, help="Downloaded thumbnail width.")
    parser.add_argument("--sleep-seconds", type=float, default=1.0, help="Delay between requests.")
    parser.add_argument("--date-checked", default=time.strftime("%Y-%m-%d"), help="License check date.")
    parser.add_argument("--exact-only", action="store_true", help="Only use optional commons_title values from the input CSV; do not text-search by player name.")
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())
