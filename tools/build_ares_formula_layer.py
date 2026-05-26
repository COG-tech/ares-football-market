#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from datetime import date, datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TODAY = date.today().isoformat()
NOW_UTC = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return default
        return out
    except (TypeError, ValueError):
        return default


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def round_score(value: float) -> float:
    return round(clamp(value), 1)


def normalize_high(value: Any, population: list[Any]) -> float | None:
    val = safe_float(value)
    vals = sorted(safe_float(item) for item in population if safe_float(item) is not None)
    if val is None or not vals:
        return None
    if len(vals) == 1 or vals[0] == vals[-1]:
        return 50.0
    return round_score((val - vals[0]) / (vals[-1] - vals[0]) * 100)


def normalize_low(value: Any, population: list[Any]) -> float | None:
    score = normalize_high(value, population)
    return None if score is None else round_score(100 - score)


def score_label(score: float | None) -> str:
    if score is None:
        return "Unavailable"
    if score >= 95:
        return "Elite"
    if score >= 90:
        return "Excellent"
    if score >= 80:
        return "Strong"
    if score >= 70:
        return "Solid"
    if score >= 60:
        return "Average"
    if score >= 50:
        return "Weak"
    return "Poor"


def data_status_label(data_mode: str) -> str:
    labels = {
        "open_match_derived": "calculated from current open match data",
        "public_beta_demo": "seeded public beta demo row",
        "premium_model_required": "requires deeper premium model data",
        "provider_data_required": "requires licensed player event or tracking data",
    }
    return labels.get(data_mode, data_mode)


def form_points(form: Any) -> float | None:
    text = str(form or "").upper()
    if not text:
        return None
    points = sum({"W": 3, "D": 1, "L": 0}.get(char, 0) for char in text)
    return points / (len(text) * 3) * 100 if text else None


def form_stability(form: Any) -> float | None:
    text = str(form or "").upper()
    if not text:
        return None
    losses = text.count("L")
    return round_score((len(text) - losses) / len(text) * 100)


def weighted_score(components: list[dict[str, Any]]) -> tuple[float | None, list[dict[str, Any]], list[str]]:
    available_weight = 0.0
    weighted_total = 0.0
    missing = []
    out = []
    for component in components:
        value = safe_float(component.get("score"))
        weight = float(component.get("weight", 0))
        item = dict(component)
        if value is None:
            missing.append(str(component["name"]))
            item["score"] = None
        else:
            available_weight += weight
            weighted_total += value * weight
            item["score"] = round_score(value)
        out.append(item)
    if available_weight <= 0:
        return None, out, missing
    return round_score(weighted_total / available_weight), out, missing


def confidence_score(required_fields: list[str], missing_fields: list[str], sample: Any, last_date: str = "") -> tuple[float, str]:
    score = 100.0
    if required_fields:
        score -= (len(missing_fields) / len(required_fields)) * 35.0
    sample_value = safe_float(sample, 0) or 0
    if sample_value < 10:
        score -= 25
    elif sample_value < 30:
        score -= 15
    elif sample_value < 100:
        score -= 7
    if last_date:
        try:
            days_old = (date.today() - datetime.strptime(last_date, "%Y-%m-%d").date()).days
            if days_old > 730:
                score -= 25
            elif days_old > 365:
                score -= 15
            elif days_old > 180:
                score -= 8
        except ValueError:
            score -= 10
    final = round_score(score)
    if final >= 80:
        return final, "High"
    if final >= 60:
        return final, "Medium"
    return final, "Low"


def formula_output(
    formula_id: str,
    formula_name: str,
    score: float | None,
    components: list[dict[str, Any]],
    required_fields: list[str],
    missing_fields: list[str],
    confidence: tuple[float, str],
    explanation: str,
    data_mode: str = "open_match_derived",
    premium_locked: bool = False,
) -> dict[str, Any]:
    return {
        "formula_id": formula_id,
        "formula_name": formula_name,
        "score": score,
        "label": score_label(score),
        "short_explanation": explanation,
        "data_status": data_status_label(data_mode),
        "data_mode": data_mode,
        "confidence": {"score": confidence[0], "label": confidence[1]},
        "components": components,
        "required_fields": required_fields,
        "missing_fields": missing_fields,
        "premium_locked": premium_locked,
    }


