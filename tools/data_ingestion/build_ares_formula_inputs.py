from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from common import (
    DATA_ROOT,
    DOWNLOADS_ROOT,
    EXPORT_ROOT,
    CLEAN_ROOT,
    current_season,
    clean_name,
    ensure_lake_layout,
    load_frame,
    local_now_iso,
    local_today,
    per90,
    position_family,
    read_json,
    round1,
    safe_float,
    safe_int,
    safe_text,
    season_from_date,
    write_csv,
    write_json,
)


NOW_LOCAL = local_now_iso()
TODAY = local_today().isoformat()


def _scale(value: float | None, factor: float = 1.0, cap: float = 100.0) -> float | None:
    if value is None:
        return None
    return round1(min(cap, max(0.0, value * factor)))


def _bucket_age(age: int | None) -> float:
    if age is None:
        return 55.0
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


def _league_context(level: Any, confederation: Any) -> float:
    level_text = safe_text(level).lower()
    conf_text = safe_text(confederation).upper()
    base = {
        "top": 88.0,
        "second": 74.0,
        "third": 62.0,
        "fourth": 56.0,
    }.get(level_text, 68.0)
    if conf_text in {"UEFA", "CONMEBOL"}:
        base += 2.0
    return round1(base)


def _role_usage(start_rate: float | None, minutes: int | None) -> float:
    start = start_rate if start_rate is not None else 0.0
    volume = min(100.0, (minutes or 0) / 30.0)
    return round1(start * 0.65 + volume * 0.35)


def _component_scores(row: dict[str, Any]) -> dict[str, float | None]:
    minutes = safe_int(row.get("minutes"))
    appearances = safe_int(row.get("appearances"))
    starts = safe_int(row.get("starts"))
    age = safe_int(row.get("age"))
    goals90 = per90(row.get("goals"), minutes)
    assists90 = per90(row.get("assists"), minutes)
    prog90 = per90(row.get("progressive_actions"), minutes)
    def90 = per90(row.get("defensive_actions"), minutes)
    goal_contrib90 = per90((safe_float(row.get("goals"), 0) or 0) + (safe_float(row.get("assists"), 0) or 0), minutes)
    start_rate = None if not appearances else round1((starts or 0) / appearances * 100.0)
    availability = safe_float(row.get("availability_pct"))
    fam = position_family(row.get("position"))

    attack = round1(min(100.0, (goals90 or 0) * 18 + (assists90 or 0) * 12 + (prog90 or 0) * 5))
    creation = round1(min(100.0, (assists90 or 0) * 18 + (prog90 or 0) * 7 + (goal_contrib90 or 0) * 8))
    defense = round1(min(100.0, (def90 or 0) * 7 + (availability or 0) * 0.4))
    if fam in {"CB", "FB/WB"}:
        performance = round1(attack * 0.14 + creation * 0.14 + defense * 0.42 + _role_usage(start_rate, minutes) * 0.30)
    elif fam in {"DM", "CM"}:
        performance = round1(attack * 0.18 + creation * 0.24 + defense * 0.24 + _role_usage(start_rate, minutes) * 0.34)
    elif fam in {"AM", "W", "CF/ST"}:
        performance = round1(attack * 0.34 + creation * 0.28 + defense * 0.10 + _role_usage(start_rate, minutes) * 0.28)
    else:
        performance = round1(attack * 0.22 + creation * 0.22 + defense * 0.22 + _role_usage(start_rate, minutes) * 0.34)

    efficiency = round1(min(100.0, (goal_contrib90 or 0) * 14 + (start_rate or 0) * 0.25))
    role_usage = _role_usage(start_rate, minutes)
    volume = round1(min(100.0, (minutes or 0) / 30.0))
    durability = round1(availability if availability is not None else 65.0)
    trend_value = safe_float(row.get("trend_value"), 0.0) or 0.0
    trend = round1(max(0.0, min(100.0, 50.0 + trend_value * 10.0)))
    age_upside = _bucket_age(age)
    position_value = {
        "GK": 72.0,
        "CB": 74.0,
        "FB/WB": 76.0,
        "DM": 78.0,
        "CM": 80.0,
        "AM": 83.0,
        "W": 86.0,
        "CF/ST": 88.0,
        "Utility": 75.0,
    }.get(fam, 75.0)
    league_context = _league_context(row.get("league_level"), row.get("confederation"))
    market_signal = round1(min(100.0, (safe_float(row.get("market_score"), 70.0) or 70.0) * 0.65 + trend * 0.35))
    movement_value = round1(max(0.0, min(100.0, 50.0 + trend_value * 14.0)))

    public_ares_formula_score = round1(
        performance * 0.30
        + efficiency * 0.20
        + role_usage * 0.15
        + volume * 0.12
        + durability * 0.10
        + trend * 0.05
        + age_upside * 0.04
        + league_context * 0.04
    )
    public_market_formula_score = round1(
        public_ares_formula_score * 0.25
        + age_upside * 0.20
        + position_value * 0.15
        + league_context * 0.15
        + market_signal * 0.10
        + movement_value * 0.05
        + durability * 0.10
    )
    return {
        "goals_per90": goals90,
        "assists_per90": assists90,
        "progressive_actions_per90": prog90,
        "defensive_actions_per90": def90,
        "goal_contrib_per90": goal_contrib90,
        "start_rate": start_rate,
        "availability_rate": availability,
        "attack_component": attack,
        "creation_component": creation,
        "defense_component": defense,
        "performance_component": performance,
        "efficiency_component": efficiency,
        "role_usage_component": role_usage,
        "volume_component": volume,
        "durability_component": durability,
        "trend_component": trend,
        "age_upside_component": age_upside,
        "position_value_component": position_value,
        "league_context_component": league_context,
        "market_signal_component": market_signal,
        "movement_value_component": movement_value,
        "public_ares_formula_score": public_ares_formula_score,
        "public_market_formula_score": public_market_formula_score,
        "ares_score_delta": round1((safe_float(row.get("ares_score"), 0.0) or 0.0) - public_ares_formula_score),
        "market_score_delta": round1((safe_float(row.get("market_score"), 0.0) or 0.0) - public_market_formula_score),
    }


