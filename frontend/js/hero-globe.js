(function () {
  "use strict";

  var COBE_URL = "https://cdn.jsdelivr.net/npm/cobe@0.6.4/+esm";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var globeDestroy = null;
  var resizeObserver = null;
  var phi = 0;

  function measure(canvas) {
    var visual = canvas.closest(".hero__globe-visual");
    if (!visual) return 200;
    return Math.max(Math.round(visual.clientWidth), 140);
  }

  function disposeGlobe(canvas) {
    if (resizeObserver) {
      resizeObserver.disconnect();
      resizeObserver = null;
    }
    if (globeDestroy) {
      globeDestroy();
      globeDestroy = null;
    }
    phi = 0;
    if (canvas) {
      var ctx = canvas.getContext("2d");
      if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
      delete canvas.dataset.globeReady;
    }
  }

  function createHeroGlobe(canvas, createGlobe) {
    var size = measure(canvas);
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var px = Math.round(size * dpr);

    canvas.width = px;
    canvas.height = px;
    canvas.style.width = size + "px";
    canvas.style.height = size + "px";

    return createGlobe(canvas, {
      devicePixelRatio: dpr,
      width: px,
      height: px,
      phi: 0,
      theta: 0.22,
      dark: 1,
      diffuse: 1.15,
      mapSamples: 14000,
      mapBrightness: 5.5,
      baseColor: [0.11, 0.2, 0.33],
      markerColor: [0.79, 0.64, 0.15],
      glowColor: [0.79, 0.64, 0.15],
      markers: [
        { location: [32.5825, 0.3476], size: 0.06 },
        { location: [36.8219, -1.2921], size: 0.05 },
        { location: [28.0473, -26.2041], size: 0.05 },
        { location: [3.3792, 6.5244], size: 0.05 },
        { location: [31.2357, 30.0444], size: 0.04 },
      ],
      onRender: function (state) {
        if (!reduceMotion) phi += 0.004;
        state.phi = phi;
      },
    });
  }

  function initGlobe() {
    var wrap = document.getElementById("heroMetaGlobe");
    var canvas = document.getElementById("heroGlobeCanvas");
    if (!wrap || !canvas || wrap.hidden) return;
    if (canvas.dataset.globeReady === "1") return;

    import(COBE_URL)
      .then(function (mod) {
        if (!wrap || wrap.hidden || canvas.dataset.globeReady === "1") return;
        var createGlobe = mod.default;
        if (!createGlobe) throw new Error("cobe module missing default export");

        disposeGlobe(canvas);
        globeDestroy = createHeroGlobe(canvas, createGlobe);
        canvas.dataset.globeReady = "1";

        var visual = canvas.closest(".hero__globe-visual");
        if (visual && window.ResizeObserver) {
          resizeObserver = new ResizeObserver(function () {
            if (!canvas.dataset.globeReady) return;
            disposeGlobe(canvas);
            globeDestroy = createHeroGlobe(canvas, mod.default);
            canvas.dataset.globeReady = "1";
          });
          resizeObserver.observe(visual);
        }
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
