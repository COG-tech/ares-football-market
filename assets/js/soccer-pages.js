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
    return '<div class="table-responsive"><table class="ares-table"><thead><tr>' + headers.map(function (header) {
      return '<th>' + safe(header) + '</th>';
    }).join("") + '</tr></thead><tbody>' + rows.map(function (row) {
      return '<tr>' + row.map(function (cell) { return '<td>' + safe(cell) + '</td>'; }).join("") + '</tr>';
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
    return '<div class="ares-role-donut"><div><strong>' + safe(minutes ? minutes[0] : "2610") + '</strong><span>Total Minutes</span></div></div><ul class="ares-role-legend"><li><b></b>' + safe(record.position || "Primary") + ' 85%</li><li><b></b>Secondary Role 12%</li><li><b></b>Other Forward 3%</li></ul>';
  }

  function pitchUsage(record) {
    return '<div class="ares-pitch-map"><div class="zone zone-top"><strong>' + safe(record.position || "CF") + '</strong><span>85%</span></div><div class="zone zone-mid"><strong>SS</strong><span>12%</span></div><div class="zone zone-low"><strong>OF</strong><span>3%</span></div></div>';
  }

  function formStrip(record) {
    const ares = scoreValue(record, "ares_score", 82);
    const values = [ares - 10, ares - 2, ares - 14, ares - 1, ares - 19, ares - 6, ares + 1, ares - 5, ares - 12, ares - 3];
    return '<div class="ares-form-chart"><div class="ares-form-line"></div>' + values.map(function (value, index) {
      const y = Math.max(10, Math.min(78, 90 - value));
      return '<span style="left:' + (4 + index * 10) + '%;top:' + y + '%"><b>' + safe((value / 10).toFixed(1)) + '</b></span>';
    }).join("") + '</div><p class="ares-muted-note">ARES Form is a proprietary rating out of 10 based on performance impact.</p>';
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

  function syntheticRows(record) {
    const ares = scoreValue(record, "ares_score", 82);
    const market = scoreValue(record, "market_score", 80);
    return {
      recentMatches: [
        ["May 10", record.league || "League", "Opponent A", 90, 1, 0, (ares / 10).toFixed(1)],
        ["May 03", record.league || "League", "Opponent B", 86, 0, 1, ((ares - 2) / 10).toFixed(1)],
        ["Apr 27", record.league || "League", "Opponent C", 78, 0, 0, ((ares - 4) / 10).toFixed(1)]
      ],
      comparable: [
        [playerLabel(record), record.age || "", record.club || "", record.position || "", ares, market, "Reference"],
        ["Similar profile A", Math.max(18, Number(record.age || 24) - 1), record.league || "", record.position || "", (ares - 1.8).toFixed(1), (market - 1.2).toFixed(1), "86%"],
        ["Similar profile B", Number(record.age || 24) + 2, record.continent || "", record.position || "", (ares - 3.1).toFixed(1), (market - 2.7).toFixed(1), "81%"]
      ]
    };
  }

  function renderOverview(record) {
    const rows = syntheticRows(record);
    const ares = scoreValue(record, "ares_score", 82);
    const market = scoreValue(record, "market_score", 80);
    return '<section class="ares-profile-dashboard">' +
      numberedCard(1, "Player Identity", statList([["Full Name", playerLabel(record)], ["Date of Birth", record.date_of_birth || "Source review"], ["Nationality", record.country || ""], ["Citizenship", record.country || ""], ["Position", record.position || ""], ["Other Position", "Secondary role review"], ["Foot", record.foot || "Source review"], ["Current Club", record.club || ""], ["League", record.league || ""], ["Contract Until", record.contract_end || "Source review"]])) +
      numberedCard(2, "ARES Performance Snapshot", '<div class="ares-snapshot-grid">' + scoreDial(ares, record.ares_tier || "Role Grade") + statList([["Position Rank", "#1 / 104", record.position || ""], ["Minutes / Role", record.minutes_role || ""], ["Goal Threat", Math.round(ares) + " /100"], ["Link-Up Play", Math.max(50, Math.round(ares - 5)) + " /100"], ["Aerial Value", Math.max(50, Math.round(ares - 4)) + " /100"], ["Pressing Impact", Math.max(40, Math.round(ares - 13)) + " /100"]]) + '<div><h3 class="ares-mini-heading">Minutes By Role</h3>' + minutesByRole(record) + '</div></div><a class="ares-inline-cta" href="profile.html?id=' + safe(record.player_id || "") + '&view=stats">View Detailed Performance -&gt;</a>', "span-2") +
      numberedCard(3, "Market Intelligence", '<div class="ares-market-intel-grid">' + statList([["Estimated Value Band", record.market_tier || "Model view"], ["Peak Value", "Model view"], ["Age Curve", record.age_curve || ""], ["Contract Signal", record.contract_end || ""], ["Durability Risk", record.durability || ""], ["League Strength", record.league || ""], ["Asset Risk", record.transfer_value_signal || "Stable"]]) + marketMiniTrend(record) + '</div>', "span-2") +
      numberedCard(4, "Position Usage", pitchUsage(record)) +
      numberedCard(5, "ARES Form Trend (Last 10 Matches)", formStrip(record), "span-2") +
      numberedCard(6, "Attacker Component Grades", metricBars([["Finishing", Math.round(ares)], ["Shot Quality", Math.round(market)], ["Chance Volume", Math.max(50, Math.round(ares - 6))], ["Link-Up Play", Math.max(50, Math.round(ares - 7))], ["Box Movement", Math.max(50, Math.round(market - 4))], ["Aerial Threat", Math.max(50, Math.round(ares - 4))], ["Pressing Impact", Math.max(40, Math.round(ares - 13))]])) +
      numberedCard(7, "Recent Matches", tableHtml(["Date", "Comp", "Opponent", "Score", "Min", "G", "A", "ARES"], rows.recentMatches.map(function (row, index) { return [row[0], row[1], row[2], index === 0 ? "1-1" : index === 1 ? "4-0" : "2-1", row[3], row[4], row[5], row[6]]; })), "span-2") +
      numberedCard(8, "Comparable Players", tableHtml(["Player", "Age", "Club", "Position", "ARES Score", "Market Score", "Similarity"], rows.comparable), "span-2") +
      '</section>';
  }

  function renderStats(record) {
    const rows = syntheticRows(record);
    const minutes = String(record.minutes_role || "").match(/\d+/);
    const minuteValue = minutes ? minutes[0] : "2604";
    return tabHeader("Stats Center", "Season performance center with per-role output, component grades, trend, and availability.") +
      kpiGrid([["Appearances", record.appearances || "32", "Season involvement"], ["Minutes", minuteValue, "Role volume"], ["Goals", record.goals || "Source review", "Output signal"], ["Assists", record.assists || "Source review", "Creation signal"]]) +
      kpiGrid([["Goals / 90", record.goals_per90 || "Model view", "Public output estimate"], ["xG / 90", record.xg_per90 || "Model view", "Chance quality estimate"], ["ARES Score", record.ares_score || "", "Performance quality"], ["Position Rank", record.position || "", "Role family"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Performance Summary</h2>' + tableHtml(["Metric", "Value"], [["ARES Score", record.ares_score || ""], ["Role Grade", record.ares_tier || ""], ["Minutes / Role", record.minutes_role || ""], ["Goal Threat", Math.round(scoreValue(record, "ares_score", 82))], ["Link-Up Play", Math.max(50, Math.round(scoreValue(record, "ares_score", 82) - 4))]]) + '</div>' + chartHtml("ARES Match Trend", "Line chart of recent ARES match grades.", "line", "Match 1 to Match 10", "ARES match grade") + '</section>' +
      '<section class="ares-section table-grid"><div class="ares-card"><h2 class="h4">Competition Split</h2>' + tableHtml(["Competition", "Min", "Goals", "Assists", "ARES"], [[record.league || "League", minuteValue, record.goals || "Model", record.assists || "Model", record.ares_score || ""], ["Cup", "180", "Model", "Model", (scoreValue(record, "ares_score", 82) - 1).toFixed(1)], ["Continental", "420", "Model", "Model", (scoreValue(record, "ares_score", 82) - 2).toFixed(1)]]) + '</div><div class="ares-card"><h2 class="h4">Component Grades</h2>' + metricBars([["Finishing", scoreValue(record, "ares_score", 82)], ["Shot Quality", scoreValue(record, "market_score", 80)], ["Chance Volume", scoreValue(record, "ares_score", 82) - 6], ["Pressing Impact", scoreValue(record, "ares_score", 82) - 10]]) + '</div></section>' +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Goals By Minute", "Area chart groups output into match time bands.", "bars", "Minute band", "Goal share") + chartHtml("Position Usage", "Pitch-map style view of primary and secondary roles.", "scatter", "Pitch zone", "Usage share") + '</section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Recent Match Log</h2>' + tableHtml(["Date", "Competition", "Opponent", "Min", "G", "A", "ARES"], rows.recentMatches) + '</section><section class="ares-section ares-card"><h2 class="h4">Availability / Absences</h2><p>Durability: ' + safe(record.durability || "Source review") + ' | Injury risk: source review | Confidence: ' + safe(record.data_confidence || "") + '</p></section>';
  }

  function renderMarket(record) {
    return tabHeader("Market Value Intelligence", "Value logic, age curve, contract signal, and transfer movement.") +
      kpiGrid([["Market Score", record.market_score || "", record.market_tier || "Asset value"], ["ARES Score", record.ares_score || "", record.ares_tier || "Quality"], ["Transfer Signal", record.transfer_value_signal || "Stable", "Movement"], ["Data Confidence", record.data_confidence || "", "Coverage"]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Estimated Value Trend", "Line-area model for public market direction, not a fee claim.", "line", "Season", "Market Score") + '<div class="ares-card"><h2 class="h4">Market Value Summary</h2>' + tableHtml(["Field", "Value"], [["Estimated Value Band", record.market_tier || ""], ["Peak Value", "Model view"], ["Age Curve", record.age_curve || ""], ["Contract Signal", record.contract_end || ""], ["League Strength", record.league || ""]]) + '</div></section>' +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Market Score Breakdown</h2>' + metricBars([["ARES Quality", scoreValue(record, "ares_score", 82)], ["Age Curve", Number(record.age || 25) <= 23 ? 92 : 76], ["Position Scarcity", scoreValue(record, "market_score", 80)], ["League Strength", 84], ["Role Security", scoreValue(record, "ares_score", 82) - 5]]) + '</div>' + chartHtml("Age Curve", "Line chart shows how asset value changes across age bands.", "line", "Age band", "Market curve") + '</section>' +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Comparable Market Assets", "Scatter compares ARES quality against football asset value.", "scatter", "ARES Score", "Market Score") + chartHtml("Transfer Value Signal", "Gauge-style board groups sell, hold, buy, watch, and risk outcomes.", "bars", "Signal type", "Signal strength") + '</section><section class="ares-section ares-card"><h2 class="h4">Recent Market Updates</h2>' + tableHtml(["Date", "Update", "Change", "Reason", "Signal"], [[record.last_updated || "Source review", "Market model refresh", record.trend_value || "Model view", record.reason || "ARES beta score review", record.transfer_value_signal || "Stable"], ["Prior window", "Role and age curve reviewed", "Model view", record.age_curve || "Source review", record.trend || "Stable"]]) + '</section><section class="ares-section ares-card"><h2 class="h4">Club Fit / Market Outlook</h2><p>Ideal context: ' + safe(record.league || "League fit review") + ' | Risk level: ' + safe(record.durability || "Source review") + ' | Signal: ' + safe(record.transfer_value_signal || "Stable") + '</p></section>';
  }

  function renderTransfers(record) {
    return tabHeader("Transfer Intelligence", "Transfer history, contract window, resale runway, and comparable moves.") +
      kpiGrid([["Last Major Move", record.club || "Current club"], ["Contract Window", record.contract_end || "Source review"], ["Resale Runway", Number(record.age || 25) <= 23 ? "Long" : "Medium"], ["Transfer Signal", record.transfer_value_signal || "Stable"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Transfer History</h2>' + tableHtml(["Date", "From", "To", "Fee", "Age", "Signal"], [["Current", "Source review", record.club || "", "Model view", record.age || "", record.transfer_value_signal || "Stable"], ["Prior", "Development club", record.club || "", "Source review", Math.max(16, Number(record.age || 24) - 2), "Development"]]) + '</div>' + chartHtml("Transfer Value At Move", "Timeline chart places each move against age and value signal.", "line", "Move date", "Value signal") + '</section>' +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Contract Window", "Countdown bar highlights when leverage changes.", "bars", "Contract year", "Leverage") + chartHtml("Comparable Transfers", "Bubble chart compares age, fee context, and ARES score.", "scatter", "Age", "ARES / fee context") + '</section><section class="ares-section ares-card"><h2 class="h4">Transfer Logic</h2><p>Positive: role security, league context, ARES quality, and data confidence. Risks: age curve, contract timing, wage load, and availability.</p></section>';
  }

  function renderRumours(record) {
    return tabHeader("Rumour Intelligence", "Controlled analytical rumour view. Live rumour feeds are not connected.") +
      kpiGrid([["Strongest Link", record.league || "Club fit"], ["Highest Fit Club", record.club || ""], ["Signal Strength", "Medium"], ["Reliability", "Seeded beta"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Rumour Table</h2>' + tableHtml(["Club", "League", "Signal", "Fit", "Reliability"], [[record.club || "Current club", record.league || "", "Hold", "78", "Seeded beta"], ["Comparable club A", record.continent || "", "Low", "66", "Seeded beta"], ["Comparable club B", record.region || "", "Medium", "72", "Seeded beta"]]) + '</div>' + chartHtml("Rumour Signal Timeline", "Line chart tracks seeded signal strength by week.", "line", "Week", "Signal strength") + '</section>' +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Club Fit Radar", "Radar-style card compares role, club need, league, cost, and age.", "bars", "Fit factor", "Fit score") + chartHtml("Fit Score vs Signal Strength", "Scatter separates club fit from movement signal.", "scatter", "Fit Score", "Signal Strength") + '</section><section class="ares-section ares-card"><h2 class="h4">Rumour Logic</h2><p>Signal Strength = club need + contract timing + role fit + market movement. This is not live gossip.</p></section>';
  }

  function renderNational(record) {
    return tabHeader("National Team Profile", "International role, tournament value, national-team output, and squad importance.") +
      kpiGrid([["Caps", record.caps || "Source review"], ["Goals", record.international_goals || "Source review"], ["Debut", record.international_debut || "Source review"], ["Tournaments", record.tournaments || "Source review"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">International Summary</h2>' + tableHtml(["Field", "Value"], [["Country", record.country || ""], ["Role", record.position || ""], ["International ARES", (scoreValue(record, "ares_score", 82) - 1.5).toFixed(1)], ["Tournament Value", record.market_tier || ""], ["Squad Importance", record.ares_tier || ""]]) + '</div>' + chartHtml("Goals By Year", "Line chart shows international output by year when connected.", "line", "Year", "Goals") + '</section>' +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Tournament Record</h2>' + tableHtml(["Tournament", "Apps", "Goals", "ARES", "Stage"], [["Continental", "Source review", "Source review", record.ares_score || "", "Source review"], ["World", "Source review", "Source review", (scoreValue(record, "ares_score", 82) - 2).toFixed(1), "Source review"]]) + '</div>' + chartHtml("Caps Timeline", "Bar chart groups international caps by year.", "bars", "Year", "Caps") + '</section><section class="ares-section ares-card"><h2 class="h4">Recent International Matches</h2>' + tableHtml(["Date", "Opponent", "Comp", "Min", "Goals", "Assists", "ARES"], [["Source review", "Source review", "International", "Source review", "Source review", "Source review", record.ares_score || ""]]) + '</section>';
  }

  function renderNews(record) {
    return tabHeader("Player News Terminal", "Player notes, club notes, market notes, injury notes, and transfer notes translated into signal impact.") +
      kpiGrid([["Latest Note", "Performance"], ["Market Impact", record.trend || "Stable"], ["Availability", record.durability || "Source review"], ["Transfer Impact", record.transfer_value_signal || "Stable"]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("News Impact Timeline", "Line chart tracks ARES, market, and risk impact from notes.", "line", "Note date", "Impact score") + '<div class="ares-card"><h2 class="h4">Category Filters</h2><p>Market Notes | Club Notes | Injury / Availability | Transfer Notes</p></div></section>' +
      '<section class="ares-section ares-card"><h2 class="h4">News Cards</h2>' + tableHtml(["Date", "Category", "Headline", "Impact", "Confidence"], [["May 06", "Market", "Value adjusted to current signal", "Market", record.data_confidence || ""], ["Apr 27", "Form", "Strong recent performance window", "ARES", record.data_confidence || ""], ["Apr 15", "Club", "Contract and role context reviewed", "Signal", record.data_confidence || ""]]) + '</section><section class="ares-section ares-card"><h2 class="h4">News Signal Summary</h2><p>Current effect: no major downgrade | Market Signal: ' + safe(record.trend || "Stable") + ' | Availability: ' + safe(record.durability || "Source review") + '</p></section>';
  }

  function renderAchievements(record) {
    return tabHeader("Achievements", "Team honours, individual honours, milestones, and ARES career badges.") +
      kpiGrid([["Team Honours", record.team_honours || "Source review"], ["Individual Honours", record.individual_honours || "Source review"], ["Golden Boots", record.golden_boots || "Source review"], ["ARES Badges", "4", "Career context"]]) +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Honours Timeline", "Timeline chart places honours across career phases.", "line", "Year", "Honour count") + chartHtml("Achievement By Career Phase", "Stacked bar groups breakout, peak, and current phase achievements.", "bars", "Career phase", "Achievement count") + '</section>' +
      '<section class="ares-section ares-card"><h2 class="h4">Achievement Table</h2>' + tableHtml(["Year", "Honour", "Club / Country", "Type", "Career Phase"], [["Source review", "Club honour", record.club || "", "Team", record.age_curve || ""], ["Source review", "ARES high-minutes player", record.club || "", "ARES badge", "Current"], ["Source review", "Market asset watch", record.country || "", "ARES badge", "Current"]]) + '</section><section class="ares-section ares-card"><h2 class="h4">ARES Career Badges</h2><p>Elite output | High-minutes player | Club asset | Market signal</p></section>';
  }

  function renderCareer(record) {
    const ares = scoreValue(record, "ares_score", 82);
    return tabHeader("Career Intelligence", "Career arc, output, minutes, ARES trend, and market development.") +
      kpiGrid([["Career Goals", record.career_goals || "Source review"], ["Career Assists", record.career_assists || "Source review"], ["Seasons Played", record.seasons_played || "Source review"], ["Peak ARES Score", ares, "Current model"]]) +
      '<section class="ares-section ares-terminal-grid"><div class="ares-card"><h2 class="h4">Season-by-Season Career Table</h2>' + tableHtml(["Season", "Club", "Apps", "Min", "G", "A", "ARES"], [["2025/26", record.club || "", "Source review", record.minutes_role || "", "Model", "Model", record.ares_score || ""], ["2024/25", record.club || "", "Source review", "Source review", "Model", "Model", (ares - 1.2).toFixed(1)], ["2023/24", record.club || "", "Source review", "Source review", "Model", "Model", (ares - 2.4).toFixed(1)]]) + '</div>' + chartHtml("ARES Score By Season", "Line chart tracks player quality by season.", "line", "Season", "ARES Score") + '</section>' +
      '<section class="ares-section ares-terminal-grid">' + chartHtml("Market Score By Season", "Line-area chart tracks market score and asset direction.", "line", "Season", "Market Score") + chartHtml("Goals By Season", "Bar chart groups output by season.", "bars", "Season", "Goals") + '</section><section class="ares-section ares-terminal-grid">' + chartHtml("Minutes By Season", "Bar chart shows role volume by season.", "bars", "Season", "Minutes") + '<div class="ares-card"><h2 class="h4">Career Arc</h2><p>Breakout: source review | Peak: source review | Current phase: ' + safe(record.age_curve || "Source review") + '</p></div></section><section class="ares-section ares-card"><h2 class="h4">Club History | National Team Career | Career Badges</h2><p>Career modules use sourced profile data where available and keep estimates labelled as seeded beta context.</p></section>';
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
    window.AresData.loadJson(dataPath).then(function (record) {
      Object.keys(mapping).forEach(function (id) { fillText(id, record[mapping[id]]); });
      const heading = document.querySelector("h1");
      if (heading && record.player_name) heading.textContent = record.player_name + " ARES Profile";
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
    window.AresData.loadJson(dataPath).then(function (rows) {
      const list = Array.isArray(rows) ? rows : rows.players || [];
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
