(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatDate(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  }

  var grid = document.getElementById("mediaGrid");
  var status = document.getElementById("mediaStatus");
  var filters = document.getElementById("mediaFilters");
  var allItems = [];
  var activeFilter = "all";

  function renderHeader(data) {
    var eyebrow = document.getElementById("mediaEyebrow");
    var title = document.getElementById("mediaTitle");
    var intro = document.getElementById("mediaIntro");
    if (eyebrow && data.eyebrow) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(data.eyebrow);
    }
    if (title && data.title_before) {
      title.innerHTML = esc(data.title_before) + ' <span class="grad">' + esc(data.title_highlight || "") + "</span>";
    }
    if (intro && data.intro) intro.textContent = data.intro;
    if (data.page_description) {
      var meta = document.querySelector('meta[name="description"]');
      if (meta) meta.setAttribute("content", data.page_description);
    }
  }

  function cardHtml(item) {
    var visual;
    if (item.media_type === "video") {
      if (item.thumbnail_url) {
        visual = '<img src="' + esc(item.thumbnail_url) + '" alt="" loading="lazy" class="media-card__video-thumb" />';
      } else {
        visual = '<div class="media-card__placeholder" aria-hidden="true"><svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></div>';
      }
    } else {
      visual = '<img src="' + esc(item.media_url) + '" alt="' + esc(item.title) + '" loading="lazy" />';
    }
    var badge = item.media_type === "video"
      ? '<span class="media-card__play" aria-hidden="true"><svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg></span>'
      : "";
    var meta = [];
    if (item.category) meta.push(esc(item.category));
    if (item.event_date) meta.push(formatDate(item.event_date));
    if (item.location) meta.push(esc(item.location));
    return (
      '<article class="media-card" tabindex="0" role="button" data-slug="' + esc(item.slug) + '" data-type="' + esc(item.media_type) + '">' +
        '<div class="media-card__visual">' +
          visual +
          badge +
          '<div class="media-card__shade"></div>' +
        '</div>' +
        '<div class="media-card__body">' +
          '<h3 class="media-card__title">' + esc(item.title) + '</h3>' +
          (meta.length ? '<p class="media-card__meta">' + meta.join(" · ") + '</p>' : "") +
        '</div>' +
      '</article>'
    );
  }

  function renderGrid() {
    if (!grid) return;
    var items = allItems.filter(function (item) {
      return activeFilter === "all" || item.media_type === activeFilter;
    });
    if (!items.length) {
      grid.innerHTML = "";
      if (status) {
        status.textContent = allItems.length ? "No items in this filter." : "Gallery coming soon.";
        status.hidden = false;
      }
      return;
    }
    if (status) status.hidden = true;
    grid.innerHTML = items.map(cardHtml).join("");
    grid.querySelectorAll(".media-card").forEach(function (card) {
      card.addEventListener("click", openLightbox);
      card.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          openLightbox.call(card, e);
        }
      });
    });
  }

  function openLightbox(e) {
    var slug = this.getAttribute("data-slug");
    var item = allItems.find(function (i) { return i.slug === slug; });
    if (!item) return;
    var box = document.getElementById("mediaLightbox");
    var media = document.getElementById("lightboxMedia");
    var cat = document.getElementById("lightboxCategory");
    var title = document.getElementById("lightboxTitle");
    var loc = document.getElementById("lightboxLocation");
    var desc = document.getElementById("lightboxDesc");
    if (!box || !media) return;
    if (item.media_type === "video") {
      media.innerHTML = '<video controls autoplay playsinline class="media-lightbox__video"><source src="' + esc(item.media_url) + '"></video>';
    } else {
      media.innerHTML = '<img src="' + esc(item.media_url) + '" alt="' + esc(item.title) + '" class="media-lightbox__img" />';
    }
    if (cat) cat.textContent = item.category || "";
    if (title) title.textContent = item.title || "";
    if (loc) loc.textContent = [formatDate(item.event_date), item.location].filter(Boolean).join(" · ");
    if (desc) desc.textContent = item.description || "";
    box.hidden = false;
    box.setAttribute("aria-hidden", "false");
    document.body.classList.add("media-lightbox-open");
  }

  function closeLightbox() {
    var box = document.getElementById("mediaLightbox");
    var media = document.getElementById("lightboxMedia");
    if (!box) return;
    box.hidden = true;
    box.setAttribute("aria-hidden", "true");
    document.body.classList.remove("media-lightbox-open");
    if (media) media.innerHTML = "";
  }

  document.querySelectorAll("[data-close-lightbox]").forEach(function (el) {
    el.addEventListener("click", closeLightbox);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeLightbox();
  });

  if (filters) {
    filters.addEventListener("click", function (e) {
      var btn = e.target.closest(".media-filters__btn");
      if (!btn) return;
      activeFilter = btn.getAttribute("data-filter") || "all";
      filters.querySelectorAll(".media-filters__btn").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      renderGrid();
    });
  }

  fetch("/api/content/media", { headers: { Accept: "application/json" } })
    .then(function (r) { if (!r.ok) throw new Error("media"); return r.json(); })
    .then(function (data) {
      renderHeader(data);
      allItems = data.items || [];
      renderGrid();
    })
    .catch(function () {
      if (status) status.textContent = "Could not load gallery.";
    });
})();
