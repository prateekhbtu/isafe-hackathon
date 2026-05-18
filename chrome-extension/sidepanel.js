/**
 * MDRS Side Panel — Results Renderer
 *
 * Listens for messages from the background worker and
 * renders analysis results in the side panel.
 */

const MODALITY_ICONS = {
  text: "📝",
  image: "🖼️",
  video: "🎬",
  audio: "🎧",
};

// ── State Management ────────────────────────────────────────────
const els = {
  empty: () => document.getElementById("empty-state"),
  loading: () => document.getElementById("loading-state"),
  error: () => document.getElementById("error-state"),
  results: () => document.getElementById("results-state"),
  loadingDetail: () => document.getElementById("loading-detail"),
  errorMessage: () => document.getElementById("error-message"),
  modalityBadge: () => document.getElementById("modality-badge"),
  sourceText: () => document.getElementById("source-text"),
  riskScore: () => document.getElementById("risk-score"),
  riskRingFill: () => document.getElementById("risk-ring-fill"),
  riskBadge: () => document.getElementById("risk-badge"),
  riskCount: () => document.getElementById("risk-count"),
  explanationText: () => document.getElementById("explanation-text"),
  geminiCard: () => document.getElementById("gemini-card"),
  geminiText: () => document.getElementById("gemini-text"),
  newsapiCard: () => document.getElementById("newsapi-card"),
  newsBadge: () => document.getElementById("news-badge"),
  newsStats: () => document.getElementById("news-stats"),
  newsReasoning: () => document.getElementById("news-reasoning"),
  newsSources: () => document.getElementById("news-sources"),
  newsArticles: () => document.getElementById("news-articles"),
  signalsCard: () => document.getElementById("signals-card"),
  signalsList: () => document.getElementById("signals-list"),
  recAction: () => document.getElementById("rec-action"),
  recSteps: () => document.getElementById("rec-steps"),
  humanReview: () => document.getElementById("human-review"),
  disclaimer: () => document.getElementById("disclaimer-text"),
};

function showState(state) {
  ["empty-state", "loading-state", "error-state", "results-state"].forEach(
    (id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = id === `${state}-state` ? "block" : "none";
    }
  );
}

function resetToEmpty() {
  showState("empty");
}

// ── Listen for Messages ─────────────────────────────────────────
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "MDRS_ANALYZE") {
    showState("loading");

    const icon = MODALITY_ICONS[msg.modality] || "📄";
    const detail = msg.payload?.url
      ? `Fetching & analyzing ${msg.modality}...`
      : `Processing ${msg.modality} content...`;
    els.loadingDetail().textContent = detail;
  }

  if (msg.type === "MDRS_RESULT") {
    renderResult(msg.modality, msg.result);
    showState("results");
  }

  if (msg.type === "MDRS_ERROR") {
    els.errorMessage().textContent = msg.error;
    showState("error");
  }
});

// ── Render Result ───────────────────────────────────────────────
function renderResult(modality, r) {
  // Modality badge
  const icon = MODALITY_ICONS[modality] || "📄";
  els.modalityBadge().textContent = `${icon} ${capitalize(modality)}`;
  els.sourceText().textContent = r.source || "";

  // Risk score ring
  const score = r.risk_score || 0;
  els.riskScore().textContent = score;

  // Animate ring
  const circumference = 2 * Math.PI * 50; // radius = 50
  const offset = circumference - (score / 100) * circumference;
  const ring = els.riskRingFill();
  ring.style.strokeDasharray = circumference;
  ring.style.strokeDashoffset = circumference;

  // Set color
  const riskLevel = (r.risk_level || "Low").toLowerCase();
  const colors = { low: "#16a34a", medium: "#ea580c", high: "#dc2626" };
  ring.style.stroke = colors[riskLevel] || colors.low;

  // Animate after short delay
  requestAnimationFrame(() => {
    setTimeout(() => {
      ring.style.strokeDashoffset = offset;
    }, 100);
  });

  // Risk badge
  const badge = els.riskBadge();
  badge.textContent = `${r.risk_level} Risk`;
  badge.className = `sp-risk-badge ${riskLevel}`;

  // Signals count
  els.riskCount().textContent = `${r.signals_detected || 0} signal${r.signals_detected !== 1 ? "s" : ""} detected`;

  // Explanation
  els.explanationText().textContent = r.explanation || "";

  // Gemini
  if (r.gemini_analysis) {
    els.geminiCard().style.display = "block";
    els.geminiText().innerHTML = formatBoldText(r.gemini_analysis);
  } else {
    els.geminiCard().style.display = "none";
  }

  // NewsAPI
  renderNewsAPI(r.newsapi_verification);

  // Signals
  renderSignals(r.signal_breakdown || []);

  // Recommendation
  renderRecommendation(r.recommendation);

  // Disclaimer
  els.disclaimer().textContent = r.disclaimer || "";
}

