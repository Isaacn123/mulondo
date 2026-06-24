(function () {
  "use strict";

  var state = {
    screens: [],
    index: 0,
    answers: {},
    selected: null,
    selectedMulti: [],
    ready: false,
    navBound: false
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function byId(id) {
    return document.getElementById(id);
  }

  function slideHtml(screen, i) {
    var type = screen.type || "welcome";
    var inner = "";

    if (type === "welcome") {
      inner =
        (screen.eyebrow ? '<p class="survey-slide__eyebrow">' + esc(screen.eyebrow) + "</p>" : "") +
        '<h3 class="survey-slide__title">' + esc(screen.title) + "</h3>" +
        (screen.subtitle ? '<p class="survey-slide__subtitle">' + esc(screen.subtitle) + "</p>" : "") +
        (screen.body ? '<p class="survey-slide__body">' + esc(screen.body) + "</p>" : "");
    } else if (type === "choice") {
      var opts = (screen.options || []).map(function (opt, oi) {
        return (
          '<button type="button" class="survey-option" data-index="' + oi + '" data-value="' + esc(opt.value || opt.label) + '">' +
          '<span class="survey-option__dot" aria-hidden="true"></span>' +
          '<span class="survey-option__label">' + esc(opt.label) + "</span>" +
          "</button>"
        );
      }).join("");
      inner =
        '<h3 class="survey-slide__title">' + esc(screen.title) + "</h3>" +
        (screen.subtitle ? '<p class="survey-slide__subtitle">' + esc(screen.subtitle) + "</p>" : "") +
        '<div class="survey-options' + (screen.allow_multiple ? " survey-options--multi" : "") + '" role="' +
        (screen.allow_multiple ? "group" : "radiogroup") + '">' + opts + "</div>";
    } else if (type === "text") {
      inner =
        '<h3 class="survey-slide__title">' + esc(screen.title) + "</h3>" +
        (screen.subtitle ? '<p class="survey-slide__subtitle">' + esc(screen.subtitle) + "</p>" : "") +
        '<label class="survey-input-wrap">' +
        '<span class="visually-hidden">' + esc(screen.title) + "</span>" +
        '<input type="text" class="survey-input" data-survey-text data-key="' + esc(screen.key) + '" placeholder="' + esc(screen.placeholder || "Your answer") + '" autocomplete="off">' +
        "</label>";
    } else if (type === "complete") {
      inner =
        '<div class="survey-complete" aria-hidden="true"><span class="survey-complete__icon">✓</span></div>' +
        '<h3 class="survey-slide__title">' + esc(screen.title) + "</h3>" +
        (screen.body ? '<p class="survey-slide__body">' + esc(screen.body) + "</p>" : "");
    }

    return (
      '<article class="survey-slide survey-slide--' + esc(type) + '" data-index="' + i + '" data-type="' + esc(type) + '" data-key="' + esc(screen.key) + '">' +
      inner +
      "</article>"
    );
  }

  function renderProgress() {
    var progress = byId("surveyProgress");
    if (!progress || !state.screens.length) return;
    progress.innerHTML = state.screens.map(function (_, i) {
      var cls = "survey__dot";
      if (i < state.index) cls += " is-done";
      if (i === state.index) cls += " is-active";
      return '<span class="' + cls + '"></span>';
    }).join("");
  }

  function currentScreen() {
    return state.screens[state.index] || null;
  }

  function activeTextInput() {
    var slide = document.querySelector('.survey-slide[data-index="' + state.index + '"]');
    return slide ? slide.querySelector("[data-survey-text]") : null;
  }

  function restoreSelection() {
    var screen = currentScreen();
    if (!screen) return;
    var key = screen.key;
    var saved = state.answers[key];
    state.selected = null;
    state.selectedMulti = [];

    if (screen.type === "choice") {
      if (screen.allow_multiple && Array.isArray(saved)) {
        state.selectedMulti = saved.slice();
      } else if (saved != null) {
        state.selected = saved;
      }
      var slide = document.querySelector('.survey-slide[data-index="' + state.index + '"]');
      if (!slide) return;
      slide.querySelectorAll(".survey-option").forEach(function (btn) {
        var val = btn.getAttribute("data-value");
        var on = screen.allow_multiple
          ? state.selectedMulti.indexOf(val) !== -1
          : state.selected === val;
        btn.classList.toggle("is-selected", on);
        btn.setAttribute("aria-pressed", on ? "true" : "false");
      });
    } else if (screen.type === "text") {
      var input = activeTextInput();
      if (input) input.value = saved || "";
    }
  }

  function showSlide(direction) {
    var slides = document.querySelectorAll(".survey-slide");
    slides.forEach(function (el, i) {
      el.classList.remove("is-active", "is-exit-left", "is-enter-right");
      if (i === state.index) el.classList.add("is-active");
    });
    if (direction === "forward" && slides[state.index]) {
      slides[state.index].classList.add("is-enter-right");
      requestAnimationFrame(function () {
        slides[state.index].classList.remove("is-enter-right");
      });
    }
    renderProgress();
    updateNav();
    restoreSelection();
  }

  function canAdvance() {
    var screen = currentScreen();
    if (!screen) return false;
    if (screen.type === "welcome" || screen.type === "complete") return true;
    if (screen.type === "text") {
      var input = activeTextInput();
      return !!(input && input.value.trim());
    }
    if (screen.type === "choice") {
      if (screen.allow_multiple) return state.selectedMulti.length > 0;
      return state.selected != null;
    }
    return true;
  }

  function saveCurrentAnswer() {
    var screen = currentScreen();
    if (!screen || screen.type === "welcome" || screen.type === "complete") return;
    if (screen.type === "choice") {
      state.answers[screen.key] = screen.allow_multiple ? state.selectedMulti.slice() : state.selected;
    } else if (screen.type === "text") {
      var input = activeTextInput();
      state.answers[screen.key] = input ? input.value.trim() : "";
    }
  }

  function updateNav() {
    var back = byId("surveyBack");
    var next = byId("surveyNext");
    var screen = currentScreen();
    if (back) back.hidden = state.index <= 0;
    if (!next || !screen) return;
    next.textContent = screen.button_text || "Continue";
    next.disabled = screen.type !== "welcome" && screen.type !== "complete" && !canAdvance();
  }

  function bindSlides() {
    document.querySelectorAll(".survey-option").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var slide = btn.closest(".survey-slide");
        if (!slide) return;
        var idx = parseInt(slide.getAttribute("data-index"), 10);
        var screen = state.screens[idx];
        if (!screen) return;
        var val = btn.getAttribute("data-value");

        if (screen.allow_multiple) {
          var pos = state.selectedMulti.indexOf(val);
          if (pos === -1) state.selectedMulti.push(val);
          else state.selectedMulti.splice(pos, 1);
          slide.querySelectorAll(".survey-option").forEach(function (b) {
            var v = b.getAttribute("data-value");
            var on = state.selectedMulti.indexOf(v) !== -1;
            b.classList.toggle("is-selected", on);
            b.setAttribute("aria-pressed", on ? "true" : "false");
          });
        } else {
          state.selected = val;
          slide.querySelectorAll(".survey-option").forEach(function (b) {
            var on = b === btn;
            b.classList.toggle("is-selected", on);
            b.setAttribute("aria-pressed", on ? "true" : "false");
          });
          saveCurrentAnswer();
          setTimeout(advance, 280);
          return;
        }
        updateNav();
      });
    });

    document.querySelectorAll("[data-survey-text]").forEach(function (textInput) {
      textInput.addEventListener("input", updateNav);
      textInput.addEventListener("keydown", function (e) {
        if (e.key === "Enter" && canAdvance()) {
          e.preventDefault();
          advance();
        }
      });
    });
  }

  function advance() {
    var screen = currentScreen();
    if (!screen) return;

    if (screen.type === "complete") {
      closeModal();
      var href = (screen.cta_link || "/membership").trim();
      if (href) window.location.href = href;
      return;
    }

    saveCurrentAnswer();
    if (state.index >= state.screens.length - 1) return;
    state.index += 1;
    showSlide("forward");
  }

  function goBack() {
    if (state.index <= 0) return;
    saveCurrentAnswer();
    state.index -= 1;
    showSlide("back");
  }

  function resetWizard() {
    state.index = 0;
    state.answers = {};
    state.selected = null;
    state.selectedMulti = [];
    showSlide("init");
  }

  function openModal() {
    if (!state.ready || !state.screens.length) return;
    var modal = byId("surveyModal");
    if (!modal) return;
    resetWizard();
    modal.hidden = false;
    modal.setAttribute("aria-hidden", "false");
    modal.classList.add("is-open");
    document.body.classList.add("survey-modal-open");
    var closeBtn = byId("surveyClose");
    if (closeBtn) closeBtn.focus();
  }

  function closeModal() {
    var modal = byId("surveyModal");
    if (!modal) return;
    modal.classList.remove("is-open");
    modal.hidden = true;
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("survey-modal-open");
    var openBtn = byId("surveyOpen");
    if (openBtn) openBtn.focus();
  }

  function bindModalControls() {
    var openBtn = byId("surveyOpen");
    var closeBtn = byId("surveyClose");
    var modal = byId("surveyModal");

    if (openBtn) openBtn.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);

    if (modal) {
      modal.querySelectorAll("[data-survey-close]").forEach(function (el) {
        el.addEventListener("click", closeModal);
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && modal && modal.classList.contains("is-open")) {
        e.preventDefault();
        closeModal();
      }
    });
  }

  function bindNavControls() {
    if (state.navBound) return;
    var back = byId("surveyBack");
    var next = byId("surveyNext");
    if (back) back.addEventListener("click", goBack);
    if (next) next.addEventListener("click", advance);
    state.navBound = true;
  }

  function initSurvey(data) {
    if (!data || !data.screens || !data.screens.length) return;

    state.screens = data.screens;
    var slidesEl = byId("surveySlides");
    var modalTitle = byId("surveyModalTitle");
    if (!slidesEl) return;

    slidesEl.innerHTML = state.screens.map(slideHtml).join("");
    if (modalTitle && data.eyebrow) modalTitle.textContent = data.eyebrow + " Survey";

    bindSlides();
    bindNavControls();
    resetWizard();
    state.ready = true;
  }

  bindModalControls();

  document.addEventListener("survey:init", function (e) {
    initSurvey(e.detail);
  });
})();
