/**
 * Bambu AI Guard — Full-Screen Home Assistant Sidebar Panel (Zest Dashboard)
 * Auto-registered in the HA sidebar as "Bambu AI Guard" when the integration is added.
 */

const PANEL_TAG = "bambu-ai-guard-panel";

const PANEL_SHEET = new CSSStyleSheet();
PANEL_SHEET.replaceSync(`
  :host {
    display: block;
    min-height: 100vh;
    box-sizing: border-box;
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
    --z-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0, 0, 0, 0.06));
    --z-accent: var(--primary-color, #03a9f4);
    --z-accent-on: var(--text-primary-color, #ffffff);
    --z-ok-bg: color-mix(in srgb, var(--success-color, #43a047) 16%, transparent);
    --z-ok-ink: var(--success-color, #2e7d32);
    --z-warn-bg: color-mix(in srgb, var(--warning-color, #ffa600) 18%, transparent);
    --z-warn-ink: var(--warning-color, #d97706);
    --z-danger-bg: color-mix(in srgb, var(--error-color, #db4437) 16%, transparent);
    --z-danger-ink: var(--error-color, #db4437);

    background: var(--z-bg);
    color: var(--z-ink);
    font-family: var(--paper-font-body1_-_font-family, Roboto, system-ui, -apple-system, sans-serif);
  }

  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: var(--app-header-background-color, var(--z-surface));
    color: var(--app-header-text-color, var(--z-ink));
    border-bottom: 1px solid var(--z-border-soft);
    gap: 12px;
    flex-wrap: wrap;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .menu-btn {
    display: none;
    background: var(--z-surface-2);
    color: var(--z-ink);
    border: 2px solid var(--z-border);
    border-radius: 10px;
    padding: 6px 10px;
    font-weight: 800;
    cursor: pointer;
  }

  @media (max-width: 870px) {
    .menu-btn {
      display: inline-flex;
    }
  }

  .brand-badge {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    border: 2px solid var(--z-border);
    background: #538900;
    display: grid;
    place-items: center;
  }

  .brand-badge svg {
    width: 26px;
    height: 26px;
  }

  h1 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .sub {
    font-size: 0.82rem;
    color: var(--z-ink-2);
    font-weight: 600;
  }

  .status-pill {
    padding: 6px 14px;
    border-radius: 999px;
    border: 2px solid var(--z-border);
    font-size: 0.82rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    background: var(--z-surface-2);
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

  .shell {
    max-width: 1180px;
    margin: 0 auto;
    padding: 20px;
    display: grid;
    grid-template-columns: 1.45fr 1fr;
    gap: 18px;
  }

  @media (max-width: 960px) {
    .shell {
      grid-template-columns: 1fr;
    }
  }

  .panel-card {
    background: var(--z-surface);
    border: var(--ha-card-border-width, 1px) solid var(--z-border);
    border-radius: var(--z-radius);
    box-shadow: var(--z-shadow);
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .card-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: space-between;
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

  .viewport-empty {
    color: #B1C4A5;
    font-size: 0.9rem;
    font-weight: 600;
    text-align: center;
    padding: 24px;
  }

  .viewport-overlay {
    position: absolute;
    inset: auto 12px 12px 12px;
    display: flex;
    justify-content: space-between;
    gap: 8px;
    pointer-events: none;
  }

  .chip {
    background: rgba(15, 23, 11, 0.85);
    color: #F2F9ED;
    border: 1.5px solid rgba(155, 225, 42, 0.55);
    border-radius: 8px;
    padding: 5px 9px;
    font-size: 0.78rem;
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
    border-radius: 12px;
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .metric-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--z-ink-2);
  }

  .metric-val {
    font-weight: 800;
    color: var(--z-ink);
    font-variant-numeric: tabular-nums;
  }

  .bar-track {
    height: 8px;
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

  .bar-fill[data-risk="warn"] { background: #E09F00; }
  .bar-fill[data-risk="danger"] { background: #D93834; }

  .details-box {
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    border-radius: 10px;
    padding: 11px 13px;
    font-size: 0.86rem;
    line-height: 1.45;
  }

  .control-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 11px;
    border-radius: 10px;
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    font-size: 0.84rem;
    font-weight: 700;
  }

  .control-row select,
  .control-row input[type="number"] {
    background: var(--z-surface);
    color: var(--z-ink);
    border: 1.5px solid var(--z-border);
    border-radius: 8px;
    padding: 5px 9px;
    font-size: 0.84rem;
    font-weight: 700;
  }

  .control-row input[type="checkbox"] {
    width: 20px;
    height: 20px;
    accent-color: var(--z-accent);
    cursor: pointer;
  }

  .slider-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 9px 11px;
    border-radius: 10px;
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    font-size: 0.84rem;
    font-weight: 700;
  }

  .slider-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .slider-badge {
    background: var(--z-surface);
    color: var(--z-ink);
    border: 1.5px solid var(--z-border);
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 0.78rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
  }

  .slider-hint {
    font-size: 0.74rem;
    font-weight: 400;
    color: var(--z-ink-2);
    line-height: 1.3;
  }

  .slider-row[hidden] {
    display: none;
  }

  .slider-row input[type="range"] {
    width: 100%;
    accent-color: var(--z-accent);
    cursor: pointer;
    margin: 0;
  }

  .actions-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  button.zest-btn {
    appearance: none;
    border: 1px solid var(--z-border);
    border-radius: 8px;
    padding: 9px 16px;
    font-size: 0.86rem;
    font-weight: 600;
    cursor: pointer;
    background: var(--z-accent);
    color: var(--z-accent-on);
  }

  button.zest-btn.secondary {
    background: var(--z-surface-2);
    color: var(--z-ink);
  }

  button.zest-btn:active {
    transform: translateY(1px);
  }

  .history-table {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 360px;
    overflow-y: auto;
  }

  .history-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 9px 12px;
    border-radius: 10px;
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    font-size: 0.82rem;
    gap: 10px;
  }

  .full-width {
    grid-column: 1 / -1;
  }

  dialog.purge-dialog {
    background: var(--z-surface);
    color: var(--z-ink);
    border: 1px solid var(--z-border);
    border-radius: var(--z-radius);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.28);
    padding: 20px;
    max-width: 400px;
    width: calc(100% - 32px);
  }

  dialog.purge-dialog:modal {
    overscroll-behavior: contain;
  }

  dialog.purge-dialog::backdrop {
    background: rgba(0, 0, 0, 0.55);
    overflow: hidden;
    overscroll-behavior: contain;
  }

  dialog.purge-dialog h3 {
    margin: 0 0 8px;
    font-size: 1.05rem;
    font-weight: 700;
  }

  dialog.purge-dialog p {
    margin: 0 0 14px;
    font-size: 0.86rem;
    color: var(--z-ink-2);
    line-height: 1.45;
  }

  .preset-row {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 14px;
  }

  .dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 16px;
  }

  button.zest-btn.danger {
    background: var(--z-danger-ink);
    color: #ffffff;
    border-color: var(--z-danger-ink);
  }
`);

