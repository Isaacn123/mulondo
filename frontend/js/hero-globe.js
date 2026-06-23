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

  function initGlobe() {
    var globe = document.getElementById("heroGlobe");
    var container = document.getElementById("heroGlobeChart");
    if (!globe || !container || globe.hidden) return;
    if (container.dataset.globeReady === "1") return;

    loadAmCharts()
      .then(function () {
        if (!globe || globe.hidden || container.dataset.globeReady === "1") return;

        disposeGlobe();

        var root = am5.Root.new("heroGlobeChart");
        globeRoot = root;
        if (root._logo) root._logo.dispose();

        root.setThemes([am5themes_Animated.new(root)]);

        var chart = root.container.children.push(
          am5map.MapChart.new(root, {
            panX: "rotateX",
            panY: "rotateY",
            projection: am5map.geoOrthographic(),
            paddingBottom: 0,
            paddingTop: 0,
            paddingLeft: 0,
            paddingRight: 0,
          })
        );

        var backgroundSeries = chart.series.push(am5map.MapPolygonSeries.new(root, {}));
        backgroundSeries.mapPolygons.template.setAll({
          fill: am5.color(0x1a3352),
          fillOpacity: 1,
          strokeOpacity: 0,
        });
        backgroundSeries.data.push({
          geometry: am5map.getGeoRectangle(90, 180, -90, -180),
        });

        var graticuleSeries = chart.series.unshift(
          am5map.GraticuleSeries.new(root, { step: 10 })
        );
        graticuleSeries.mapLines.template.setAll({
          stroke: am5.color(0xd4af37),
          strokeOpacity: 0.14,
        });

        var polygonSeries = chart.series.push(
          am5map.MapPolygonSeries.new(root, {
            geoJSON: am5geodata_worldLow,
          })
        );
        polygonSeries.mapPolygons.template.setAll({
          fill: am5.color(0x4a9e78),
          stroke: am5.color(0xd4af37),
          strokeOpacity: 0.28,
          strokeWidth: 0.5,
          interactive: false,
        });

        chart.set("rotationX", -25);
        chart.set("rotationY", 18);

        if (!reduceMotion) {
          var rotation = -25;
          chart.events.on("frameended", function () {
            rotation -= 0.12;
            chart.set("rotationX", rotation);
          });
        }

        chart.appear(1000, 100);
        container.dataset.globeReady = "1";
        setTimeout(function () {
          root.resize();
        }, 120);
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
