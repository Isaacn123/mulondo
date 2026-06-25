(function (global) {
  "use strict";

  var LIMITS = {
    image: 2 * 1024 * 1024,
    video: 50 * 1024 * 1024,
    pdf: 25 * 1024 * 1024,
  };

  var LABELS = {
    image: "2 MB",
    video: "50 MB",
    pdf: "25 MB",
  };

  function limitLabel(kind) {
    return LABELS[kind] || "";
  }

  function parseDetail(detail) {
    if (!detail) return "Upload failed.";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map(function (item) {
          return item.msg || String(item);
        })
        .join(", ");
    }
    return String(detail);
  }

  function showUploadAlert(message, title) {
    var modal = document.getElementById("uploadErrorModal");
    var body = document.getElementById("uploadErrorModalBody");
    var heading = document.getElementById("uploadErrorModalTitle");
    if (!modal || !body) {
      global.alert(message);
      return;
    }
    body.textContent = message || "Upload failed.";
    if (heading) heading.textContent = title || "Upload error";
    if (global.jQuery) {
      global.jQuery(modal).modal("show");
    } else {
      global.alert(message);
    }
  }

  function validateFile(file, kind) {
    if (!file) return "Choose a file first.";
    var max = LIMITS[kind];
    if (!max) return null;
    if (file.size > max) {
      return "File is too large. Maximum size is " + limitLabel(kind) + ".";
    }
    return null;
  }

  function validateKycFile(file) {
    if (!file) return "Choose a file first.";
    var isPdf =
      file.type === "application/pdf" ||
      (file.name || "").toLowerCase().endsWith(".pdf");
    return validateFile(file, isPdf ? "pdf" : "image");
  }

  function validateMediaFile(file, kind) {
    if (kind === "video") return validateFile(file, "video");
    return validateFile(file, "image");
  }

  function fetchUpload(url, formData, options) {
    options = options || {};
    return fetch(url, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
    }).then(function (response) {
      return response.text().then(function (text) {
        var data = null;
        if (text) {
          try {
            data = JSON.parse(text);
          } catch (e) {
            data = null;
          }
        }
        if (!response.ok) {
          var message = data ? parseDetail(data.detail) : "";
          if (!message && response.status === 413) {
            message = "File is too large for the server limit.";
          }
          if (!message) {
            message = "Upload failed (" + response.status + ").";
          }
          var err = new Error(message);
          if (options.alert !== false) showUploadAlert(message);
          throw err;
        }
        return data;
      });
    });
  }

  global.UploadUtils = {
    LIMITS: LIMITS,
    LABELS: LABELS,
    limitLabel: limitLabel,
    showUploadAlert: showUploadAlert,
    validateFile: validateFile,
    validateKycFile: validateKycFile,
    validateMediaFile: validateMediaFile,
    parseDetail: parseDetail,
    fetchUpload: fetchUpload,
  };
})(window);
