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

  function initProfile(dataPath, mapping) {
    window.AresData.loadJson(dataPath).then(function (record) {
      Object.keys(mapping).forEach(function (id) { fillText(id, record[mapping[id]]); });
      const heading = document.querySelector("h1");
      if (heading && record.player_name) heading.textContent = record.player_name + " ARES Profile";
      fillPlayerImage(record);
      renderPlayerProfileTables(record);
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
      renderPlayerProfileTables(record);
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
