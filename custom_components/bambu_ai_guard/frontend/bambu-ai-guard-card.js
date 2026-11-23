/**
 * Bambu AI Guard — Zest Custom Lovelace Card for Home Assistant
 * Zest Light/Dark Neo-Brutalist design with live composite snapshot and defect gauges.
 */

const CARD_TAG = "bambu-ai-guard-card";

const ZEST_SHEET = new CSSStyleSheet();
ZEST_SHEET.replaceSync(`
  :host {
    display: block;
    color-scheme: light dark;

    /* Native Home Assistant theme variables */
    --z-bg: var(--primary-background-color, #fafafa);
    --z-surface: var(--ha-card-background, var(--card-background-color, #ffffff));
    --z-surface-2: var(--secondary-background-color, rgba(127, 127, 127, 0.08));
    --z-ink: var(--primary-text-color, #212121);
    --z-ink-2: var(--secondary-text-color, #727272);
    --z-border: var(--ha-card-border-color, var(--divider-color, rgba(127, 127, 127, 0.25)));
    --z-border-soft: var(--divider-color, rgba(127, 127, 127, 0.18));
    --z-radius: var(--ha-card-border-radius, 12px);
    --z-shadow: var(--ha-card-box-shadow, none);
    --z-accent: var(--primary-color, #03a9f4);
    --z-accent-on: var(--text-primary-color, #ffffff);
    --z-ok-bg: color-mix(in srgb, var(--success-color, #43a047) 16%, transparent);
    --z-ok-ink: var(--success-color, #2e7d32);
    --z-warn-bg: color-mix(in srgb, var(--warning-color, #ffa600) 18%, transparent);
    --z-warn-ink: var(--warning-color, #d97706);
    --z-danger-bg: color-mix(in srgb, var(--error-color, #db4437) 16%, transparent);
    --z-danger-ink: var(--error-color, #db4437);
  }

  :host([hidden]) {
    display: none;
  }

  .zest-card {
    background: var(--z-surface);
    color: var(--z-ink);
    border: var(--ha-card-border-width, 1px) solid var(--z-border);
    border-radius: var(--z-radius);
    box-shadow: var(--z-shadow);
    padding: 16px;
    font-family: var(--paper-font-body1_-_font-family, Roboto, system-ui, -apple-system, sans-serif);
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .brand-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    border: 2px solid var(--z-border);
    background: #538900;
    display: grid;
    place-items: center;
    flex-shrink: 0;
  }

  .brand-icon svg {
    width: 24px;
    height: 24px;
  }

  .title-wrap h3 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: -0.01em;
  }

  .subtitle {
    margin: 2px 0 0;
    font-size: 0.78rem;
    color: var(--z-ink-2);
    font-weight: 600;
  }

  .status-pill {
    padding: 5px 11px;
    border-radius: 999px;
    border: 2px solid var(--z-border);
    font-size: 0.76rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    background: var(--z-surface-2);
    color: var(--z-ink);
  }

  .status-pill[data-status="OK"] {
    background: var(--z-ok-bg);
    color: var(--z-ok-ink);
  }

  .status-pill[data-status="WARNING"] {
    background: var(--z-warn-bg);
    color: var(--z-warn-ink);
  }

  .status-pill[data-status="FAILURE"],
  .status-pill[data-status="API_ERROR"] {
    background: var(--z-danger-bg);
    color: var(--z-danger-ink);
  }

  .viewport {
    position: relative;
    border-radius: 12px;
    border: 2px solid var(--z-border);
    overflow: hidden;
    background: #0d130a;
    aspect-ratio: 16 / 9;
    display: grid;
    place-items: center;
  }

  .viewport img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .viewport-overlay {
    position: absolute;
    inset: auto 10px 10px 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    pointer-events: none;
  }

  .chip {
    background: rgba(15, 23, 11, 0.84);
    color: #F2F9ED;
    border: 1.5px solid rgba(155, 225, 42, 0.55);
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 0.73rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
  }

  .metric-box {
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border);
    border-radius: 11px;
    padding: 9px 11px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .metric-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--z-ink-2);
  }

  .metric-val {
    font-weight: 800;
    color: var(--z-ink);
    font-variant-numeric: tabular-nums;
  }

  .bar-track {
    height: 7px;
    border-radius: 999px;
    background: var(--z-surface);
    border: 1px solid var(--z-border-soft);
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    background: var(--z-accent);
    width: 0%;
    transition: width 0.25s ease;
  }

  .bar-fill[data-risk="warn"] {
    background: #E09F00;
  }

  .bar-fill[data-risk="danger"] {
    background: #D93834;
  }

  .details-box {
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    border-radius: 10px;
    padding: 9px 11px;
    font-size: 0.8rem;
    line-height: 1.4;
    color: var(--z-ink);
  }

  .actions-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    justify-content: space-between;
  }

  button.zest-btn {
    appearance: none;
    border: 2px solid var(--z-border);
    border-radius: 10px;
    box-shadow: var(--z-shadow);
    padding: 8px 13px;
    font-size: 0.8rem;
    font-weight: 800;
    cursor: pointer;
    background: var(--z-accent);
    color: var(--z-accent-on);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  button.zest-btn.secondary {
    background: var(--z-surface-2);
    color: var(--z-ink);
  }

  button.zest-btn:active {
    transform: translateY(1px);
  }

  details.history-drawer {
    border-top: 1.5px dashed var(--z-border-soft);
    padding-top: 10px;
  }

  details.history-drawer summary {
    cursor: pointer;
    font-size: 0.82rem;
    font-weight: 800;
    color: var(--z-ink);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .history-list {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    max-height: 210px;
    overflow-y: auto;
  }

  .history-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 10px;
    border-radius: 8px;
    background: var(--z-surface-2);
    border: 1px solid var(--z-border-soft);
    font-size: 0.76rem;
    gap: 8px;
  }

  .history-name {
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .history-meta {
    color: var(--z-ink-2);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
  }
`);

