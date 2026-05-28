from __future__ import annotations

import csv
import json
import math
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_ROOT = REPO_ROOT
DATA_ROOT = REPO_ROOT / "data"
LAKE_ROOT = Path(r"D:\ARES\football\data_lake")
DOWNLOADS_ROOT = Path.home() / "Downloads"
LOCAL_TZ = ZoneInfo("Asia/Taipei")

RAW_ROOT = LAKE_ROOT / "raw"
CLEAN_ROOT = LAKE_ROOT / "clean"
REGISTRY_ROOT = LAKE_ROOT / "registry"
LOG_ROOT = LAKE_ROOT / "logs"
EXPORT_ROOT = LAKE_ROOT / "exports"
DUCKDB_PATH = LAKE_ROOT / "ares_data.duckdb"


def ensure_lake_layout() -> None:
    for path in [
        RAW_ROOT / "football_data_co_uk",
        RAW_ROOT / "football_data_org",
        RAW_ROOT / "statsbomb_open",
        RAW_ROOT / "clubelo",
        RAW_ROOT / "fbref_manual",
        RAW_ROOT / "capology_manual",
        RAW_ROOT / "kaggle_transfermarkt",
        RAW_ROOT / "sportmonks",
        RAW_ROOT / "api_football",
        CLEAN_ROOT / "matches",
        CLEAN_ROOT / "teams",
        CLEAN_ROOT / "players",
        CLEAN_ROOT / "player_seasons",
        CLEAN_ROOT / "player_match_stats",
        CLEAN_ROOT / "team_match_stats",
        CLEAN_ROOT / "events",
        CLEAN_ROOT / "lineups",
        CLEAN_ROOT / "standings",
        CLEAN_ROOT / "transfers",
        CLEAN_ROOT / "market_values",
        CLEAN_ROOT / "wages",
        CLEAN_ROOT / "clubelo",
        CLEAN_ROOT / "source_registry",
        REGISTRY_ROOT,
        LOG_ROOT,
        EXPORT_ROOT,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_frame(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    if path.suffix.lower() == ".json":
        payload = read_json(path, [])
        if isinstance(payload, list):
            return pd.DataFrame(payload)
        if isinstance(payload, dict):
            return pd.DataFrame([payload])
        return pd.DataFrame()
    if path.suffix.lower() in {".csv", ".txt"}:
        return pd.read_csv(path, encoding="utf-8-sig")
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path)
    return pd.DataFrame()


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def round1(value: float) -> float:
    return round(clamp(value), 1)


def per90(value: Any, minutes: Any) -> float | None:
    v = safe_float(value)
    m = safe_float(minutes)
    if v is None or m in (None, 0):
        return None
    return round1(v * 90.0 / m)


def clean_name(value: Any) -> str:
    text = safe_text(value).lower()
    text = re.sub(r"[\u0300-\u036f]", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def season_from_date(value: Any) -> str:
    text = safe_text(value)
    if not text:
        return ""
    try:
        parsed = datetime.fromisoformat(text[:10]).date()
    except ValueError:
        return ""
    if parsed.month >= 7:
        return f"{parsed.year}-{str(parsed.year + 1)[-2:]}"
    return f"{parsed.year - 1}-{str(parsed.year)[-2:]}"


def current_season(today: date | None = None) -> str:
    current = today or date.today()
    if current.month >= 7:
        return f"{current.year}-{str(current.year + 1)[-2:]}"
    return f"{current.year - 1}-{str(current.year)[-2:]}"


def local_today() -> date:
    return datetime.now(LOCAL_TZ).date()


def local_now_iso() -> str:
    return datetime.now(LOCAL_TZ).replace(microsecond=0).isoformat()


def position_family(position: Any) -> str:
    text = safe_text(position).upper()
    if text in {"GK", "GOALKEEPER"}:
        return "GK"
    if text in {"CB", "LCB", "RCB", "DF"}:
        return "CB"
    if text in {"FB", "LB", "RB", "LWB", "RWB"}:
        return "FB/WB"
    if text in {"DM", "CDM"}:
        return "DM"
    if text in {"CM", "CMF"}:
        return "CM"
    if text in {"AM", "CAM"}:
        return "AM"
    if text in {"W", "LW", "RW", "WF"}:
        return "W"
    if text in {"CF", "ST", "FW", "SS"}:
        return "CF/ST"
    return "Utility"


def source_status(data_mode: str) -> str:
    mapping = {
        "public_beta_demo": "PUBLIC_BETA_DEMO",
        "open_match_derived": "PUBLIC_OPEN",
        "provider_data_required": "PROVIDER_REQUIRED",
        "premium_model_required": "PROVIDER_REQUIRED",
        "user_provided": "USER_PROVIDED",
        "estimated": "PUBLIC_ESTIMATE",
    }
    return mapping.get(data_mode, data_mode.upper())


def source_skip_record(source_id: str, reason: str) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "status": "source_skipped_missing_key" if "key" in reason.lower() else "source_skipped",
        "reason": reason,
        "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
