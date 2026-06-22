(function () {
  "use strict";

  var listEl = document.getElementById("blogList");
  var statusEl = document.getElementById("blogStatus");
  if (!listEl) return;

  function apiBase() {
    var port = window.location.port;
    if (port === "3001" || port === "3000" || port === "3008" || port === "80" || port === "443" || port === "") {
      return "";
    }
    return "http://localhost:8008";
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatDate(value) {
    if (!value) return "";
    var date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" });
  }

  function renderMedia(post) {
    if (!post.media_url) return "";
    var url = escapeHtml(post.media_url);
    if (post.media_type === "video") {
      return (
        '<div class="blog-card__media">' +
        '<video controls preload="metadata" playsinline src="' + url + '"></video>' +
        "</div>"
      );
    }
    if (post.media_type === "image") {
      return (
        '<div class="blog-card__media">' +
        '<img src="' + url + '" alt="" loading="lazy">' +
        "</div>"
      );
    }
    return "";
  }

  function renderPosts(posts) {
    if (!posts.length) {
      listEl.innerHTML = '<p class="blog__status">No published articles yet. Check back soon.</p>';
      return;
    }

    listEl.innerHTML = posts.map(function (post) {
      var meta = [post.author, formatDate(post.published_at)].filter(Boolean).join(" · ");
      return (
        '<article class="blog-card panel-box">' +
          renderMedia(post) +
          '<p class="panel-box__title">' + escapeHtml(meta || "Article") + "</p>" +
          "<h2 class=\"blog-card__title\">" + escapeHtml(post.title) + "</h2>" +
          (post.excerpt ? '<p class="blog-card__excerpt">' + escapeHtml(post.excerpt) + "</p>" : "") +
          (post.body ? '<div class="blog-card__body">' + escapeHtml(post.body).replace(/\n/g, "<br>") + "</div>" : "") +
        "</article>"
      );
    }).join("");
  }

  fetch(apiBase() + "/api/content/blog", { headers: { Accept: "application/json" } })
    .then(function (res) {
      if (!res.ok) throw new Error("Failed to load blog posts");
      return res.json();
    })
    .then(renderPosts)
    .catch(function () {
      if (statusEl) {
        statusEl.textContent = "Unable to load articles right now.";
      } else {
        listEl.innerHTML = '<p class="blog__status">Unable to load articles right now.</p>';
      }
    });
})();
