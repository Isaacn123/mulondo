(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function initGlobe(canvas) {
    if (!canvas || canvas.dataset.globeReady === "1") return;
    var wrap = canvas.closest(".hero__globe-sphere");
    if (!wrap) return;

    var size = Math.max(wrap.clientWidth || 0, 108);
    if (size < 80) size = 152;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(size * dpr);
    canvas.height = Math.round(size * dpr);
    canvas.style.width = size + "px";
    canvas.style.height = size + "px";

    var ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    var img = new Image();
    var rotation = 0;
    var rafId = 0;

    function draw() {
      var w = size;
      var h = size;
      var cx = w / 2;
      var cy = h / 2;
      var radius = w * 0.46;

      ctx.clearRect(0, 0, w, h);

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.closePath();
      ctx.clip();

      var ocean = ctx.createRadialGradient(cx - radius * 0.25, cy - radius * 0.3, radius * 0.1, cx, cy, radius);
      ocean.addColorStop(0, "#3d7aad");
      ocean.addColorStop(0.55, "#1a4d7a");
      ocean.addColorStop(1, "#0c2238");
      ctx.fillStyle = ocean;
      ctx.fillRect(0, 0, w, h);

      if (img.complete && img.naturalWidth) {
        var mapW = radius * 2.15;
        var mapH = radius * 2.15;
        var offset = rotation * mapW;
        var y = cy - mapH / 2;
        ctx.drawImage(img, cx - radius - offset, y, mapW, mapH);
        ctx.drawImage(img, cx - radius - offset + mapW, y, mapW, mapH);
      }

      ctx.restore();

      ctx.save();
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      var shade = ctx.createRadialGradient(cx - radius * 0.35, cy - radius * 0.35, radius * 0.05, cx, cy, radius);
      shade.addColorStop(0, "rgba(255,255,255,0.34)");
      shade.addColorStop(0.45, "rgba(255,255,255,0.04)");
      shade.addColorStop(1, "rgba(0,0,0,0.42)");
      ctx.fillStyle = shade;
      ctx.fill();
      ctx.restore();

      ctx.strokeStyle = "rgba(212,175,55,0.18)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.stroke();
    }

    function tick() {
      if (!reduceMotion) rotation += 0.0045;
      draw();
      rafId = requestAnimationFrame(tick);
    }

    img.onload = function () {
      canvas.dataset.globeReady = "1";
      if (!rafId) tick();
    };
    img.onerror = function () {
      canvas.dataset.globeReady = "1";
      if (!rafId) tick();
    };
    img.src = "/assets/world-map.svg";
    draw();
    if (!reduceMotion) rafId = requestAnimationFrame(tick);
  }

  function boot() {
    document.querySelectorAll(".hero__globe-canvas").forEach(initGlobe);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
  document.addEventListener("cms:loaded", boot);
  document.addEventListener("hero:globe-ready", boot);
})();
