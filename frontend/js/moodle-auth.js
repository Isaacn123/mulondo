(function () {
  "use strict";

  function setStatus(el, msg, ok) {
    if (!el) return;
    el.textContent = msg;
    el.className = "form__status" + (ok ? " ok" : msg ? " err" : "");
  }

  function postAuth(path, body) {
    return fetch("/api/auth/moodle/" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body)
    });
  }

  var registerForm = document.getElementById("moodleRegisterForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("moodleRegisterStatus");
      var pw = document.getElementById("moodleRegPassword").value;
      var pw2 = document.getElementById("moodleRegPassword2").value;
      if (pw !== pw2) {
        setStatus(status, "Passwords do not match.", false);
        return;
      }
      if (pw.length < 8) {
        setStatus(status, "Password must be at least 8 characters.", false);
        return;
      }
      if (!document.getElementById("moodleRegTerms").checked) {
        setStatus(status, "Please accept the terms to continue.", false);
        return;
      }
      var payload = {
        first_name: document.getElementById("moodleRegFirst").value.trim(),
        last_name: document.getElementById("moodleRegLast").value.trim(),
        email: document.getElementById("moodleRegEmail").value.trim(),
        password: pw
      };
      setStatus(status, "Creating your Moodle account…", true);
      postAuth("register", payload)
        .then(function (r) {
          if (r.ok) return r.json();
          return r.json().then(function (d) { throw new Error(d.detail || "auth"); });
        })
        .then(function () {
          setStatus(status, "Account created — redirecting to Moodle sign in…", true);
          setTimeout(function () { window.location.href = "/moodle/login"; }, 1200);
        })
        .catch(function (err) {
          setStatus(status, err.message || "Could not create account. Email may already be registered.", false);
        });
    });
  }

  var loginForm = document.getElementById("moodleLoginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("moodleLoginStatus");
      var email = document.getElementById("moodleLoginEmail").value.trim();
      var password = document.getElementById("moodleLoginPassword").value;
      if (!email || !password) {
        setStatus(status, "Please enter your email and password.", false);
        return;
      }
      setStatus(status, "Signing in…", true);
      postAuth("login", { email: email, password: password })
        .then(function (r) {
          if (r.ok) return r.json();
          return r.json().then(function (d) { throw new Error(d.detail || "auth"); });
        })
        .then(function (data) {
          window.location.href = data.redirect || "/moodle/";
        })
        .catch(function (err) {
          var msg = "Invalid email or password. Please try again.";
          if (err && err.message && err.message !== "auth") msg = err.message;
          setStatus(status, msg, false);
        });
    });
  }
})();
