(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function isHomePage() {
    var path = window.location.pathname.replace(/\/+$/, "") || "/";
    return path === "/" || path === "/index.html";
  }

  function resolveHref(href) {
    if (!href) return href;
    if (href.charAt(0) === "#" && !isHomePage()) {
      return "/" + href;
    }
    return href;
  }

  function currentPath() {
    return window.location.pathname.replace(/\/+$/, "") || "/";
  }

  function isCurrentLink(href) {
    var resolved = resolveHref(href);
    if (!resolved) return false;
    if (resolved.charAt(0) === "#") return false;
    var path = currentPath();
    if (resolved === path) return true;
    if (path === "/blog" && resolved === "/blog") return true;
    if (path === "/media" && resolved === "/media") return true;
    if (path === "/membership" && resolved === "/membership") return true;
    return false;
  }

  function sortLinks(links) {
    return links.slice().sort(function (a, b) {
      if (b.sort_order !== a.sort_order) return b.sort_order - a.sort_order;
      return String(a.label).localeCompare(String(b.label));
    });
  }

  function renderHeader(links) {
    var nav = document.getElementById("navLinks");
    if (!nav || !links.length) return;

    nav.innerHTML = links.map(function (link) {
      var href = resolveHref(link.href);
      var cls = link.style === "cta" ? ' class="btn btn--gold nav__cta"' : "";
      var current = isCurrentLink(link.href) ? ' aria-current="page"' : "";
      return '<a href="' + esc(href) + '"' + cls + current + ">" + esc(link.label) + "</a>";
    }).join("");
  }

  function normalizeNavLabel(link) {
    if (!link) return link;
    var label = String(link.label || "");
    var href = String(link.href || "");
    if (/sign\s*in\s*(to|into)?\s*moodle/i.test(label) || (/\/moodle\/login/.test(href) && /moodle/i.test(label))) {
      return Object.assign({}, link, {
        label: "Sign In to AISkills",
        href: "/moodle/login",
        key: link.key === "moodle" ? "moodle-login" : (link.key || "moodle-login"),
      });
    }
    if (link.key === "moodle" || (href === "#moodle" || href === "/#moodle")) {
      if (/^moodle$/i.test(label.trim())) {
        return Object.assign({}, link, { label: "AISkills Program", href: "#moodle" });
      }
    }
    return link;
  }

  function isConnectLink(link) {
    return link.enabled && (
      link.key === "moodle-login" ||
      link.key === "moodle" ||
      link.key === "investor-login" ||
      link.key === "investors" ||
      link.href === "/moodle/login" ||
      link.href === "#moodle" ||
      link.href === "/#moodle"
    );
  }

  function renderFooterConnect(links) {
    var root = document.querySelector("[data-footer-connect-links]");
    if (!root || !links.length) return;
    root.innerHTML = links.map(function (link) {
      var href = resolveHref(link.href);
      return '<a href="' + esc(href) + '">' + esc(link.label) + "</a>";
    }).join("");
  }

  function renderFooter(links) {
    var root = document.querySelector("[data-footer-nav]");
    if (!root || !links.length) return;
    var heading = root.querySelector("h4");
    var headingHtml = heading ? heading.outerHTML : "<h4>Navigate</h4>";
    var anchorHtml = links.map(function (link) {
      var href = resolveHref(link.href);
      return '<a href="' + esc(href) + '">' + esc(link.label) + "</a>";
    }).join("");
    root.innerHTML = headingHtml + anchorHtml;
  }

  fetch("/api/content/navigation", { headers: { Accept: "application/json" } })
    .then(function (r) {
      if (!r.ok) throw new Error("navigation");
      return r.json();
    })
    .then(function (data) {
      if (!data || !data.links) return;
      var links = data.links.map(normalizeNavLabel);
      var headerLinks = sortLinks(
        links.filter(function (link) {
          return link.enabled && link.show_in_header;
        })
      );
      var footerLinks = sortLinks(
        links.filter(function (link) {
          return link.enabled && link.show_in_footer;
        })
      );
      var connectLinks = sortLinks(links.filter(isConnectLink));
      if (headerLinks.length) renderHeader(headerLinks);
      if (footerLinks.length) renderFooter(footerLinks);
      if (connectLinks.length) renderFooterConnect(connectLinks);
    })
    .catch(function () {});
})();