const PANEL_TEMPLATE = document.createElement("template");
PANEL_TEMPLATE.innerHTML = `
  <div class="topbar">
    <div class="topbar-left">
      <button type="button" class="menu-btn" id="btn-menu" aria-label="Toggle sidebar">☰</button>
      <div class="brand-badge" aria-hidden="true">
        <svg viewBox="0 0 64 64">
          <path d="M18 49V19a5 5 0 0 1 5-5h18a5 5 0 0 1 5 5v30" fill="none" stroke="#FDFFFB" stroke-width="4.5" stroke-linecap="round"/>
          <path d="M19 25.5h26" fill="none" stroke="#DCF4A6" stroke-width="4.5" stroke-linecap="round"/>
          <rect x="27" y="21" width="10" height="13" rx="2.5" fill="#FDFFFB" stroke="#1A260E" stroke-width="2"/>
          <path d="M27.5 34h9L32 41.5Z" fill="#9BE12A"/>
          <rect x="23.5" y="43" width="17" height="4" rx="2" fill="#9BE12A"/>
          <path d="M13 49h38" fill="none" stroke="#FDFFFB" stroke-width="5" stroke-linecap="round"/>
        </svg>
      </div>
      <div>
        <h1 id="panel-title">Bambu AI Guard</h1>
      </div>
    </div>
    <div class="status-pill" id="status-pill" data-status="IDLE">IDLE</div>
  </div>

  <div class="shell">
    <div class="panel-card">
      <h2 class="card-title">
        <span>Live AI Camera Inspection</span>
        <button type="button" class="zest-btn" id="btn-inspect">Inspect Now (AI)</button>
      </h2>
      <div class="viewport">
        <img id="snapshot-img" alt="Bambu AI Guard Snapshot" hidden />
        <div class="viewport-empty" id="snapshot-empty">Click "Inspect Now (AI)" to capture your first snapshot and verify your camera &amp; Gemini API connection.</div>
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
          <div class="metric-head"><span>Corner Warping</span><span class="metric-val" id="val-warping">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-warping"></div></div>
        </div>
        <div class="metric-box">
          <div class="metric-head"><span>Part Detachment</span><span class="metric-val" id="val-detachment">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-detachment"></div></div>
        </div>
        <div class="metric-box">
          <div class="metric-head"><span>First-Layer Defect</span><span class="metric-val" id="val-first-layer">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-first-layer"></div></div>
        </div>
      </div>

      <div class="details-box" id="details-text">Waiting for first inspection...</div>
    </div>

    <div class="panel-card">
      <h2 class="card-title"><span>Guard Controls &amp; Frequency</span></h2>

      <div class="control-row">
        <div>
          <label for="ctrl-autopause">Auto-Pause on Failure</label>
          <div class="slider-hint">Automatically pauses your printer if a critical failure is detected.</div>
        </div>
        <input type="checkbox" id="ctrl-autopause" />
      </div>

      <div class="control-row">
        <label for="ctrl-mode">When to Check Your Print</label>
        <select id="ctrl-mode">
          <option value="both">Layers or Time (Recommended)</option>
          <option value="layers">By Layer Count Only</option>
          <option value="minutes">By Time Interval Only</option>
        </select>
      </div>

      <div class="slider-row">
        <div class="slider-head">
          <label for="ctrl-l1">Extra Checks on Layer 1</label>
          <span class="slider-badge" id="val-ctrl-l1">3 checks</span>
        </div>
        <div class="slider-hint">Catches peeling or bad bed adhesion early while Layer 1 is still printing.</div>
        <input type="range" id="ctrl-l1" min="0" max="5" step="1" value="3" />
      </div>

      <div class="slider-row" id="row-ctrl-layers">
        <div class="slider-head">
          <label for="ctrl-layers">Check Every… (Layers)</label>
          <span class="slider-badge" id="val-ctrl-layers">10 layers</span>
        </div>
        <div class="slider-hint">Inspects your print every time this many layers finish.</div>
        <input type="range" id="ctrl-layers" min="1" max="50" step="1" value="10" />
      </div>

      <div class="slider-row" id="row-ctrl-mins">
        <div class="slider-head">
          <label for="ctrl-mins">Check Every… (Minutes)</label>
          <span class="slider-badge" id="val-ctrl-mins">5 min</span>
        </div>
        <div class="slider-hint">Inspects if this many minutes pass during a slow, large layer.</div>
        <input type="range" id="ctrl-mins" min="1" max="60" step="1" value="5" />
      </div>

      <div class="slider-row">
        <div class="slider-head">
          <label for="ctrl-thresh">Auto-Pause Confidence</label>
          <span class="slider-badge" id="val-ctrl-thresh">80%</span>
        </div>
        <div class="slider-hint">80% recommended. Lower pauses earlier; higher pauses only on obvious failures.</div>
        <input type="range" id="ctrl-thresh" min="50" max="95" step="5" value="80" />
      </div>
    </div>

    <div class="panel-card full-width">
      <h2 class="card-title">
        <span id="history-title">Lifetime Print History (0 prints)</span>
        <button type="button" class="zest-btn secondary" id="btn-open-purge">Purge History…</button>
      </h2>
      <div class="history-table" id="history-table"></div>
    </div>
  </div>

  <dialog class="purge-dialog" id="purge-dialog" closedby="any" aria-labelledby="purge-dialog-title">
    <h3 id="purge-dialog-title">Purge Print History</h3>
    <p>Choose how many recent prints to keep. All older print logs and snapshots will be permanently deleted.</p>
    <div class="preset-row">
      <button type="button" class="zest-btn secondary" data-preset="50">Keep 50</button>
      <button type="button" class="zest-btn secondary" data-preset="20">Keep 20</button>
      <button type="button" class="zest-btn secondary" data-preset="10">Keep 10</button>
      <button type="button" class="zest-btn secondary" data-preset="0">Delete All (0)</button>
    </div>
    <div class="control-row">
      <label for="ctrl-keep">Keep last X prints</label>
      <input type="number" id="ctrl-keep" min="0" max="1000" step="1" value="50" style="width:84px;" />
    </div>
    <form method="dialog" class="dialog-actions">
      <button value="cancel" class="zest-btn secondary" autofocus>Cancel</button>
      <button value="confirm" class="zest-btn danger">Confirm Purge</button>
    </form>
  </dialog>
`;

