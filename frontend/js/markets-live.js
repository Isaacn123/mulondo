(function () {
  "use strict";

  var BINANCE_WS = "wss://stream.binance.com:9443/stream";
  var BINANCE_REST = "https://api.binance.com/api/v3/ticker/24hr";

  var state = {
    symbols: [],
    meta: {},
    ws: null,
    reconnectTimer: null,
    flashTimers: {}
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
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
    var el = document.getElementById("marketsLiveStatus");
    if (!el) return;
    el.textContent = text;
    el.classList.toggle("is-live", !!ok);
    el.classList.toggle("is-error", ok === false);
  }

  function rowClass(index) {
    return index % 2 === 0 ? "markets-live-table__row" : "markets-live-table__row markets-live-table__row--alt";
  }

  function buildRows(config) {
    var tbody = document.getElementById("marketsLiveBody");
    if (!tbody) return;

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
  }

  function flashCell(cell) {
    if (!cell) return;
    cell.classList.add("is-flash");
    var key = cell.closest("[data-symbol]") ? cell.closest("[data-symbol]").getAttribute("data-symbol") + "-last" : "cell";
    clearTimeout(state.flashTimers[key]);
    state.flashTimers[key] = setTimeout(function () {
      cell.classList.remove("is-flash");
    }, 700);
  }

  function applyTicker(symbol, ticker) {
    var row = document.querySelector('#marketsLiveBody tr[data-symbol="' + symbol + '"]');
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
      if (prev && prev !== next) flashCell(lastCell);
      lastCell.setAttribute("data-value", next);
      lastCell.textContent = formatPrice(last, meta.decimals);
    }

    if (changeCell && changeText) {
      changeCell.classList.toggle("is-up", up);
      changeCell.classList.toggle("is-down", !up);
      changeText.textContent = formatChange(change, meta.decimals);
      var arrow = changeCell.querySelector(".markets-live-table__arrow");
      if (arrow) arrow.className = "markets-live-table__arrow " + (up ? "is-up" : "is-down");
    }

    if (pctCell) {
      pctCell.classList.toggle("is-up", up);
      pctCell.classList.toggle("is-down", !up);
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
    if (!config || !config.symbols || !config.symbols.length) return;

    var panel = document.getElementById("marketsLivePanel");
    if (panel) {
      panel.hidden = false;
      panel.classList.add("in");
    }

    var title = document.getElementById("marketsLiveTitle");
    if (title && config.title) title.textContent = config.title;

    var tbody = document.getElementById("marketsLiveBody");
    if (tbody) tbody.innerHTML = "";

    buildRows(config);
    fetchInitial().then(connectWebSocket);
  }

  document.addEventListener("markets:live-table", function (e) {
    initLiveTable(e.detail);
  });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      if (state.ws) state.ws.close();
    } else if (state.symbols.length) {
      connectWebSocket();
    }
  });
})();
