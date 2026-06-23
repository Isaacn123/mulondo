/**
 * Backup: amCharts 5 orthographic hero globe (duplicate of active hero-globe.js).
 * Swap script in index.html if you want this loaded from a separate file.
 */
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

  function measureGlobeSize(container) {
    var visual = container.closest(".hero__globe-visual");
    var sphere = container.closest(".hero__globe-sphere");
    var el = visual || sphere;
    if (!el) return 220;
    var rect = el.getBoundingClientRect();
    var size = Math.round(Math.min(rect.width, rect.height));
    return Math.max(size, 160);
  }

  function applyChartBox(container, root) {
    var size = measureGlobeSize(container);
    container.style.width = size + "px";
    container.style.height = size + "px";
    container.style.transform = "translate(-50%, -50%) scale(1.1)";
    if (root) root.resize();
    return size;
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
      chart.removeAttribute("style");
      delete chart.dataset.globeReady;
    }
  }

  function fitGlobe(chart, root, container) {
    applyChartBox(container, root);
    if (!chart) return;
    chart.set("zoomLevel", 1);
    chart.set("maxZoomLevel", 1);
    chart.set("minZoomLevel", 1);
    chart.set("rotationX", -20);
    chart.set("rotationY", 0);
    chart.goHome(0);
    if (root) root.resize();
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
    var globe = document.getElementById("heroMetaGlobe");
    var container = document.getElementById("heroGlobeChart");
    if (!globe || !container || globe.hidden) return;
    if (container.dataset.globeReady === "1") return;

    loadAmCharts()
      .then(function () {
        if (!globe || globe.hidden || container.dataset.globeReady === "1") return;

        disposeGlobe();
        applyChartBox(container);

        var root = am5.Root.new("heroGlobeChart");
        globeRoot = root;
        if (root._logo) root._logo.dispose();

        root.setThemes([am5themes_Animated.new(root)]);

        var chart = root.container.children.push(
          am5map.MapChart.new(root, {
            panX: "rotateX",
            panY: "rotateY",
            projection: am5map.geoOrthographic(),
            paddingTop: 0,
            paddingBottom: 0,
            paddingLeft: 0,
            paddingRight: 0,
          })
        );

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

        polygonSeries.events.on("datavalidated", function () {
          fitGlobe(chart, root, container);
        });

        chart.appear(800, 80);
        container.dataset.globeReady = "1";

        var visual = container.closest(".hero__globe-visual");
        if (visual && window.ResizeObserver) {
          resizeObserver = new ResizeObserver(function () {
            if (globeRoot) fitGlobe(chart, globeRoot, container);
          });
          resizeObserver.observe(visual);
        }

        setTimeout(function () {
          fitGlobe(chart, root, container);
          startRotation(chart);
        }, 300);
      })
      .catch(function (err) {
        console.warn("Hero globe (amCharts backup) failed to load:", err);
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
