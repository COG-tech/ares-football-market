(function (window) {
  "use strict";

  const data = window.AresData;

  function resultLabel(item) {
    if (item.player_name) {
      return item.player_name + (item.position ? " (" + item.position + ")" : "");
    }
    return item.team || item.school || item.league || item.id || "Result";
  }

  function resultMeta(item) {
    return [item.type, item.team, item.school, item.league].filter(Boolean).join(" | ");
  }

  function matchesQuery(item, query) {
    return [
      item.player_name,
      item.team,
      item.school,
      item.league,
      item.position,
      item.keywords
    ].filter(Boolean).join(" ").toLowerCase().includes(query);
  }

  async function init(options) {
    const input = document.getElementById(options.inputId);
    const results = document.getElementById(options.resultsId);
    if (!input || !results) {
      return;
    }

    const items = options.items || await data.loadJson(options.dataPath || "data/player_search.json");

    function closeResults() {
      results.classList.remove("is-open");
      results.innerHTML = "";
    }

    input.addEventListener("input", function () {
      const query = input.value.trim().toLowerCase();
      if (query.length < 2) {
        closeResults();
        return;
      }

      const matches = items.filter(function (item) {
        return matchesQuery(item, query);
      }).slice(0, options.limit || 6);

      if (!matches.length) {
        results.innerHTML = "<div>No placeholder matches found.</div>";
        results.classList.add("is-open");
        return;
      }

      results.innerHTML = matches.map(function (item) {
        const label = resultLabel(item);
        const meta = resultMeta(item);
        const url = item.url || "#";
        return '<a href="' + data.safeText(url) + '"><strong>' + data.safeText(label) + "</strong><small>" + data.safeText(meta) + "</small></a>";
      }).join("");
      results.classList.add("is-open");
    });

    document.addEventListener("click", function (event) {
      if (!results.contains(event.target) && event.target !== input) {
        closeResults();
      }
    });
  }

  window.AresSearch = {
    init: init
  };
}(window));
