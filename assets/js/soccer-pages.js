(function (window) {
  "use strict";

  function initTable(options) {
    const data = window.AresData;
    const tables = window.AresTables;
    data.loadJson(options.dataPath)
      .then(function (rows) {
        tables.renderTable(options.bodyId, rows, options.columns);
        tables.makeTableSortable(options.tableId);
        if (options.searchId) {
          tables.makeTableSearchable(options.searchId, options.tableId);
          applyQueryFilter(options.searchId);
          const input = document.getElementById(options.searchId);
          if (input && input.value.trim()) input.dispatchEvent(new Event("input", { bubbles: true }));
        }
      })
      .catch(function () { data.showLoadError(options.errorId || options.bodyId, "Data could not be loaded."); });
  }

  function applyQueryFilter(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q") || params.get("club") || params.get("league") || params.get("country") || params.get("region") || params.get("position") || params.get("tier") || params.get("type") || "";
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
          const meta = [item.type, item.position, item.club, item.league, item.country, item.region].filter(Boolean).join(" | ");
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

  function fillPlayerImage(record) {
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

  function initProfile(dataPath, mapping) {
    window.AresData.loadJson(dataPath).then(function (record) {
      Object.keys(mapping).forEach(function (id) { fillText(id, record[mapping[id]]); });
      fillPlayerImage(record);
    });
  }

  window.AresSoccer = { initTable, initSearch, initProfile };
}(window));
