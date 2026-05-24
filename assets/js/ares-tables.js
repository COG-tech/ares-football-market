(function (window) {
  "use strict";

  const data = window.AresData;
  const tableStates = {};

  function getStateByTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return null;
    const tbody = table.querySelector("tbody");
    return tbody && tbody.id ? tableStates[tbody.id] || null : null;
  }

  function renderScoreChip(value, type) {
    const className = type === "market" ? "ares-market-chip" : "ares-score-chip";
    return '<span class="' + className + '">' + data.formatScore(value) + "</span>";
  }

  function renderTierChip(value) {
    return '<span class="ares-tier-chip">' + data.safeText(value) + "</span>";
  }

  function renderTrendChip(value) {
    const trend = data.formatTrend(value);
    const key = trend.toLowerCase();
    const className = key === "up" || key === "rising" ? "ares-trend-up" : key === "down" || key === "falling" ? "ares-trend-down" : "ares-trend-flat";
    return '<span class="' + className + '">' + trend + "</span>";
  }

  function renderConfidenceChip(value) {
    const confidence = data.formatConfidence(value);
    const key = confidence.toLowerCase();
    const className = key === "high" ? "ares-confidence-high" : key === "medium" ? "ares-confidence-medium" : "ares-confidence-low";
    return '<span class="' + className + '">' + confidence + "</span>";
  }

  function renderModeBadge(value) {
    return "";
  }

  function initials(value) {
    return String(value || "AR").split(/\s+/).filter(Boolean).slice(0, 3).map(function (part) { return part.charAt(0); }).join("").toUpperCase() || "AR";
  }

  function prefixedHref(url, prefix) {
    let href = url || "#";
    if (prefix && href !== "#" && !href.match(/^(https?:)?\/\//) && !href.startsWith("../") && !href.startsWith("/")) href = prefix + href;
    return href;
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

  function imageIsSafe(row) {
    const status = String(row.photo_license_status || "").toLowerCase();
    return Boolean(row.photo_url) && ["ares_owned", "provider_supplied", "licensed_commons", "commons_licensed", "cc_by", "cc_by_sa", "public_domain", "approved_provider"].includes(status);
  }

  function renderPlayerAvatar(row) {
    const label = row.player_name || row.name || "ARES player";
    const alt = data.safeText([label, row.position, row.club].filter(Boolean).join(", "));
    // Image safety rule: only render provider-supplied or licensed image URLs already present in data.
    // Do not scrape Transfermarkt, Google Images, club sites, agency previews, or social media.
    if (imageIsSafe(row)) return '<span class="ares-player-photo"><img src="' + data.safeText(assetHref(row.photo_url)) + '" alt="' + alt + '" loading="lazy" onerror="this.remove()"></span>';
    return '<span class="ares-player-avatar-stack" title="' + alt + '"><span class="ares-player-photo" aria-label="' + alt + '">' + data.safeText(row.initials || initials(label)) + '</span><span class="ares-position-mini">' + data.safeText(row.position || "FB") + '</span><span class="ares-avatar-club">' + data.safeText(row.club || row.region || "ARES") + "</span></span>";
  }

  function renderBadge(row, type) {
    const url = type === "league" ? row.league_badge_url : row.club_badge_url;
    const label = type === "league" ? row.league_name : row.club_name;
    const fallback = initials(label || "ARES");
    const alt = data.safeText((label || "ARES") + " badge");
    if (url) return '<span class="ares-media-badge"><img src="' + data.safeText(assetHref(url)) + '" alt="' + alt + '" loading="lazy" onerror="this.remove()"></span>';
    return '<span class="ares-media-badge" aria-label="' + alt + '">' + data.safeText(fallback) + "</span>";
  }

  function renderPlayerIdentity(label, row, column) {
    const href = prefixedHref(row.player_url || row.url || column.fallbackUrl || "players/profile.html", column.pathPrefix);
    const avatar = column.showAvatar === false ? "" : renderPlayerAvatar(row);
    return '<a class="ares-player-identity" href="' + data.safeText(href) + '">' + avatar + '<span>' + data.safeText(label) + "</span></a>";
  }

  function renderLink(label, url, fallbackUrl, prefix) {
    return '<a href="' + data.safeText(prefixedHref(url || fallbackUrl || "#", prefix)) + '">' + data.safeText(label) + "</a>";
  }

  function renderCell(row, column) {
    const value = row[column.key];
    if (typeof column.render === "function") return column.render(value, row, column);
    if (column.render === "score") return renderScoreChip(value, column.scoreType || "ares");
    if (column.render === "market") return renderScoreChip(value, "market");
    if (column.render === "tier") return renderTierChip(value);
    if (column.render === "trend") return renderTrendChip(value);
    if (column.render === "confidence") return renderConfidenceChip(value);
    if (column.render === "mode") return renderModeBadge(value);
    if (column.render === "playerImage") return renderPlayerAvatar(row);
    if (column.render === "clubBadge") return renderBadge(row, "club");
    if (column.render === "leagueBadge") return renderBadge(row, "league");
    if (column.render === "playerLink") return renderPlayerIdentity(value, row, column);
    if (column.render === "clubLink") return renderLink(value, row.club_url, column.fallbackUrl || "clubs/profile.html", column.pathPrefix);
    if (column.render === "leagueLink") return renderLink(value, row.league_url, column.fallbackUrl || "leagues/league-template.html", column.pathPrefix);
    if (column.render === "link") return renderLink(column.label || value || "Open", row[column.urlKey || "url"], column.fallbackUrl, column.pathPrefix);
    return data.safeText(value);
  }

  function rowMatches(row, columns, query) {
    if (!query) return true;
    return columns.map(function (column) { return row[column.key]; }).join(" ").toLowerCase().includes(query);
  }

  function sortedRows(rows, state) {
    if (!state.sort || !state.sort.key) return rows.slice();
    const factor = state.sort.direction === "desc" ? -1 : 1;
    const key = state.sort.key;
    const type = state.sort.type || "text";
    return rows.slice().sort(function (leftRow, rightRow) {
      const left = type === "number" ? Number(leftRow[key] || 0) : String(leftRow[key] || "").toLowerCase();
      const right = type === "number" ? Number(rightRow[key] || 0) : String(rightRow[key] || "").toLowerCase();
      if (left < right) return -1 * factor;
      if (left > right) return 1 * factor;
      return 0;
    });
  }

  function updateCount(tbody, count) {
    const table = tbody.closest("table");
    const countElement = table && table.dataset.countId ? document.getElementById(table.dataset.countId) : null;
    if (countElement) countElement.textContent = count + " rows";
  }

  function renderTable(containerId, rows, columns) {
    const tbody = document.getElementById(containerId);
    if (!tbody) return;
    const existingState = tableStates[containerId] || {};
    const visibleColumns = (columns || existingState.columns || []).filter(function (column) { return column.key !== "data_mode"; });
    const state = Object.assign(existingState, { rows: Array.isArray(rows) ? rows : [], columns: visibleColumns });
    tableStates[containerId] = state;
    const visibleRows = sortedRows(state.rows.filter(function (row) { return rowMatches(row, state.columns, state.query || ""); }), state);
    if (!visibleRows.length) {
      tbody.innerHTML = '<tr><td colspan="' + Math.max(1, state.columns.length) + '">No matching rows for this filter set. Clear filters to view the full board.</td></tr>';
      updateCount(tbody, 0);
      return;
    }
    tbody.innerHTML = visibleRows.map(function (row) {
      return "<tr>" + state.columns.map(function (column) {
        const label = data.safeText(column.label || column.key || "");
        return '<td data-label="' + label + '">' + renderCell(row, column) + "</td>";
      }).join("") + "</tr>";
    }).join("");
    updateCount(tbody, visibleRows.length);
  }

  function rerenderTable(tableId) {
    const state = getStateByTable(tableId);
    if (!state) return;
    renderTable(document.getElementById(tableId).querySelector("tbody").id, state.rows, state.columns);
  }

  function makeTableSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const tbody = table.querySelector("tbody");
    if (!tbody || !tbody.id) return;
    table.querySelectorAll("[data-sort]").forEach(function (button) {
      button.addEventListener("click", function () {
        const state = tableStates[tbody.id] || {};
        const key = button.dataset.sort;
        const direction = state.sort && state.sort.key === key && state.sort.direction === "asc" ? "desc" : "asc";
        state.sort = { key: key, direction: direction, type: button.dataset.type || "text" };
        tableStates[tbody.id] = state;
        rerenderTable(tableId);
      });
    });
  }

  function makeTableSearchable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) return;
    const tbody = table.querySelector("tbody");
    if (!tbody || !tbody.id) return;
    input.addEventListener("input", function () {
      const state = tableStates[tbody.id] || {};
      state.query = input.value.trim().toLowerCase();
      tableStates[tbody.id] = state;
      rerenderTable(tableId);
    });
  }

  window.AresTables = { renderTable, makeTableSortable, makeTableSearchable, renderScoreChip, renderTierChip, renderTrendChip, renderConfidenceChip, renderLink, renderPlayerAvatar };
}(window));
