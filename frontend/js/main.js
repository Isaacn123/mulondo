/* =========================================================
   Mulondo Daniel — site interactions
   ========================================================= */
(function () {
  "use strict";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Preloader ---------- */
  window.addEventListener("load", function () {
    var pre = document.getElementById("preloader");
    if (pre) setTimeout(function () { pre.classList.add("is-done"); }, 500);
  });

  /* ---------- Year ---------- */
  var y = document.getElementById("year");
  if (y) y.textContent = new Date().getFullYear();

  /* ---------- Nav: scroll state + scroll progress ---------- */
  var nav = document.getElementById("nav");
  var progress = document.getElementById("scrollProgress");
  var floatCta = document.getElementById("floatingCta");
  function onScroll() {
    var sc = window.scrollY || document.documentElement.scrollTop;
    if (nav) nav.classList.toggle("scrolled", sc > 30);
    if (progress) {
      var h = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.width = (h > 0 ? (sc / h) * 100 : 0) + "%";
    }
    if (floatCta) floatCta.classList.toggle("show", sc > 700 && sc < (document.documentElement.scrollHeight - window.innerHeight - 600));
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  var toggle = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");
  var overlay = document.getElementById("navOverlay");
  var scrollY = 0;
  function setMenuOpen(open) {
    if (!links || !toggle) return;
    if (open) {
      scrollY = window.scrollY || document.documentElement.scrollTop;
      document.body.style.top = "-" + scrollY + "px";
    } else {
      document.body.style.top = "";
      window.scrollTo(0, scrollY);
    }
    links.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("nav-open", open);
    if (overlay) overlay.classList.toggle("is-visible", open);
  }
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      setMenuOpen(!links.classList.contains("open"));
    });
    if (overlay) {
      overlay.addEventListener("click", function () { setMenuOpen(false); });
    }
    links.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setMenuOpen(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && links.classList.contains("open")) setMenuOpen(false);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 980 && links.classList.contains("open")) setMenuOpen(false);
    });
  }

  /* ---------- Reveal on scroll + bars + counters ---------- */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add("in");
      // animate bars within
      e.target.querySelectorAll(".bar").forEach(function (b) { b.classList.add("in"); });
      // counters
      e.target.querySelectorAll(".num[data-count]").forEach(animateCount);
      io.unobserve(e.target);
    });
  }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });

  function animateCount(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    var target = parseFloat(el.dataset.count);
    var suffix = el.dataset.suffix || "";
    if (reduceMotion) { el.textContent = target + suffix; return; }
    var start = 0, dur = 1400, t0 = null;
    function step(ts) {
      if (!t0) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(start + (target - start) * eased) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function observeRevealTargets() {
    document.querySelectorAll(".reveal, #allocBars").forEach(function (el) { io.observe(el); });
    document.querySelectorAll(".num[data-count]").forEach(function (el) { io.observe(el); });
  }

  observeRevealTargets();
  document.addEventListener("cms:loaded", observeRevealTargets);

  /* =======================================================
     Investment / compounding calculator
     ======================================================= */
  var initial = document.getElementById("initial");
  var initialRange = document.getElementById("initialRange");
  var apyRange = document.getElementById("apyRange");
  var apyVal = document.getElementById("apyVal");
  var contribRange = document.getElementById("contribRange");
  var contribVal = document.getElementById("contribVal");
  var horizonRange = document.getElementById("horizonRange");
  var horizonVal = document.getElementById("horizonVal");
  var rowsWrap = document.getElementById("calcRows");
  var summaryWrap = document.getElementById("calcSummary");
  var canvas = document.getElementById("calcChart");
  var ctx = canvas ? canvas.getContext("2d") : null;

  var chartYears = 5; // horizon currently plotted (drives chart year markers)

  function clamp(v, lo, hi) {
    v = +v;
    if (!isFinite(v)) return lo;
    return Math.min(hi, Math.max(lo, v));
  }
  function fmt(n) {
    if (!isFinite(n)) n = 0;
    return "$" + Math.round(n).toLocaleString("en-US");
  }
  function setRangeFill(el) {
    var min = +el.min, max = +el.max, v = +el.value;
    var p = max > min ? ((v - min) / (max - min) * 100) : 0;
    el.style.setProperty("--p", clamp(p, 0, 100) + "%");
  }

  // FV with monthly contributions; apy interpreted as effective annual yield
  function projection(P, apy, C, months) {
    var m = Math.pow(1 + apy, 1 / 12) - 1; // effective monthly rate
    var fv = P * Math.pow(1 + m, months);
    if (m > 0) fv += C * ((Math.pow(1 + m, months) - 1) / m);
    else fv += C * months;
    return isFinite(fv) ? fv : 0;
  }

  function seriesFor(P, apy, C, maxMonths) {
    var arr = [];
    for (var i = 0; i <= maxMonths; i++) arr.push(projection(P, apy, C, i));
    return arr;
  }

  // Throttled recompute (leading + trailing) so dragging a slider never floods
  // the main thread, while guaranteeing the final value always renders. Uses a
  // timestamp + setTimeout rather than requestAnimationFrame, which browsers
  // suspend in background/hidden tabs (that would freeze the calculator).
  var lastRun = 0, trailingTimer = null, MIN_GAP = 40;
  function scheduleRecalc() {
    var now = Date.now();
    if (now - lastRun >= MIN_GAP) {
      lastRun = now;
      compute();
    } else {
      clearTimeout(trailingTimer);
      trailingTimer = setTimeout(function () { lastRun = Date.now(); compute(); }, MIN_GAP);
    }
  }

  function compute() {
    if (!initial) return;
    // sanitize every input — guards against NaN / Infinity / out-of-range
    var P = clamp(initial.value, 0, 100000000);
    var apy = clamp(apyRange.value, +apyRange.min, +apyRange.max) / 100;
    var C = clamp(contribRange.value, +contribRange.min, +contribRange.max);
    var years = clamp(horizonRange.value, +horizonRange.min, +horizonRange.max);
    var months = years * 12;
    chartYears = years;

    if (apyVal) apyVal.textContent = Math.round(apy * 100) + "%";
    if (contribVal) contribVal.textContent = fmt(C);
    if (horizonVal) horizonVal.textContent = years + (years === 1 ? " year" : " years");
    [initialRange, contribRange, horizonRange, apyRange].forEach(setRangeFill);

    // headline summary at the chosen horizon
    var fvFinal = projection(P, apy, C, months);
    var investedFinal = P + C * months;
    var gainFinal = fvFinal - investedFinal;
    if (summaryWrap) {
      summaryWrap.innerHTML =
        '<div class="calc__summary-main">' +
          '<span class="calc__summary-h">Projected value after ' + years + (years === 1 ? ' year' : ' years') + '</span>' +
          '<strong>' + fmt(fvFinal) + '</strong>' +
        '</div>' +
        '<div class="calc__summary-sub">' +
          '<span>Invested <b>' + fmt(investedFinal) + '</b></span>' +
          '<span>Growth <b class="up">+' + fmt(gainFinal) + '</b></span>' +
        '</div>';
    }

    // year-by-year table
    if (rowsWrap) {
      var rows = "";
      for (var yr = 1; yr <= years; yr++) {
        var mo = yr * 12;
        var fv = projection(P, apy, C, mo);
        var invested = P + C * mo;
        var growth = fv - invested;
        rows += '<tr>' +
          '<td data-label="Year">Year ' + yr + '</td>' +
          '<td data-label="Invested">' + fmt(invested) + '</td>' +
          '<td class="val" data-label="Projected Value">' + fmt(fv) + '</td>' +
          '<td class="up" data-label="Growth">+' + fmt(growth) + '</td>' +
          '</tr>';
      }
      rowsWrap.innerHTML = rows;
    }

    drawChart(seriesFor(P, apy, C, months));
  }

  var _cw = 0; // cached canvas pixel width to avoid reallocating every frame
  function drawChart(data) {
    if (!ctx) return;
    var dpr = window.devicePixelRatio || 1;
    var w = canvas.clientWidth || (canvas.parentElement ? canvas.parentElement.clientWidth : 0) || Math.min(600, window.innerWidth - 48), h = 200;
    // only resize the backing store when the layout width actually changes
    if (Math.round(w * dpr) !== _cw) {
      _cw = Math.round(w * dpr);
      canvas.width = w * dpr; canvas.height = h * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    // sanitize series so a non-finite value can never poison the geometry
    data = data.map(function (v) { return isFinite(v) ? v : 0; });

    var pad = { l: 8, r: 8, t: 14, b: 22 };
    var max = Math.max.apply(null, data) || 1;
    var min = Math.min.apply(null, data);
    if (!isFinite(max)) max = 1;
    if (!isFinite(min)) min = 0;
    var iw = w - pad.l - pad.r, ih = h - pad.t - pad.b;
    function X(i) { return pad.l + (i / (data.length - 1)) * iw; }
    function Y(v) { return pad.t + ih - ((v - min) / (max - min || 1)) * ih; }

    // gridlines
    ctx.strokeStyle = "rgba(255,255,255,.06)";
    ctx.lineWidth = 1;
    for (var g = 0; g <= 3; g++) {
      var gy = pad.t + (ih / 3) * g;
      ctx.beginPath(); ctx.moveTo(pad.l, gy); ctx.lineTo(w - pad.r, gy); ctx.stroke();
    }

    // area fill
    var grad = ctx.createLinearGradient(0, pad.t, 0, h);
    grad.addColorStop(0, "rgba(212,175,55,.35)");
    grad.addColorStop(1, "rgba(212,175,55,0)");
    ctx.beginPath();
    ctx.moveTo(X(0), Y(data[0]));
    data.forEach(function (v, i) { ctx.lineTo(X(i), Y(v)); });
    ctx.lineTo(X(data.length - 1), h - pad.b);
    ctx.lineTo(X(0), h - pad.b);
    ctx.closePath();
    ctx.fillStyle = grad; ctx.fill();

    // line
    ctx.beginPath();
    ctx.moveTo(X(0), Y(data[0]));
    data.forEach(function (v, i) { ctx.lineTo(X(i), Y(v)); });
    ctx.strokeStyle = "#e8c873"; ctx.lineWidth = 2.4;
    ctx.lineJoin = "round"; ctx.stroke();

    // year markers
    ctx.font = "10px 'JetBrains Mono', monospace";
    var labelEvery = chartYears > 7 ? 2 : 1;
    for (var yr = 1; yr <= chartYears; yr++) {
      var idx = yr * 12;
      if (idx >= data.length) idx = data.length - 1;
      var px = X(idx), py = Y(data[idx]);
      ctx.beginPath(); ctx.arc(px, py, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = "#d4af37"; ctx.fill();
      ctx.strokeStyle = "#08090c"; ctx.lineWidth = 2; ctx.stroke();
      if (yr % labelEvery === 0 || yr === chartYears) {
        ctx.fillStyle = "#6b7484"; ctx.textAlign = "center";
        ctx.fillText(yr + "y", px, h - 6);
      }
    }
  }

  if (initial) {
    // range -> number field
    initialRange.addEventListener("input", function () {
      initial.value = initialRange.value;
      scheduleRecalc();
    });
    // number field -> range (clamp to range bounds, allow blank while typing)
    initial.addEventListener("input", function () {
      if (initial.value !== "") {
        var v = clamp(initial.value, +initialRange.min, +initialRange.max);
        initialRange.value = v;
      }
      scheduleRecalc();
    });
    // normalise the field when the user leaves it
    initial.addEventListener("blur", function () {
      initial.value = clamp(initial.value, 0, 100000000);
      scheduleRecalc();
    });
    apyRange.addEventListener("input", scheduleRecalc);
    contribRange.addEventListener("input", scheduleRecalc);
    horizonRange.addEventListener("input", scheduleRecalc);
    window.addEventListener("resize", function () {
      clearTimeout(window.__rt);
      window.__rt = setTimeout(scheduleRecalc, 150);
    });
    compute();
  }

  /* =======================================================
     TradingView widgets (lazy-loaded on view)
     ======================================================= */
  var TV = {
    ticker: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js",
      cfg: {
        symbols: [
          { proName: "BINANCE:BTCUSDT", title: "Bitcoin" },
          { proName: "BINANCE:ETHUSDT", title: "Ethereum" },
          { proName: "OANDA:XAUUSD", title: "Gold" },
          { proName: "NASDAQ:NVDA", title: "NVIDIA" },
          { proName: "NASDAQ:TSLA", title: "Tesla" },
          { proName: "FOREXCOM:SPXUSD", title: "S&P 500" },
          { proName: "FX:EURUSD", title: "EUR/USD" },
          { proName: "BINANCE:SOLUSDT", title: "Solana" }
        ],
        showSymbolLogo: true, isTransparent: true, displayMode: "adaptive",
        colorTheme: "dark", locale: "en"
      }
    },
    chart: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js",
      cfg: {
        autosize: true, symbol: "BINANCE:BTCUSDT", interval: "D", timezone: "Africa/Nairobi",
        theme: "dark", style: "1", locale: "en", hide_side_toolbar: true,
        allow_symbol_change: true, calendar: false, support_host: "https://www.tradingview.com",
        backgroundColor: "rgba(11,18,32,0)", gridColor: "rgba(255,255,255,0.05)",
        withdateranges: true, details: false
      }
    },
    overview: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-market-overview.js",
      cfg: {
        colorTheme: "dark", dateRange: "12M", showChart: true, locale: "en",
        isTransparent: true, showSymbolLogo: true, width: "100%", height: "100%",
        plotLineColorGrowing: "#d4af37", plotLineColorFalling: "#9aa3b2",
        gridLineColor: "rgba(255,255,255,0.05)", scaleFontColor: "#9aa3b2",
        belowLineFillColorGrowing: "rgba(212,175,55,0.12)", belowLineFillColorFalling: "rgba(154,163,178,0.08)",
        symbolActiveColor: "rgba(212,175,55,0.15)",
        tabs: [
          { title: "Crypto", symbols: [
            { s: "BINANCE:BTCUSDT", d: "Bitcoin" }, { s: "BINANCE:ETHUSDT", d: "Ethereum" },
            { s: "BINANCE:SOLUSDT", d: "Solana" }, { s: "BINANCE:BNBUSDT", d: "BNB" } ] },
          { title: "Indices", symbols: [
            { s: "FOREXCOM:SPXUSD", d: "S&P 500" }, { s: "FOREXCOM:NSXUSD", d: "Nasdaq 100" },
            { s: "FOREXCOM:DJI", d: "Dow 30" } ] },
          { title: "Commodities", symbols: [
            { s: "OANDA:XAUUSD", d: "Gold" }, { s: "OANDA:XAGUSD", d: "Silver" },
            { s: "TVC:USOIL", d: "Crude Oil" } ] },
          { title: "Forex", symbols: [
            { s: "FX:EURUSD", d: "EUR/USD" }, { s: "FX:GBPUSD", d: "GBP/USD" },
            { s: "FX:USDJPY", d: "USD/JPY" } ] }
        ]
      }
    },
    screener: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-screener.js",
      cfg: {
        width: "100%", height: "100%", defaultColumn: "overview", defaultScreen: "general",
        market: "crypto", showToolbar: true, colorTheme: "dark", locale: "en", isTransparent: true
      }
    },
    news: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-timeline.js",
      cfg: {
        feedMode: "all_symbols", isTransparent: true, displayMode: "regular",
        width: "100%", height: "100%", colorTheme: "dark", locale: "en"
      }
    },
    events: {
      src: "https://s3.tradingview.com/external-embedding/embed-widget-events.js",
      cfg: {
        colorTheme: "dark", isTransparent: true, width: "100%", height: "100%",
        locale: "en", importanceFilter: "0,1", countryFilter: "us,eu,gb,jp,cn,za,ng,ke"
      }
    }
  };

  function mountTV(container) {
    var key = container.getAttribute("data-tv");
    var spec = TV[key];
    if (!spec || container.dataset.mounted) return;
    container.dataset.mounted = "1";
    var inner = document.createElement("div");
    inner.className = "tradingview-widget-container__widget";
    inner.style.height = "calc(100% - 0px)";
    inner.style.width = "100%";
    container.appendChild(inner);
    var s = document.createElement("script");
    s.src = spec.src; s.async = true; s.type = "text/javascript";
    s.innerHTML = JSON.stringify(spec.cfg);
    container.appendChild(s);
  }

  var tvObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) { mountTV(e.target); tvObserver.unobserve(e.target); }
    });
  }, { rootMargin: "200px" });

  document.querySelectorAll("[data-tv]").forEach(function (el) {
    // ticker mounts immediately (top of page); others lazy
    if (el.getAttribute("data-tv") === "ticker") mountTV(el);
    else tvObserver.observe(el);
  });

  /* =======================================================
     Calendly init
     ======================================================= */
  function initCalendly(force) {
    var el = document.querySelector(".calendly-inline-widget");
    if (!el || !window.Calendly) return;
    if (el.dataset.cinit && !force) return;
    if (force && el.dataset.cinit) {
      el.innerHTML = "";
      delete el.dataset.cinit;
    }
    el.dataset.cinit = "1";
    window.Calendly.initInlineWidget({ url: el.getAttribute("data-url"), parentElement: el });
  }
  // widget.js auto-inits inline widgets, but ensure it runs after load too
  window.addEventListener("load", function () { setTimeout(function () { initCalendly(false); }, 800); });
  document.addEventListener("cms:loaded", function () { setTimeout(function () { initCalendly(true); }, 100); });

  /* =======================================================
     Contact form (Formspree) with graceful fallback
     ======================================================= */
  var form = document.getElementById("onboardForm");
  var status = document.getElementById("formStatus");
  if (form) {
    form.addEventListener("submit", function (ev) {
      var action = form.getAttribute("action") || "";
      var configured = action.indexOf("your-form-id") === -1 && action.indexOf("formspree.io") !== -1;

      if (!configured) {
        // No backend wired yet -> fall back to mailto so nothing is lost
        ev.preventDefault();
        var data = new FormData(form);
        var body = [];
        data.forEach(function (v, k) { body.push(k + ": " + v); });
        var subject = "Investment Review Request — " + (data.get("name") || "Website");
        window.location.href = "mailto:danielmulondo@gmail.com?subject=" +
          encodeURIComponent(subject) + "&body=" + encodeURIComponent(body.join("\n"));
        if (status) { status.textContent = "Opening your email app to send the request…"; status.className = "form__status ok"; }
        return;
      }

      // Configured Formspree -> AJAX submit
      ev.preventDefault();
      if (status) { status.textContent = "Sending…"; status.className = "form__status"; }
      fetch(action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } })
        .then(function (r) {
          if (r.ok) {
            form.reset();
            [initialRange, apyRange, contribRange].forEach(function (x) { if (x) setRangeFill(x); });
            if (status) { status.textContent = "Thank you — your confidential request has been received."; status.className = "form__status ok"; }
          } else {
            if (status) { status.textContent = "Something went wrong. Please email danielmulondo@gmail.com."; status.className = "form__status err"; }
          }
        })
        .catch(function () {
          if (status) { status.textContent = "Network error. Please email danielmulondo@gmail.com."; status.className = "form__status err"; }
        });
    });
  }

  /* =======================================================
     Handcrafted micro-interactions (pointer-fine only)
     ======================================================= */
  var finePointer = window.matchMedia("(hover:hover) and (pointer:fine)").matches;

  if (finePointer && !reduceMotion) {
    // cursor-follow glow across the "expensive" cards
    document.querySelectorAll(".card,.pillar,.why__item,.partner__card").forEach(function (c) {
      c.addEventListener("pointermove", function (e) {
        var r = c.getBoundingClientRect();
        c.style.setProperty("--mx", ((e.clientX - r.left) / r.width * 100) + "%");
        c.style.setProperty("--my", ((e.clientY - r.top) / r.height * 100) + "%");
      }, { passive: true });
    });

    // About portrait: subtle 3D tilt + spotlight that tracks the cursor
    var aboutPhoto = document.getElementById("aboutPhoto");
    if (aboutPhoto) {
      var spot = aboutPhoto.querySelector(".about__spotlight");
      var tiltRaf = null, rx = 0, ry = 0;
      aboutPhoto.addEventListener("pointermove", function (e) {
        var r = aboutPhoto.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        rx = (py - 0.5) * -7; ry = (px - 0.5) * 7;
        if (spot) { spot.style.setProperty("--mx", (px * 100) + "%"); spot.style.setProperty("--my", (py * 100) + "%"); }
        if (!tiltRaf) tiltRaf = requestAnimationFrame(function () {
          tiltRaf = null;
          aboutPhoto.style.transform = "rotateX(" + rx + "deg) rotateY(" + ry + "deg)";
        });
      }, { passive: true });
      aboutPhoto.addEventListener("pointerleave", function () { aboutPhoto.style.transform = ""; });
    }

    // magnetic pull on the standalone primary buttons
    document.querySelectorAll(".btn--gold:not(.btn--block):not(.nav__cta)").forEach(function (b) {
      b.addEventListener("pointermove", function (e) {
        var r = b.getBoundingClientRect();
        var mx = e.clientX - r.left - r.width / 2, my = e.clientY - r.top - r.height / 2;
        b.style.transform = "translate(" + (mx * 0.22) + "px," + (my * 0.32) + "px)";
      }, { passive: true });
      b.addEventListener("pointerleave", function () { b.style.transform = ""; });
    });
  }

  /* =======================================================
     Services embers — a slow upward drift (money in motion)
     ======================================================= */
  (function () {
    var cv = document.getElementById("embersCanvas");
    if (!cv || reduceMotion) return;
    var ctx = cv.getContext("2d");
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var W = 0, H = 0, parts = [], running = false, rafId = null;

    function size() {
      var r = cv.getBoundingClientRect();
      W = r.width; H = r.height;
      cv.width = Math.max(1, W * dpr); cv.height = Math.max(1, H * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function seed(p, init) {
      p.x = Math.random() * W;
      p.y = init ? Math.random() * H : H + 8;
      p.r = Math.random() * 1.6 + 0.6;
      p.s = Math.random() * 0.45 + 0.18;      // rise speed
      p.drift = (Math.random() - 0.5) * 0.28;  // lateral sway
      p.a = Math.random() * 0.45 + 0.18;       // base alpha
      p.tw = Math.random() * Math.PI * 2;      // twinkle phase
    }
    function build() {
      var n = W < 600 ? 14 : (W < 980 ? 24 : 36);
      parts = [];
      for (var i = 0; i < n; i++) { var p = {}; seed(p, true); parts.push(p); }
    }
    function frame() {
      if (!running) return;
      ctx.clearRect(0, 0, W, H);
      for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        p.y -= p.s; p.x += p.drift; p.tw += 0.03;
        if (p.y < -8) seed(p, false);
        var tw = Math.sin(p.tw) * 0.3 + 0.7;
        var rad = p.r * 4;
        var g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, rad);
        g.addColorStop(0, "rgba(232,200,115," + (p.a * tw).toFixed(3) + ")");
        g.addColorStop(1, "rgba(212,175,55,0)");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.arc(p.x, p.y, rad, 0, Math.PI * 2); ctx.fill();
      }
      rafId = requestAnimationFrame(frame);
    }
    size(); build();
    // start immediately; the observer only pauses it when off-screen (perf)
    running = true; rafId = requestAnimationFrame(frame);
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) {
        running = e.isIntersecting;
        if (running) { cancelAnimationFrame(rafId); rafId = requestAnimationFrame(frame); }
      });
    }, { threshold: 0 });
    io.observe(cv);
    window.addEventListener("resize", function () {
      clearTimeout(cv.__t); cv.__t = setTimeout(function () { size(); build(); }, 200);
    });
  })();
})();