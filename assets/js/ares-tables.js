(function (window) {
  "use strict";

  const data = window.AresData;
  const tableStates = {};

  function getStateByTable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
      return null;
    }
    const tbody = table.querySelector("tbody");
    if (!tbody || !tbody.id) {
      return null;
    }
    return tableStates[tbody.id] || null;
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
    const className = key === "up" ? "ares-trend-up" : key === "down" ? "ares-trend-down" : "ares-trend-flat";
    return '<span class="' + className + '">' + trend + "</span>";
  }

  function renderConfidenceChip(value) {
    const confidence = data.formatConfidence(value);
    const key = confidence.toLowerCase();
    const className = key === "high" ? "ares-confidence-high" : key === "medium" ? "ares-confidence-medium" : "ares-confidence-low";
    return '<span class="' + className + '">' + confidence + "</span>";
  }

  function renderLink(label, url, fallbackUrl, prefix) {
    let href = url || fallbackUrl || "#";
    if (prefix && href !== "#" && !href.match(/^(https?:)?\/\//) && !href.startsWith("../") && !href.startsWith("/")) {
      href = prefix + href;
    }
    return '<a href="' + data.safeText(href) + '">' + data.safeText(label) + "</a>";
  }

  function renderCell(row, column) {
    const value = row[column.key];
    if (typeof column.render === "function") {
      return column.render(value, row, column);
    }
    if (column.render === "score") {
      return renderScoreChip(value, column.scoreType || "ares");
    }
    if (column.render === "market") {
      return renderScoreChip(value, "market");
    }
    if (column.render === "tier") {
      return renderTierChip(value);
    }
    if (column.render === "trend") {
      return renderTrendChip(value);
    }
    if (column.render === "confidence") {
      return renderConfidenceChip(value);
    }
    if (column.render === "playerLink") {
      return renderLink(value, row.player_url || row.url, column.fallbackUrl || "players/player-template.html", column.pathPrefix);
    }
    if (column.render === "clubLink") {
      return renderLink(value, row.club_url, column.fallbackUrl || "clubs/club-template.html", column.pathPrefix);
    }
    if (column.render === "leagueLink") {
      return renderLink(value, row.league_url, column.fallbackUrl || "leagues/league-template.html", column.pathPrefix);
    }
    if (column.render === "link") {
      return renderLink(column.label || value || "Open", row[column.urlKey || "url"], column.fallbackUrl, column.pathPrefix);
    }
    return data.safeText(value);
  }

  function rowMatches(row, columns, query) {
    if (!query) {
      return true;
    }
    return columns
      .map(function (column) {
        return row[column.key];
      })
      .join(" ")
      .toLowerCase()
      .includes(query);
  }

  function sortedRows(rows, state) {
    if (!state.sort || !state.sort.key) {
      return rows.slice();
    }
    const factor = state.sort.direction === "desc" ? -1 : 1;
    const key = state.sort.key;
    const type = state.sort.type || "text";
    return rows.slice().sort(function (leftRow, rightRow) {
      const left = type === "number" ? Number(leftRow[key] || 0) : String(leftRow[key] || "").toLowerCase();
      const right = type === "number" ? Number(rightRow[key] || 0) : String(rightRow[key] || "").toLowerCase();
      if (left < right) {
        return -1 * factor;
      }
      if (left > right) {
        return 1 * factor;
      }
      return 0;
    });
  }

  function updateCount(tbody, count) {
    const table = tbody.closest("table");
    const countId = table ? table.dataset.countId : "";
    const countElement = countId ? document.getElementById(countId) : null;
    if (countElement) {
      countElement.textContent = count + " rows";
    }
  }

  function renderTable(containerId, rows, columns) {
    const tbody = document.getElementById(containerId);
    if (!tbody) {
      return;
    }
    const existingState = tableStates[containerId] || {};
    const state = Object.assign(existingState, {
      rows: Array.isArray(rows) ? rows : [],
      columns: columns || existingState.columns || []
    });
    tableStates[containerId] = state;

    const query = state.query || "";
    const visibleRows = sortedRows(
      state.rows.filter(function (row) {
        return rowMatches(row, state.columns, query);
      }),
      state
    );

    tbody.innerHTML = visibleRows
      .map(function (row) {
        return "<tr>" + state.columns.map(function (column) {
          return "<td>" + renderCell(row, column) + "</td>";
        }).join("") + "</tr>";
      })
      .join("");
    updateCount(tbody, visibleRows.length);
  }

  function rerenderTable(tableId) {
    const state = getStateByTable(tableId);
    if (!state) {
      return;
    }
    const table = document.getElementById(tableId);
    const tbody = table.querySelector("tbody");
    renderTable(tbody.id, state.rows, state.columns);
  }

  function makeTableSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
      return;
    }
    const tbody = table.querySelector("tbody");
    if (!tbody || !tbody.id) {
      return;
    }
    table.querySelectorAll("[data-sort]").forEach(function (button) {
      button.addEventListener("click", function () {
        const state = tableStates[tbody.id] || {};
        const key = button.dataset.sort;
        const direction = state.sort && state.sort.key === key && state.sort.direction === "asc" ? "desc" : "asc";
        state.sort = {
          key: key,
          direction: direction,
          type: button.dataset.type || "text"
        };
        tableStates[tbody.id] = state;
        rerenderTable(tableId);
      });
    });
  }

  function makeTableSearchable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    if (!input || !table) {
      return;
    }
    const tbody = table.querySelector("tbody");
    if (!tbody || !tbody.id) {
      return;
    }
    input.addEventListener("input", function () {
      const state = tableStates[tbody.id] || {};
      state.query = input.value.trim().toLowerCase();
      tableStates[tbody.id] = state;
      rerenderTable(tableId);
    });
  }

  window.AresTables = {
    renderTable: renderTable,
    makeTableSortable: makeTableSortable,
    makeTableSearchable: makeTableSearchable,
    renderScoreChip: renderScoreChip,
    renderTierChip: renderTierChip,
    renderTrendChip: renderTrendChip,
    renderConfidenceChip: renderConfidenceChip,
    renderLink: renderLink
  };
}(window));
