(function (window) {
  "use strict";

  const RENDERABLE_LICENSES = new Set(["owned", "licensed", "template_licensed", "open_license"]);
  let registryPromise = null;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function loadRegistry(path) {
    if (!registryPromise) {
      registryPromise = fetch(path, { cache: "no-store" })
        .then(function (response) {
          if (!response.ok) throw new Error("Media registry unavailable");
          return response.json();
        })
        .then(function (items) {
          return Array.isArray(items) ? items : [];
        })
        .catch(function () {
          return [];
        });
    }
    return registryPromise;
  }

  function isRenderable(item) {
    if (!item) return false;
    const status = String(item.license_status || "").toLowerCase();
    return item.public_allowed === true && RENDERABLE_LICENSES.has(status);
  }

  function mediaFor(items, entityType, entityId, mediaType) {
    const wantedType = String(entityType || "").toLowerCase();
    const wantedId = String(entityId || "").toLowerCase();
    const wantedMedia = String(mediaType || "").toLowerCase();
    return (items || []).find(function (item) {
      return String(item.entity_type || "").toLowerCase() === wantedType &&
        String(item.entity_id || "").toLowerCase() === wantedId &&
        String(item.media_type || "").toLowerCase() === wantedMedia &&
        isRenderable(item);
    }) || null;
  }

  function initials(label) {
    const words = String(label || "ARES").trim().split(/\s+/).filter(Boolean);
    if (!words.length) return "AR";
    if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
    return (words[0][0] + words[1][0]).toUpperCase();
  }

  function renderBadge(item, label, extraClass) {
    const classes = ["ares-media-badge"];
    if (extraClass) classes.push(extraClass);
    if (isRenderable(item)) {
      const src = item.local_path || item.asset_url;
      if (src) {
        return '<span class="' + classes.join(" ") + '"><img src="' + escapeHtml(src) + '" alt="' + escapeHtml(item.display_name || label || "") + '"></span>';
      }
    }
    return '<span class="' + classes.join(" ") + ' ares-media-fallback">' + escapeHtml(initials(label)) + '</span>';
  }

  window.AresMedia = {
    loadRegistry: loadRegistry,
    isRenderable: isRenderable,
    mediaFor: mediaFor,
    renderBadge: renderBadge,
    initials: initials
  };
}(window));
