// Upload page: drag & drop, client-side validation, upload -> analyze -> dashboard.
(function () {
  "use strict";
  const MAX_MB = parseFloat(document.getElementById("upload-script").dataset.maxMb || "5");
  const ALLOWED = ["pdf", "docx"];

  const form = document.getElementById("upload-form");
  const dropzone = document.getElementById("dropzone");
  const input = document.getElementById("file-input");
  const chip = document.getElementById("file-chip");
  const btn = document.getElementById("analyze-btn");
  const alertBox = document.getElementById("alert-box");
  const progressArea = document.getElementById("progress-area");
  const bar = document.getElementById("progress-bar");
  let selectedFile = null;

  const fmtSize = (b) => (b < 1024 * 1024 ? (b / 1024).toFixed(1) + " KB" : (b / 1048576).toFixed(2) + " MB");

  function showError(msg) {
    alertBox.textContent = msg;               // textContent: never inject HTML
    alertBox.classList.remove("d-none");
    alertBox.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function clearError() { alertBox.classList.add("d-none"); alertBox.textContent = ""; }

  function setFile(file) {
    clearError();
    if (!file) return;
    const ext = file.name.includes(".") ? file.name.split(".").pop().toLowerCase() : "";
    if (!ALLOWED.includes(ext)) { reset(); return showError("Unsupported file type. Please upload a PDF or DOCX resume."); }
    if (file.size === 0) { reset(); return showError("The selected file is empty."); }
    if (file.size > MAX_MB * 1024 * 1024) { reset(); return showError(`The file is too large (${fmtSize(file.size)}). Maximum size is ${MAX_MB} MB.`); }
    selectedFile = file;
    document.getElementById("file-name").textContent = file.name;
    document.getElementById("file-size").textContent = `${fmtSize(file.size)} · ${ext.toUpperCase()}`;
    document.getElementById("file-icon").className = ext === "pdf" ? "bi bi-file-earmark-pdf" : "bi bi-file-earmark-word";
    chip.classList.remove("d-none");
    btn.disabled = false;
  }
  function reset() {
    selectedFile = null; input.value = ""; chip.classList.add("d-none"); btn.disabled = true;
  }

  dropzone.addEventListener("click", () => input.click());
  dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
  input.addEventListener("change", () => setFile(input.files[0]));
  ["dragenter", "dragover"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("dragover"); }));
  ["dragleave", "drop"].forEach((ev) => dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove("dragover"); }));
  dropzone.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
  document.getElementById("file-clear").addEventListener("click", reset);

  function step(name, pct) {
    const order = ["upload", "extract", "analyze", "done"];
    const idx = order.indexOf(name);
    document.querySelectorAll(".progress-steps li").forEach((li) => {
      const i = order.indexOf(li.dataset.step);
      li.classList.toggle("done", i < idx);
      li.classList.toggle("active", i === idx);
    });
    bar.style.width = pct + "%";
  }

  // XMLHttpRequest gives real upload progress events (fetch does not).
  function uploadFile(file) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const fd = new FormData();
      fd.append("resume", file);
      xhr.open("POST", "/api/resumes/upload");
      xhr.upload.onprogress = (e) => { if (e.lengthComputable) step("upload", Math.round((e.loaded / e.total) * 30)); };
      xhr.upload.onload = () => step("extract", 40);
      xhr.onload = () => {
        let data = {};
        try { data = JSON.parse(xhr.responseText); } catch (_) { /* non-JSON error page */ }
        if (xhr.status >= 200 && xhr.status < 300 && data.success) resolve(data);
        else reject(new Error(data.error || (xhr.status === 413 ? `The file exceeds the ${MAX_MB} MB limit.` : "Upload failed. Please try again.")));
      };
      xhr.onerror = () => reject(new Error("Network error - please check your connection and try again."));
      xhr.send(fd);
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearError();
    if (!selectedFile) return showError("Please choose a PDF or DOCX resume first.");
    const role = form.querySelector('input[name="role"]:checked');
    if (!role) return showError("Please select a target job role.");

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>Analyzing…';
    progressArea.classList.remove("d-none");
    step("upload", 5);
    try {
      const up = await uploadFile(selectedFile);
      step("analyze", 65);
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_id: up.resume.id, role: role.value }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success) throw new Error(data.error || "Analysis failed. Please try again.");
      step("done", 100);
      window.location.assign(data.dashboard_url);
    } catch (err) {
      progressArea.classList.add("d-none");
      showError(err.message);
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-stars me-2"></i>Analyze Resume';
    }
  });
})();
