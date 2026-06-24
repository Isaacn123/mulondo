(function () {
  "use strict";

  var BINANCE_WS = "wss://stream.binance.com:9443/stream";
  var BINANCE_REST = "https://api.binance.com/api/v3/ticker/24hr";

  var DEFAULT_SYMBOLS = [
    { symbol: "BTCUSDT", label: "Bitcoin", decimals: 2, link: "" },
    { symbol: "ETHUSDT", label: "Ethereum", decimals: 2, link: "" },
    { symbol: "BNBUSDT", label: "BNB", decimals: 2, link: "" },
    { symbol: "SOLUSDT", label: "Solana", decimals: 2, link: "" },
    { symbol: "XRPUSDT", label: "XRP", decimals: 4, link: "" },
    { symbol: "ADAUSDT", label: "Cardano", decimals: 4, link: "" },
    { symbol: "DOGEUSDT", label: "Dogecoin", decimals: 5, link: "" },
    { symbol: "AVAXUSDT", label: "Avalanche", decimals: 2, link: "" },
    { symbol: "LINKUSDT", label: "Chainlink", decimals: 2, link: "" },
    { symbol: "TRXUSDT", label: "TRON", decimals: 4, link: "" }
  ];

  var state = {
    symbols: [],
    meta: {},
    ws: null,
    reconnectTimer: null,
    flashTimers: {},
    root: null,
    statusEl: null,
    ready: false
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function normalizeConfig(config) {
    config = config || {};
    var symbols = Array.isArray(config.symbols) && config.symbols.length
      ? config.symbols.slice(0, 10)
      : DEFAULT_SYMBOLS.slice();
    return {
      enabled: config.enabled !== false,
      title: config.title || "Live Crypto Markets",
      symbols: symbols
    };
  }

  function formatPrice(value, decimals) {
    var n = Number(value);
    if (!isFinite(n)) return "—";
    return n.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  function formatChange(value, decimals) {
    var n = Math.abs(Number(value));
    if (!isFinite(n)) return "—";
    return formatPrice(n, decimals);
  }

  function setStatus(text, ok) {
    if (!state.statusEl) return;
    state.statusEl.textContent = text;
    state.statusEl.classList.toggle("is-live", !!ok);
    state.statusEl.classList.toggle("is-error", ok === false);
  }

  function rowClass(index) {
    return index % 2 === 0 ? "markets-live-table__row" : "markets-live-table__row markets-live-table__row--alt";
  }

  function buildRows(config) {
    var tbody = state.root && state.root.querySelector("[data-live-body]");
    if (!tbody) return false;

    tbody.innerHTML = "";
    state.symbols = [];
    state.meta = {};

    config.symbols.forEach(function (item, index) {
      var symbol = String(item.symbol || "").toUpperCase();
      if (!symbol) return;
      state.symbols.push(symbol);
      state.meta[symbol] = {
        label: item.label || symbol,
        decimals: item.decimals != null ? item.decimals : 2,
        link: item.link || "",
        index: index
      };

      var nameCell = item.link
        ? '<a href="' + esc(item.link) + '" class="markets-live-table__name">' + esc(item.label || symbol) + "</a>"
        : '<span class="markets-live-table__name">' + esc(item.label || symbol) + "</span>";

      tbody.insertAdjacentHTML(
        "beforeend",
        '<tr class="' + rowClass(index) + '" data-symbol="' + esc(symbol) + '">' +
        '<td class="markets-live-table__market">' + nameCell + "</td>" +
        '<td class="markets-live-table__last" data-field="last">—</td>' +
        '<td class="markets-live-table__chg markets-live-table__hide-sm" data-field="change"><span class="markets-live-table__arrow" aria-hidden="true"></span><span data-field="change-text">—</span></td>' +
        '<td class="markets-live-table__pct" data-field="pct">—</td>' +
        "</tr>"
      );
    });

    return state.symbols.length > 0;
  }

  function flashCell(cell, up) {
    if (!cell) return;
    cell.classList.remove("is-flash-up", "is-flash-down");
    cell.classList.add(up ? "is-flash-up" : "is-flash-down");
    var key = cell.closest("[data-symbol]")
      ? cell.closest("[data-symbol]").getAttribute("data-symbol") + "-last"
      : "cell";
    clearTimeout(state.flashTimers[key]);
    state.flashTimers[key] = setTimeout(function () {
      cell.classList.remove("is-flash-up", "is-flash-down");
    }, 650);
  }

  function setDirection(el, up) {
    if (!el) return;
    el.classList.toggle("is-up", up);
    el.classList.toggle("is-down", !up);
  }

  function applyTicker(symbol, ticker) {
    if (!state.root) return;
    var row = state.root.querySelector('tr[data-symbol="' + symbol + '"]');
    var meta = state.meta[symbol];
    if (!row || !meta || !ticker) return;

    var last = Number(ticker.c || ticker.lastPrice);
    var change = Number(ticker.p || ticker.priceChange);
    var pct = Number(ticker.P || ticker.priceChangePercent);
    var up = change >= 0;

    var lastCell = row.querySelector('[data-field="last"]');
    var changeCell = row.querySelector('[data-field="change"]');
    var changeText = row.querySelector('[data-field="change-text"]');
    var pctCell = row.querySelector('[data-field="pct"]');

    if (lastCell) {
      var prev = lastCell.getAttribute("data-value");
      var next = String(last);
      if (prev && prev !== next) {
        var tickUp = Number(next) >= Number(prev);
        flashCell(lastCell, tickUp);
        setDirection(lastCell, tickUp);
      } else if (!prev) {
        setDirection(lastCell, up);
      }
      lastCell.setAttribute("data-value", next);
      lastCell.textContent = formatPrice(last, meta.decimals);
    }

    if (changeCell && changeText) {
      setDirection(changeCell, up);
      changeText.textContent = (up ? "+" : "−") + formatChange(change, meta.decimals);
      var arrow = changeCell.querySelector(".markets-live-table__arrow");
      if (arrow) arrow.className = "markets-live-table__arrow " + (up ? "is-up" : "is-down");
    }

    if (pctCell) {
      setDirection(pctCell, up);
      pctCell.textContent = (up ? "+" : "") + pct.toFixed(2) + "%";
    }
  }

  function fetchInitial() {
    if (!state.symbols.length) return Promise.resolve();
    var query = encodeURIComponent(JSON.stringify(state.symbols));
    return fetch(BINANCE_REST + "?symbols=" + query)
      .then(function (r) {
        if (!r.ok) throw new Error("binance-rest");
        return r.json();
      })
      .then(function (rows) {
        rows.forEach(function (row) {
          applyTicker(row.symbol, row);
        });
        setStatus("Live", true);
      })
      .catch(function () {
        setStatus("Live feed delayed", false);
      });
  }

  function connectWebSocket() {
    if (!state.symbols.length) return;
    if (state.ws) {
      try { state.ws.close(); } catch (e) { /* ignore */ }
      state.ws = null;
    }

    var streams = state.symbols.map(function (s) {
      return s.toLowerCase() + "@ticker";
    }).join("/");

    setStatus("Connecting…", null);
    state.ws = new WebSocket(BINANCE_WS + "?streams=" + streams);

    state.ws.onopen = function () {
      setStatus("Live", true);
    };

    state.ws.onmessage = function (event) {
      try {
        var payload = JSON.parse(event.data);
        var data = payload.data || payload;
        if (data && data.s) applyTicker(data.s, data);
      } catch (e) { /* ignore malformed */ }
    };

    state.ws.onerror = function () {
      setStatus("Connection error", false);
    };

    state.ws.onclose = function () {
      setStatus("Reconnecting…", false);
      clearTimeout(state.reconnectTimer);
      state.reconnectTimer = setTimeout(connectWebSocket, 3000);
    };
  }

  function initLiveTable(config) {
    config = normalizeConfig(config);
    if (!config.symbols.length) return;

    var root = document.querySelector("[data-binance-live-table]");
    if (!root) return;

    if (config.enabled === false) {
      root.hidden = true;
      return;
    }

    state.root = root;
    state.statusEl = root.querySelector("[data-live-status]");
    var titleEl = root.querySelector("[data-live-title]");
    if (titleEl && config.title) titleEl.textContent = config.title;

    root.hidden = false;
    root.classList.add("in");

    if (!buildRows(config)) return;

    if (!state.ready) {
      state.ready = true;
      fetchInitial().then(connectWebSocket);
    }
  }

  function loadLiveTableConfig() {
    return fetch("/api/content/markets", { headers: { Accept: "application/json" } })
      .then(function (r) {
        if (!r.ok) throw new Error("markets");
        return r.json();
      })
      .then(function (d) {
        return d && d.live_table ? d.live_table : null;
      })
      .catch(function () {
        return null;
      });
  }

  function bootLiveTable(config) {
    initLiveTable(config || null);
  }

  document.addEventListener("markets:live-table", function (e) {
    bootLiveTable(e.detail);
  });

  document.addEventListener("cms:loaded", function () {
    if (state.ready) return;
    loadLiveTableConfig().then(bootLiveTable);
  });

  if (document.querySelector("[data-binance-live-table]")) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", function () {
        if (!state.ready) bootLiveTable(null);
      });
    } else if (!state.ready) {
      bootLiveTable(null);
    }
  }

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      if (state.ws) state.ws.close();
    } else if (state.symbols.length) {
      connectWebSocket();
    }
  });
})();
