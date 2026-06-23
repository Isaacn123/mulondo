(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function get(path) {
    return fetch("/api/content/" + path, { headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) throw new Error(path);
        return r.json();
      });
  }

  function sectionHead(root, d) {
    var eyebrow = root.querySelector(".section__head .eyebrow, .eyebrow--center, .eyebrow");
    var title = root.querySelector(".section__title, .section__title--center");
    var intro = root.querySelector(".section__intro");
    if (eyebrow && d.eyebrow) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow);
    }
    if (title && d.title_before) {
      title.innerHTML = esc(d.title_before) + ' <span class="grad">' + esc(d.title_highlight || "") + "</span>" +
        (d.title_after ? " " + esc(d.title_after) : "");
    }
    if (intro && d.intro) intro.textContent = d.intro;
  }

  function renderHero(d) {
    var root = document.getElementById("hero");
    if (!root || !d) return;
    var eyebrow = root.querySelector(".hero__copy .eyebrow");
    if (eyebrow && d.eyebrow_text) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow_text);
    }
    var title = root.querySelector(".hero__title");
    if (title) {
      title.innerHTML = esc(d.title_before || "") + ' <span class="grad">' + esc(d.title_highlight || "") + "</span>";
    }
    var sub = root.querySelector(".hero__sub");
    if (sub) sub.textContent = d.subtitle || "";
    var btns = root.querySelectorAll(".hero__cta .btn");
    if (btns[0] && d.primary_btn) {
      btns[0].href = d.primary_btn.link || "#contact";
      btns[0].innerHTML = esc(d.primary_btn.text) + ' <span class="btn__arrow">&rarr;</span>';
    }
    if (btns[1] && d.secondary_btn) {
      btns[1].href = d.secondary_btn.link || "#philosophy";
      btns[1].textContent = d.secondary_btn.text || "";
    }
    var showMeta = !!d.show_meta_stats;
    var showGlobe = d.show_globe !== false;
    var extras = root.querySelector(".hero__extras");
    var meta = root.querySelector(".hero__meta");
    var globe = root.querySelector(".hero__globe");
    if (extras) {
      extras.hidden = !showMeta && !showGlobe;
      extras.classList.toggle("hero__extras--stats-only", showMeta && !showGlobe);
      extras.classList.toggle("hero__extras--globe-only", !showMeta && showGlobe);
      extras.classList.toggle("hero__extras--both", showMeta && showGlobe);
    }
    if (meta) {
      meta.hidden = !showMeta;
      if (showMeta && d.meta_stats) {
        meta.innerHTML = d.meta_stats.map(function (s) {
          return '<div><span class="num" data-count="' + esc(s.value) + '" data-suffix="' + esc(s.suffix || "") + '">0</span><label>' + esc(s.label) + "</label></div>";
        }).join("");
      } else {
        meta.innerHTML = "";
      }
    }
    if (globe) {
      globe.hidden = !showGlobe;
      var caption = root.querySelector(".hero__globe-caption-text");
      if (caption) caption.textContent = d.globe_caption || "Global markets & Africa-native perspective";
    }
    var panel = d.panel || {};
    var tag = root.querySelector(".panel__tag");
    var live = root.querySelector(".panel__live");
    var label = root.querySelector(".panel__label");
    var value = root.querySelector(".panel__value strong");
    if (tag) tag.textContent = panel.tag || "";
    if (live) live.innerHTML = "<i></i> " + esc(panel.live || "");
    if (label) label.textContent = panel.label || "";
    if (value) value.textContent = panel.value || "";
    var bars = document.getElementById("allocBars");
    if (bars && panel.allocations) {
      bars.innerHTML = panel.allocations.map(function (a) {
        return '<div class="alloc"><span>' + esc(a.name) + '</span><div class="bar in"><i style="--w:' + esc(a.percent) + '%"></i></div><b>' + esc(a.percent) + "%</b></div>";
      }).join("");
    }
    var foot = root.querySelector(".panel__foot");
    if (foot && panel.foot_left) {
      foot.innerHTML = "<span>" + esc(panel.foot_left) + '</span><span class="up">' + esc(panel.foot_right || "") + "</span>";
    }
    var cards = root.querySelectorAll(".floatcard");
    (d.float_cards || []).forEach(function (c, i) {
      if (!cards[i]) return;
      var k = cards[i].querySelector(".floatcard__k");
      var v = cards[i].querySelector(".floatcard__v");
      if (k) k.textContent = c.key || "";
      if (v) v.textContent = c.value || "";
    });
    var portrait = document.getElementById("heroPortrait");
    var portraitImg = document.getElementById("heroPortraitImg");
    var img = d.image || {};
    if (img.src) {
      if (portraitImg) {
        portraitImg.src = img.src;
        portraitImg.alt = img.alt || "";
        portraitImg.style.objectPosition = img.object_position || "center top";
      }
      if (portrait) portrait.hidden = false;
      root.classList.add("has-hero-image");
    } else {
      if (portraitImg) {
        portraitImg.removeAttribute("src");
        portraitImg.alt = "";
      }
      if (portrait) portrait.hidden = true;
      root.classList.remove("has-hero-image");
    }
  }

  function renderTrust(d) {
    var root = document.getElementById("trust");
    if (!root || !d) return;
    var grid = root.querySelector(".trust__grid");
    if (grid && d.stats) {
      grid.innerHTML = d.stats.map(function (s) {
        if (s.type === "counter") {
          return '<div class="stat reveal in"><strong class="num" data-count="' + esc(s.value) + '" data-suffix="' + esc(s.suffix || "") + '">0</strong><span>' + esc(s.label) + "</span></div>";
        }
        return '<div class="stat reveal in"><strong>' + esc(s.title) + "</strong><span>" + esc(s.label) + "</span></div>";
      }).join("");
    }
    var note = root.querySelector(".trust__note");
    if (note) {
      note.innerHTML = esc(d.note_before || "Serving investors across") + " <strong>" + esc(d.countries || "") + "</strong> " + esc(d.note_after || "");
    }
  }

  function renderAbout(d) {
    var root = document.getElementById("about");
    if (!root || !d) return;
    var img = root.querySelector(".about__photo img");
    if (img && d.image) {
      img.src = d.image.src || img.src;
      img.alt = d.image.alt || img.alt;
      if (d.image.width) img.width = d.image.width;
      if (d.image.height) img.height = d.image.height;
      var og = document.querySelector('meta[property="og:image"]');
      if (og && d.image.src) {
        var src = d.image.src;
        if (!/^https?:\/\//i.test(src)) {
          src = src.charAt(0) === "/" ? window.location.origin + src : window.location.origin + "/" + src.replace(/^\.\//, "");
        }
        og.content = src;
        var tw = document.querySelector('meta[name="twitter:image"]');
        if (tw) tw.content = src;
      }
    }
    var badge = root.querySelector(".about__badge");
    if (badge && d.badges) {
      badge.innerHTML = d.badges.map(function (b) { return "<span>" + esc(b) + "</span>"; }).join("");
    }
    var eyebrow = root.querySelector(".about__copy .eyebrow");
    if (eyebrow) eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow || "About");
    var title = root.querySelector(".about__copy .section__title");
    if (title) title.innerHTML = esc(d.title_before || "Meet") + ' <span class="grad">' + esc(d.title_highlight || "") + "</span>";
    var lead = root.querySelector(".about__copy .lead");
    if (lead) lead.textContent = d.lead || "";
    var paras = root.querySelectorAll(".about__copy > p");
    if (paras[1]) {
      paras[1].innerHTML = esc(d.role_prefix || "") + "<strong>" + esc(d.role_title || "") +
        ' <a href="' + esc(d.company_url || "#") + '" target="_blank" rel="noopener" class="inline-link">' + esc(d.company_name || "") + "</a></strong>, " +
        esc(d.body_after || "");
    }
    var list = root.querySelector(".about__list");
    if (list && d.highlights) {
      list.innerHTML = d.highlights.map(function (h) { return "<li>" + esc(h) + "</li>"; }).join("");
    }
    var cta = root.querySelector(".about__copy .btn");
    if (cta) {
      cta.href = d.cta_link || "#contact";
      cta.innerHTML = esc(d.cta_text || "Request an Introduction") + ' <span class="btn__arrow">&rarr;</span>';
    }
  }

  function renderPhilosophy(d) {
    var root = document.getElementById("philosophy");
    if (!root || !d) return;
    sectionHead(root, d);
    var quote = root.querySelector(".pullquote");
    if (quote && d.pullquote) quote.innerHTML = "&ldquo;" + esc(d.pullquote) + "&rdquo;";
    var pillars = root.querySelector(".pillars");
    if (pillars && d.pillars) {
      pillars.innerHTML = d.pillars.map(function (p) {
        return '<article class="pillar reveal in' + (p.highlighted ? " pillar--hi" : "") + '">' +
          '<span class="pillar__no">' + esc(p.number) + "</span><h3>" + esc(p.title) + "</h3><p>" + esc(p.description) + "</p></article>";
      }).join("");
    }
  }

  function renderServices(d) {
    var root = document.getElementById("services");
    if (!root || !d) return;
    sectionHead(root, d);
    var cards = root.querySelector(".cards");
    if (cards && d.cards) {
      cards.innerHTML = d.cards.map(function (c) {
        return '<article class="card reveal in"><div class="card__icon">' + esc(c.icon) + "</div><h3>" + esc(c.title) + "</h3><p>" + esc(c.description) + "</p></article>";
      }).join("");
    }
  }

  function renderMarkets(d) {
    var root = document.getElementById("markets");
    if (!root || !d) return;
    sectionHead(root, d);
    if (d.widgets) {
      Object.keys(d.widgets).forEach(function (key) {
        var box = root.querySelector('[data-tv="' + key + '"]');
        if (!box) box = root.querySelector(".tv-" + key);
        var titleEl = box && box.closest(".panel-box") ? box.closest(".panel-box").querySelector(".panel-box__title") : null;
        if (titleEl && d.widgets[key].title) titleEl.textContent = d.widgets[key].title;
      });
    }
  }

  function renderCalculator(d) {
    var root = document.getElementById("calculator");
    if (!root || !d) return;
    sectionHead(root, d);
    var disc = root.querySelector(".calc__disclaimer");
    if (disc && d.disclaimer) disc.innerHTML = "<strong>Illustrative only.</strong> " + esc(d.disclaimer);
    var cta = root.querySelector(".calc__results .btn");
    if (cta) {
      cta.href = d.cta_link || "#contact";
      cta.innerHTML = esc(d.cta_text || "Request a Review") + ' <span class="btn__arrow">&rarr;</span>';
    }
    function applyField(name, id, rangeId) {
      var field = d[name];
      if (!field) return;
      var input = document.getElementById(id);
      var range = document.getElementById(rangeId);
      var label = root.querySelector('label[for="' + rangeId + '"], label[for="' + id + '"]');
      if (label && field.label) {
        var b = label.querySelector("b");
        label.childNodes[0].textContent = field.label + " ";
        if (b) label.appendChild(b);
      }
      if (input && field.default != null) input.value = field.default;
      if (range) {
        if (field.range_min != null) range.min = field.range_min;
        if (field.range_max != null) range.max = field.range_max;
        if (field.range_step != null) range.step = field.range_step;
        if (field.default != null) range.value = field.default;
      }
      var scale = range && range.parentElement ? range.parentElement.querySelector(".field__scale") : null;
      if (scale && field.scale_labels && field.scale_labels.length) {
        scale.innerHTML = field.scale_labels.map(function (l) { return "<span>" + esc(l) + "</span>"; }).join("");
      }
    }
    applyField("initial_capital", "initial", "initialRange");
    applyField("monthly_contribution", "contribRange", "contribRange");
    applyField("investment_horizon", "horizonRange", "horizonRange");
    applyField("annual_rate", "apyRange", "apyRange");
    ["initial", "initialRange", "apyRange", "contribRange", "horizonRange"].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.dispatchEvent(new Event("input"));
    });
  }

  function renderInsights(d) {
    var root = document.getElementById("insights");
    if (!root || !d) return;
    sectionHead(root, d);
    if (d.news && d.news.title) {
      var news = root.querySelector(".tv-news");
      if (news) {
        var t = news.closest(".panel-box").querySelector(".panel-box__title");
        if (t) t.textContent = d.news.title;
      }
    }
    if (d.economic_calendar && d.economic_calendar.title) {
      var ev = root.querySelector(".tv-events");
      if (ev) {
        var t = ev.closest(".panel-box").querySelector(".panel-box__title");
        if (t) t.textContent = d.economic_calendar.title;
      }
    }
  }

  function renderCoverage(d) {
    var root = document.getElementById("coverage");
    if (!root || !d) return;
    sectionHead(root, d);
    var list = root.querySelector(".coverage__list");
    if (list) {
      var items = (d.countries || []).concat(d.regions || []);
      list.innerHTML = items.map(function (c) { return "<li>" + esc(c) + "</li>"; }).join("");
    }
  }

  function renderClients(d) {
    var root = document.getElementById("clients");
    if (!root || !d) return;
    sectionHead(root, d);
    var grid = root.querySelector(".clients__grid");
    if (grid && d.profiles) {
      grid.innerHTML = d.profiles.map(function (p) { return "<span>" + esc(p) + "</span>"; }).join("");
    }
  }

  function renderAiBanner(d) {
    var root = document.getElementById("aiBanner");
    if (!root || !d) return;
    var eyebrow = root.querySelector(".eyebrow");
    if (eyebrow && d.eyebrow) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow);
    }
    var link = root.querySelector(".ai-banner__frame");
    var img = root.querySelector(".ai-banner__frame img");
    if (link) {
      link.href = d.link || "#contact";
      if (d.link_label) link.setAttribute("aria-label", d.link_label);
    }
    if (img && d.image) {
      img.src = d.image.src || img.src;
      img.alt = d.image.alt || img.alt;
      if (d.image.width) img.width = d.image.width;
      if (d.image.height) img.height = d.image.height;
    }
  }

  function renderPartner(d) {
    var root = document.getElementById("partner");
    if (!root || !d) return;
    var eyebrow = root.querySelector(".eyebrow");
    if (eyebrow && d.eyebrow) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow);
    }
    var logoLink = root.querySelector(".partner__logo");
    var logo = root.querySelector(".partner__logo img");
    if (logoLink) {
      logoLink.href = d.url || logoLink.href;
      if (d.name) logoLink.setAttribute("aria-label", d.name + " — visit website");
    }
    if (logo && d.logo) {
      logo.src = d.logo.src || logo.src;
      logo.alt = d.logo.alt || d.name || logo.alt;
    }
    var text = root.querySelector(".partner__text");
    if (text) text.textContent = d.text || "";
    var btn = root.querySelector(".partner__card .btn");
    if (btn) {
      btn.href = d.url || btn.href;
      btn.innerHTML = esc(d.button_text || "Visit partner") + ' <span class="btn__arrow">&rarr;</span>';
    }
  }

  function renderContact(d) {
    var root = document.getElementById("contact");
    if (!root || !d) return;
    sectionHead(root, d);
    var form = d.form || {};
    var h3 = root.querySelector(".contact__form-wrap h3");
    var sub = root.querySelector(".contact__form-wrap .contact__sub");
    if (h3) h3.textContent = form.title || h3.textContent;
    if (sub) sub.textContent = form.subtitle || sub.textContent;
    var onboard = document.getElementById("onboardForm");
    if (onboard && form.action_url) onboard.action = form.action_url;
    var submit = onboard && onboard.querySelector('button[type="submit"]');
    if (submit && form.submit_text) submit.innerHTML = esc(form.submit_text) + ' <span class="btn__arrow">&rarr;</span>';
    var consent = onboard && onboard.querySelector(".form__check span");
    if (consent && form.consent_text) consent.textContent = form.consent_text;
    var country = document.getElementById("fcountry");
    if (country && form.country_placeholder) country.placeholder = form.country_placeholder;
    var msg = document.getElementById("fmsg");
    if (msg && form.message_placeholder) msg.placeholder = form.message_placeholder;
    var investor = document.getElementById("finvestor");
    if (investor && form.investor_types) {
      investor.innerHTML = form.investor_types.map(function (t) {
        return "<option>" + esc(t) + "</option>";
      }).join("");
    }
    var capital = document.getElementById("fhorizon");
    if (capital && form.capital_ranges) {
      capital.innerHTML = form.capital_ranges.map(function (t) {
        return "<option>" + esc(t) + "</option>";
      }).join("");
    }
    var cal = d.calendly || {};
    var bookH = root.querySelector(".contact__book h3");
    var bookSub = root.querySelector(".contact__book .contact__sub");
    if (bookH) bookH.textContent = cal.title || bookH.textContent;
    if (bookSub) bookSub.textContent = cal.subtitle || bookSub.textContent;
    var widget = root.querySelector(".calendly-inline-widget");
    if (widget && cal.widget_url) {
      widget.setAttribute("data-url", cal.widget_url);
      if (cal.widget_height) widget.style.height = cal.widget_height + "px";
    }
    var fallback = root.querySelector(".contact__fallback");
    if (fallback && cal.fallback_url) fallback.href = cal.fallback_url;
  }

  function renderMediaPreview(d) {
    var root = document.getElementById("mediaPreview");
    if (!root || !d) return;
    var eyebrow = document.getElementById("mediaPreviewEyebrow");
    var title = document.getElementById("mediaPreviewTitle");
    var intro = document.getElementById("mediaPreviewIntro");
    var grid = document.getElementById("mediaPreviewGrid");
    if (eyebrow && d.eyebrow) {
      eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow);
    }
    if (title && d.title_before) {
      title.innerHTML = esc(d.title_before) + ' <span class="grad">' + esc(d.title_highlight || "") + "</span>";
    }
    if (intro && d.intro) intro.textContent = d.intro;
    if (!grid || !d.items || !d.items.length) return;
    var picks = d.items.slice(0, 3);
    grid.innerHTML = picks.map(function (item) {
      var src = item.media_type === "video" ? (item.thumbnail_url || item.media_url) : item.media_url;
      return '<a href="/media" class="media-preview__card"><img src="' + esc(src) + '" alt="' + esc(item.title) + '" loading="lazy" /></a>';
    }).join("");
    grid.hidden = false;
  }

  function applyHomepageLayout(layout) {
    var main = document.getElementById("top");
    if (!main || !layout || !layout.sections) return;

    var ordered = layout.sections.slice().sort(function (a, b) {
      return b.sort_order - a.sort_order;
    });
    var footer = document.querySelector("footer");

    ordered.forEach(function (section) {
      var el = document.getElementById(section.element_id);
      if (!el) return;
      el.hidden = !section.enabled;
      if (!section.enabled) return;
      if (main.contains(el)) main.appendChild(el);
      else if (footer && footer.parentNode) footer.parentNode.insertBefore(el, footer);
    });
  }

  function enabledSectionKeys(layout) {
    if (!layout || !layout.sections) return null;
    var keys = {};
    layout.sections.forEach(function (section) {
      if (section.enabled) keys[section.key] = true;
    });
    return keys;
  }

  var sections = [
    ["hero", renderHero],
    ["trust", renderTrust],
    ["about", renderAbout],
    ["philosophy", renderPhilosophy],
    ["services", renderServices],
    ["markets", renderMarkets],
    ["calculator", renderCalculator],
    ["insights", renderInsights],
    ["coverage", renderCoverage],
    ["clients", renderClients],
    ["media", renderMediaPreview],
    ["contact", renderContact],
    ["ai-banner", renderAiBanner],
    ["partner", renderPartner]
  ];

  function loadCmsSections(enabled) {
    var toLoad = sections.filter(function (pair) {
      return !enabled || enabled[pair[0]];
    });
    return Promise.allSettled(
      toLoad.map(function (pair) {
        return get(pair[0]).then(pair[1]);
      })
    ).then(function () {
      document.documentElement.classList.remove("cms-loading");
      document.documentElement.classList.add("cms-ready");
      document.dispatchEvent(new CustomEvent("cms:loaded"));
    });
  }

  if (document.getElementById("top")) {
    fetch("/api/content/homepage-layout", { headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) throw new Error("homepage-layout");
        return r.json();
      })
      .then(function (layout) {
        applyHomepageLayout(layout);
        return loadCmsSections(enabledSectionKeys(layout));
      })
      .catch(function () {
        return loadCmsSections(null);
      });
  } else {
    loadCmsSections(null);
  }
})();
