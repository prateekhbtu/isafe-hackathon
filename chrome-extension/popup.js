/**
 * MDRS Popup Script
 * Handles:
 * - Backend status check
 * - API URL configuration
 * - Side panel opener
 */

const DEFAULT_API_URL = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", async () => {
  const apiUrlInput = document.getElementById("api-url");
  const saveBtn = document.getElementById("save-url-btn");
  const saveHint = document.getElementById("save-hint");
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  const openPanelBtn = document.getElementById("open-panel-btn");
  const geminiKeyInput = document.getElementById("gemini-key");
  const saveKeyBtn = document.getElementById("save-key-btn");
  const keyHint = document.getElementById("key-hint");

  // Load saved API URL + Gemini API key
  const { apiUrl, geminiApiKey } = await chrome.storage.sync.get({
    apiUrl: DEFAULT_API_URL,
    geminiApiKey: "",
  });
  apiUrlInput.value = apiUrl;
  geminiKeyInput.value = geminiApiKey;

  // Check backend status
  checkStatus(apiUrl);

  // Save URL
  saveBtn.addEventListener("click", async () => {
    const url = apiUrlInput.value.trim();
    if (!url) return;

    // Remove trailing slash
    const cleanUrl = url.replace(/\/+$/, "");
    await chrome.storage.sync.set({ apiUrl: cleanUrl });
    apiUrlInput.value = cleanUrl;

    saveHint.textContent = "✓ Saved";
    saveHint.style.color = "#16a34a";
    setTimeout(() => {
      saveHint.textContent = "";
    }, 2000);

    checkStatus(cleanUrl);
  });

  // Save Gemini API key (BYOK)
  saveKeyBtn.addEventListener("click", async () => {
    const key = geminiKeyInput.value.trim();
    await chrome.storage.sync.set({ geminiApiKey: key });

    keyHint.textContent = key
      ? "✓ Saved — your key will be used for scans"
      : "✓ Cleared — hosted Gemini will be used";
    keyHint.style.color = "#16a34a";
    setTimeout(() => {
      keyHint.textContent =
        "Stored only in this browser. Sent with each scan and used instead of the hosted Gemini.";
      keyHint.style.color = "";
    }, 2500);
  });

  // Open side panel
  openPanelBtn.addEventListener("click", async () => {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (tab) {
      chrome.runtime.sendMessage({
        type: "MDRS_OPEN_SIDEPANEL",
        tabId: tab.id,
      });
    }
    window.close();
  });

  // ── Status Check ────────────────────────────────────────────
  async function checkStatus(url) {
    statusDot.className = "popup-status-dot";
    statusText.textContent = "Checking...";

    try {
      const resp = await fetch(`${url}/`, { signal: AbortSignal.timeout(5000) });
      if (resp.ok) {
        const data = await resp.json();
        statusDot.classList.add("online");
        statusText.textContent = "Online";

        // Show features if available
        if (data.features) {
          const features = [];
          if (data.features.newsapi_verification) features.push("NewsAPI");
          if (data.features.youtube_support) features.push("YouTube");
          if (features.length) {
            statusText.textContent = `Online · ${features.join(", ")}`;
          }
        }
      } else {
        statusDot.classList.add("offline");
        statusText.textContent = "Error";
      }
    } catch {
      statusDot.classList.add("offline");
      statusText.textContent = "Offline";
    }
  }
});
