(function () {
  "use strict";

  var AMCHARTS = [
    "https://cdn.amcharts.com/lib/5/index.js",
    "https://cdn.amcharts.com/lib/5/map.js",
    "https://cdn.amcharts.com/lib/5/geodata/worldLow.js",
    "https://cdn.amcharts.com/lib/5/themes/Animated.js",
  ];

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var globeRoot = null;
  var resizeObserver = null;
  var scriptsPromise = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[src="' + src + '"]');
      if (existing) {
        if (existing.dataset.loaded === "1") resolve();
        else existing.addEventListener("load", resolve, { once: true });
        return;
      }
      var script = document.createElement("script");
      script.src = src;
      script.async = true;
      script.onload = function () {
        script.dataset.loaded = "1";
        resolve();
      };
      script.onerror = function () {
        reject(new Error("Failed to load " + src));
      };
      document.head.appendChild(script);
    });
  }

  function loadAmCharts() {
    if (window.am5 && window.am5map && window.am5geodata_worldLow && window.am5themes_Animated) {
      return Promise.resolve();
    }
    if (!scriptsPromise) {
      scriptsPromise = AMCHARTS.reduce(function (chain, src) {
        return chain.then(function () {
          return loadScript(src);
        });
      }, Promise.resolve());
    }
    return scriptsPromise;
  }

  function disposeGlobe() {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    if (globeRoot) {
      globeRoot.dispose();
      globeRoot = null;
    }
    var chart = document.getElementById("heroGlobeChart");
    if (chart) {
      chart.innerHTML = "";
      delete chart.dataset.globeReady;
    }
  }

  function startRotation(chart) {
    if (reduceMotion || !chart || !window.am5) return;
    var start = chart.get("rotationX", -20);
    chart.animate({
      key: "rotationX",
      from: start,
      to: start - 360,
      duration: 50000,
      loops: Infinity,
      easing: am5.ease.linear,
    });
  }

  function initGlobe() {
    var wrap = document.getElementById("heroMetaGlobe");
    var container = document.getElementById("heroGlobeChart");
    if (!wrap || !container || wrap.hidden) return;
    if (container.dataset.globeReady === "1") return;

    loadAmCharts()
      .then(function () {
        if (!wrap || wrap.hidden || container.dataset.globeReady === "1") return;

        disposeGlobe();

        var root = am5.Root.new("heroGlobeChart");
        globeRoot = root;
        if (root._logo) root._logo.dispose();

        root.setThemes([am5themes_Animated.new(root)]);
        root.container.setAll({
          width: am5.percent(100),
          height: am5.percent(100),
        });

        var chart = root.container.children.push(
          am5map.MapChart.new(root, {
            panX: "none",
            panY: "none",
            projection: am5map.geoOrthographic(),
            width: am5.percent(100),
            height: am5.percent(100),
            centerX: am5.p50,
            centerY: am5.p50,
            paddingTop: 0,
            paddingBottom: 0,
            paddingLeft: 0,
            paddingRight: 0,
          })
        );

        chart.set("zoomLevel", 1);
        chart.set("maxZoomLevel", 1);
        chart.set("minZoomLevel", 1);

        var backgroundSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {}));
        backgroundSeries.mapPolygons.template.setAll({
          fill: am5.color(0x1e3a5f),
          fillOpacity: 1,
          strokeOpacity: 0,
        });
        backgroundSeries.data.push({
          geometry: am5map.getGeoRectangle(90, 180, -90, -180),
        });

        var graticuleSeries = chart.series.unshift(
          am5map.GraticuleSeries.new(root, { step: 12 })
        );
        graticuleSeries.mapLines.template.setAll({
          stroke: am5.color(0xc9a227),
          strokeOpacity: 0.16,
        });

        var polygonSeries = chart.series.push(
          am5map.MapPolygonSeries.new(root, {
            geoJSON: am5geodata_worldLow,
          })
        );
        polygonSeries.mapPolygons.template.setAll({
          fill: am5.color(0x5eb89a),
          stroke: am5.color(0xc9a227),
          strokeOpacity: 0.35,
          strokeWidth: 0.6,
          interactive: false,
        });

        chart.set("rotationX", -20);
        chart.set("rotationY", 0);

        polygonSeries.events.on("datavalidated", function () {
          chart.goHome(0);
          root.resize();
        });

        chart.appear(800, 80);
        container.dataset.globeReady = "1";

        var visual = container.closest(".hero__globe-visual");
        if (visual && window.ResizeObserver) {
          resizeObserver = new ResizeObserver(function () {
            if (globeRoot) globeRoot.resize();
          });
          resizeObserver.observe(visual);
        }

        setTimeout(function () {
          root.resize();
          startRotation(chart);
        }, 300);
      })
      .catch(function (err) {
        console.warn("Hero globe failed to load:", err);
      });
  }

  function boot() {
    requestAnimationFrame(function () {
      requestAnimationFrame(initGlobe);
    });
  }

  document.addEventListener("hero:globe-ready", boot);
  document.addEventListener("cms:loaded", boot);
})();
