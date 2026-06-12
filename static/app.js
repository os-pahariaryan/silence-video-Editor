const API_BASE = "/api/v1";

const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const fileNameEl = document.getElementById("file-name");
const configForm = document.getElementById("config-form");
const submitBtn = document.getElementById("submit-btn");
const uploadSection = document.getElementById("upload-section");
const settingsSection = document.getElementById("settings-section");
const progressSection = document.getElementById("progress-section");
const previewSection = document.getElementById("preview-section");
const progressFill = document.getElementById("progress-fill");
const stageLabel = document.getElementById("stage-label");
const jobIdLabel = document.getElementById("job-id-label");
const errorLabel = document.getElementById("error-label");
const previewVideo = document.getElementById("preview-video");
const actionsSection = document.getElementById("actions-section");
const downloadBtn = document.getElementById("download-btn");
const resetBtn = document.getElementById("reset-btn");
const resetBtn2 = document.getElementById("reset-btn-2");
const statusBanner = document.getElementById("status-banner");
const statusBannerText = document.getElementById("status-banner-text");
const statusBadge = document.getElementById("status-badge");
const previewTab = document.getElementById("preview-tab");
const tabs = document.querySelectorAll(".tab");

let selectedFile = null;
let pollTimer = null;
let currentJobId = null;
let previewBlobUrl = null;

/* Tab switching */
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    if (tab.classList.contains("hidden")) return;
    const target = tab.dataset.tab;
    if (target === "progress") return;
    switchTab(target);
  });
});

function switchTab(name) {
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) => {
    if (p.dataset.panel === "progress") return;
    p.classList.toggle("active", p.dataset.panel === name);
    p.classList.toggle("hidden", p.dataset.panel !== name && p.dataset.panel !== "progress");
  });
}

/* File upload */
browseBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  fileInput.click();
});

dropZone.addEventListener("click", () => fileInput.click());

dropZone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropZone.classList.add("drag-over");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("drag-over");
});

dropZone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) setFile(file);
});

function setFile(file) {
  selectedFile = file;
  fileNameEl.textContent = `${file.name} (${formatSize(file.size)})`;
  fileNameEl.classList.remove("hidden");
  submitBtn.disabled = false;
  setBadge("idle", "IDLE");
}

function formatSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* Status helpers */
function setBadge(type, text) {
  statusBadge.className = `badge badge-${type}`;
  statusBadge.textContent = text;
}

function showBanner(text) {
  statusBannerText.textContent = text;
  statusBanner.classList.remove("hidden");
}

function hideBanner() {
  statusBanner.classList.add("hidden");
}

/* Submit */
configForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedFile) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading…";

  const formData = new FormData();
  formData.append("file", selectedFile);
  for (const [key, value] of new FormData(configForm)) {
    formData.append(key, value);
  }

  try {
    const res = await fetch(`${API_BASE}/jobs`, { method: "POST", body: formData });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Upload failed");
    }
    const data = await res.json();
    currentJobId = data.job_id;
    showProgress();
    startPolling(currentJobId);
  } catch (err) {
    alert(`Error: ${err.message}`);
    submitBtn.disabled = false;
    submitBtn.textContent = "Remove silence";
  }
});

function showProgress() {
  hideBanner();
  setBadge("processing", "PROCESSING");

  uploadSection.classList.remove("active");
  uploadSection.classList.add("hidden");
  settingsSection.classList.remove("active");
  settingsSection.classList.add("hidden");
  progressSection.classList.remove("hidden");
  progressSection.classList.add("active");
  previewSection.classList.add("hidden");
  previewSection.classList.remove("active");
  previewTab.classList.add("hidden");

  tabs.forEach((t) => t.classList.remove("active"));

  jobIdLabel.textContent = currentJobId;
  progressFill.style.width = "0%";
  stageLabel.textContent = "Queued…";
  errorLabel.classList.add("hidden");
  hidePreview();
}

function startPolling(jobId) {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => pollJob(jobId), 2000);
  pollJob(jobId);
}

async function pollJob(jobId) {
  try {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!res.ok) throw new Error("Failed to fetch job status");
    const data = await res.json();

    progressFill.style.width = `${data.progress}%`;
    stageLabel.textContent = `${capitalize(data.stage)} — ${data.progress}%`;

    if (data.status === "completed" && data.download_ready) {
      clearInterval(pollTimer);
      setBadge("ready", "READY");
      showBanner("Your edited video is ready to preview and download.");
      await showPreview(jobId);
    } else if (data.status === "failed") {
      clearInterval(pollTimer);
      setBadge("failed", "FAILED");
      errorLabel.textContent = data.error || "Processing failed";
      errorLabel.classList.remove("hidden");
      stageLabel.textContent = "Processing failed";
    }
  } catch (err) {
    console.error("Poll error:", err);
  }
}

function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

async function showPreview(jobId) {
  const url = `${API_BASE}/jobs/${jobId}/download`;

  progressSection.classList.remove("active");
  progressSection.classList.add("hidden");
  previewSection.classList.remove("hidden");
  previewSection.classList.add("active");
  previewTab.classList.remove("hidden");
  switchTab("preview");

  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load preview");
    const blob = await res.blob();
    if (previewBlobUrl) URL.revokeObjectURL(previewBlobUrl);
    previewBlobUrl = URL.createObjectURL(blob);
    previewVideo.src = previewBlobUrl;
    previewVideo.load();
  } catch (err) {
    previewVideo.src = url;
    previewVideo.load();
    console.error("Preview load error:", err);
  }

  downloadBtn.onclick = () => {
    window.location.href = url;
  };
}

function hidePreview() {
  previewVideo.pause();
  previewVideo.removeAttribute("src");
  previewVideo.load();
  if (previewBlobUrl) {
    URL.revokeObjectURL(previewBlobUrl);
    previewBlobUrl = null;
  }
}

function resetApp() {
  if (pollTimer) clearInterval(pollTimer);
  selectedFile = null;
  currentJobId = null;
  fileInput.value = "";
  fileNameEl.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.textContent = "Remove silence";
  hidePreview();
  hideBanner();
  setBadge("idle", "IDLE");

  progressSection.classList.add("hidden");
  progressSection.classList.remove("active");
  previewSection.classList.add("hidden");
  previewSection.classList.remove("active");
  previewTab.classList.add("hidden");

  uploadSection.classList.remove("hidden");
  uploadSection.classList.add("active");
  settingsSection.classList.remove("hidden");
  switchTab("upload");
}

resetBtn.addEventListener("click", resetApp);
resetBtn2.addEventListener("click", resetApp);
