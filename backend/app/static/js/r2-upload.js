(function () {
  "use strict";

  var U = window.UploadUtils;

  function parseError(data) {
    if (U) return U.parseDetail(data.detail);
    var msg = data.detail || "Upload failed";
    if (Array.isArray(msg)) {
      msg = msg.map(function (e) {
        return e.msg || String(e);
      }).join(", ");
    }
    return msg;
  }

  function setLoading(block, on) {
    var btn = block.querySelector(".r2-upload-btn");
    var icon = block.querySelector(".r2-upload-icon");
    var spinner = block.querySelector(".r2-upload-spinner");
    var fileInput = block.querySelector(".r2-file-input");
    if (btn) btn.classList.toggle("disabled", on);
    if (icon) icon.classList.toggle("d-none", on);
    if (spinner) spinner.classList.toggle("d-none", !on);
    if (fileInput) fileInput.disabled = on;
  }

  function setStatus(block, text) {
    var status = block.querySelector(".r2-preview-status");
    if (status) status.textContent = text || "";
  }

  function revokeBlob(block) {
    var blobUrl = block.getAttribute("data-blob-url");
    if (blobUrl) {
      URL.revokeObjectURL(blobUrl);
      block.removeAttribute("data-blob-url");
    }
  }

  function syncPreview(input, block) {
    var preview = block.querySelector(".r2-preview");
    var previewImg = block.querySelector(".r2-preview-img");
    var urlLine = block.querySelector(".r2-preview-url");
    if (!preview || !previewImg) return;

    var url = (input.value || "").trim();
    if (url) {
      previewImg.onerror = function () {
        setStatus(block, "Could not load preview");
      };
      previewImg.onload = function () {
        setStatus(block, "");
      };
      previewImg.src = url;
      preview.classList.remove("d-none");
      if (urlLine) urlLine.textContent = url;
    } else {
      previewImg.removeAttribute("src");
      preview.classList.add("d-none");
      if (urlLine) urlLine.textContent = "";
      setStatus(block, "");
      revokeBlob(block);
    }
  }

  function showLocalPreview(file, block, input) {
    if (!file || !file.type || file.type.indexOf("image/") !== 0) return;
    revokeBlob(block);
    var blobUrl = URL.createObjectURL(file);
    block.setAttribute("data-blob-url", blobUrl);
    var preview = block.querySelector(".r2-preview");
    var previewImg = block.querySelector(".r2-preview-img");
    var urlLine = block.querySelector(".r2-preview-url");
    if (previewImg) {
      previewImg.src = blobUrl;
      previewImg.onload = function () { setStatus(block, "Local preview"); };
    }
    if (preview) preview.classList.remove("d-none");
    if (urlLine) urlLine.textContent = file.name + " (uploading…)";
  }

  document.querySelectorAll(".r2-image-upload").forEach(function (block) {
    var input = block.querySelector("[data-r2-input]");
    var fileInput = block.querySelector(".r2-file-input");
    var errEl = block.querySelector(".r2-error");
    if (!input || !fileInput) return;

    var folder = block.getAttribute("data-r2-folder") || "cms";

    function clearError() {
      if (!errEl) return;
      errEl.classList.add("d-none");
      errEl.textContent = "";
    }

    function showError(msg, popup) {
      if (!msg) return;
      if (errEl) {
        errEl.textContent = msg;
        errEl.classList.remove("d-none");
      }
      if (popup !== false && U) U.showUploadAlert(msg);
    }

    fileInput.addEventListener("change", function () {
      if (!fileInput.files || !fileInput.files[0]) return;
      var file = fileInput.files[0];
      clearError();

      if (U) {
        var sizeErr = U.validateFile(file, "image");
        if (sizeErr) {
          showError(sizeErr);
          fileInput.value = "";
          return;
        }
      }

      showLocalPreview(file, block, input);

      var fd = new FormData();
      fd.append("file", file);
      setLoading(block, true);
      setStatus(block, "Uploading…");

      var uploadPromise = U
        ? U.fetchUpload("/admin/upload/image?folder=" + encodeURIComponent(folder), fd, { alert: false })
        : fetch("/admin/upload/image?folder=" + encodeURIComponent(folder), {
            method: "POST",
            body: fd,
            credentials: "same-origin",
          }).then(function (r) {
            return r.json().then(function (d) {
              if (!r.ok) throw new Error(parseError(d));
              return d;
            });
          });

      uploadPromise
        .then(function (data) {
          revokeBlob(block);
          input.value = data.url;
          syncPreview(input, block);
          setStatus(block, "Uploaded");
          fileInput.value = "";
        })
        .catch(function (err) {
          showError(err.message || "Upload failed.");
          setStatus(block, "Upload failed");
        })
        .finally(function () {
          setLoading(block, false);
        });
    });

    input.addEventListener("input", function () {
      clearError();
      revokeBlob(block);
      syncPreview(input, block);
    });
    input.addEventListener("change", function () {
      clearError();
      revokeBlob(block);
      syncPreview(input, block);
    });

    syncPreview(input, block);
  });
})();