def build_public_player_formula_inputs(players: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in players:
        comp = _component_scores(row)
        minutes = safe_int(row.get("minutes"))
        season = row.get("season") or season_from_date(row.get("last_updated")) or current_season()
        base = {
            "source_id": row.get("data_mode", "public_beta_demo"),
            "player_id": row.get("player_id"),
            "player_name": row.get("player_name"),
            "player_name_clean": clean_name(row.get("player_name")),
            "club": row.get("club"),
            "club_id": row.get("club_id"),
            "league": row.get("league"),
            "league_id": row.get("league_id"),
            "season": season,
            "position": row.get("position"),
            "age": row.get("age"),
            "minutes": minutes,
            "starts": row.get("starts"),
            "appearances": row.get("appearances"),
            "goals": row.get("goals"),
            "assists": row.get("assists"),
            "non_penalty_goals": row.get("goals"),
            "shots": None,
            "shots_on_target": None,
            "xg": None,
            "npxg": None,
            "xa": None,
            "key_passes": None,
            "progressive_passes": row.get("progressive_actions"),
            "progressive_carries": row.get("progressive_actions"),
            "tackles": None,
            "interceptions": None,
            "blocks": None,
            "clearances": None,
            "aerials_won": None,
            "aerials_lost": None,
            "yellow_cards": None,
            "red_cards": None,
            "market_value": None,
            "estimated_wage": None,
            "country": row.get("country"),
            "continent": row.get("continent"),
            "confederation": row.get("confederation"),
            "league_level": row.get("league_level"),
            "role": row.get("role"),
            "role_security": row.get("role_security"),
            "durability": row.get("durability"),
            "trend": row.get("trend"),
            "trend_value": row.get("trend_value"),
            "contract_end": row.get("contract_end"),
            "age_curve": row.get("age_curve"),
            "data_confidence": row.get("data_confidence"),
            "confidence": row.get("confidence"),
            "last_updated": row.get("last_updated"),
            "source": row.get("source"),
            "score_source": row.get("score_source"),
            "ares_score": row.get("ares_score"),
            "ares_tier": row.get("ares_tier"),
            "market_score": row.get("market_score"),
            "market_tier": row.get("market_tier"),
            "transfer_value_signal": row.get("transfer_value_signal"),
            "minutes_role": row.get("minutes_role"),
            "position_usage": row.get("position_usage"),
            "foot": row.get("foot"),
            "height_cm": row.get("height_cm"),
            "source_url": row.get("url"),
            "player_url": row.get("player_url"),
            "club_url": row.get("club_url"),
            "league_url": row.get("league_url"),
            "photo_url": row.get("photo_url"),
            "photo_source": row.get("photo_source"),
            "photo_license_status": row.get("photo_license_status"),
            "photo_status": row.get("photo_status"),
            "image_confidence": row.get("image_confidence"),
            "identity_mode": row.get("identity_mode"),
            "identity_source": row.get("identity_source"),
            "identity_source_url": row.get("identity_source_url"),
            "identity_checked": row.get("identity_checked"),
            "wikidata_qid": row.get("wikidata_qid"),
            "commons_title": row.get("commons_title"),
            "license_short_name": row.get("license_short_name"),
            "license_url": row.get("license_url"),
            "rights_checked": row.get("rights_checked"),
            "slug": row.get("slug"),
            "data_status": row.get("data_mode", "PUBLIC_BETA_DEMO").upper(),
            "fetched_at": NOW_LOCAL,
        }
        base.update(comp)
        rows.append(base)

    df = pd.DataFrame(rows)
    if not df.empty:
        df.sort_values(by=["ares_score", "market_score", "player_name"], ascending=[False, False, True], inplace=True, na_position="last")
        df.reset_index(drop=True, inplace=True)
        df.insert(0, "rank", range(1, len(df) + 1))
    return df


def build_team_formula_inputs(team_rows: list[dict[str, Any]], league_rows: list[dict[str, Any]]) -> pd.DataFrame:
    league_frame = pd.DataFrame(league_rows)
    league_lookup = {safe_text(row.get("league_code")): row for row in league_rows}
    rows: list[dict[str, Any]] = []
    for row in team_rows:
        league = league_lookup.get(safe_text(row.get("league_code")), {})
        recent_form = safe_text(row.get("recent_form"))
        form_points = sum({"W": 3, "D": 1, "L": 0}.get(char, 0) for char in recent_form) / max(1, len(recent_form)) if recent_form else None
        row_out = {
            "source_id": "football_data_co_uk",
            "country": row.get("country"),
            "league_code": row.get("league_code"),
            "league_name": row.get("league_name"),
            "team": row.get("team"),
            "venue": row.get("venue"),
            "matches": row.get("matches"),
            "wins": row.get("wins"),
            "draws": row.get("draws"),
            "losses": row.get("losses"),
            "goals_for": row.get("goals_for"),
            "goals_against": row.get("goals_against"),
            "points": row.get("points"),
            "first_date": row.get("first_date"),
            "last_date": row.get("last_date"),
            "points_per_match": row.get("points_per_match"),
            "goal_difference_per_match": round1((safe_float(row.get("goal_difference"), 0.0) or 0.0) / max(1.0, safe_float(row.get("matches"), 1.0) or 1.0)),
            "goals_for_per_match": row.get("goals_for_per_match"),
            "goals_against_per_match": row.get("goals_against_per_match"),
            "recent_form_points": form_points,
            "home_points_per_match": row.get("points_per_match") if row.get("venue") == "home" else None,
            "away_points_per_match": row.get("points_per_match") if row.get("venue") == "away" else None,
            "home_form": recent_form if row.get("venue") == "home" else None,
            "away_form": recent_form if row.get("venue") == "away" else None,
            "data_trust": round1(100.0 if row.get("matches", 0) and row.get("last_date") else 80.0),
            "league_strength_proxy": row.get("points_per_match"),
            "goals_per_match": league.get("goals_per_match"),
            "home_win_rate": league.get("home_win_rate"),
            "draw_rate": league.get("draw_rate"),
            "away_win_rate": league.get("away_win_rate"),
            "coverage_depth": league.get("completed_matches"),
            "data_status": "PUBLIC_OPEN",
        }
        rows.append(row_out)
    return pd.DataFrame(rows)


def build_league_formula_inputs(league_rows: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in league_rows:
        rows.append(
            {
                "source_id": "football_data_co_uk",
                "competition_id": row.get("league_code"),
                "competition_name": row.get("league_name"),
                "country": row.get("country"),
                "season": current_season(),
                "completed_matches": row.get("completed_matches"),
                "teams_seen": row.get("teams_seen"),
                "goals_per_match": row.get("goals_per_match"),
                "home_win_rate": row.get("home_win_rate"),
                "draw_rate": row.get("draw_rate"),
                "away_win_rate": row.get("away_win_rate"),
                "coverage_depth": row.get("completed_matches"),
                "league_strength_proxy": row.get("goals_per_match"),
                "data_status": "PUBLIC_OPEN",
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    ensure_lake_layout()
    players = read_json(DATA_ROOT / "public_players.json", [])
    teams = read_json(DATA_ROOT / "public_clubs.json", [])
    leagues = read_json(DATA_ROOT / "public_leagues.json", [])
    team_stats = read_json(DATA_ROOT / "open_match_team_stats.json", [])
    league_stats = read_json(DATA_ROOT / "open_match_league_stats.json", [])
    matches = read_json(DATA_ROOT / "matches.json", [])
    transfers = read_json(DATA_ROOT / "public_transfers.json", [])

    player_df = build_public_player_formula_inputs(players)
    team_df = build_team_formula_inputs(team_stats, league_stats)
    league_df = build_league_formula_inputs(league_stats)

    competition_df = pd.DataFrame(
        [
            {
                "source_id": "public_beta_demo",
                "competition_id": row.get("league_id"),
                "competition_name": row.get("league_name"),
                "country": row.get("country"),
                "country_code": safe_text(row.get("country"))[:3].upper() if row.get("country") else "",
                "league_code": safe_text(row.get("league_id")),
                "season": current_season(),
                "tier": row.get("tier"),
                "gender": row.get("gender", ""),
                "source_competition_id": row.get("league_id"),
                "first_seen": row.get("last_updated"),
                "last_seen": row.get("last_updated"),
                "data_status": row.get("data_mode", "PUBLIC_BETA_DEMO").upper(),
            }
            for row in leagues
        ]
    )
    team_catalog = pd.DataFrame(
        [
            {
                "source_id": "public_beta_demo",
                "team_id": row.get("club_id"),
                "team_name": row.get("club_name"),
                "team_name_clean": clean_name(row.get("club_name")),
                "country": row.get("country"),
                "competition_id": row.get("league_id"),
                "season": current_season(),
                "source_team_id": row.get("club_id"),
                "clubelo_id": "",
                "transfermarkt_id": "",
                "fbref_id": "",
                "sportmonks_id": "",
                "api_football_id": "",
                "data_status": row.get("data_mode", "PUBLIC_BETA_DEMO").upper(),
            }
            for row in teams
        ]
    )
    player_catalog = pd.DataFrame(
        [
            {
                "source_id": row.get("data_mode", "public_beta_demo"),
                "player_id": row.get("player_id"),
                "player_name": row.get("player_name"),
                "player_name_clean": clean_name(row.get("player_name")),
                "birth_date": row.get("date_of_birth"),
                "age": row.get("age"),
                "nationality": row.get("nationality") or row.get("country"),
                "primary_position": row.get("position"),
                "secondary_positions": row.get("position_usage"),
                "foot": row.get("foot"),
                "height_cm": row.get("height_cm"),
                "current_team_id": row.get("club_id"),
                "source_player_id": row.get("player_id"),
                "transfermarkt_id": "",
                "fbref_id": "",
                "sportmonks_id": "",
                "api_football_id": "",
                "data_status": row.get("data_mode", "PUBLIC_BETA_DEMO").upper(),
            }
            for row in players
        ]
    )
    match_df = pd.DataFrame(
        [
            {
                "source_id": "football_data_co_uk",
                "match_id": row.get("match_id"),
                "competition_id": row.get("league_code"),
                "season": row.get("source_season") or current_season(),
                "date": row.get("date"),
                "time": row.get("time"),
                "home_team_id": clean_name(row.get("home_team")),
                "away_team_id": clean_name(row.get("away_team")),
                "home_team_name": row.get("home_team"),
                "away_team_name": row.get("away_team"),
                "home_goals": row.get("full_time_home_goals"),
                "away_goals": row.get("full_time_away_goals"),
                "result": row.get("full_time_result"),
                "venue": "",
                "round": "",
                "status": "finished" if not row.get("is_placeholder") else "placeholder",
                "source_match_id": row.get("match_id"),
                "source_url": row.get("source_url"),
                "data_status": "PUBLIC_OPEN" if not row.get("is_placeholder") else "PUBLIC_BETA_DEMO",
                "fetched_at": NOW_LOCAL,
            }
            for row in matches
        ]
    )
    team_match_df = pd.DataFrame(
        [
            {
                "source_id": "football_data_co_uk",
                "match_id": f"{row.get('league_code')}_{row.get('team')}_{row.get('venue')}_{row.get('first_date')}",
                "team_id": clean_name(row.get("team")),
                "opponent_team_id": "",
                "is_home": row.get("venue") == "home",
                "goals_for": row.get("goals_for"),
                "goals_against": row.get("goals_against"),
                "shots": None,
                "shots_on_target": None,
                "corners": None,
                "fouls": None,
                "cards_yellow": None,
                "cards_red": None,
                "xg_for": None,
                "xg_against": None,
                "possession": None,
                "passes": None,
                "passes_completed": None,
                "data_status": "PUBLIC_OPEN",
            }
            for row in team_stats
        ]
    )
    transfer_df = pd.DataFrame(
        [
            {
                "source_id": row.get("data_mode", "public_beta_demo"),
                "player_id": row.get("player_id"),
                "date": row.get("date"),
                "from_team_id": row.get("from_club_url") or clean_name(row.get("from_club")),
                "to_team_id": row.get("to_club_url") or clean_name(row.get("to_club")),
                "fee": None,
                "currency": "",
                "loan": str(row.get("transfer_type", "")).lower().find("loan") >= 0,
                "contract_until": None,
                "data_status": row.get("data_mode", "PUBLIC_BETA_DEMO").upper(),
                "license_status": row.get("photo_license_status", ""),
            }
            for row in transfers
        ]
    )
    market_value_df = player_df[
        ["source_id", "player_id", "club_id"]
    ].rename(columns={"club_id": "team_id"}).copy()
    market_value_df["date"] = TODAY
    market_value_df["market_value"] = pd.NA
    market_value_df["currency"] = ""
    market_value_df["source_market_value_id"] = market_value_df["player_id"]
    market_value_df["data_status"] = player_df["data_status"]
    market_value_df["license_status"] = player_df["data_status"]

    wages_df = market_value_df.copy()
    wages_df["season"] = current_season()
    wages_df["annual_wage"] = pd.NA
    wages_df["weekly_wage"] = pd.NA
    wages_df["estimated_band"] = ""
    wages_df["verified"] = False
    wages_df["source_url"] = ""

    exports = {
        "ares_public_player_formula_inputs.parquet": player_df,
        "ares_team_formula_inputs.parquet": team_df,
        "ares_league_formula_inputs.parquet": league_df,
        "ares_competitions.parquet": competition_df,
        "ares_teams.parquet": team_catalog,
        "ares_players.parquet": player_catalog,
        "ares_matches.parquet": match_df,
        "ares_team_match_stats.parquet": team_match_df,
        "ares_transfers.parquet": transfer_df,
        "ares_market_values.parquet": market_value_df,
        "ares_wages.parquet": wages_df,
    }
    for filename, frame in exports.items():
        path = EXPORT_ROOT / filename
        frame.to_parquet(path, index=False)

    clean_targets = {
        CLEAN_ROOT / "players" / "public_players_formula_inputs.parquet": player_df,
        CLEAN_ROOT / "matches" / "football_data_co_uk_matches.parquet": match_df,
        CLEAN_ROOT / "team_match_stats" / "football_data_co_uk_team_match_stats.parquet": team_match_df,
        CLEAN_ROOT / "standings" / "football_data_co_uk_team_season_rollups.parquet": team_df.groupby(["country", "league_code", "league_name", "team"], as_index=False).agg(
            matches=("matches", "max"),
            wins=("wins", "sum"),
            draws=("draws", "sum"),
            losses=("losses", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            points=("points", "sum"),
            first_date=("first_date", "min"),
            last_date=("last_date", "max"),
        ),
    }
    for path, frame in clean_targets.items():
        frame.to_parquet(path, index=False)

    csv_path = DOWNLOADS_ROOT / f"ares_player_metrics_{TODAY}.csv"
    csv_frame = player_df.copy()
    csv_frame.to_csv(csv_path, index=False, encoding="utf-8-sig")

    write_json(
        EXPORT_ROOT / "ares_player_formula_inputs_meta.json",
        {
            "generated_at_local": NOW_LOCAL,
            "rows": len(player_df),
            "columns": list(player_df.columns),
            "source": "data/public_players.json",
            "formula_status": "public_beta_demo_and_calculated_component_proxies",
            "downloads_csv": str(csv_path),
        },
    )
    print(f"Wrote formula inputs to {EXPORT_ROOT}")
    print(f"Wrote latest player CSV to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
