(function (window) {
  "use strict";

  function prepareRows(rows, options) {
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
        if (options.searchId) {
          tables.makeTableSearchable(options.searchId, options.tableId);
          applyQueryFilter(options.searchId);
          const input = document.getElementById(options.searchId);
          if (input && input.value.trim()) input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      })
      .catch(function () { data.showLoadError(options.errorId || options.bodyId, "Board data is refreshing. Try the full board navigation or clear filters."); });
  }

  function applyQueryFilter(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q") || params.get("club") || params.get("league") || params.get("country") || params.get("continent") || params.get("region") || params.get("confederation") || params.get("position") || params.get("tier") || params.get("type") || "";
    if (!query || query === "Global") return;
    input.value = query;
    input.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function initSearch(inputId, resultsId, dataPath) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    if (!input || !results) return;
    window.AresData.loadJson(dataPath).then(function (items) {
      input.addEventListener("input", function () {
        const query = input.value.trim().toLowerCase();
        if (query.length < 2) {
          results.classList.remove("is-open");
          results.innerHTML = "";
          return;
        }
        const matches = items.filter(function (item) {
          return [item.player_name, item.club_name, item.club, item.league, item.country, item.region, item.position, item.keywords].filter(Boolean).join(" ").toLowerCase().includes(query);
        }).slice(0, 8);
        results.innerHTML = matches.length ? matches.map(function (item) {
          const label = item.player_name || item.club_name || item.league || item.id || "Result";
          const meta = [item.type, item.position, item.club, item.league, item.country, item.continent, item.region].filter(Boolean).join(" | ");
          const url = item.url || "#";
          return '<a href="' + window.AresData.safeText(url) + '"><strong>' + window.AresData.safeText(label) + '</strong><small>' + window.AresData.safeText(meta) + '</small></a>';
        }).join("") : "<div>No matching public rows found.</div>";
        results.classList.add("is-open");
      });
    });
  }

  function fillText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value === undefined || value === null ? "" : value;
  }

  function initials(value) {
    return String(value || "AR").split(/\s+/).filter(Boolean).slice(0, 3).map(function (part) { return part.charAt(0); }).join("").toUpperCase() || "AR";
  }

  function imageIsSafe(record) {
    const status = String(record.photo_license_status || "").toLowerCase();
    return Boolean(record.photo_url) && ["ares_owned", "provider_supplied", "licensed_commons", "commons_licensed", "cc_by", "cc_by_sa", "public_domain", "approved_provider"].includes(status);
  }

  function assetHref(url) {
    const href = String(url || "");
    if (!href || href.match(/^(https?:)?\/\//) || href.startsWith("/") || href.startsWith("../")) return href;
    const theme = document.querySelector('link[href*="assets/css/ares-theme"]');
    const themeHref = theme ? theme.getAttribute("href") || "" : "";
    const assetIndex = themeHref.indexOf("assets/");
    const prefix = assetIndex > 0 ? themeHref.slice(0, assetIndex) : "";
    return href.startsWith("assets/") ? prefix + href : href;
  }

  function siteHref(url) {
    const href = String(url || "");
    if (!href) return "#";
    if (href.startsWith("clubs/club-")) return "/ares-football-market/" + href.replace(/^\/+/, "");
    if (href.match(/^(https?:)?\/\//) || href.startsWith("/") || href.startsWith("../")) return href;
    return "../" + href;
  }

  function safe(value) {
    return window.AresData.safeText(value === undefined || value === null ? "" : value);
  }

  function cleanText(value) {
    return String(value === undefined || value === null ? "" : value).trim();
  }

  function hasFact(value) {
    const text = cleanText(value);
    if (!text) return false;
    return !/^(source review|model view|provider pending|not connected|n\/a|null|undefined)$/i.test(text);
  }

  function factValue(value, fallback) {
    return hasFact(value) ? value : (fallback || "");
  }

  function playerCountry(record) {
    return factValue(record.national_team_country) || factValue(record.sport_country) || factValue(record.nationality) || factValue(record.citizenship) || "";
  }

  function heightValue(record) {
    if (hasFact(record.height)) return record.height;
    if (Number(record.height_cm) > 0) return (Number(record.height_cm) / 100).toFixed(2) + " m";
    return "";
  }

  function confidenceDetail(record) {
    const mode = cleanText(record.stats_mode || record.score_source || "ARES beta estimate");
    if (/official/i.test(mode)) return "Official provider coverage";
    return "Identity/photo sourced; scores are beta estimates";
  }

  function sourceModeNote(record) {
    return safe(record.stats_mode || "ARES beta estimate; not official match statistics");
  }

  function per90(count, minutes) {
    const c = Number(count);
    const m = Number(minutes);
    if (!Number.isFinite(c) || !Number.isFinite(m) || m <= 0) return "";
    return (c * 90 / m).toFixed(2);
  }

  function profileRows() {
    return Array.isArray(window.AresProfileRows) ? window.AresProfileRows : [];
  }

  const PROFILE_CONTEXT_PATHS = {
    dataStatus: "../data/data_status.json",
    matches: "../data/matches.json",
    openSummary: "../data/open_match_summary.json",
    transfers: "../data/public_transfers.json",
    marketChanges: "../data/public_market_changes.json",
    clubHonours: "../data/club_honours.json"
  };

  function contextRows(key) {
    const context = window.AresProfileContext || {};
    return Array.isArray(context[key]) ? context[key] : [];
  }

  function contextObject(key) {
    const context = window.AresProfileContext || {};
    return context[key] && !Array.isArray(context[key]) ? context[key] : {};
  }

  function loadProfileContext() {
    if (window.AresProfileContextPromise) return window.AresProfileContextPromise;
    const keys = Object.keys(PROFILE_CONTEXT_PATHS);
    window.AresProfileContextPromise = Promise.all(keys.map(function (key) {
      return window.AresData.loadJson(PROFILE_CONTEXT_PATHS[key]).catch(function () {
        return key === "dataStatus" ? {} : [];
      });
    })).then(function (payload) {
      const context = {};
      keys.forEach(function (key, index) { context[key] = payload[index]; });
      window.AresProfileContext = context;
      return context;
    });
    return window.AresProfileContextPromise;
  }

  function normalizeName(value) {
    return cleanText(value).toLowerCase()
      .replace(/&/g, " and ")
      .replace(/\b(f\.?c\.?|afc|cf|sc|club|football|association)\b/g, " ")
      .replace(/[^a-z0-9]+/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function shortClubName(record) {
    return cleanText(record.club).replace(/\s+(F\.?C\.?|A\.?F\.?C\.?|Football Club)$/i, "").trim();
  }

  function teamMatchesRecord(record, team) {
    const club = normalizeName(shortClubName(record) || record.club);
    const candidate = normalizeName(team);
    if (!club || !candidate) return false;
    if (candidate === club || candidate.includes(club) || club.includes(candidate)) return true;
    const clubParts = club.split(" ").filter(function (part) { return part.length > 3; });
    return clubParts.length && clubParts.every(function (part) { return candidate.includes(part); });
  }

  function parseMatchDate(value) {
    const text = cleanText(value);
    const parts = text.split(/[/-]/).map(Number);
    if (parts.length === 3 && parts[2] > 1900) return new Date(parts[2], parts[1] - 1, parts[0]).getTime();
    const parsed = Date.parse(text);
    return Number.isFinite(parsed) ? parsed : 0;
  }

  function relatedMatches(record, limit) {
    const matches = contextRows("matches").slice().sort(function (left, right) {
      return parseMatchDate(right.date) - parseMatchDate(left.date);
    });
    const clubMatches = matches.filter(function (match) {
      return teamMatchesRecord(record, match.home_team) || teamMatchesRecord(record, match.away_team);
    });
    const leagueMatches = matches.filter(function (match) {
      return cleanText(match.league_name) === cleanText(record.league);
    });
    return (clubMatches.length ? clubMatches : leagueMatches).slice(0, limit || 5);
  }

  function leagueOpenSummary(record) {
    const summaries = contextRows("openSummary");
    return summaries.find(function (item) {
      return cleanText(item.league_name) === cleanText(record.league);
    }) || summaries.find(function (item) {
      return cleanText(item.country) === cleanText(record.country);
    }) || {};
  }

  function playerMarketChanges(record, limit) {
    const rows = contextRows("marketChanges");
    const exact = rows.filter(function (item) { return cleanText(item.player_id) === cleanText(record.player_id); });
    const related = rows.filter(function (item) {
      return cleanText(item.player_id) !== cleanText(record.player_id) &&
        (cleanText(item.league) === cleanText(record.league) || cleanText(item.position) === cleanText(record.position) || cleanText(item.country) === cleanText(record.country));
    });
    return exact.concat(related).slice(0, limit || 5);
  }

  function playerTransfers(record, limit) {
    const rows = contextRows("transfers");
    const exact = rows.filter(function (item) { return cleanText(item.player_id) === cleanText(record.player_id); });
    const related = rows.filter(function (item) {
      return cleanText(item.player_id) !== cleanText(record.player_id) &&
        (cleanText(item.position) === cleanText(record.position) || cleanText(item.to_league) === cleanText(record.league) || cleanText(item.from_league) === cleanText(record.league));
    });
    return exact.concat(related).slice(0, limit || 5);
  }

  function currentClubHonours(record, limit) {
    const club = normalizeName(shortClubName(record) || record.club);
    return contextRows("clubHonours").filter(function (item) {
      return cleanText(item.club_id) === cleanText(record.club_id) || normalizeName(item.club_name) === club;
    }).slice(0, limit || 6);
  }

  function clampScore(value) {
    return Math.max(0, Math.min(100, Number(value) || 0));
  }

  function round1(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(1) : "";
  }

  function round2(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(2) : "";
  }

  function derivedMetrics(record) {
    const minutes = Number(record.minutes || 0);
    const appearances = Number(record.appearances || 0);
    const starts = Number(record.starts || 0);
    const goals = Number(record.goals || 0);
    const assists = Number(record.assists || 0);
    const progressive = Number(record.progressive_actions || 0);
    const defensive = Number(record.defensive_actions || 0);
    const availability = Number(record.availability_pct || 0);
    const ares = scoreValue(record, "ares_score", 82);
    const market = scoreValue(record, "market_score", 80);
    const startRate = appearances > 0 ? starts / appearances : 0;
    const trend = Number(record.trend_value || 0);
    const contractRunway = Math.max(0, Number(record.contract_end || 0) - 2026);
    const goals90 = minutes > 0 ? goals * 90 / minutes : 0;
    const assists90 = minutes > 0 ? assists * 90 / minutes : 0;
    const progressive90 = minutes > 0 ? progressive * 90 / minutes : 0;
    const defensive90 = minutes > 0 ? defensive * 90 / minutes : 0;
    return {
      minutes: minutes,
      appearances: appearances,
      starts: starts,
      startRate: startRate,
      goals90: goals90,
      assists90: assists90,
      progressive90: progressive90,
      defensive90: defensive90,
      availability: availability,
      ares: ares,
      market: market,
      trend: trend,
      contractRunway: contractRunway,
      outputScore: clampScore(ares * 0.35 + goals90 * 20 + assists90 * 24 + progressive90 * 1.1),
      chanceScore: clampScore(ares * 0.34 + assists90 * 32 + progressive90 * 1.35 + startRate * 8),
      progressionScore: clampScore(ares * 0.34 + progressive90 * 2.35 + startRate * 10),
      defensiveScore: clampScore(ares * 0.24 + defensive90 * 2.65 + availability * 0.34),
      keepingScore: clampScore(ares * 0.36 + defensive90 * 1.4 + availability * 0.38 + startRate * 16),
      roleScore: clampScore(ares * 0.27 + availability * 0.35 + startRate * 22 + Math.min(minutes / 12, 18)),
      marketFormula: clampScore(market * 0.46 + ares * 0.28 + availability * 0.12 + Math.min(contractRunway * 4, 10) + trend * 3)
    };
  }

  function positionFamily(record) {
    const raw = cleanText(record.position || record.position_label || record.position_usage).toUpperCase();
    if (/\b(GK|GOALKEEPER)\b/.test(raw)) return "GK";
    if (/\b(CB|DF|DEF|FB|LB|RB|WB|BACK|DEFENDER)\b/.test(raw)) return "DF";
    if (/\b(FW|ST|CF|SS|LW|RW|WINGER|FORWARD|ATTACKER)\b/.test(raw)) return "FW";
    return "MF";
  }

  function positionFormulaRows(record) {
    const metrics = derivedMetrics(record);
    const family = positionFamily(record);
    if (family === "GK") {
      return [
        ["Shot Stopping / Box Security", round1(metrics.keepingScore), "ARES 36% + defensive actions /90 + availability + start rate"],
        ["Distribution", round1(clampScore(metrics.ares * 0.32 + metrics.progressive90 * 2.8 + metrics.startRate * 12)), "ARES + progressive actions /90 + role load"],
        ["Command Reliability", round1(clampScore(metrics.ares * 0.31 + metrics.availability * 0.42 + metrics.startRate * 18)), "ARES + availability + starts / appearances"],
        ["Availability", round1(metrics.availability), "Public beta availability estimate"],
        ["Role Security", round1(metrics.roleScore), "ARES + availability + start rate + minutes load"]
      ];
    }
    if (family === "DF") {
      return [
        ["Defensive Value", round1(metrics.defensiveScore), "ARES 24% + defensive actions /90 + availability"],
        ["Ball Progression", round1(metrics.progressionScore), "ARES + progressive actions /90 + start rate"],
        ["Box / Set-Piece Value", round1(clampScore(metrics.ares * 0.3 + metrics.goals90 * 10 + metrics.defensive90 * 1.8)), "ARES + defensive actions /90 + low-weight goals /90"],
        ["Availability", round1(metrics.availability), "Public beta availability estimate"],
        ["Role Security", round1(metrics.roleScore), "ARES + availability + start rate + minutes load"]
      ];
    }
    if (family === "FW") {
      return [
        ["Finishing", round1(metrics.outputScore), "ARES 35% + goals /90 + assists /90 + progression"],
        ["Chance Quality", round1(metrics.chanceScore), "ARES + assists /90 + progressive actions /90 + start rate"],
        ["Link-Up Play", round1(metrics.progressionScore), "ARES + progressive actions /90 + role load"],
        ["Pressing / Defensive Work", round1(metrics.defensiveScore), "ARES + defensive actions /90 + availability"],
        ["Role Security", round1(metrics.roleScore), "ARES + availability + start rate + minutes load"]
      ];
    }
    return [
      ["Progression", round1(metrics.progressionScore), "ARES + progressive actions /90 + start rate"],
      ["Chance Creation", round1(metrics.chanceScore), "ARES + assists /90 + progressive actions /90 + start rate"],
      ["Defensive Work", round1(metrics.defensiveScore), "ARES + defensive actions /90 + availability"],
      ["Availability", round1(metrics.availability), "Public beta availability estimate"],
      ["Role Security", round1(metrics.roleScore), "ARES + availability + start rate + minutes load"]
    ];
  }

  function componentTitle(record) {
    const family = positionFamily(record);
    if (family === "GK") return "Goalkeeper Component Grades";
    if (family === "DF") return "Defender Component Grades";
    if (family === "FW") return "Attacker Component Grades";
    return "Midfielder Component Grades";
  }

  function formulaRows(record) {
    const metrics = derivedMetrics(record);
    return positionFormulaRows(record).concat([
      ["Market Conviction", round1(metrics.marketFormula), "Market score + ARES + availability + contract runway + trend"]
    ]);
  }

  function formulaTable(record) {
    return tableHtml(["Component", "Score", "Formula Inputs"], formulaRows(record));
  }

  function componentBars(record) {
    return metricBars(positionFormulaRows(record).map(function (row) { return [row[0], row[1]]; }));
  }

  function recentMatchesTable(record, limit) {
    const rows = relatedMatches(record, limit || 5).map(function (match) {
      const side = teamMatchesRecord(record, match.home_team) ? "Home" : (teamMatchesRecord(record, match.away_team) ? "Away" : "League");
      return [
        match.date || "",
        match.league_name || "",
        match.home_team || "",
        match.full_time_score || "",
        match.away_team || "",
        side,
        match.source_confidence || match.source || "Open CSV"
      ];
    });
    return rows.length ? tableHtml(["Date", "League", "Home", "FT", "Away", "Context", "Source"], rows) : pendingBlock("Open match context unavailable", "No related open match rows were found for this player, club, or league.");
  }

  function leagueCoverageTable(record) {
    const summary = leagueOpenSummary(record);
    const status = contextObject("dataStatus");
    const rows = [
      ["Open Match Rows", status.open_match_rows || summary.matches || "", status.open_match_source || summary.source || "Football-Data.co.uk open CSV"],
      ["League Coverage", summary.league_name || record.league || "", (summary.matches ? summary.matches + " matches" : "Coverage pending")],
      ["Seasons", summary.seasons || "", [summary.first_date, summary.last_date].filter(Boolean).join(" to ")],
      ["Clubs Seen", summary.clubs_seen || "", summary.country || record.country || ""]
    ];
    return tableHtml(["Coverage", "Value", "Source / Scope"], rows.filter(function (row) { return hasFact(row[1]); }));
  }

  function marketChangesTable(record, limit) {
    const rows = playerMarketChanges(record, limit || 5).map(function (item) {
      return [
        item.last_updated || "",
        item.player_name || "",
        item.club || "",
        item.change || "",
        item.trend || "",
        item.reason || "",
        item.source || "ARES public market model"
      ];
    });
    return rows.length ? tableHtml(["Date", "Player", "Club", "Change", "Trend", "Reason", "Source"], rows) : tableHtml(["Date", "Player", "Club", "Change", "Trend", "Reason", "Source"], [[record.last_updated || "", playerLabel(record), record.club || "", trendDetail(record), record.trend || "", record.reason || "", record.source || "ARES public beta"]]);
  }

  function transfersTable(record, limit) {
    const rows = playerTransfers(record, limit || 5).map(function (item) {
      return [
        item.date || "",
        item.player_name || item.player || "",
        item.position || "",
        item.from_club || "",
        item.to_club || "",
        item.transfer_type || item.movement_type || "",
        item.market_impact || item.ares_impact || item.reason || ""
      ];
    });
    return rows.length ? tableHtml(["Date", "Player", "Pos", "From", "To", "Type", "Impact"], rows) : pendingBlock("Transfer rows unavailable", "No related transfer rows were found in the downloaded public transfer bundle.");
  }

  function honoursTable(record, limit) {
    const rows = currentClubHonours(record, limit || 6).map(function (item) {
      return [
        item.club_name || record.club || "",
        item.competition || "",
        item.honour_type || "",
        item.count || "",
        item.years || "",
        item.source_text || item.source_url || ""
      ];
    });
    return rows.length ? tableHtml(["Club", "Competition", "Honour", "Count", "Years", "Source"], rows) : pendingBlock("Club honour rows unavailable", "No sourced club-honour rows were found for this current club in the downloaded bundle.");
  }

  function profileDataNotice(record) {
    const status = contextObject("dataStatus");
    const source = status.open_match_source || "Football-Data.co.uk open CSV";
    return '<p class="ares-data-footnote">ARES player components are formula estimates from the public player record. Open match rows provide EPL/team context only; they are not player event logs. Source: ' + safe(source) + '.</p>';
  }

  function playerBadges(record) {
    const metrics = derivedMetrics(record);
    const badges = [
      record.ares_tier || "ARES profile",
      record.market_tier || "Market profile",
      record.role || "Role profile",
      record.age_curve || "Age curve",
      record.data_confidence ? record.data_confidence + " confidence" : "",
      metrics.availability ? round1(metrics.availability) + "% availability" : ""
    ].filter(Boolean);
    return '<div class="ares-badge-grid">' + badges.map(function (item) {
      return '<span>' + safe(item) + '</span>';
    }).join("") + '</div>';
  }

  function positionRank(record) {
    const position = cleanText(record.position);
    const rows = profileRows().filter(function (item) {
      return cleanText(item.position) === position && Number.isFinite(Number(item.ares_score));
    }).sort(function (left, right) {
      return Number(right.ares_score || 0) - Number(left.ares_score || 0);
    });
    const index = rows.findIndex(function (item) { return cleanText(item.player_id) === cleanText(record.player_id); });
    if (index >= 0) return "#" + (index + 1) + " / " + rows.length;
    return position || "";
  }

  function samePositionComparables(record) {
    const age = Number(record.age || 0);
    const ares = scoreValue(record, "ares_score", 82);
    const market = scoreValue(record, "market_score", 80);
    const position = cleanText(record.position);
    return profileRows().filter(function (item) {
      return cleanText(item.player_id) !== cleanText(record.player_id) && cleanText(item.position) === position;
    }).map(function (item) {
      const distance = Math.abs(Number(item.ares_score || 0) - ares) + Math.abs(Number(item.market_score || 0) - market) + Math.abs(Number(item.age || age) - age) * 0.35;
      return { item: item, distance: distance };
    }).sort(function (left, right) { return left.distance - right.distance; }).slice(0, 3).map(function (entry, index) {
      const item = entry.item;
      return [
        playerLabel(item),
        item.age || "",
        item.club || "",
        item.position || "",
        item.ares_score || "",
        item.market_score || "",
        Math.max(64, 92 - index * 5 - Math.round(entry.distance)).toString() + "%"
      ];
    });
  }

  function comparablePlayersTable(record) {
    const rows = [[
      playerLabel(record),
      record.age || "",
      record.club || "",
      record.position || "",
      record.ares_score || "",
      record.market_score || "",
      "Reference"
    ]].concat(samePositionComparables(record));
    return tableHtml(["Player", "Age", "Club", "Position", "ARES Score", "Market Score", "Similarity"], rows);
  }

  function pendingBlock(title, message) {
    return '<div class="ares-data-pending"><strong>' + safe(title) + '</strong><p>' + safe(message) + '</p></div>';
  }

  function transferSignal(record) {
    const raw = cleanText(record.transfer_value_signal || record.trend || "Stable");
    return raw.replace(/\s[-+]?\d+(\.\d+)?$/, "") || raw;
  }

  function trendDetail(record) {
    const trend = cleanText(record.trend);
    const value = cleanText(record.trend_value);
    return [trend, value && value !== "0" ? value : ""].filter(Boolean).join(" ");
  }

  function statListFacts(items, emptyMessage) {
    const filtered = items.filter(function (item) { return hasFact(item[1]); });
    if (!filtered.length) return pendingBlock("Source data pending", emptyMessage || "This module is waiting for approved source data.");
    return statList(filtered);
  }

  function scoreValue(record, key, fallback) {
    const value = Number(record[key]);
    return Number.isFinite(value) ? value : fallback;
  }

  function pct(value) {
    const number = Math.max(0, Math.min(100, Number(value) || 0));
    return String(Math.round(number));
  }

  function kpiGrid(items) {
    return '<section class="ares-section ares-kpi-grid">' + items.map(function (item) {
      return '<div class="ares-kpi-card"><span class="label">' + safe(item[0]) + '</span><span class="value">' + safe(item[1]) + '</span><span class="meta">' + safe(item[2]) + '</span></div>';
    }).join("") + '</section>';
  }

  function chartHtml(title, explanation, kind, xAxis, yAxis) {
    const titleKey = String(title || "").toLowerCase();
    let barLabels = [["18", 48], ["22", 72], ["26", 56], ["30", 88], ["32", 64], ["36", 78]];
    if (titleKey.includes("position") || titleKey.includes("radar")) {
      barLabels = [["GK", 42], ["DF", 68], ["MF", 74], ["W", 82], ["CF", 91], ["SS", 55]];
    } else if (titleKey.includes("goals by minute")) {
      barLabels = [["0-15", 40], ["16-30", 62], ["31-45", 54], ["46-60", 76], ["61-90", 88]];
    } else if (titleKey.includes("contract")) {
      barLabels = [["2026", 42], ["2027", 82], ["2028", 58]];
    } else if (titleKey.includes("transfer value signal")) {
      barLabels = [["Sell", 36], ["Hold", 84], ["Buy", 52], ["Risk", 28]];
    } else if (titleKey.includes("caps")) {
      barLabels = [["2019", 34], ["2021", 52], ["2023", 73], ["2025", 82]];
    } else if (titleKey.includes("achievement")) {
      barLabels = [["Breakout", 38], ["Peak", 86], ["Late", 64]];
    } else if (titleKey.includes("minutes")) {
      barLabels = [["2022", 65], ["2023", 78], ["2024", 84], ["2025", 72]];
    }
    let visual = '<div class="ares-chart-bars">' + barLabels.map(function (item) {
      return '<span style="height:' + item[1] + '%"><b>' + safe(item[0]) + '</b><em>' + safe(item[1]) + '</em></span>';
    }).join("") + '</div>';
    if (kind === "scatter") {
      let scatterLabels = [["Watch", 15, 62], ["Elite", 48, 26], ["Risk", 70, 42]];
      if (titleKey.includes("market")) scatterLabels = [["Hidden", 15, 62], ["Elite", 48, 26], ["Overpriced", 67, 42]];
      if (titleKey.includes("transfer")) scatterLabels = [["Low fee", 15, 62], ["Prime", 48, 26], ["High fee", 67, 42]];
      visual = '<div class="ares-chart-scatter"><i style="left:18%;top:58%"></i><i style="left:34%;top:44%"></i><i style="left:52%;top:31%"></i><i style="left:67%;top:22%"></i><i style="left:78%;top:39%"></i></div><div class="ares-chart-scatter-labels">' + scatterLabels.map(function (item) {
        return '<span style="left:' + item[1] + '%;top:' + item[2] + '%">' + safe(item[0]) + '</span>';
      }).join("") + '</div>';
    } else if (kind === "line") {
      let lineLabels = [["82", 6, 56], ["89", 34, 32], ["91", 61, 44], ["95", 82, 20]];
      if (titleKey.includes("value")) lineLabels = [["2018", 6, 56], ["2021", 34, 32], ["Peak", 61, 22], ["Now", 82, 44]];
      if (titleKey.includes("year")) lineLabels = [["2015", 6, 56], ["2018", 34, 32], ["2022", 61, 44], ["2025", 82, 20]];
      if (titleKey.includes("season")) lineLabels = [["2019/20", 6, 56], ["2021/22", 34, 32], ["2023/24", 61, 44], ["2025/26", 82, 20]];
      visual = '<div class="ares-chart-line"></div><div class="ares-chart-line-labels">' + lineLabels.map(function (item) {
        return '<span style="left:' + item[1] + '%;top:' + item[2] + '%">' + safe(item[0]) + '</span>';
      }).join("") + '</div>';
    }
    return '<div class="ares-graph-card"><h2 class="h4">' + safe(title) + '</h2><p class="ares-muted-note">' + safe(explanation) + '</p><div class="ares-chart-frame" title="' + safe(title + ": " + explanation) + '">' + visual + '</div><div class="ares-chart-axis"><span>X-axis: ' + safe(xAxis) + '</span><span>Y-axis: ' + safe(yAxis) + '</span></div><div class="ares-chart-legend"><span>ARES quality</span><span>Market value</span><span>Transfer signal</span><span>Confidence</span></div><p class="ares-chart-explainer">How to read: ' + safe(explanation) + '</p><p class="ares-chart-seeded-note">Seeded beta data. Live feeds are not connected.</p></div>';
  }

  function tableHtml(headers, rows) {
    if (!rows || !rows.length) return pendingBlock("Data feed pending", "ARES has no approved row-level source for this module yet.");
    return '<div class="table-responsive"><table class="ares-table"><thead><tr>' + headers.map(function (header) {
      return '<th>' + safe(header) + '</th>';
    }).join("") + '</tr></thead><tbody>' + rows.map(function (row) {
      return '<tr>' + row.map(function (cell, index) { return '<td data-label="' + safe(headers[index] || "") + '">' + safe(cell) + '</td>'; }).join("") + '</tr>';
    }).join("") + '</tbody></table></div>';
  }

  function metricBars(items) {
    return '<div class="ares-metric-bars">' + items.map(function (item) {
      return '<div class="ares-metric-row"><span>' + safe(item[0]) + '</span><div><i style="width:' + pct(item[1]) + '%"></i></div><strong>' + safe(item[1]) + '</strong></div>';
    }).join("") + '</div>';
  }

  function numberedCard(index, title, content, extraClass) {
    return '<section class="ares-numbered-card ' + safe(extraClass || "") + '"><h2><span>' + safe(index) + '</span>' + safe(title) + '<small>i</small></h2>' + content + '</section>';
  }

  function statList(items) {
    return '<div class="ares-profile-stat-list">' + items.map(function (item) {
      return '<div><span>' + safe(item[0]) + '</span><strong>' + safe(item[1]) + '</strong><small>' + safe(item[2] || "") + '</small></div>';
    }).join("") + '</div>';
  }

  function scoreDial(value, label) {
    return '<div class="ares-score-dial"><div><strong>' + safe(Math.round(Number(value) || 0)) + '</strong></div><span>' + safe(label) + '</span></div>';
  }

  function minutesByRole(record) {
    const minutes = String(record.minutes_role || "").match(/\d+/);
    const total = minutes ? minutes[0] : cleanText(record.minutes);
    return '<div class="ares-role-donut"><div><strong>' + safe(total || "0") + '</strong><span>Beta minutes</span></div></div><ul class="ares-role-legend"><li><b></b>' + safe(record.position || "Primary") + ' 85%</li><li><b></b>Secondary role 12%</li><li><b></b>Other role 3%</li></ul><p class="ares-chart-seeded-note">' + sourceModeNote(record) + '</p>';
  }

  function pitchUsage(record) {
    return '<div class="ares-pitch-map"><div class="zone zone-top"><strong>' + safe(record.position || "Primary") + '</strong><span>85%</span></div><div class="zone zone-mid"><strong>Secondary</strong><span>12%</span></div><div class="zone zone-low"><strong>Other</strong><span>3%</span></div></div><p class="ares-chart-explainer">How to read: role share is an ARES beta positional model until event and tracking feeds connect.</p>';
  }

  function formStrip(record) {
    const ares = scoreValue(record, "ares_score", 82);
    const values = [ares - 10, ares - 2, ares - 14, ares - 1, ares - 19, ares - 6, ares + 1, ares - 5, ares - 12, ares - 3];
    return '<div class="ares-form-chart"><div class="ares-form-line"></div>' + values.map(function (value, index) {
      const y = Math.max(10, Math.min(78, 90 - value));
      return '<span style="left:' + (4 + index * 10) + '%;top:' + y + '%"><b>' + safe((value / 10).toFixed(1)) + '</b></span>';
    }).join("") + '</div><p class="ares-muted-note">ARES Form is a beta rating out of 10 based on season profile, role, and ARES score. It is not an official match-feed log.</p>';
  }

  function marketMiniTrend(record) {
    return '<div class="ares-mini-trend"><h3 class="ares-mini-heading">Market Value Trend</h3><p class="ares-muted-note">Line-area model for public market direction, not a fee claim.</p><div class="ares-mini-line-chart"><span style="left:4%;top:58%">2018</span><span style="left:40%;top:30%">Peak</span><span style="left:82%;top:52%">Now</span></div><div class="ares-chart-axis"><span>X-axis: Season</span><span>Y-axis: Market Score</span></div><p class="ares-chart-explainer">How to read: the curve shows ARES market score direction, with live price feeds not connected.</p><p class="ares-chart-seeded-note">Seeded beta data. Live feeds are not connected.</p></div>';
  }

  function tabHeader(title, text) {
    return '<div class="ares-tab-heading"><div><h2>' + safe(title) + '</h2><p>' + safe(text) + '</p><p class="ares-tab-trust-note">Seeded beta data. Live feeds are not connected.</p></div><span class="ares-beta-badge">Seeded Beta</span></div>';
  }

  function playerLabel(record) {
    return record.player_name || record.display_name || "This player";
  }

  function renderOverview(record) {
    const ares = scoreValue(record, "ares_score", 82);
    const metrics = derivedMetrics(record);
    return '<section class="ares-profile-dashboard">' +
      numberedCard(1, "Player Identity", statListFacts([["Full Name", playerLabel(record)], ["Date of Birth", record.date_of_birth], ["Nationality", playerCountry(record)], ["Citizenship", record.citizenship], ["Position", record.position], ["Height", heightValue(record)], ["Foot", record.foot], ["Current Club", record.club], ["League", record.league], ["Contract Until", record.contract_end]], "Identity fields are populated only when Wikidata or approved roster data provides them."), "span-4") +
      numberedCard(2, "ARES Performance Snapshot", '<div class="ares-snapshot-grid">' + scoreDial(ares, record.ares_tier || "Role Grade") + statList([["Position Rank", positionRank(record), record.position || ""], ["Minutes / Role", record.minutes_role || ""], ["Start Rate", round1(metrics.startRate * 100) + "%", String(metrics.starts || 0) + " starts / " + String(metrics.appearances || 0) + " apps"], ["Progressive Actions /90", round2(metrics.progressive90)], ["Defensive Actions /90", round2(metrics.defensive90)], ["Availability", round1(metrics.availability) + "%"]]) + minutesByRole(record) + '</div>', "span-8") +
      numberedCard(3, "Market Intelligence", '<div class="ares-market-intel-grid">' + statListFacts([["Estimated Value Band", record.market_tier || ""], ["Age Curve", record.age_curve || ""], ["Contract Signal", record.contract_end || ""], ["Durability Risk", record.durability || (record.availability_pct ? record.availability_pct + " availability estimate" : "")], ["League Strength", record.league || ""], ["Asset Risk", record.trend || ""]], "Market intelligence fields are populated only when the model and source data are available.") + marketMiniTrend(record) + '</div>', "span-7") +
      numberedCard(4, "Position Usage", pitchUsage(record), "span-5") +
      numberedCard(5, "ARES Form Trend (Last 10 Matches)", formStrip(record), "span-8") +
      numberedCard(6, componentTitle(record), componentBars(record), "span-4") +
      numberedCard(7, "Recent Open Matches", recentMatchesTable(record, 4) + profileDataNotice(record), "span-6") +
      numberedCard(8, "Comparable Players", comparablePlayersTable(record), "span-6") +
      '</section>';
  }

  function renderStats(record) {
    const minutes = String(record.minutes_role || "").match(/\d+/);
    const minuteValue = minutes ? minutes[0] : cleanText(record.minutes);
    const goalsPer90 = per90(record.goals, minuteValue);
    const assistsPer90 = per90(record.assists, minuteValue);
    const metrics = derivedMetrics(record);
    return tabHeader("Stats Center", "Position-aware ARES formulas built from the public player record plus EPL/open-match context.") +
      kpiGrid([["Appearances", record.appearances || "", "Public beta player row"], ["Starts", record.starts || "", round1(metrics.startRate * 100) + "% start rate"], ["Minutes", minuteValue || "", record.role || "Role load"], ["ARES Score", record.ares_score || "", record.ares_tier || "ARES quality"]]) +
      kpiGrid([["Goals / 90", positionFamily(record) === "GK" ? "N/A" : (goalsPer90 || "0.00"), positionFamily(record) === "GK" ? "Excluded for GK formula" : "computed from goals and minutes"], ["Assists / 90", assistsPer90 || "0.00", "computed from assists and minutes"], ["Progressive / 90", round2(metrics.progressive90), "progressive actions / minutes"], ["Defensive / 90", round2(metrics.defensive90), "defensive actions / minutes"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Position Formula Breakdown</h2>' + formulaTable(record) + profileDataNotice(record) + '</div><div class="ares-card"><h2 class="h4">' + safe(componentTitle(record)) + '</h2>' + componentBars(record) + '</div></section>' +
      '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Competition Split</h2>' + tableHtml(["Competition", "Apps", "Starts", "Min", "G", "A", "ARES"], [[record.league || "League", record.appearances || "", record.starts || "", minuteValue || "", record.goals || "", record.assists || "", record.ares_score || ""]]) + '</div><div class="ares-card"><h2 class="h4">Open League Coverage</h2>' + leagueCoverageTable(record) + '</div></section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Recent Team / EPL Context</h2>' + recentMatchesTable(record, 6) + profileDataNotice(record) + '</section>';
  }

  function renderMarket(record) {
    return tabHeader("Market Value Intelligence", "Value logic, age curve, contract signal, and transfer movement.") +
      kpiGrid([["Market Score", record.market_score || "", record.market_tier || "Asset value"], ["ARES Score", record.ares_score || "", record.ares_tier || "Quality"], ["Transfer Signal", transferSignal(record), "Movement"], ["Data Confidence", record.data_confidence || "", confidenceDetail(record)]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Estimated Value Trend", "Line-area model for public market direction, not a fee claim.", "line", "Season", "Market Score") + '<div class="ares-card"><h2 class="h4">Market Value Summary</h2>' + tableHtml(["Field", "Value", "Source"], [["Estimated Value Band", record.market_tier || "", "Public beta row"], ["Age Curve", record.age_curve || "", "ARES age model"], ["Contract Signal", record.contract_end || "", "Public profile"], ["League Strength", record.league || "", "Open match coverage"], ["Model Source", record.score_source || "ARES beta estimate", record.source || ""]]) + '</div></section>' +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Market Formula Breakdown</h2>' + tableHtml(["Component", "Value", "Formula"], [["Market Conviction", round1(derivedMetrics(record).marketFormula), "Market score + ARES + availability + contract runway + trend"], ["ARES Quality", record.ares_score || "", record.ares_tier || ""], ["Availability", record.availability_pct ? record.availability_pct + "%" : "", record.durability || ""], ["Contract Runway", record.contract_end || "", "Contract year minus 2026"], ["Trend", trendDetail(record), record.reason || ""]]) + '</div>' + chartHtml("Age Curve", "Line chart shows how asset value changes across age bands.", "line", "Age band", "Market curve") + '</section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Downloaded Market Movement Rows</h2>' + marketChangesTable(record, 6) + '</section><section class="ares-section ares-card"><h2 class="h4">Comparable Market Assets</h2>' + comparablePlayersTable(record) + '</section>';
  }

  function renderTransfers(record) {
    return tabHeader("Transfer Intelligence", "Transfer history, contract window, resale runway, and comparable moves.") +
      kpiGrid([["Current Club", record.club || ""], ["Contract Window", record.contract_end || "Contract feed pending"], ["Resale Runway", Number(record.age || 25) <= 23 ? "Long" : "Medium"], ["Transfer Signal", transferSignal(record)]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Downloaded Transfer Rows</h2>' + transfersTable(record, 6) + '</div>' + chartHtml("Transfer Value At Move", "Timeline chart places related moves against age and value signal.", "line", "Move date", "Value signal") + '</section>' +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Transfer Formula</h2>' + tableHtml(["Signal", "Value", "Logic"], [["Transfer Signal", transferSignal(record), trendDetail(record)], ["Resale Runway", Number(record.age || 25) <= 23 ? "Long" : "Medium", "Age curve: " + cleanText(record.age_curve || "")], ["Role Security", record.role_security || "", "Minutes, starts, availability"], ["Contract Window", record.contract_end || "", "Contract leverage"], ["Market Conviction", round1(derivedMetrics(record).marketFormula), "Market score + ARES + availability + contract + trend"]]) + '</div>' + chartHtml("Comparable Transfers", "Bubble chart compares age, role context, and ARES score.", "scatter", "Age", "ARES / fee context") + '</section>';
  }

  function renderRumours(record) {
    return tabHeader("Rumour Intelligence", "No fake gossip. This tab converts downloaded transfer and market rows into controlled signal context.") +
      kpiGrid([["Current Club", record.club || ""], ["League Context", record.league || ""], ["Signal", transferSignal(record), trendDetail(record)], ["Reliability", record.data_confidence || "", confidenceDetail(record)]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Related Movement Signals</h2>' + transfersTable(record, 5) + '</div>' + chartHtml("Rumour Signal Timeline", "Signal is derived from public transfer and market rows, not live gossip.", "line", "Week", "Signal strength") + '</section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Market Notes Driving Rumour Context</h2>' + marketChangesTable(record, 5) + '</section><section class="ares-section ares-card"><h2 class="h4">Signal Logic</h2>' + tableHtml(["Factor", "Current Read", "Why It Matters"], [["Role", record.role || "", "Buyer fit depends on position family and role load"], ["Contract", record.contract_end || "", "Longer runway changes negotiation leverage"], ["Age Curve", record.age_curve || "", "Prime/u23/veteran risk"], ["Market", record.market_tier || "", "Price tier and scarcity"], ["Data Confidence", record.data_confidence || "", "Controls how aggressively ARES ranks the signal"]]) + '</section>';
  }

  function renderNational(record) {
    return tabHeader("National Team Profile", "International role, tournament value, national-team output, and squad importance.") +
      kpiGrid([["Nationality", playerCountry(record) || "Identity pending"], ["Citizenship", record.citizenship || ""], ["Position Family", positionFamily(record), "Formula branch"], ["International ARES", round1(scoreValue(record, "ares_score", 82) - 1.5), "Club ARES adjusted for tournament risk"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">International Summary</h2>' + tableHtml(["Field", "Value", "Source"], [["Country / Eligibility", playerCountry(record) || "Pending", record.identity_source || record.source || ""], ["Citizenship", record.citizenship || "", "Wikidata identity"], ["Role", record.position || "", "ARES public player row"], ["Tournament Value", record.market_tier || "", "Market model"], ["Squad Importance", record.ares_tier || "", "ARES quality tier"]]) + '</div>' + chartHtml("Tournament Value", "Formula view of international value by role, age, availability, and market tier.", "bars", "Factor", "Value") + '</section>' +
      '<section class="ares-section ares-card"><h2 class="h4">National Team Data Status</h2>' + pendingBlock("Caps feed not in downloaded bundle", "The current downloaded public bundle has identity and eligibility data, but no official national-team cap or match-event feed. ARES does not invent caps or goals.") + '</section>';
  }

  function renderNews(record) {
    return tabHeader("Player News Terminal", "Player notes, club notes, market notes, injury notes, and transfer notes translated into signal impact.") +
      kpiGrid([["Latest Note", "ARES model refresh"], ["Market Impact", record.trend || "Stable"], ["Availability", record.durability || "Feed pending"], ["Transfer Impact", transferSignal(record)]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("News Impact Timeline", "Line chart tracks ARES, market, and risk impact from downloaded model notes.", "line", "Note date", "Impact score") + '<div class="ares-card"><h2 class="h4">Source Categories</h2>' + tableHtml(["Category", "Status", "Scope"], [["Market Notes", "Loaded", "public_market_changes.json"], ["Club / League Context", "Loaded", "matches.json + open_match_summary.json"], ["Identity / Photo", "Loaded", record.source || ""], ["Injury Feed", "Not connected", "Availability estimate only"]]) + '</div></section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Downloaded Market / Model Notes</h2>' + marketChangesTable(record, 6) + '</section><section class="ares-section ares-card"><h2 class="h4">News Signal Summary</h2><p>Current effect: ' + safe(record.reason || "ARES public beta model refresh") + ' | Market Signal: ' + safe(record.trend || "Stable") + ' | Availability: ' + safe(record.durability || "Feed pending") + '</p></section>';
  }

  function renderAchievements(record) {
    return tabHeader("Achievements", "Team honours, individual honours, milestones, and ARES career badges.") +
      kpiGrid([["Current Club Honours", currentClubHonours(record, 99).length || "0", "Downloaded club_honours rows"], ["ARES Tier", record.ares_tier || "", "Player quality badge"], ["Market Tier", record.market_tier || "", "Asset badge"], ["Data Confidence", record.data_confidence || "", confidenceDetail(record)]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Honours Timeline", "Timeline chart places current-club honours across career context.", "line", "Year", "Honour count") + '<div class="ares-card"><h2 class="h4">ARES Career Badges</h2>' + playerBadges(record) + '</div></section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Downloaded Club Honours</h2>' + honoursTable(record, 8) + '</section><section class="ares-section ares-card"><h2 class="h4">Individual Honours Data Status</h2>' + pendingBlock("Individual honours feed not in downloaded bundle", "Club honours are loaded. Player-level individual awards are not present in the current public bundle, so ARES does not invent them.") + '</section>';
  }

  function renderCareer(record) {
    const ares = scoreValue(record, "ares_score", 82);
    const metrics = derivedMetrics(record);
    return tabHeader("Career Intelligence", "Career arc, output, minutes, ARES trend, and market development.") +
      kpiGrid([["Current Goals", record.goals || "0", "Public beta season row"], ["Current Assists", record.assists || "0", "Public beta season row"], ["Minutes", record.minutes || "", record.role || ""], ["Peak ARES Score", ares, "Current model"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Current Season Career Row</h2>' + tableHtml(["Season", "Club", "Apps", "Starts", "Min", "G", "A", "ARES"], [["Current", record.club || "", record.appearances || "", record.starts || "", record.minutes || "", record.goals || "", record.assists || "", record.ares_score || ""]]) + '<p class="ares-chart-seeded-note">The downloaded public player bundle exposes the current public row, not full historical player event logs.</p></div>' + chartHtml("ARES Score By Season", "Current model trend anchored to ARES, market, role, and availability.", "line", "Season", "ARES Score") + '</section>' +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Career Arc Formula</h2>' + tableHtml(["Factor", "Value", "Read"], [["Age Curve", record.age_curve || "", "Current phase"], ["Role", record.role || "", "Minutes / starts profile"], ["Progressive /90", round2(metrics.progressive90), "Ball progression signal"], ["Defensive /90", round2(metrics.defensive90), "Work-rate signal"], ["Market Conviction", round1(metrics.marketFormula), "Asset direction"]]) + '</div>' + chartHtml("Minutes By Season", "Bar chart shows role volume context.", "bars", "Season", "Minutes") + '</section><section class="ares-section ares-card"><h2 class="h4">Recent Career Context Matches</h2>' + recentMatchesTable(record, 6) + profileDataNotice(record) + '</section>';
  }

  function renderProfileTab(record, active) {
    if (active === "stats") return renderStats(record);
    if (active === "market") return renderMarket(record);
    if (active === "transfers") return renderTransfers(record);
    if (active === "rumours") return renderRumours(record);
    if (active === "national-team") return renderNational(record);
    if (active === "news") return renderNews(record);
    if (active === "achievements") return renderAchievements(record);
    if (active === "career") return renderCareer(record);
    return renderOverview(record);
  }

  function applyProfileTabs(record) {
    const params = new URLSearchParams(window.location.search);
    const playerId = params.get("id") || params.get("player_id") || record.player_id || "";
    const active = (params.get("view") || "overview").toLowerCase();
    document.body.setAttribute("data-profile-view", active);
    document.body.classList.toggle("ares-profile-view-stats", active === "stats" || active === "overview");
    document.querySelectorAll("[data-profile-view]").forEach(function (tab) {
      const view = String(tab.getAttribute("data-profile-view") || "overview").toLowerCase();
      tab.href = "profile.html?id=" + encodeURIComponent(playerId) + "&view=" + encodeURIComponent(view);
      tab.classList.toggle("is-active", view === active);
    });
    const note = document.getElementById("player-view-note");
    if (!note) return;
    note.innerHTML = renderProfileTab(record, active);
  }

  function fillPlayerImage(record) {
    const container = document.getElementById("player-photo");
    if (!container) return;
    const label = [record.player_name, record.position, record.club].filter(Boolean).join(", ");
    if (imageIsSafe(record)) {
      container.innerHTML = '<img src="' + window.AresData.safeText(assetHref(record.photo_url)) + '" alt="' + window.AresData.safeText(label) + '" loading="lazy" onerror="this.remove()">';
    } else {
      container.innerHTML = '<span>' + window.AresData.safeText(record.initials || initials(record.player_name)) + '</span><small>' + window.AresData.safeText(record.position || "") + '</small>';
      container.setAttribute("aria-label", label);
    }
    fillText("photo-source", record.photo_source || "ARES fallback");
    fillText("photo-license", record.photo_license_status || "branded_fallback");
    fillText("photo-credit", record.photo_credit || "ARES branded fallback avatar");
  }

  function setOptionalFact(id, value) {
    const element = document.getElementById(id);
    if (!element) return;
    const wrapper = element.closest("div");
    if (hasFact(value)) {
      element.textContent = value;
      if (wrapper) wrapper.hidden = false;
    } else if (wrapper) {
      wrapper.hidden = true;
    } else {
      element.textContent = "";
    }
  }

  function applyProfileIdentity(record) {
    fillText("country", playerCountry(record));
    const separator = document.querySelector(".ares-profile-separator");
    if (separator) separator.hidden = !hasFact(playerCountry(record));
    setOptionalFact("height", heightValue(record));
    setOptionalFact("foot", record.foot);
    setOptionalFact("date-of-birth", record.date_of_birth);
    setOptionalFact("joined", record.joined);
    setOptionalFact("agent", record.agent);
    setOptionalFact("outfitter", record.outfitter);
    fillText("identity-source", record.identity_source || record.source || "ARES public beta");
    fillText("stats-mode", record.stats_mode || record.score_source || "ARES beta estimate");
    fillText("transfer-value-signal", transferSignal(record));
    fillText("trend", trendDetail(record) || "Stable");
    fillText("confidence-detail", confidenceDetail(record));
  }

  function fillPlayerLinks(record) {
    const club = document.getElementById("club");
    if (club && record.club_url) {
      club.innerHTML = '<a class="ares-table-link" href="' + window.AresData.safeText(siteHref(record.club_url)) + '">' + window.AresData.safeText(record.club || "") + "</a>";
    }
    const roster = document.getElementById("player-roster-link");
    if (roster && record.club_url) {
      roster.href = siteHref(record.club_url);
      roster.hidden = false;
    }
  }

  function initProfile(dataPath, mapping) {
    Promise.all([window.AresData.loadJson(dataPath), loadProfileContext()]).then(function (payload) {
      const record = payload[0];
      window.AresProfileRows = [record];
      Object.keys(mapping).forEach(function (id) { fillText(id, record[mapping[id]]); });
      const heading = document.querySelector("h1");
      if (heading && record.player_name) heading.textContent = record.player_name + " ARES Profile";
      applyProfileIdentity(record);
      fillPlayerImage(record);
      fillPlayerLinks(record);
      renderPlayerProfileTables(record);
      applyProfileTabs(record);
    });
  }

  function showProfileMessage(message) {
    const panel = document.getElementById("profile-message");
    if (panel) {
      panel.hidden = false;
      panel.innerHTML = '<p>' + window.AresData.safeText(message) + ' <a href="index.html">Return to Player Search.</a></p>';
    }
  }

  function initProfileById(dataPath, mapping) {
    const params = new URLSearchParams(window.location.search);
    const requested = (params.get("id") || params.get("player_id") || params.get("slug") || "").trim().toLowerCase();
    if (!requested) {
      showProfileMessage("Player not found.");
      return;
    }
    Promise.all([window.AresData.loadJson(dataPath), loadProfileContext()]).then(function (payload) {
      const rows = payload[0];
      const list = Array.isArray(rows) ? rows : rows.players || [];
      window.AresProfileRows = list;
      const record = list.find(function (item) {
        return String(item.player_id || "").toLowerCase() === requested || String(item.slug || "").toLowerCase() === requested;
      });
      if (!record) {
        showProfileMessage("Player not found.");
        return;
      }
      Object.keys(mapping).forEach(function (id) { fillText(id, record[mapping[id]]); });
      const heading = document.querySelector("h1");
      if (heading && record.player_name) heading.textContent = record.player_name + " ARES Profile";
      applyProfileIdentity(record);
      fillPlayerImage(record);
      fillPlayerLinks(record);
      renderPlayerProfileTables(record);
      applyProfileTabs(record);
    }).catch(function () {
      showProfileMessage("Player not found.");
    });
  }

  function renderPlayerProfileTables(record) {
    if (!window.AresTables || !record) return;
    const season = [record];
    window.AresTables.renderTable("player-season-body", season, [
      { key: "league", label: "League" },
      { key: "club", label: "Club" },
      { key: "minutes_role", label: "Minutes / Role" },
      { key: "ares_score", label: "ARES", render: "score" },
      { key: "market_score", label: "Market", render: "market" },
      { key: "data_confidence", label: "Confidence", render: "confidence" }
    ]);
    window.AresTables.renderTable("player-role-body", season, [
      { key: "position", label: "Position" },
      { key: "position_usage", label: "Position Usage" },
      { key: "role_security", label: "Role Security" },
      { key: "durability", label: "Durability" },
      { key: "trend", label: "Trend", render: "trend" }
    ]);
    window.AresTables.renderTable("player-market-body", season, [
      { key: "market_tier", label: "Market Tier", render: "tier" },
      { key: "transfer_value_signal", label: "Transfer Signal" },
      { key: "contract_end", label: "Contract End" },
      { key: "reason", label: "Market Note" }
    ]);
  }

  function initClubProfileById(clubsPath, playersPath, mapping) {
    const params = new URLSearchParams(window.location.search);
    const requested = (params.get("id") || params.get("club_id") || params.get("slug") || "").trim().toLowerCase();
    if (!requested) {
      showProfileMessage("Club not found.");
      return;
    }
    Promise.all([window.AresData.loadJson(clubsPath), window.AresData.loadJson(playersPath)]).then(function (payload) {
      const clubs = Array.isArray(payload[0]) ? payload[0] : payload[0].clubs || [];
      const players = Array.isArray(payload[1]) ? payload[1] : payload[1].players || [];
      const club = clubs.find(function (item) {
        return String(item.club_id || "").toLowerCase() === requested || String(item.club_name || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") === requested;
      });
      if (!club) {
        showProfileMessage("Club not found.");
        return;
      }
      Object.keys(mapping).forEach(function (id) { fillText(id, club[mapping[id]]); });
      const heading = document.querySelector("h1");
      if (heading && club.club_name) heading.textContent = club.club_name + " Portfolio";
      const roster = players.filter(function (player) {
        return player.club_id === club.club_id || player.club === club.club_name;
      }).sort(function (left, right) { return Number(right.market_score || 0) - Number(left.market_score || 0); });
      window.AresTables.renderTable("club-roster-body", roster, [
        { key: "player_name", label: "Player", render: "playerLink", pathPrefix: "../", showAvatar: true },
        { key: "age", label: "Age" },
        { key: "position", label: "Position" },
        { key: "minutes_role", label: "Minutes / Role" },
        { key: "ares_score", label: "ARES", render: "score" },
        { key: "market_score", label: "Market", render: "market" },
        { key: "market_tier", label: "Tier", render: "tier" },
        { key: "trend", label: "Trend", render: "trend" },
        { key: "data_confidence", label: "Confidence", render: "confidence" }
      ]);
      window.AresTables.renderTable("club-u23-body", roster.filter(function (player) { return Number(player.age) <= 23; }), [
        { key: "player_name", label: "Player", render: "playerLink", pathPrefix: "../", showAvatar: true },
        { key: "age", label: "Age" },
        { key: "position", label: "Position" },
        { key: "market_score", label: "Market", render: "market" },
        { key: "reason", label: "Reason" }
      ]);
    }).catch(function () {
      showProfileMessage("Club not found.");
    });
  }

  window.AresSoccer = { initTable, initSearch, initProfile, initProfileById, initClubProfileById };
}(window));
