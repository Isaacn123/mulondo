(function () {
  "use strict";

  function setStatus(el, msg, ok) {
    if (!el) return;
    el.textContent = msg;
    el.className = "form__status" + (ok ? " ok" : msg ? " err" : "");
  }

  function postAuth(path, body) {
    return fetch("/api/auth/" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body)
    });
  }

  var loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("loginStatus");
      var email = document.getElementById("loginEmail").value.trim();
      var password = document.getElementById("loginPassword").value;
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
          window.location.href = data.redirect || "/investors/";
        })
        .catch(function (err) {
          var msg = "Invalid email or password. Please try again.";
          if (err && err.message && err.message !== "auth") msg = err.message;
          setStatus(status, msg, false);
        });
    });
  }

  var registerForm = document.getElementById("registerForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("registerStatus");
      var pw = document.getElementById("regPassword").value;
      var pw2 = document.getElementById("regPassword2").value;
      if (pw !== pw2) {
        setStatus(status, "Passwords do not match.", false);
        return;
      }
      if (pw.length < 8) {
        setStatus(status, "Password must be at least 8 characters.", false);
        return;
      }
      if (!document.getElementById("regTerms").checked) {
        setStatus(status, "Please accept the terms to continue.", false);
        return;
      }
      var payload = {
        first_name: document.getElementById("regFirst").value.trim(),
        last_name: document.getElementById("regLast").value.trim(),
        email: document.getElementById("regEmail").value.trim(),
        password: pw
      };
      setStatus(status, "Creating your account…", true);
      postAuth("register", payload)
        .then(function (r) {
          if (r.ok) return r.json();
          return r.json().then(function (d) { throw new Error(d.detail || "auth"); });
        })
        .then(function () {
          setStatus(status, "Account created — you can sign in now.", true);
          setTimeout(function () { window.location.href = "/login"; }, 1200);
        })
        .catch(function (err) {
          setStatus(status, err.message || "Could not create account. Email may already be registered.", false);
        });
    });
  }
})();
