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
        }
      })
      .catch(function () {
        data.showLoadError(options.errorId || options.bodyId, "Placeholder data could not be loaded.");
      });
  }

  function initSearch(inputId, resultsId, dataPath) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    if (!input || !results) {
      return;
    }

    window.AresData.loadJson(dataPath).then(function (items) {
      input.addEventListener("input", function () {
        const query = input.value.trim().toLowerCase();
        if (query.length < 2) {
          results.classList.remove("is-open");
          results.innerHTML = "";
          return;
        }
        const matches = items.filter(function (item) {
          return [
            item.player_name,
            item.club_name,
            item.club,
            item.league,
            item.position,
            item.keywords
          ].filter(Boolean).join(" ").toLowerCase().includes(query);
        }).slice(0, 6);

        results.innerHTML = matches.length ? matches.map(function (item) {
          const label = item.player_name || item.club_name || item.league || item.id || "Result";
          const meta = [item.type, item.position, item.club, item.league].filter(Boolean).join(" | ");
          const url = item.url || "#";
          return '<a href="' + window.AresData.safeText(url) + '"><strong>' + window.AresData.safeText(label) + '</strong><small>' + window.AresData.safeText(meta) + '</small></a>';
        }).join("") : "<div>No placeholder matches found.</div>";
        results.classList.add("is-open");
      });
    });
  }

  function fillText(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value === undefined || value === null ? "" : value;
    }
  }

  function initProfile(dataPath, mapping) {
    window.AresData.loadJson(dataPath).then(function (record) {
      Object.keys(mapping).forEach(function (id) {
        fillText(id, record[mapping[id]]);
      });
    });
  }

  window.AresSoccer = {
    initTable: initTable,
    initSearch: initSearch,
    initProfile: initProfile
  };
}(window));