const CARD_TEMPLATE = document.createElement("template");
CARD_TEMPLATE.innerHTML = `
  <div class="zest-card">
    <div class="header">
      <div class="brand">
        <div class="brand-icon" aria-hidden="true">
          <svg viewBox="0 0 64 64">
            <path d="M18 49V19a5 5 0 0 1 5-5h18a5 5 0 0 1 5 5v30" fill="none" stroke="#FDFFFB" stroke-width="4.5" stroke-linecap="round"/>
            <path d="M19 25.5h26" fill="none" stroke="#DCF4A6" stroke-width="4.5" stroke-linecap="round"/>
            <rect x="27" y="21" width="10" height="13" rx="2.5" fill="#FDFFFB" stroke="#1A260E" stroke-width="2"/>
            <path d="M27.5 34h9L32 41.5Z" fill="#9BE12A"/>
            <rect x="23.5" y="43" width="17" height="4" rx="2" fill="#9BE12A"/>
            <path d="M13 49h38" fill="none" stroke="#FDFFFB" stroke-width="5" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="title-wrap">
          <h3 id="printer-title">Bambu AI Guard</h3>
        </div>
      </div>
      <div class="status-pill" id="status-pill" data-status="IDLE">IDLE</div>
    </div>

    <div class="viewport">
      <img id="snapshot-img" alt="Bambu AI Guard Composite Snapshot" loading="lazy" />
      <div class="viewport-overlay">
        <span class="chip" id="layer-chip">Layer — / —</span>
        <span class="chip" id="latency-chip">gemini-decision-1</span>
      </div>
    </div>

    <div class="metrics-grid">
      <div class="metric-box">
        <div class="metric-head"><span>Spaghetti</span><span class="metric-val" id="val-spaghetti">—</span></div>
        <div class="bar-track"><div class="bar-fill" id="bar-spaghetti"></div></div>
      </div>
      <div class="metric-box">
        <div class="metric-head"><span>Warping</span><span class="metric-val" id="val-warping">—</span></div>
        <div class="bar-track"><div class="bar-fill" id="bar-warping"></div></div>
      </div>
      <div class="metric-box">
        <div class="metric-head"><span>Detachment</span><span class="metric-val" id="val-detachment">—</span></div>
        <div class="bar-track"><div class="bar-fill" id="bar-detachment"></div></div>
      </div>
      <div class="metric-box">
        <div class="metric-head"><span>First Layer</span><span class="metric-val" id="val-first-layer">—</span></div>
        <div class="bar-track"><div class="bar-fill" id="bar-first-layer"></div></div>
      </div>
    </div>

    <div class="details-box" id="details-text">Waiting for print checkpoint inspection...</div>

    <div class="actions-row">
      <button type="button" class="zest-btn" id="btn-inspect">Inspect Now (AI)</button>
      <button type="button" class="zest-btn secondary" id="btn-purge">Purge Old History (&gt; X)</button>
    </div>

    <details class="history-drawer">
      <summary>
        <span>Setup &amp; Connection Help (API Key / Printer Code)</span>
        <span>▾</span>
      </summary>
      <div class="details-box" style="margin-top:8px;">
        <strong>Free Gemini API Key:</strong> Open <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener" style="color:var(--z-accent);font-weight:700;">aistudio.google.com/apikey</a> → <em>Create API Key</em>.<br/>
        <strong>Find IP &amp; Access Code on Printer:</strong><br/>
        • <strong>P1P / P1S:</strong> Settings → WLAN<br/>
        • <strong>A1 / A1 Mini:</strong> Settings → LAN Only Mode (or WLAN)<br/>
        • <strong>X1C / X1E:</strong> Settings → Network
      </div>
    </details>

    <details class="history-drawer">
      <summary>
        <span id="history-summary-label">Lifetime Print History (0 prints)</span>
        <span>▾</span>
      </summary>
      <div class="history-list" id="history-list"></div>
    </details>
  </div>
`;

