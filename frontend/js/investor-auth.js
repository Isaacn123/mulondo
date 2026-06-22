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

  var registerForm = document.getElementById("investorRegisterForm");
  if (registerForm) {
    registerForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("investorRegisterStatus");
      var pw = document.getElementById("investorRegPassword").value;
      var pw2 = document.getElementById("investorRegPassword2").value;
      if (pw !== pw2) {
        setStatus(status, "Passwords do not match.", false);
        return;
      }
      if (pw.length < 8) {
        setStatus(status, "Password must be at least 8 characters.", false);
        return;
      }
      if (!document.getElementById("investorRegTerms").checked) {
        setStatus(status, "Please accept the terms to continue.", false);
        return;
      }
      var payload = {
        first_name: document.getElementById("investorRegFirst").value.trim(),
        last_name: document.getElementById("investorRegLast").value.trim(),
        email: document.getElementById("investorRegEmail").value.trim(),
        password: pw
      };
      setStatus(status, "Creating your account…", true);
      postAuth("register", payload)
        .then(function (r) {
          if (r.ok) return r.json();
          return r.json().then(function (d) { throw new Error(d.detail || "auth"); });
        })
        .then(function () {
          setStatus(status, "Account created — redirecting to sign in…", true);
          setTimeout(function () { window.location.href = "/investors/login"; }, 1200);
        })
        .catch(function (err) {
          setStatus(status, err.message || "Could not create account. Email may already be registered.", false);
        });
    });
  }

  var loginForm = document.getElementById("investorLoginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var status = document.getElementById("investorLoginStatus");
      var email = document.getElementById("investorLoginEmail").value.trim();
      var password = document.getElementById("investorLoginPassword").value;
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
})();
