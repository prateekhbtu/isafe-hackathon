/**
 * MDRS Chrome Extension — Content Script
 *
 * Injected on every page. Responsibilities:
 * 1. Detect text selection and show a floating "Scan" button
 * 2. Communicate with background for analysis
 * 3. Minimal DOM footprint — styled in content.css
 */

(() => {
  // Avoid double-injection
  if (window.__mdrsContentInjected) return;
  window.__mdrsContentInjected = true;

  let floatingBtn = null;
  let hideTimeout = null;

  // ── Create Floating Scan Button ─────────────────────────────────
  function createFloatingButton() {
    if (floatingBtn) return floatingBtn;

    const btn = document.createElement("div");
    btn.id = "mdrs-scan-btn";
    btn.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span>Scan</span>
    `;
    btn.style.display = "none";
    document.body.appendChild(btn);

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();

      const sel = window.getSelection();
      const text = sel ? sel.toString().trim() : "";

      if (text.length < 5) return;

      // Send to background to trigger analysis + open side panel
      chrome.runtime.sendMessage({
        type: "MDRS_CONTENT_SCAN_TEXT",
        text,
        source: window.location.href,
      });

      hideFloatingButton();
    });

    floatingBtn = btn;
    return btn;
  }

  // ── Show / Hide ─────────────────────────────────────────────────
  function showFloatingButton(x, y) {
    const btn = createFloatingButton();

    // Position near selection but clamped to viewport
    const btnWidth = 85;
    const btnHeight = 34;
    const padding = 8;

    let left = x - btnWidth / 2;
    let top = y - btnHeight - padding;

    // Clamp
    left = Math.max(padding, Math.min(left, window.innerWidth - btnWidth - padding));
    top = Math.max(padding, top);

    btn.style.left = `${left}px`;
    btn.style.top = `${top}px`;
    btn.style.display = "flex";

    // Auto-hide after 6 seconds
    clearTimeout(hideTimeout);
    hideTimeout = setTimeout(hideFloatingButton, 6000);
  }

  function hideFloatingButton() {
    if (floatingBtn) {
      floatingBtn.style.display = "none";
    }
    clearTimeout(hideTimeout);
  }

  // ── Selection Listener ──────────────────────────────────────────
  document.addEventListener("mouseup", (e) => {
    // Ignore clicks on our own button
    if (e.target?.id === "mdrs-scan-btn" || e.target?.closest("#mdrs-scan-btn"))
      return;

    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel ? sel.toString().trim() : "";

      if (text.length >= 10) {
        // Get selection bounds
        const range = sel.getRangeAt(0);
        const rect = range.getBoundingClientRect();

        showFloatingButton(
          rect.left + rect.width / 2 + window.scrollX,
          rect.top + window.scrollY
        );
      } else {
        hideFloatingButton();
      }
    }, 10);
  });

  // Hide on scroll or click elsewhere
  document.addEventListener("mousedown", (e) => {
    if (e.target?.id !== "mdrs-scan-btn" && !e.target?.closest("#mdrs-scan-btn")) {
      hideFloatingButton();
    }
  });

  // ── Listen for results from background to show notification ─────
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "MDRS_SHOW_NOTIFICATION") {
      showNotification(msg.message, msg.level);
    }
  });

  function showNotification(message, level = "info") {
    const notif = document.createElement("div");
    notif.className = `mdrs-notification mdrs-notification-${level}`;
    notif.textContent = message;
    document.body.appendChild(notif);

    requestAnimationFrame(() => {
      notif.classList.add("mdrs-notification-show");
    });

    setTimeout(() => {
      notif.classList.remove("mdrs-notification-show");
      setTimeout(() => notif.remove(), 300);
    }, 4000);
  }
})();