LIVE_FORMULAS = [
    ("ares_power_core", "ARES Power Core", "team", False, "Measures real club strength, not brand reputation."),
    ("ares_strike_force", "ARES Strike Force", "team", False, "Measures team attacking force."),
    ("ares_shield_index", "ARES Shield Index", "team", False, "Measures defensive control."),
    ("ares_balance_index", "ARES Balance Index", "team", False, "Identifies complete teams."),
    ("ares_form_pulse", "ARES Form Pulse", "team", False, "Detects current momentum."),
    ("ares_home_fortress", "ARES Home Fortress", "team", False, "Shows home dominance."),
    ("ares_road_threat", "ARES Road Threat", "team", False, "Shows away strength."),
    ("ares_venue_split_edge", "ARES Venue Split Edge", "team", False, "Shows home reliance or road capability."),
    ("ares_attack_defense_gap", "ARES Attack Defense Gap", "team", False, "Shows attacking or defensive imbalance."),
    ("ares_warning_zone_flag", "ARES Warning Zone Flag", "team", False, "Highlights risk."),
    ("ares_fragile_contender_flag", "ARES Fragile Contender Flag", "team", False, "Identifies high-result teams with weak structure."),
    ("ares_rising_club_flag", "ARES Rising Club Flag", "team", False, "Finds clubs moving upward using form as the live proxy."),
    ("ares_underrated_club_flag", "ARES Underrated Club Flag", "team", False, "Finds clubs stronger than public reputation where data supports it."),
    ("ares_league_gravity", "ARES League Gravity", "league", False, "Measures competitive weight of a league."),
    ("ares_chaos_index", "ARES Chaos Index", "league", False, "Identifies volatile leagues."),
    ("ares_goal_climate", "ARES Goal Climate", "league", False, "Explains whether scoring is inflated or suppressed."),
    ("ares_home_field_gravity", "ARES Home-Field Gravity", "league", False, "Measures home advantage."),
    ("ares_draw_density", "ARES Draw Density", "league", False, "Identifies compressed leagues."),
    ("ares_data_trust_index", "ARES Data Trust Index", "league", False, "Shows reliability of the score inputs."),
    ("ares_coverage_depth", "ARES Coverage Depth", "league", False, "Shows data sample size."),
    ("ares_competitive_balance", "ARES Competitive Balance", "league", False, "Shows whether a league is dominated or deep."),
]


CORE_FORMULAS = [
    "ARES Player Score", "ARES Market Score", "ARES Confidence Score", "Confidence Adjusted Output",
    "League Adjusted Component", "Minutes Adjusted Component", "Age Adjusted Market Component",
    "Team ARES Score", "Team Market Score", "League Strength",
]

POSITION_FORMULAS = [
    "GK ARES", "CB ARES", "FB/WB ARES", "DM ARES", "CM ARES", "AM ARES", "W ARES", "CF/ST ARES", "SS ARES",
]

SIGNATURE_LENSES = [
    "Shot Denial Index", "Box Command Index", "Sweeper Radius", "Build-Up GK Value", "Error Immunity", "Pressure Distribution Score",
    "Backline Firewall", "Duel Authority", "Aerial Command", "Line-Break Value", "Space Control", "Recovery Range", "Set-Piece Gravity",
    "Corridor Control", "Wide Security", "Progression Engine", "Overlap Value", "Underlap Value", "Recovery Shield", "Final-Third Delivery", "Inverted Build Value",
    "Zone Eraser", "Counterattack Kill Rate", "Possession Insurance", "Pivot Control", "Press Escape Value", "Central Shield", "Passing Lane Denial",
    "Tempo Engine", "Two-Way Influence", "Territory Gain", "Sequence Control", "Press Resistance", "Late Arrival Threat",
    "Unlock Index", "Half-Space Command", "Final-Third Gravity", "Chance Quality Creation", "Carry to Damage", "Pressure Survival",
    "Isolation Threat", "Carry Gravity", "Cutback Damage", "Weak-Side Danger", "Goal Threat", "Defensive Buy-In",
    "Box Gravity", "Shot Value Index", "Finishing Edge", "Center Back Occupation", "Run Timing Value", "Link Value", "Press Trigger Value", "Aerial Pin Value",
    "Between-Lines Damage", "Shadow Run Value", "Hybrid Threat", "Combination Value", "Late Box Entry", "Press Trap Value",
]

