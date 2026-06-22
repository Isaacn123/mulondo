(function () {
  "use strict";

  function parseError(data) {
    var msg = data.detail || "Upload failed";
    if (Array.isArray(msg)) {
      msg = msg.map(function (e) {
        return e.msg || String(e);
      }).join(", ");
    }
    return msg;
  }

  function syncPreview(input, block) {
    var preview = block.querySelector(".r2-preview");
    var previewImg = block.querySelector(".r2-preview-img");
    if (!preview || !previewImg) return;
    if (input.value) {
      previewImg.src = input.value;
      preview.classList.remove("d-none");
    } else {
      preview.classList.add("d-none");
    }
  }

  document.querySelectorAll(".r2-image-upload").forEach(function (block) {
    var input = block.querySelector("[data-r2-input]");
    var fileInput = block.querySelector(".r2-file-input");
    var errEl = block.querySelector(".r2-error");
    if (!input || !fileInput) return;

    var folder = block.getAttribute("data-r2-folder") || "cms";

    fileInput.addEventListener("change", function () {
      if (!fileInput.files || !fileInput.files[0]) return;
      var fd = new FormData();
      fd.append("file", fileInput.files[0]);
      if (errEl) {
        errEl.classList.add("d-none");
        errEl.textContent = "";
      }
      fetch("/admin/upload/image?folder=" + encodeURIComponent(folder), {
        method: "POST",
        body: fd,
        credentials: "same-origin",
      })
        .then(function (r) {
          return r.json().then(function (d) {
            if (!r.ok) throw new Error(parseError(d));
            return d;
          });
        })
        .then(function (data) {
          input.value = data.url;
          syncPreview(input, block);
          fileInput.value = "";
        })
        .catch(function (err) {
          if (errEl) {
            errEl.textContent = err.message || "Upload failed.";
            errEl.classList.remove("d-none");
          }
        });
    });

    input.addEventListener("input", function () {
      syncPreview(input, block);
    });
    syncPreview(input, block);
  });
})();