class BambuAIGuardCard extends HTMLElement {
  #hass = null;
  #config = {};
  #bound = false;

  constructor() {
    super();
    this.attachShadow({ mode: "open", delegatesFocus: true });
    this.shadowRoot.adoptedStyleSheets = [ZEST_SHEET];
    this.shadowRoot.append(CARD_TEMPLATE.content.cloneNode(true));
  }

  connectedCallback() {
    if (!this.#bound) {
      this.#bound = true;
      this.shadowRoot.getElementById("btn-inspect").addEventListener("click", () => {
        if (this.#hass) {
          this.#hass.callService("bambu_ai_guard", "inspect_now", {});
        }
      });
      this.shadowRoot.getElementById("btn-purge").addEventListener("click", () => {
        if (this.#hass) {
          this.#hass.callService("bambu_ai_guard", "purge_history", {});
        }
      });
    }
    this.#render();
  }

  setConfig(config) {
    this.#config = config || {};
    this.#render();
  }

  set hass(hass) {
    this.#hass = hass;
    this.#render();
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig() {
    return {};
  }

  #findEntityId(suffix) {
    if (!this.#hass) return null;
    if (this.#config.status_entity && suffix === "ai_guard_status") {
      return this.#config.status_entity;
    }
    const allIds = Object.keys(this.#hass.states);
    return (
      allIds.find((id) => id.includes(suffix)) ||
      allIds.find((id) => id.endsWith(suffix))
    );
  }

  #updateBar(barId, valId, pct) {
    const bar = this.shadowRoot.getElementById(barId);
    const label = this.shadowRoot.getElementById(valId);
    if (pct === null || pct === undefined || Number.isNaN(Number(pct))) {
      label.textContent = "—";
      bar.style.width = "0%";
      bar.removeAttribute("data-risk");
      return;
    }
    const num = Math.max(0, Math.min(100, Number(pct)));
    label.textContent = `${num.toFixed(0)}%`;
    bar.style.width = `${num}%`;
    if (num >= 80) {
      bar.setAttribute("data-risk", "danger");
    } else if (num >= 50) {
      bar.setAttribute("data-risk", "warn");
    } else {
      bar.removeAttribute("data-risk");
    }
  }

  #render() {
    if (!this.#hass || !this.shadowRoot) return;

    const statusId =
      this.#findEntityId("ai_guard_status") ||
      this.#findEntityId("statut_ai_guard");
    const camId =
      this.#findEntityId("ai_guard_composite_snapshot") ||
      this.#findEntityId("snapshot_composite_ai_guard");
    const historyId =
      this.#findEntityId("ai_print_history") ||
      this.#findEntityId("historique_des_impressions_ia");

    const statusState = statusId ? this.#hass.states[statusId] : null;
    const camState = camId ? this.#hass.states[camId] : null;
    const historyState = historyId ? this.#hass.states[historyId] : null;

    if (statusState) {
      const attrs = statusState.attributes || {};
      const st = statusState.state || "IDLE";
      const pill = this.shadowRoot.getElementById("status-pill");
      pill.textContent = st;
      pill.setAttribute("data-status", st);

      const model = attrs.printer_model || "Bambu Lab";
      this.shadowRoot.getElementById("printer-title").textContent =
        this.#config.title || `Bambu AI Guard · ${model}`;

      const layer = attrs.layer ?? "—";
      const totalLayers = attrs.total_layers ?? "—";
      this.shadowRoot.getElementById("layer-chip").textContent =
        `Layer ${layer} / ${totalLayers}`;

      const lat = attrs.latency_ms ? `${attrs.latency_ms} ms` : "gemini-decision-1";
      this.shadowRoot.getElementById("latency-chip").textContent = lat;

      this.#updateBar("bar-spaghetti", "val-spaghetti", attrs.spaghetti_pct);
      this.#updateBar("bar-warping", "val-warping", attrs.warping_pct);
      this.#updateBar("bar-detachment", "val-detachment", attrs.detachment_pct);
      this.#updateBar(
        "bar-first-layer",
        "val-first-layer",
        attrs.first_layer_defect_pct
      );

      this.shadowRoot.getElementById("details-text").textContent =
        attrs.details || "Ready.";
    }

    if (camState && camState.attributes && camState.attributes.entity_picture) {
      const img = this.shadowRoot.getElementById("snapshot-img");
      const picUrl = camState.attributes.entity_picture;
      if (img.getAttribute("src") !== picUrl) {
        img.setAttribute("src", picUrl);
      }
    }

    if (historyState) {
      const hAttrs = historyState.attributes || {};
      const total = hAttrs.total_prints_recorded ?? historyState.state ?? 0;
      const keepSetting = hAttrs.purge_keep_prints_setting ?? 50;
      this.shadowRoot.getElementById("history-summary-label").textContent =
        `Lifetime Print History (${total} prints)`;
      this.shadowRoot.getElementById("btn-purge").textContent =
        `Purge Old (&gt; ${keepSetting})`.replace("&gt;", ">");

      const listEl = this.shadowRoot.getElementById("history-list");
      const prints = Array.isArray(hAttrs.recent_prints)
        ? hAttrs.recent_prints.slice(0, 15)
        : [];
      listEl.replaceChildren(
        ...prints.map((item) => {
          const row = document.createElement("div");
          row.className = "history-item";
          const nameSpan = document.createElement("span");
          nameSpan.className = "history-name";
          nameSpan.textContent = `${item.status === "FAILURE" ? "🚨" : item.status === "WARNING" ? "⚠️" : "✅"} ${item.print_name || "Print"}`;
          const metaSpan = document.createElement("span");
          metaSpan.className = "history-meta";
          metaSpan.textContent = `L${item.last_layer || 0}/${item.total_layers || 0} · ${item.inspections_count || 0} checks`;
          row.append(nameSpan, metaSpan);
          return row;
        })
      );
    }
  }
}

if (!customElements.get(CARD_TAG)) {
  customElements.define(CARD_TAG, BambuAIGuardCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === CARD_TAG)) {
  window.customCards.push({
    type: CARD_TAG,
    name: "Bambu AI Guard Card",
    description:
      "Live composite snapshot, Spaghetti/Warping/Detachment gauges, and Print History.",
    preview: true,
  });
}