ROLE_FIT_FORMULAS = [
    "ARES Role Fit", "Target Man Fit", "Poacher Fit", "False Nine Fit", "Isolation Winger Fit", "Inside Forward Fit",
    "Touchline Winger Fit", "Inverted Fullback Fit", "Overlapping Fullback Fit", "Ball-Winning Midfielder Fit",
    "Deep-Lying Playmaker Fit", "Box-to-Box Midfielder Fit", "Ball-Playing Center Back Fit", "Stopper Center Back Fit", "Sweeper Keeper Fit",
]

MARKET_FORMULAS = [
    "ARES Scarcity Signal", "ARES Transfer Value Signal", "ARES Breakout Signal", "ARES Fall Risk Signal",
    "ARES Role Security Score", "ARES Demand Heat", "ARES Contract Mobility", "ARES Asset Risk Score",
    "ARES Comparable Player Index", "ARES Movement History Score",
]

CLUB_LEAGUE_PREMIUM = [
    "ARES Team Market Edge", "ARES Squad Architecture", "ARES U23 Asset Engine", "ARES Contract Control Score",
    "ARES Injury Load Risk", "ARES Club Strategy Grade", "ARES Translation Risk", "ARES Export Signal",
    "ARES Premium Intelligence Lock",
]


def slug(name: str) -> str:
    return name.lower().replace("/", "_").replace("-", "_").replace(" ", "_").replace("__", "_")


def registry_entry(formula_id: str, name: str, category: str, status: str, premium: bool, importance: str, data_mode: str) -> dict[str, Any]:
    return {
        "formula_id": formula_id,
        "formula_name": name,
        "category": category,
        "status": status,
        "premium_locked": premium,
        "score_scale": "0-100",
        "importance": importance,
        "website_copy": f"{name} is an ARES intelligence lens for {category.replace('_', ' ')} evaluation.",
        "required_fields": [],
        "optional_fields": [],
        "components": [],
        "calculation_notes": "Components are normalized to 0-100 before weighting. Missing fields reduce confidence.",
        "data_mode": data_mode,
    }


def build_registry() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    registry = [registry_entry(fid, name, category, "live_now", premium, importance, "open_match_derived") for fid, name, category, premium, importance in LIVE_FORMULAS]
    player_registry = []
    premium_registry = []
    for name in CORE_FORMULAS:
        mode = "premium_model_required" if name not in {"ARES Confidence Score", "Confidence Adjusted Output", "League Adjusted Component"} else "open_match_derived"
        entry = registry_entry(slug(name), name, "core", "registered", mode != "open_match_derived", "Official ARES core formula.", mode)
        registry.append(entry)
        if entry["premium_locked"]:
            premium_registry.append(entry)
    for name in POSITION_FORMULAS:
        entry = registry_entry(slug(name), name, "player_position", "registered", True, "Official position-specific player score.", "provider_data_required")
        registry.append(entry)
        player_registry.append(entry)
        premium_registry.append(entry)
    for name in SIGNATURE_LENSES:
        entry = registry_entry(slug(name), name, "signature_position_lens", "registered", True, "Premium position component lens.", "provider_data_required")
        registry.append(entry)
        player_registry.append(entry)
        premium_registry.append(entry)
    for name in ROLE_FIT_FORMULAS:
        entry = registry_entry(slug(name), name, "role_fit", "registered", True, "Premium role-fit formula.", "provider_data_required")
        registry.append(entry)
        player_registry.append(entry)
        premium_registry.append(entry)
    for name in MARKET_FORMULAS:
        entry = registry_entry(slug(name), name, "market_transfer", "registered", True, "Premium football asset and transfer intelligence formula.", "premium_model_required")
        registry.append(entry)
        premium_registry.append(entry)
    for name in CLUB_LEAGUE_PREMIUM:
        entry = registry_entry(slug(name), name, "club_league_premium", "registered", True, "Premium club or league intelligence formula.", "premium_model_required")
        registry.append(entry)
        premium_registry.append(entry)
    return registry, player_registry, premium_registry