class BambuAIGuardPanel extends HTMLElement {
  #hass = null;
  #bound = false;
  #entityMap = {};

  constructor() {
    super();
    this.attachShadow({ mode: "open", delegatesFocus: true });
    this.shadowRoot.adoptedStyleSheets = [PANEL_SHEET];
    this.shadowRoot.append(PANEL_TEMPLATE.content.cloneNode(true));
  }

  connectedCallback() {
    if (!this.#bound) {
      this.#bound = true;
      const sr = this.shadowRoot;
      sr.getElementById("btn-menu").addEventListener("click", () => {
        this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
      });
      const imgEl = sr.getElementById("snapshot-img");
      const emptyEl = sr.getElementById("snapshot-empty");
      imgEl.addEventListener("load", () => {
        imgEl.hidden = false;
        emptyEl.hidden = true;
      });
      imgEl.addEventListener("error", () => {
        imgEl.hidden = true;
        emptyEl.hidden = false;
        emptyEl.textContent = "Printer camera offline or standby — turn on printer or click \"Inspect Now (AI)\" to capture a frame.";
      });
      sr.getElementById("btn-inspect").addEventListener("click", () => {
        if (this.#hass) this.#hass.callService("bambu_ai_guard", "inspect_now", {});
      });
      const purgeDialog = sr.getElementById("purge-dialog");
      const keepInput = sr.getElementById("ctrl-keep");
      sr.getElementById("btn-open-purge").addEventListener("click", () => {
        purgeDialog.showModal();
      });
      sr.querySelectorAll("[data-preset]").forEach((btn) => {
        btn.addEventListener("click", () => {
          keepInput.value = btn.getAttribute("data-preset");
        });
      });
      purgeDialog.addEventListener("close", () => {
        const outcome = purgeDialog.returnValue;
        purgeDialog.returnValue = "";
        if (outcome === "confirm" && this.#hass) {
          const keepVal = Math.max(0, Math.round(Number(keepInput.value || 0)));
          this.#hass.callService("bambu_ai_guard", "purge_history", {
            keep_last_prints: keepVal,
          });
        }
      });
      sr.getElementById("ctrl-autopause").addEventListener("change", (e) => {
        this.#toggleSwitch(this.#entityMap.autoPause, e.target.checked);
      });
      sr.getElementById("ctrl-mode").addEventListener("change", (e) => {
        const modeVal = e.target.value;
        sr.getElementById("row-ctrl-layers").hidden = modeVal === "minutes";
        sr.getElementById("row-ctrl-mins").hidden = modeVal === "layers";
        if (this.#hass && this.#entityMap.mode) {
          this.#hass.callService("select", "select_option", {
            entity_id: this.#entityMap.mode,
            option: modeVal,
          });
        }
      });
      const formatBadge = (elId, rawVal) => {
        const n = Math.round(Number(rawVal));
        const badge = sr.getElementById(`val-${elId}`);
        if (!badge || Number.isNaN(n)) return;
        if (elId === "ctrl-l1") badge.textContent = `${n} check${n === 1 ? "" : "s"}`;
        else if (elId === "ctrl-layers") badge.textContent = `${n} layer${n === 1 ? "" : "s"}`;
        else if (elId === "ctrl-mins") badge.textContent = `${n} min`;
        else if (elId === "ctrl-thresh") badge.textContent = `${n}%`;
      };
      const bindNum = (elId, key) => {
        const el = sr.getElementById(elId);
        el.addEventListener("input", (e) => formatBadge(elId, e.target.value));
        el.addEventListener("change", (e) => {
          formatBadge(elId, e.target.value);
          const eid = this.#entityMap[key];
          if (this.#hass && eid) {
            this.#hass.callService("number", "set_value", {
              entity_id: eid,
              value: Math.round(Number(e.target.value)),
            });
          }
        });
      };
      bindNum("ctrl-l1", "l1");
      bindNum("ctrl-layers", "layers");
      bindNum("ctrl-mins", "mins");
      bindNum("ctrl-thresh", "thresh");
      bindNum("ctrl-keep", "keep");
    }
    this.#render();
  }

  set hass(hass) {
    this.#hass = hass;
    this.#render();
  }

  #toggleSwitch(entityId, turnOn) {
    if (!this.#hass || !entityId) return;
    this.#hass.callService("switch", turnOn ? "turn_on" : "turn_off", {
      entity_id: entityId,
    });
  }

  #find(domain, needles) {
    if (!this.#hass) return null;
    const ids = Object.keys(this.#hass.states).filter((id) => id.startsWith(`${domain}.`));
    for (const n of needles) {
      const hit = ids.find((id) => id.includes(n));
      if (hit) return hit;
    }
    return null;
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
    if (num >= 80) bar.setAttribute("data-risk", "danger");
    else if (num >= 50) bar.setAttribute("data-risk", "warn");
    else bar.removeAttribute("data-risk");
  }

  #render() {
    if (!this.#hass || !this.shadowRoot) return;
    const sr = this.shadowRoot;

    this.#entityMap = {
      status: this.#find("sensor", ["ai_guard_status", "statut_ai_guard"]),
      camera: this.#find("camera", ["ai_guard_composite_snapshot", "snapshot_composite_ai_guard"]),
      history: this.#find("sensor", ["ai_print_history", "historique_des_impressions_ia"]),
      autoPause: this.#find("switch", ["ai_auto_pause", "pause_auto_ia"]),
      median: this.#find("switch", ["nozzle_erasing_filter", "anti_buse", "median_filter"]),
      mode: this.#find("select", ["check_schedule_mode", "frequence_d_inspection"]),
      l1: this.#find("number", ["first_layer_checks", "premiere_couche"]),
      layers: this.#find("number", ["layer_check_interval", "intervalle_de_couches"]),
      mins: this.#find("number", ["minute_check_interval", "intervalle_de_minutes"]),
      thresh: this.#find("number", ["auto_pause_threshold", "seuil_de_pause"]),
      keep: this.#find("number", ["keep_last_x_prints", "conserver_les_x"]),
    };

    const stObj = this.#entityMap.status ? this.#hass.states[this.#entityMap.status] : null;
    if (stObj) {
      const a = stObj.attributes || {};
      const st = stObj.state || "IDLE";
      const pill = sr.getElementById("status-pill");
      pill.textContent = st;
      pill.setAttribute("data-status", st);
      sr.getElementById("panel-title").textContent = `Bambu AI Guard · ${a.printer_model || "Printer"}`;
      sr.getElementById("layer-chip").textContent = `Layer ${a.layer ?? "—"} / ${a.total_layers ?? "—"}`;
      sr.getElementById("latency-chip").textContent = a.latency_ms ? `${a.latency_ms} ms` : "gemini-decision-1";
      sr.getElementById("details-text").textContent = a.details || "Ready.";

      this.#updateBar("bar-spaghetti", "val-spaghetti", a.spaghetti_pct);
      this.#updateBar("bar-warping", "val-warping", a.warping_pct);
      this.#updateBar("bar-detachment", "val-detachment", a.detachment_pct);
      this.#updateBar("bar-first-layer", "val-first-layer", a.first_layer_defect_pct);
    }

    const camObj = this.#entityMap.camera ? this.#hass.states[this.#entityMap.camera] : null;
    if (camObj && camObj.attributes && camObj.attributes.entity_picture) {
      const img = sr.getElementById("snapshot-img");
      const url = camObj.attributes.entity_picture;
      if (img.getAttribute("src") !== url) {
        img.setAttribute("src", url);
      }
    }

    const syncCheck = (elId, key) => {
      const s = this.#entityMap[key] ? this.#hass.states[this.#entityMap[key]] : null;
      if (s) sr.getElementById(elId).checked = s.state === "on";
    };
    const syncVal = (elId, key, isInt = false) => {
      const el = sr.getElementById(elId);
      const s = this.#entityMap[key] ? this.#hass.states[this.#entityMap[key]] : null;
      if (s && document.activeElement !== el && sr.activeElement !== el) {
        const val = isInt ? String(Math.round(Number(s.state))) : s.state;
        el.value = val;
        const badge = sr.getElementById(`val-${elId}`);
        if (badge && isInt) {
          const n = Math.round(Number(s.state));
          if (elId === "ctrl-l1") badge.textContent = `${n} check${n === 1 ? "" : "s"}`;
          else if (elId === "ctrl-layers") badge.textContent = `${n} layer${n === 1 ? "" : "s"}`;
          else if (elId === "ctrl-mins") badge.textContent = `${n} min`;
          else if (elId === "ctrl-thresh") badge.textContent = `${n}%`;
        }
      }
    };
    syncCheck("ctrl-autopause", "autoPause");
    syncVal("ctrl-mode", "mode", false);
    const activeMode = sr.getElementById("ctrl-mode").value;
    sr.getElementById("row-ctrl-layers").hidden = activeMode === "minutes";
    sr.getElementById("row-ctrl-mins").hidden = activeMode === "layers";
    syncVal("ctrl-l1", "l1", true);
    syncVal("ctrl-layers", "layers", true);
    syncVal("ctrl-mins", "mins", true);
    syncVal("ctrl-thresh", "thresh", true);
    syncVal("ctrl-keep", "keep", true);

    const histObj = this.#entityMap.history ? this.#hass.states[this.#entityMap.history] : null;
    if (histObj) {
      const ha = histObj.attributes || {};
      const total = ha.total_prints_recorded ?? histObj.state ?? 0;
      sr.getElementById("history-title").textContent = `Lifetime Print History (${total} prints)`;

      const table = sr.getElementById("history-table");
      const prints = Array.isArray(ha.recent_prints) ? ha.recent_prints : [];
      if (prints.length === 0) {
        table.innerHTML = `<div class="details-box">No prints recorded yet. Start a print or click "Inspect Now (AI)" to log your first entry!</div>`;
      } else {
        table.replaceChildren(
          ...prints.map((item) => {
            const row = document.createElement("div");
            row.className = "history-row";
            const left = document.createElement("span");
            left.style.fontWeight = "700";
            left.textContent = `${item.status === "FAILURE" ? "🚨" : item.status === "WARNING" ? "⚠️" : "✅"} ${item.print_name || "Print"}`;
            const right = document.createElement("span");
            right.style.color = "var(--z-ink-2)";
            right.textContent = `L${item.last_layer || 0}/${item.total_layers || 0} · ${item.inspections_count || 0} checks · Max Spaghetti ${item.max_spaghetti_pct ?? 0}%`;
            row.append(left, right);
            return row;
          })
        );
      }
    }
  }
}

if (!customElements.get(PANEL_TAG)) {
  customElements.define(PANEL_TAG, BambuAIGuardPanel);
}
