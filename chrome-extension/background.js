/**
 * MDRS Chrome Extension — Background Service Worker
 *
 * Responsibilities:
 * 1. Context menu creation (right-click on text/image/audio/video)
 * 2. API communication with MDRS backend
 * 3. Side panel orchestration
 * 4. Message routing between content script ↔ side panel
 */

// ── Default Config ──────────────────────────────────────────────────
const DEFAULT_API_URL = "http://localhost:8000";

async function getApiUrl() {
  const { apiUrl } = await chrome.storage.sync.get({ apiUrl: DEFAULT_API_URL });
  return apiUrl;
}

// ── Context Menus ───────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(() => {
  // Parent menu
  chrome.contextMenus.create({
    id: "mdrs-parent",
    title: "🛡️ MDRS — Scan for Deception",
    contexts: ["selection", "image", "audio", "video"],
  });

  // Text selection
  chrome.contextMenus.create({
    id: "mdrs-scan-text",
    parentId: "mdrs-parent",
    title: 'Scan Selected Text',
    contexts: ["selection"],
  });

  // Image
  chrome.contextMenus.create({
    id: "mdrs-scan-image",
    parentId: "mdrs-parent",
    title: "Scan This Image",
    contexts: ["image"],
  });

  // Audio
  chrome.contextMenus.create({
    id: "mdrs-scan-audio",
    parentId: "mdrs-parent",
    title: "Scan This Audio",
    contexts: ["audio"],
  });

  // Video
  chrome.contextMenus.create({
    id: "mdrs-scan-video",
    parentId: "mdrs-parent",
    title: "Scan This Video",
    contexts: ["video"],
  });

  // Enable side panel on all sites
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });
});

// ── Context Menu Click Handler ──────────────────────────────────────
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (!info.menuItemId.toString().startsWith("mdrs-scan")) return;

  const menuId = info.menuItemId.toString();

  // Open side panel first
  try {
    await chrome.sidePanel.open({ tabId: tab.id });
  } catch (e) {
    console.error("Failed to open side panel:", e);
  }

  // Small delay so sidepanel loads
  await new Promise((r) => setTimeout(r, 400));

  if (menuId === "mdrs-scan-text") {
    const selectedText = info.selectionText || "";
    if (!selectedText.trim()) return;

    // Send to side panel
    chrome.runtime.sendMessage({
      type: "MDRS_ANALYZE",
      modality: "text",
      payload: { text: selectedText, source: info.pageUrl },
    });

    // Also trigger the API
    analyzeText(selectedText, info.pageUrl);
  } else if (menuId === "mdrs-scan-image") {
    const imageUrl = info.srcUrl;
    if (!imageUrl) return;

    chrome.runtime.sendMessage({
      type: "MDRS_ANALYZE",
      modality: "image",
      payload: { url: imageUrl, source: info.pageUrl },
    });

    analyzeImageByUrl(imageUrl, info.pageUrl);
  } else if (menuId === "mdrs-scan-audio") {
    const audioUrl = info.srcUrl;
    if (!audioUrl) return;

    chrome.runtime.sendMessage({
      type: "MDRS_ANALYZE",
      modality: "audio",
      payload: { url: audioUrl, source: info.pageUrl },
    });

    analyzeMediaByUrl("audio", audioUrl, info.pageUrl);
  } else if (menuId === "mdrs-scan-video") {
    const videoUrl = info.srcUrl;
    if (!videoUrl) return;

    chrome.runtime.sendMessage({
      type: "MDRS_ANALYZE",
      modality: "video",
      payload: { url: videoUrl, source: info.pageUrl },
    });

    analyzeMediaByUrl("video", videoUrl, info.pageUrl);
  }
});

// ── Message Handler (from content script or popup) ──────────────────
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "MDRS_CONTENT_SCAN_TEXT") {
    // Text sent from content script floating button
    chrome.sidePanel.open({ tabId: sender.tab.id }).then(() => {
      setTimeout(() => {
        chrome.runtime.sendMessage({
          type: "MDRS_ANALYZE",
          modality: "text",
          payload: { text: message.text, source: message.source },
        });
        analyzeText(message.text, message.source);
      }, 400);
    });
    sendResponse({ ok: true });
  }

  if (message.type === "MDRS_OPEN_SIDEPANEL") {
    chrome.sidePanel.open({ tabId: message.tabId || sender.tab?.id });
    sendResponse({ ok: true });
  }

  if (message.type === "MDRS_GET_STATUS") {
    getApiUrl().then((url) => {
      fetch(`${url}/`)
        .then((r) => r.json())
        .then((data) => sendResponse({ online: true, data }))
        .catch(() => sendResponse({ online: false }));
    });
    return true; // async
  }

  return false;
});

// ── API Call Functions ───────────────────────────────────────────────

async function analyzeText(text, pageUrl) {
  const apiUrl = await getApiUrl();

  const formData = new FormData();
  formData.append("text", text);
  formData.append("source", pageUrl || "Chrome Extension");

  try {
    const resp = await fetch(`${apiUrl}/analyze/text`, {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${resp.status}`);
    }

    const result = await resp.json();

    chrome.runtime.sendMessage({
      type: "MDRS_RESULT",
      modality: "text",
      result,
    });
  } catch (err) {
    chrome.runtime.sendMessage({
      type: "MDRS_ERROR",
      modality: "text",
      error: err.message || "Analysis failed",
    });
  }
}

async function analyzeImageByUrl(imageUrl, pageUrl) {
  const apiUrl = await getApiUrl();

  try {
    // Download image as blob
    const imgResp = await fetch(imageUrl);
    if (!imgResp.ok) throw new Error("Could not fetch image");
    const blob = await imgResp.blob();

    const formData = new FormData();
    formData.append("file", blob, "image.jpg");
    formData.append("source", pageUrl || "Chrome Extension");
    formData.append("context", `Image from: ${pageUrl}`);

    const resp = await fetch(`${apiUrl}/analyze/image`, {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${resp.status}`);
    }

    const result = await resp.json();
    chrome.runtime.sendMessage({ type: "MDRS_RESULT", modality: "image", result });
  } catch (err) {
    chrome.runtime.sendMessage({
      type: "MDRS_ERROR",
      modality: "image",
      error: err.message || "Image analysis failed",
    });
  }
}

async function analyzeMediaByUrl(modality, mediaUrl, pageUrl) {
  const apiUrl = await getApiUrl();

  const formData = new FormData();
  formData.append("url", mediaUrl);
  formData.append("source", pageUrl || "Chrome Extension");

  try {
    const resp = await fetch(`${apiUrl}/analyze/${modality}`, {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${resp.status}`);
    }

    const result = await resp.json();
    chrome.runtime.sendMessage({ type: "MDRS_RESULT", modality, result });
  } catch (err) {
    chrome.runtime.sendMessage({
      type: "MDRS_ERROR",
      modality,
      error: err.message || `${modality} analysis failed`,
    });
  }
}