def group_values(rows: list[dict[str, Any]], key_fields: tuple[str, ...], value_field: str) -> dict[tuple[Any, ...], list[Any]]:
    grouped: dict[tuple[Any, ...], list[Any]] = {}
    for row in rows:
        key = tuple(row.get(field) for field in key_fields)
        grouped.setdefault(key, []).append(row.get(value_field))
    return grouped


def league_context_score(league_code: str, league_stats: dict[str, dict[str, Any]]) -> float:
    league = league_stats.get(league_code, {})
    depth = safe_float(league.get("completed_matches"), 0) or 0
    teams = safe_float(league.get("teams_seen"), 0) or 0
    return round_score(min(100, depth / 80) * 0.6 + min(100, teams * 2.5) * 0.4)


def build_team_outputs(team_rows: list[dict[str, Any]], league_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    league_stats = {row["league_code"]: row for row in league_rows}
    values = {
        "ppm": group_values(team_rows, ("league_code", "venue"), "points_per_match"),
        "gd": group_values(team_rows, ("league_code", "venue"), "goal_difference"),
        "gf": group_values(team_rows, ("league_code", "venue"), "goals_for_per_match"),
        "ga": group_values(team_rows, ("league_code", "venue"), "goals_against_per_match"),
    }
    outputs = []
    by_team: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    for row in team_rows:
        key = (row["league_code"], row["venue"])
        ppm = normalize_high(row.get("points_per_match"), values["ppm"][key])
        gd = normalize_high(row.get("goal_difference"), values["gd"][key])
        gf = normalize_high(row.get("goals_for_per_match"), values["gf"][key])
        ga_control = normalize_low(row.get("goals_against_per_match"), values["ga"][key])
        form = form_points(row.get("recent_form"))
        stable = form_stability(row.get("recent_form"))
        league_context = league_context_score(row["league_code"], league_stats)
        required = ["points_per_match", "goal_difference", "goals_for_per_match", "goals_against_per_match", "recent_form", "league_code"]
        missing_base = [field for field in required if row.get(field) in ("", None)]
        confidence = confidence_score(required, missing_base, row.get("matches"), row.get("last_date", ""))

        formulas = {}
        specs = {
            "ares_power_core": ("ARES Power Core", [(ppm, 0.30, "Results Strength"), (gd, 0.25, "Goal Difference Strength"), (gf, 0.15, "Attack Output"), (ga_control, 0.15, "Defensive Control"), (league_context, 0.10, "League Context"), (form, 0.05, "Recent Form")], "Real club strength using results, goal difference, attack, defense, league context, and recent form."),
            "ares_strike_force": ("ARES Strike Force", [(gf, 0.45, "Goals For Per Match"), (max(gd or 0, 0), 0.25, "Goal Difference Attack Component"), (form, 0.20, "Recent Attacking Form"), (normalize_high(league_stats.get(row["league_code"], {}).get("goals_per_match"), [item.get("goals_per_match") for item in league_rows]), 0.10, "League Goal Environment")], "Attacking pressure relative to the league environment."),
            "ares_shield_index": ("ARES Shield Index", [(ga_control, 0.45, "Goals Against Control"), (max(gd or 0, 0), 0.25, "Goal Difference Protection"), (form, 0.20, "Recent Defensive Form"), (normalize_low(league_stats.get(row["league_code"], {}).get("goals_per_match"), [item.get("goals_per_match") for item in league_rows]), 0.10, "League Goal Environment")], "Defensive control relative to league scoring conditions."),
            "ares_balance_index": ("ARES Balance Index", [(gf, 0.35, "Attack Output"), (ga_control, 0.35, "Defensive Control"), (gd, 0.20, "Goal Difference Strength"), (stable, 0.10, "Form Stability")], "Shows whether a club is strong on both sides of the match."),
            "ares_form_pulse": ("ARES Form Pulse", [(form, 0.60, "Recent Form Points"), (stable, 0.25, "Recent Form Stability"), (ppm, 0.15, "Season Strength Context")], "Short-term movement before the league table fully reflects it."),
        }
        if row["venue"] == "home":
            specs["ares_home_fortress"] = ("ARES Home Fortress", [(ppm, 0.45, "Home Points Per Match"), (gd, 0.25, "Home Goal Difference"), (gf, 0.15, "Home Attack"), (ga_control, 0.15, "Home Defense")], "How difficult a club is to beat at home.")
        if row["venue"] == "away":
            specs["ares_road_threat"] = ("ARES Road Threat", [(ppm, 0.45, "Away Points Per Match"), (gd, 0.25, "Away Goal Difference"), (gf, 0.15, "Away Attack"), (ga_control, 0.15, "Away Defense")], "Whether a club carries its strength away from home.")

        for formula_id, (name, raw_components, explanation) in specs.items():
            comps = [{"name": cname, "weight": weight, "score": score} for score, weight, cname in raw_components]
            score, comps, missing = weighted_score(comps)
            formulas[formula_id] = formula_output(formula_id, name, score, comps, required, missing_base + missing, confidence, explanation)

        strike = formulas["ares_strike_force"]["score"]
        shield = formulas["ares_shield_index"]["score"]
        balance = formulas["ares_balance_index"]["score"]
        pulse = formulas["ares_form_pulse"]["score"]
        formulas["ares_attack_defense_gap"] = formula_output(
            "ares_attack_defense_gap",
            "ARES Attack Defense Gap",
            None if strike is None or shield is None else round(strike - shield, 1),
            [],
            ["ARES_STRIKE_FORCE", "ARES_SHIELD_INDEX"],
            [],
            confidence,
            "Positive means attack-heavy; negative means defense-heavy.",
        )
        warning_score = max(0, 100 - min([v for v in [pulse, shield, confidence[0]] if v is not None], default=100))
        formulas["ares_warning_zone_flag"] = formula_output("ares_warning_zone_flag", "ARES Warning Zone Flag", round_score(warning_score), [], ["Form Pulse", "Shield Index", "Data Trust"], [], confidence, "Highlights form, defensive, venue, or data risk.")
        fragile = 100 if (ppm or 0) >= 75 and ((balance or 100) < 55 or (shield or 100) < 55 or confidence[0] < 60) else 0
        formulas["ares_fragile_contender_flag"] = formula_output("ares_fragile_contender_flag", "ARES Fragile Contender Flag", fragile, [], ["Results Strength", "Balance Index", "Shield Index", "Data Trust"], [], confidence, "Flags high-result teams with weak structure.")
        rising = round_score((pulse or 0) * 0.70 + max(strike or 0, shield or 0) * 0.30)
        formulas["ares_rising_club_flag"] = formula_output("ares_rising_club_flag", "ARES Rising Club Flag", rising, [], ["Form Pulse", "Strike Force", "Shield Index"], [], confidence, "Uses Form Pulse as the live rising-club proxy.")
        underrated = round_score((formulas["ares_power_core"]["score"] or 0) * 0.60 + confidence[0] * 0.20 + league_context * 0.20)
        formulas["ares_underrated_club_flag"] = formula_output("ares_underrated_club_flag", "ARES Underrated Club Flag", underrated, [], ["Power Core", "Data Trust", "League Gravity"], ["brand_tier"], confidence, "Public beta flag for clubs whose football signal may exceed brand reputation.")

        item = {
            "country": row["country"],
            "league_code": row["league_code"],
            "league_name": row["league_name"],
            "team": row["team"],
            "venue": row["venue"],
            "data_mode": "open_match_derived",
            "data_status": data_status_label("open_match_derived"),
            "source": row.get("source", "Football-Data.co.uk open CSV"),
            "matches": row.get("matches"),
            "first_date": row.get("first_date"),
            "last_date": row.get("last_date"),
            "formulas": formulas,
        }
        outputs.append(item)
        by_team.setdefault((row["league_code"], row["team"]), {})[row["venue"]] = item

    for (league_code, team), venues in by_team.items():
        home = venues.get("home")
        away = venues.get("away")
        if not home or not away:
            continue
        hscore = home["formulas"].get("ares_home_fortress", {}).get("score")
        ascore = away["formulas"].get("ares_road_threat", {}).get("score")
        if hscore is None or ascore is None:
            continue
        split = abs(hscore - ascore)
        label = "balanced" if split <= 10 else "venue tilt" if split <= 25 else "heavy venue split"
        for item in (home, away):
            conf = item["formulas"]["ares_power_core"]["confidence"]
            item["formulas"]["ares_venue_split_edge"] = formula_output(
                "ares_venue_split_edge",
                "ARES Venue Split Edge",
                round_score(split),
                [{"name": "Home Fortress", "weight": 0.5, "score": hscore}, {"name": "Road Threat", "weight": 0.5, "score": ascore}],
                ["ARES_HOME_FORTRESS", "ARES_ROAD_THREAT"],
                [],
                (conf["score"], conf["label"]),
                f"Venue profile: {label}.",
            )
    return outputs


def build_league_outputs(league_rows: list[dict[str, Any]], team_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    team_scores_by_league: dict[str, list[float]] = {}
    team_gd_by_league: dict[str, list[float]] = {}
    for row in team_outputs:
        score = row["formulas"]["ares_power_core"]["score"]
        if score is not None:
            team_scores_by_league.setdefault(row["league_code"], []).append(score)
        gd = safe_float(row.get("formulas", {}).get("ares_power_core", {}).get("components", [{}])[1].get("score"))
        if gd is not None:
            team_gd_by_league.setdefault(row["league_code"], []).append(gd)

    goals_pop = [row.get("goals_per_match") for row in league_rows]
    match_pop = [row.get("completed_matches") for row in league_rows]
    teams_pop = [row.get("teams_seen") for row in league_rows]
    outputs = []
    for row in league_rows:
        code = row["league_code"]
        teams = team_scores_by_league.get(code, [])
        top_team = max(teams) if teams else None
        med_team = median(teams) if teams else None
        rates = [safe_float(row.get("home_win_rate"), 0) or 0, safe_float(row.get("draw_rate"), 0) or 0, safe_float(row.get("away_win_rate"), 0) or 0]
        competitiveness = round_score(100 - ((max(rates) - min(rates)) * 100))
        goal_env = normalize_high(row.get("goals_per_match"), goals_pop)
        depth = normalize_high(row.get("completed_matches"), match_pop)
        teams_seen = normalize_high(row.get("teams_seen"), teams_pop)
        conf = confidence_score(["completed_matches", "teams_seen", "goals_per_match", "home_win_rate", "draw_rate", "away_win_rate"], [], row.get("completed_matches"), row.get("last_date", ""))
        data_trust_components = [
            {"name": "Source Coverage", "weight": 0.30, "score": depth},
            {"name": "Match Depth", "weight": 0.25, "score": depth},
            {"name": "Recency", "weight": 0.20, "score": conf[0]},
            {"name": "League Completeness", "weight": 0.15, "score": teams_seen},
            {"name": "Field Completeness", "weight": 0.10, "score": 100},
        ]
        data_trust, data_trust_components, _ = weighted_score(data_trust_components)
        league_specs = {
            "ares_league_gravity": ("ARES League Gravity", [(med_team, 0.30, "Team Strength Median"), (top_team, 0.20, "Top Team Strength"), (competitiveness, 0.20, "Match Competitiveness"), (goal_env, 0.15, "Goal Environment"), (data_trust, 0.15, "Data Trust")], "Competitive weight of the league."),
            "ares_chaos_index": ("ARES Chaos Index", [(goal_env, 0.30, "Goal Environment Volatility"), (normalize_low(row.get("draw_rate"), [x.get("draw_rate") for x in league_rows]), 0.20, "Draw Rate Inversion"), (round_score(abs((safe_float(row.get("home_win_rate"), 0) or 0) - (safe_float(row.get("away_win_rate"), 0) or 0)) * 100), 0.20, "Home Away Imbalance"), (100 - competitiveness, 0.20, "Result Volatility"), (data_trust, 0.10, "Data Depth Adjustment")], "Volatility of the league environment."),
            "ares_goal_climate": ("ARES Goal Climate", [(goal_env, 1.0, "Goals Per Match")], "High or low scoring league environment."),
            "ares_home_field_gravity": ("ARES Home-Field Gravity", [(normalize_high(row.get("home_win_rate"), [x.get("home_win_rate") for x in league_rows]), 0.70, "Home Win Rate"), (round_score((safe_float(row.get("home_goals"), 0) or 0) / max(safe_float(row.get("goals"), 1) or 1, 1) * 100), 0.30, "Home Goal Share")], "Strength of home advantage."),
            "ares_draw_density": ("ARES Draw Density", [(normalize_high(row.get("draw_rate"), [x.get("draw_rate") for x in league_rows]), 1.0, "Draw Rate")], "How often the league compresses matches into draws."),
            "ares_data_trust_index": ("ARES Data Trust Index", [(data_trust, 1.0, "Data Trust")], "Reliability of score inputs."),
            "ares_coverage_depth": ("ARES Coverage Depth", [(depth, 0.40, "Completed Matches"), (depth, 0.30, "Seasons Covered Proxy"), (teams_seen, 0.20, "Teams Seen"), (conf[0], 0.10, "Recency")], "Historical sample size supporting the signal."),
            "ares_competitive_balance": ("ARES Competitive Balance", [(competitiveness, 0.35, "Points Distribution Balance Proxy"), (normalize_low(max(team_gd_by_league.get(code, [0])) - min(team_gd_by_league.get(code, [0])), [max(v) - min(v) for v in team_gd_by_league.values() if v]), 0.25, "Goal Difference Spread Inversion"), (normalize_low(top_team, [max(v) for v in team_scores_by_league.values() if v]), 0.20, "Top Team Dominance Inversion"), (normalize_high(row.get("draw_rate"), [x.get("draw_rate") for x in league_rows]), 0.10, "Draw Density"), (teams_seen, 0.10, "Team Depth")], "Whether the league is dominated or deep."),
        }
        formulas = {}
        for formula_id, (name, raw_components, explanation) in league_specs.items():
            comps = [{"name": cname, "weight": weight, "score": score} for score, weight, cname in raw_components]
            score, comps, missing = weighted_score(comps)
            formulas[formula_id] = formula_output(formula_id, name, score, comps, ["league_code"], missing, conf, explanation)
        outputs.append({**row, "data_mode": "open_match_derived", "data_status": data_status_label("open_match_derived"), "formulas": formulas})
    return outputs


def build_methodology_cards(registry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards = []
    for item in registry:
        if item["status"] == "live_now" or item["category"] in {"player_position", "role_fit", "market_transfer", "club_league_premium"}:
            cards.append(
                {
                    "formula_id": item["formula_id"],
                    "title": item["formula_name"],
                    "what_it_means": item["website_copy"],
                    "why_it_matters": item["importance"],
                    "data_status": data_status_label(item["data_mode"]),
                    "access": "Premium" if item["premium_locked"] else "Public Beta Demo",
                    "premium_locked": item["premium_locked"],
                }
            )
    return cards


def main() -> int:
    team_rows = read_json(DATA / "open_match_team_stats.json")
    league_rows = read_json(DATA / "open_match_league_stats.json")
    registry, player_registry, premium_registry = build_registry()
    team_outputs = build_team_outputs(team_rows, league_rows)
    league_outputs = build_league_outputs(league_rows, team_outputs)
    cards = build_methodology_cards(registry)

    write_json(DATA / "ares_formula_registry.json", registry)
    write_json(DATA / "ares_team_formula_outputs.json", team_outputs)
    write_json(DATA / "ares_league_formula_outputs.json", league_outputs)
    write_json(DATA / "ares_player_formula_registry.json", player_registry)
    write_json(DATA / "ares_premium_formula_registry.json", premium_registry)
    write_json(DATA / "ares_methodology_cards.json", cards)
    write_json(
        DATA / "ares_formula_build_log.json",
        {
            "generated_at_utc": NOW_UTC,
            "generated_date": TODAY,
            "source_files": ["data/open_match_team_stats.json", "data/open_match_league_stats.json"],
            "registry_formulas": len(registry),
            "player_registry_formulas": len(player_registry),
            "premium_registry_formulas": len(premium_registry),
            "team_input_rows": len(team_rows),
            "team_formula_output_rows": len(team_outputs),
            "league_input_rows": len(league_rows),
            "league_formula_output_rows": len(league_outputs),
            "methodology_cards": len(cards),
            "data_modes": ["open_match_derived", "public_beta_demo", "premium_model_required", "provider_data_required"],
        },
    )
    print(f"Built {len(registry)} formula registry entries.")
    print(f"Built {len(team_outputs)} team formula rows and {len(league_outputs)} league formula rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
