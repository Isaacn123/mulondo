(function () {
  "use strict";

  var SCRIPTS = [
    "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js",
    "https://cdn.jsdelivr.net/npm/globe.gl@2.34.0/dist/globe.gl.min.js",
  ];
  var PLACES_URL =
    "https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_populated_places_simple.geojson";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var globeInstance = null;
  var resizeObserver = null;
  var scriptsPromise = null;
  var rafId = 0;

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
    if (window.THREE && window.Globe) return Promise.resolve();
    if (!scriptsPromise) {
      scriptsPromise = SCRIPTS.reduce(function (chain, src) {
        return chain.then(function () {
          return loadScript(src);
        });
      }, Promise.resolve());
    }
    return scriptsPromise;
  }

  function measureSize(mount) {
    var visual = mount.closest(".hero__globe-visual");
    var el = visual || mount;
    var rect = el.getBoundingClientRect();
    var size = Math.round(Math.min(rect.width, rect.height));
    return Math.max(size, 140);
  }

  function disposeGlobe(mount) {
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    globeInstance = null;
    if (mount) {
      mount.innerHTML = "";
      delete mount.dataset.globeReady;
    }
  }

  function resizeGlobe(mount) {
    if (!globeInstance || !mount) return;
    var size = measureSize(mount);
    mount.style.width = size + "px";
    mount.style.height = size + "px";
    globeInstance.width(size).height(size);
  }

  function startRotation() {
    if (!globeInstance || reduceMotion) return;
    var controls = globeInstance.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.45;
      controls.enableZoom = false;
      controls.enablePan = false;
    }
  }

  function buildGlobe(mount) {
    var size = measureSize(mount);
    mount.style.width = size + "px";
    mount.style.height = size + "px";

    var globe = Globe()(mount)
      .width(size)
      .height(size)
      .backgroundColor("rgba(0,0,0,0)")
      .showGlobe(true)
      .globeImageUrl(null)
      .globeMaterial(
        new THREE.MeshPhongMaterial({
          color: 0x1a3352,
          transparent: true,
          opacity: 0.92,
        })
      )
      .showAtmosphere(true)
      .atmosphereColor("rgba(201,162,39,0.22)")
      .atmosphereAltitude(0.18)
      .pointAltitude(0.015)
      .pointRadius(0.22)
      .pointColor(function () {
        return "#c9a227";
      });

    globe.pointOfView({ lat: 8, lng: 18, altitude: 1.75 });
    globeInstance = globe;
    startRotation();

    return fetch(PLACES_URL)
      .then(function (res) {
        return res.json();
      })
      .then(function (geo) {
        var points = (geo.features || []).map(function (feature) {
          var props = feature.properties || {};
          return {
            lat: props.latitude,
            lng: props.longitude,
            pop: props.pop_max || 50000,
          };
        });
        globe.pointsData(points).pointRadius(function (d) {
          return Math.min(0.42, 0.12 + Math.sqrt(d.pop) * 0.00004);
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
