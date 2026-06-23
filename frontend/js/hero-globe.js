(function () {
  "use strict";

  var GLOBE_SCRIPT = "https://cdn.jsdelivr.net/npm/globe.gl@2.34.0/dist/globe.gl.min.js";
  var COUNTRIES_URL =
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson";
  var PLACES_URL =
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_populated_places_simple.geojson";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var globeInstance = null;
  var resizeObserver = null;
  var scriptPromise = null;

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

  function loadGlobeGl() {
    if (window.Globe) return Promise.resolve();
    if (!scriptPromise) scriptPromise = loadScript(GLOBE_SCRIPT);
    return scriptPromise;
  }

  function measureSize(mount) {
    var visual = mount.closest(".hero__globe-visual");
    if (!visual) return 240;
    var rect = visual.getBoundingClientRect();
    var size = Math.round(Math.min(rect.width, rect.height));
    return Math.max(size, 180);
  }

  function disposeGlobe(mount) {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    globeInstance = null;
    if (mount) {
      mount.innerHTML = "";
      mount.removeAttribute("style");
      delete mount.dataset.globeReady;
    }
  }

  function resizeGlobe(mount) {
    if (!globeInstance || !mount) return;
    var size = measureSize(mount);
    mount.style.width = size + "px";
    mount.style.height = size + "px";
    globeInstance.width(size).height(size);
    var renderer = globeInstance.renderer && globeInstance.renderer();
    if (renderer && renderer.setPixelRatio) {
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    }
  }

  function startRotation() {
    if (!globeInstance || reduceMotion) return;
    var controls = globeInstance.controls();
    if (!controls) return;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.4;
    controls.enableZoom = false;
    controls.enablePan = false;
  }

  function buildGlobe(mount) {
    var size = measureSize(mount);
    mount.style.width = size + "px";
    mount.style.height = size + "px";

    var THREE = window.THREE;
    var globe = Globe()(mount)
      .width(size)
      .height(size)
      .backgroundColor("rgba(0,0,0,0)")
      .showGlobe(true)
      .globeImageUrl(null)
      .globeMaterial(
        new THREE.MeshPhongMaterial({
          color: 0x1a3352,
          emissive: 0x0a1628,
          shininess: 12,
        })
      )
      .showAtmosphere(true)
      .atmosphereColor("#c9a227")
      .atmosphereAltitude(0.2)
      .pointAltitude(0.02)
      .pointColor(function () {
        return "#e8c873";
      });

    globe.pointOfView({ lat: 4, lng: 22, altitude: 1.55 });
    globeInstance = globe;
    startRotation();

    var renderer = globe.renderer && globe.renderer();
    if (renderer && renderer.setPixelRatio) {
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    }

    return Promise.all([
      fetch(COUNTRIES_URL).then(function (res) {
        return res.json();
      }),
      fetch(PLACES_URL).then(function (res) {
        return res.json();
      }),
    ])
      .then(function (results) {
        var countries = results[0];
        var places = results[1];

        globe
          .polygonsData(countries.features || [])
          .polygonCapColor(function () {
            return "rgba(201, 162, 39, 0.42)";
          })
          .polygonSideColor(function () {
            return "rgba(26, 51, 82, 0.35)";
          })
          .polygonStrokeColor(function () {
            return "rgba(232, 200, 115, 0.55)";
          })
          .polygonAltitude(0.012);

        var points = (places.features || []).map(function (feature) {
          var props = feature.properties || {};
          return {
            lat: props.latitude,
            lng: props.longitude,
            pop: props.pop_max || 50000,
          };
        });

        globe.pointsData(points).pointRadius(function (d) {
          return Math.min(0.55, 0.18 + Math.sqrt(d.pop) * 0.00005);
        });

        resizeGlobe(mount);
      })
      .catch(function () {
        resizeGlobe(mount);
      });
  }

  function initGlobe() {
    var wrap = document.getElementById("heroMetaGlobe");
    var mount = document.getElementById("heroGlobeMount");
    if (!wrap || !mount || wrap.hidden) return;
    if (mount.dataset.globeReady === "1") return;

    loadGlobeGl()
      .then(function () {
        if (!wrap || wrap.hidden || mount.dataset.globeReady === "1") return;
        disposeGlobe(mount);
        return buildGlobe(mount);
      })
      .then(function () {
        if (!mount || mount.dataset.globeReady === "1") return;
        mount.dataset.globeReady = "1";

        var visual = mount.closest(".hero__globe-visual");
        if (visual && window.ResizeObserver) {
          resizeObserver = new ResizeObserver(function () {
            resizeGlobe(mount);
          });
          resizeObserver.observe(visual);
        }

        setTimeout(function () {
          resizeGlobe(mount);
        }, 350);
        setTimeout(function () {
          resizeGlobe(mount);
        }, 900);
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
