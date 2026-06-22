(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function setText(id, value) {
    var el = document.getElementById(id);
    if (el && value != null) el.textContent = value;
  }

  function initMembershipForm(tiers) {
    var tierSelect = document.getElementById("mTier");
    if (tierSelect && tiers && tiers.length) {
      tiers.forEach(function (t) {
        var opt = document.createElement("option");
        opt.value = t.name || "";
        opt.textContent = t.name || "Tier";
        tierSelect.appendChild(opt);
      });
    }

    var form = document.getElementById("membershipRequestForm");
    var status = document.getElementById("membershipFormStatus");
    if (!form) return;

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (status) { status.textContent = "Sending…"; status.className = "form__status"; }

      var data = new FormData(form);
      var payload = {
        name: data.get("name") || "",
        email: data.get("email") || "",
        phone: data.get("phone") || "",
        country: data.get("country") || "",
        tier: data.get("tier") || "",
        message: data.get("message") || ""
      };

      fetch("/api/submissions/membership", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload)
      })
        .then(function (r) { return r.json().then(function (body) { return { ok: r.ok, body: body }; }); })
        .then(function (res) {
          if (res.ok) {
            form.reset();
            if (status) {
              status.textContent = (res.body && res.body.message) || "Thank you — your membership request has been received.";
              status.className = "form__status ok";
            }
          } else {
            var detail = (res.body && res.body.detail) || "Something went wrong. Please try again.";
            if (status) {
              status.textContent = typeof detail === "string" ? detail : "Please check the form and try again.";
              status.className = "form__status err";
            }
          }
        })
        .catch(function () {
          if (status) { status.textContent = "Network error. Please try again later."; status.className = "form__status err"; }
        });
    });
  }

  fetch("/api/content/membership", { headers: { Accept: "application/json" } })
    .then(function (r) {
      if (!r.ok) throw new Error("membership");
      return r.json();
    })
    .then(function (d) {
      if (d.page_description) {
        var meta = document.getElementById("metaDescription");
        if (meta) meta.setAttribute("content", d.page_description);
      }

      var eyebrow = document.getElementById("mEyebrow");
      if (eyebrow) eyebrow.innerHTML = '<span class="eyebrow__dot"></span> ' + esc(d.eyebrow);
      var title = document.getElementById("mTitle");
      if (title) title.innerHTML = esc(d.title_before) + ' <span class="grad">' + esc(d.title_highlight) + "</span>";
      setText("mIntro", d.intro);
      setText("mOverviewTitle", d.overview_title);
      setText("mOverviewText", d.overview_text);
      setText("mCertTitle", d.certification_title);
      setText("mCertText", d.certification_text);
      setText("mEnrollTitle", d.enroll_title);
      setText("mEnrollSubtitle", d.enroll_subtitle);

      var btn = document.getElementById("mEnrollBtn");
      if (btn && d.enroll_button_text) {
        btn.innerHTML = esc(d.enroll_button_text) + ' <span class="btn__arrow">&rarr;</span>';
      }

      var modules = document.getElementById("mModules");
      if (modules && d.modules) {
        modules.innerHTML = d.modules.map(function (m) {
          return '<article class="membership-module reveal in"><h3>' + esc(m.title) + "</h3><p>" + esc(m.description) + "</p></article>";
        }).join("");
      }

      var tiers = d.tiers || [];
      var tiersEl = document.getElementById("mTiers");
      if (tiersEl && tiers.length) {
        tiersEl.innerHTML = tiers.map(function (t) {
          var feats = (t.features || []).map(function (f) {
            return "<li>" + esc(f) + "</li>";
          }).join("");
          return (
            '<article class="membership-tier reveal in' + (t.highlighted ? " membership-tier--hi" : "") + '">' +
              "<h3>" + esc(t.name) + "</h3>" +
              '<p class="membership-tier__price"><strong>' + esc(t.price) + "</strong>" + esc(t.period || "") + "</p>" +
              "<ul>" + feats + "</ul>" +
              '<a href="#enroll" class="btn ' + (t.highlighted ? "btn--gold" : "btn--ghost") + ' btn--block">' +
                esc(t.cta_text || "Enroll") + ' <span class="btn__arrow">&rarr;</span></a>' +
            "</article>"
          );
        }).join("");
      }

      initMembershipForm(tiers);

      var benefits = document.getElementById("mBenefits");
      if (benefits && d.benefits) {
        benefits.innerHTML = d.benefits.map(function (b) {
          return "<li>" + esc(b) + "</li>";
        }).join("");
      }

      var outcomes = document.getElementById("mCertOutcomes");
      if (outcomes && d.certification_outcomes) {
        outcomes.innerHTML = d.certification_outcomes.map(function (o) {
          return "<li>" + esc(o) + "</li>";
        }).join("");
      }
    })
    .catch(function () {
      setText("mIntro", "Unable to load membership program details. Please try again later or contact us.");
      initMembershipForm([]);
    });
})();
