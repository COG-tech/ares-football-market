(function (window) {
  "use strict";

  function safeText(value) {
    if (value === null || value === undefined || value === "") {
      return "";
    }
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async function loadJson(path) {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error("Unable to load " + path);
    }
    return response.json();
  }

  function formatScore(value) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return safeText(value);
    }
    return numberValue.toFixed(1);
  }

  function formatTrend(value) {
    const trend = safeText(value).trim();
    if (!trend) {
      return "Flat";
    }
    return trend.charAt(0).toUpperCase() + trend.slice(1).toLowerCase();
  }

  function formatConfidence(value) {
    const confidence = safeText(value).trim();
    if (!confidence) {
      return "Low";
    }
    return confidence.charAt(0).toUpperCase() + confidence.slice(1).toLowerCase();
  }

  function showLoadError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) {
      return;
    }
    container.innerHTML = '<div class="alert alert-warning mb-0">' + safeText(message) + "</div>";
  }

  window.AresData = {
    loadJson: loadJson,
    safeText: safeText,
    formatScore: formatScore,
    formatTrend: formatTrend,
    formatConfidence: formatConfidence,
    showLoadError: showLoadError
  };
}(window));