// ── NewsAPI Renderer ────────────────────────────────────────────
function renderNewsAPI(newsapi) {
  const card = els.newsapiCard();

  if (!newsapi || !newsapi.newsapi_available || newsapi.credibility_score === null) {
    card.style.display = "none";
    return;
  }

  card.style.display = "block";

  // Badge
  const badge = els.newsBadge();
  const level = newsapi.credibility_level || "Medium";
  const colors = { High: "#16a34a", Medium: "#ea580c", Low: "#dc2626" };
  badge.textContent = `${level} Credibility`;
  badge.style.background = colors[level] || colors.Medium;

  // Stats
  els.newsStats().innerHTML = `
    <div class="sp-news-stat">
      <span class="sp-news-stat-value">${newsapi.credibility_score}</span>
      <span class="sp-news-stat-label">Score</span>
    </div>
    <div class="sp-news-stat">
      <span class="sp-news-stat-value">${newsapi.corroborating_sources || 0}</span>
      <span class="sp-news-stat-label">Sources</span>
    </div>
    <div class="sp-news-stat">
      <span class="sp-news-stat-value">${newsapi.total_related_articles || 0}</span>
      <span class="sp-news-stat-label">Articles</span>
    </div>
  `;

  // Reasoning
  els.newsReasoning().textContent = newsapi.credibility_reasoning || "";
  els.newsReasoning().style.display = newsapi.credibility_reasoning
    ? "block"
    : "none";

  // Sources
  const sources = newsapi.top_sources || [];
  if (sources.length > 0) {
    els.newsSources().innerHTML = sources
      .slice(0, 8)
      .map((s) => `<span class="sp-source-tag">${escapeHtml(s)}</span>`)
      .join("");
    els.newsSources().style.display = "flex";
  } else {
    els.newsSources().style.display = "none";
  }

  // Articles
  const articles = newsapi.sample_articles || [];
  if (articles.length > 0) {
    els.newsArticles().innerHTML = articles
      .slice(0, 3)
      .map(
        (a) => `
        <a href="${escapeHtml(a.url)}" target="_blank" rel="noopener" class="sp-article-link">
          <span class="sp-article-source">${escapeHtml(a.source?.name || "")}</span>
          <span class="sp-article-title">${escapeHtml(a.title || "")}</span>
        </a>
      `
      )
      .join("");
    els.newsArticles().style.display = "flex";
  } else {
    els.newsArticles().style.display = "none";
  }
}

// ── Signals Renderer ────────────────────────────────────────────
function renderSignals(signals) {
  const card = els.signalsCard();
  const list = els.signalsList();

  if (!signals.length) {
    card.style.display = "none";
    return;
  }

  card.style.display = "block";
  list.innerHTML = signals
    .map(
      (s) => `
      <div class="sp-signal">
        <div class="sp-signal-header">
          <span class="sp-signal-type">${s.signal.startsWith("newsapi_") ? "📰 " : ""}${s.signal.replace(/_/g, " ")}</span>
          <span class="sp-confidence-tag">${Math.round(s.confidence * 100)}%</span>
        </div>
        <p class="sp-signal-desc">${escapeHtml(s.description)}</p>
      </div>
    `
    )
    .join("");
}

// ── Recommendation Renderer ─────────────────────────────────────
function renderRecommendation(rec) {
  if (!rec) return;

  const pLevel = (rec.priority || "low").toLowerCase();
  els.recAction().innerHTML = `
    ${escapeHtml(rec.action)}
    <span class="sp-priority-tag ${pLevel}">${rec.priority} Priority</span>
  `;

  els.recSteps().innerHTML = (rec.suggested_steps || [])
    .map((s) => `<li>${escapeHtml(s)}</li>`)
    .join("");

  els.humanReview().style.display = rec.human_review_required
    ? "block"
    : "none";
}

// ── Helpers ─────────────────────────────────────────────────────
function capitalize(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

function escapeHtml(str) {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatBoldText(text) {
  if (!text) return "";
  return escapeHtml(text).replace(
    /\*\*(.*?)\*\*/g,
    '<strong style="font-weight:600;color:var(--text-primary)">$1</strong>'
  );
}
