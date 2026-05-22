(function (window, document) {
  "use strict";

  const FALLBACK_NAV = {
    menus: [
      { id: "clubs", label: "Clubs", summary: "Browse football clubs.", sidebar: [{ label: "All Clubs", href: "clubs/index.html" }], groups: [{ title: "Clubs", items: [{ label: "All Clubs", href: "clubs/index.html" }] }] },
      { id: "leagues", label: "Leagues", summary: "Browse football leagues.", sidebar: [{ label: "All Leagues", href: "leagues/index.html" }], groups: [{ title: "Leagues", items: [{ label: "All Leagues", href: "leagues/index.html" }] }] }
    ]
  };

  function safeText(value) {
    return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function normalizeRoot(root) {
    if (!root || root === ".") return "";
    return root.replace(/\/+$/, "") + "/";
  }

  function href(root, path) {
    if (!path) return "#";
    if (/^https?:\/\//i.test(path)) return path;
    return normalizeRoot(root) + String(path).replace(/^\/+/, "");
  }

  function detectRoot(header) {
    const explicit = header.getAttribute("data-ares-root");
    if (explicit) return explicit;
    const brand = header.querySelector(".ares-brand");
    const brandHref = brand ? brand.getAttribute("href") || "" : "";
    return brandHref.indexOf("../") === 0 ? ".." : ".";
  }

  function activeMenuId() {
    const path = window.location.pathname.toLowerCase();
    if (path.includes("/clubs/")) return "clubs";
    if (path.includes("/leagues/asia")) return "asia";
    if (path.includes("/leagues/mls")) return "mls";
    if (path.includes("/leagues/north-america")) return "north-america";
    if (path.includes("/leagues/")) return "leagues";
    if (path.includes("/transfers/")) return "transfers";
    if (path.includes("/watchlist/")) return "watchlist";
    if (path.includes("/players/")) return "players";
    if (path.includes("/rankings/market")) return "market-rankings";
    if (path.includes("/rankings/ares")) return "ares-rankings";
    if (path.includes("methodology") || path.includes("about")) return "methodology";
    return "home";
  }

  function initials(label, abbr) {
    return (abbr || String(label || "AR").split(/\s+/).map(function (word) { return word[0]; }).join("")).slice(0, 3).toUpperCase();
  }

  function icon(item) {
    return '<span class="ares-mega-icon" aria-hidden="true">' + safeText(initials(item.label, item.abbr)) + "</span>";
  }

  function renderItems(root, items) {
    return (items || []).map(function (item) {
      return '<a class="ares-mega-link" href="' + safeText(href(root, item.href)) + '">' + icon(item) + '<span>' + safeText(item.label) + "</span></a>";
    }).join("");
  }

  function renderMenu(root, menu, activeId) {
    const groups = (menu.groups || []).map(function (group) {
      return '<section class="ares-mega-group"><h3>' + safeText(group.title) + '</h3><div class="ares-mega-links">' + renderItems(root, group.items) + "</div></section>";
    }).join("");
    const active = menu.id === activeId ? " is-active" : "";
    const footer = menu.footer ? '<a class="ares-mega-footer" href="' + safeText(href(root, menu.footer.href)) + '">' + safeText(menu.footer.label) + "</a>" : "";
    return '<div class="ares-menu' + active + '" data-ares-menu="' + safeText(menu.id) + '">' +
      '<button class="ares-menu-button" type="button" aria-expanded="false">' + safeText(menu.label) + '<span aria-hidden="true">v</span></button>' +
      '<div class="ares-mega-panel" role="menu">' +
      '<aside class="ares-mega-sidebar"><strong>' + safeText(menu.label) + '</strong><p>' + safeText(menu.summary || "") + '</p><div>' + renderItems(root, menu.sidebar || []) + '</div></aside>' +
      '<div class="ares-mega-groups">' + groups + '</div>' + footer +
      '</div></div>';
  }

  function closeMenus(header) {
    header.querySelectorAll(".ares-menu.is-open").forEach(function (menu) {
      menu.classList.remove("is-open");
      const button = menu.querySelector(".ares-menu-button");
      if (button) button.setAttribute("aria-expanded", "false");
    });
  }

  function wire(header) {
    const toggle = header.querySelector(".ares-nav-toggle");
    const nav = header.querySelector(".ares-mega-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        const open = header.classList.toggle("is-mobile-open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }
    header.querySelectorAll(".ares-menu").forEach(function (menu) {
      const button = menu.querySelector(".ares-menu-button");
      function open() {
        closeMenus(header);
        menu.classList.add("is-open");
        if (button) button.setAttribute("aria-expanded", "true");
      }
      if (button) button.addEventListener("click", function (event) {
        event.stopPropagation();
        const alreadyOpen = menu.classList.contains("is-open");
        closeMenus(header);
        if (!alreadyOpen) open();
      });
      menu.addEventListener("mouseenter", open);
      menu.addEventListener("mouseleave", function () {
        if (!window.matchMedia("(max-width: 768px)").matches) closeMenus(header);
      });
    });
    document.addEventListener("click", function (event) {
      if (!header.contains(event.target)) closeMenus(header);
    });
  }

  function mount(header, data) {
    const root = detectRoot(header);
    const nav = header.querySelector(".ares-nav");
    const brand = header.querySelector(".ares-brand");
    if (!nav) return;
    header.classList.add("ares-mega-topbar");
    nav.classList.add("ares-mega-nav");
    nav.id = nav.id || "ares-mega-nav";
    if (!header.querySelector(".ares-nav-toggle")) {
      const toggle = document.createElement("button");
      toggle.className = "ares-nav-toggle";
      toggle.type = "button";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-controls", nav.id);
      toggle.textContent = "Menu";
      header.insertBefore(toggle, nav);
    }
    const activeId = activeMenuId();
    if (brand) brand.setAttribute("href", href(root, "index.html"));
    nav.innerHTML = '<a class="ares-home-link' + (activeId === "home" ? " is-active" : "") + '" href="' + safeText(href(root, "index.html")) + '">Home</a>' +
      (data.menus || FALLBACK_NAV.menus).map(function (menu) { return renderMenu(root, menu, activeId); }).join("");
    wire(header);
  }

  function init() {
    const header = document.querySelector(".ares-topbar");
    if (!header) return;
    const root = detectRoot(header);
    fetch(href(root, "data/navigation.json"), { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("navigation unavailable");
        return response.json();
      })
      .then(function (data) { mount(header, data); })
      .catch(function () { mount(header, FALLBACK_NAV); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
}(window, document));
