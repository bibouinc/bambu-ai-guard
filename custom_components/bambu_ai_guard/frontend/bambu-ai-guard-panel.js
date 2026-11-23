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

  .tab-bar {
    display: flex;
    gap: 6px;
    padding: 0 20px;
    background: var(--app-header-background-color, var(--z-surface));
    border-bottom: 1px solid var(--z-border-soft);
    overflow-x: auto;
  }

  .tab-btn {
    appearance: none;
    background: transparent;
    border: 0;
    border-bottom: 3px solid transparent;
    color: var(--z-ink-2);
    padding: 12px 16px;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }

  .tab-btn ha-icon {
    --mdc-icon-size: 18px;
  }

  .tab-btn[aria-selected="true"] {
    color: var(--z-accent);
    border-bottom-color: var(--z-accent);
  }

  .tab-pane {
    max-width: 1120px;
    margin: 0 auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .tab-pane[hidden] {
    display: none;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }

  .kpi-card {
    background: var(--z-surface);
    border: var(--ha-card-border-width, 1px) solid var(--z-border);
    border-radius: var(--z-radius);
    box-shadow: var(--z-shadow);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .kpi-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--z-ink-2);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .kpi-label ha-icon {
    --mdc-icon-size: 16px;
    color: var(--z-accent);
  }

  .kpi-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--z-ink);
    font-variant-numeric: tabular-nums;
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
    .tab-bar {
    display: flex;
    gap: 6px;
    padding: 0 20px;
    background: var(--app-header-background-color, var(--z-surface));
    border-bottom: 1px solid var(--z-border-soft);
    overflow-x: auto;
  }

  .tab-btn {
    appearance: none;
    background: transparent;
    border: 0;
    border-bottom: 3px solid transparent;
    color: var(--z-ink-2);
    padding: 12px 16px;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    white-space: nowrap;
  }

  .tab-btn ha-icon {
    --mdc-icon-size: 18px;
  }

  .tab-btn[aria-selected="true"] {
    color: var(--z-accent);
    border-bottom-color: var(--z-accent);
  }

  .tab-pane {
    max-width: 1120px;
    margin: 0 auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .tab-pane[hidden] {
    display: none;
  }

  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
  }

  .kpi-card {
    background: var(--z-surface);
    border: var(--ha-card-border-width, 1px) solid var(--z-border);
    border-radius: var(--z-radius);
    box-shadow: var(--z-shadow);
    padding: 14px 16px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .kpi-label {
    font-size: 0.76rem;
    font-weight: 700;
    color: var(--z-ink-2);
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .kpi-label ha-icon {
    --mdc-icon-size: 16px;
    color: var(--z-accent);
  }

  .kpi-value {
    font-size: 1.5rem;
    font-weight: 800;
    color: var(--z-ink);
    font-variant-numeric: tabular-nums;
  }

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

  .label-with-icon {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .label-with-icon ha-icon,
  .section-label ha-icon,
  .card-title ha-icon,
  .metric-head ha-icon,
  button.zest-btn ha-icon {
    --mdc-icon-size: 18px;
    color: var(--z-accent);
    flex-shrink: 0;
  }

  button.zest-btn ha-icon {
    color: currentColor;
  }

  button.zest-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }

  .section-label {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--z-ink-2);
    margin: 4px 0 -4px 2px;
  }

  .section-divider {
    border: 0;
    border-top: 1px solid var(--z-border-soft);
    margin: 6px 0 2px;
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

  .gallery-strip {
    display: grid;
    grid-auto-flow: column;
    grid-auto-columns: minmax(175px, 195px);
    gap: 12px;
    overflow-x: auto;
    padding: 4px 2px 10px;
    scroll-snap-type: x proximity;
  }

  .gallery-card {
    scroll-snap-align: start;
    background: var(--z-surface-2);
    border: 1.5px solid var(--z-border-soft);
    border-radius: 11px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    cursor: pointer;
    transition: border-color 0.15s ease, transform 0.12s ease;
    padding: 0;
    text-align: left;
    color: var(--z-ink);
  }

  .gallery-card:hover {
    border-color: var(--z-accent);
    transform: translateY(-2px);
  }

  .gallery-card[data-selected="true"] {
    border: 2px solid var(--z-accent);
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--z-accent) 25%, transparent);
  }

  .gallery-thumb {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
    background: #141414;
  }

  .gallery-meta {
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .gallery-title {
    font-size: 0.78rem;
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .gallery-sub {
    font-size: 0.7rem;
    color: var(--z-ink-2);
  }

  .replay-bar {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
  }

  .replay-bar select {
    flex: 1 1 260px;
    background: var(--z-surface-2);
    color: var(--z-ink);
    border: 1px solid var(--z-border);
    border-radius: 8px;
    padding: 9px 11px;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .replay-banner {
    padding: 11px 14px;
    border-radius: 10px;
    font-size: 0.86rem;
    font-weight: 700;
    border: 1px solid var(--z-border-soft);
    background: var(--z-surface-2);
  }

  .replay-banner[data-state="ok"] {
    background: var(--z-ok-bg);
    color: var(--z-ok-ink);
  }

  .replay-banner[data-state="fail"] {
    background: var(--z-danger-bg);
    color: var(--z-danger-ink);
  }

  .replay-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(195px, 1fr));
    gap: 10px;
  }

  .replay-step {
    background: var(--z-surface-2);
    border: 1px solid var(--z-border-soft);
    border-radius: 10px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .replay-step[data-pause="true"] {
    border: 2px solid var(--z-danger-ink);
  }

  .replay-step img {
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: cover;
    display: block;
    background: #111;
  }

  .replay-step-meta {
    padding: 8px 10px;
    font-size: 0.76rem;
    display: flex;
    flex-direction: column;
    gap: 3px;
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

  <div class="tab-bar" role="tablist" aria-label="Bambu AI Guard Sections">
    <button type="button" class="tab-btn" role="tab" id="tab-live" data-tab="live" aria-selected="true">
      <ha-icon icon="mdi:camera-iris"></ha-icon>Live Guard
    </button>
    <button type="button" class="tab-btn" role="tab" id="tab-stats" data-tab="stats" aria-selected="false">
      <ha-icon icon="mdi:chart-box-outline"></ha-icon>Stats &amp; Replay
    </button>
    <button type="button" class="tab-btn" role="tab" id="tab-settings" data-tab="settings" aria-selected="false">
      <ha-icon icon="mdi:tune-variant"></ha-icon>Settings
    </button>
  </div>

  <div class="tab-pane" id="pane-live" role="tabpanel">
    <div class="panel-card">
      <h2 class="card-title">
        <span class="label-with-icon"><ha-icon icon="mdi:camera-iris"></ha-icon>Live AI Camera Inspection</span>
        <button type="button" class="zest-btn" id="btn-inspect"><ha-icon icon="mdi:magnify-scan"></ha-icon>Inspect Now (AI)</button>
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
          <div class="metric-head"><span class="label-with-icon"><ha-icon icon="mdi:pasta"></ha-icon>Spaghetti</span><span class="metric-val" id="val-spaghetti">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-spaghetti"></div></div>
        </div>
        <div class="metric-box">
          <div class="metric-head"><span class="label-with-icon"><ha-icon icon="mdi:angle-acute"></ha-icon>Corner Warping</span><span class="metric-val" id="val-warping">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-warping"></div></div>
        </div>
        <div class="metric-box">
          <div class="metric-head"><span class="label-with-icon"><ha-icon icon="mdi:cube-off-outline"></ha-icon>Part Detachment</span><span class="metric-val" id="val-detachment">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-detachment"></div></div>
        </div>
        <div class="metric-box">
          <div class="metric-head"><span class="label-with-icon"><ha-icon icon="mdi:layers-off"></ha-icon>First-Layer Defect</span><span class="metric-val" id="val-first-layer">—</span></div>
          <div class="bar-track"><div class="bar-fill" id="bar-first-layer"></div></div>
        </div>
      </div>

      <div class="details-box" id="details-text">Waiting for first inspection...</div>
    </div>
  </div>

  <div class="tab-pane" id="pane-stats" role="tabpanel" hidden>
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label"><ha-icon icon="mdi:printer-3d"></ha-icon>Prints Monitored</div>
        <div class="kpi-value" id="kpi-prints">0</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><ha-icon icon="mdi:magnify-scan"></ha-icon>Total AI Checks</div>
        <div class="kpi-value" id="kpi-checks">0</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><ha-icon icon="mdi:shield-alert-outline"></ha-icon>Failures Caught</div>
        <div class="kpi-value" id="kpi-failures">0</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label"><ha-icon icon="mdi:speedometer"></ha-icon>Last API Latency</div>
        <div class="kpi-value" id="kpi-latency">—</div>
      </div>
    </div>

    <div class="panel-card">
      <h2 class="card-title">
        <span class="label-with-icon"><ha-icon icon="mdi:movie-play-outline"></ha-icon>Try on a Previous Print</span>
        <div class="actions-row">
          <button type="button" class="zest-btn secondary" id="btn-refresh-timelapses"><ha-icon icon="mdi:refresh"></ha-icon>Refresh</button>
          <button type="button" class="zest-btn" id="btn-run-replay" disabled><ha-icon icon="mdi:play-circle-outline"></ha-icon>Simulate Selected Print</button>
        </div>
      </h2>
      <div class="slider-hint" style="margin-top:-6px;">Pick any previous print below to replay it with your current settings and see the exact layer where Auto-Pause would have triggered (dry-run only).</div>
      <div class="gallery-strip" id="replay-gallery">
        <div class="details-box">Loading previous print thumbnails…</div>
      </div>
      <div class="replay-banner" id="replay-banner" hidden></div>
      <div class="replay-grid" id="replay-grid"></div>
    </div>

    <div class="panel-card">
      <h2 class="card-title">
        <span class="label-with-icon"><ha-icon icon="mdi:history"></ha-icon><span id="history-title">Lifetime Print History (0 prints)</span></span>
        <button type="button" class="zest-btn secondary" id="btn-open-purge"><ha-icon icon="mdi:delete-sweep-outline"></ha-icon>Purge History…</button>
      </h2>
      <div class="history-table" id="history-table"></div>
    </div>
  </div>

  <div class="tab-pane" id="pane-settings" role="tabpanel" hidden>
    <div class="panel-card">
      <h2 class="card-title"><span class="label-with-icon"><ha-icon icon="mdi:tune-variant"></ha-icon>Guard Settings</span></h2>

      <div class="section-label"><ha-icon icon="mdi:shield-check-outline"></ha-icon>Safety &amp; Alerts</div>

      <div class="control-row">
        <div>
          <label for="ctrl-autopause" class="label-with-icon"><ha-icon icon="mdi:pause-octagon-outline"></ha-icon>Auto-Pause on Failure</label>
          <div class="slider-hint">Automatically pauses your printer if a critical failure is detected.</div>
        </div>
        <input type="checkbox" id="ctrl-autopause" />
      </div>

      <div class="slider-row">
        <div class="slider-head">
          <label for="ctrl-thresh" class="label-with-icon"><ha-icon icon="mdi:gauge"></ha-icon>Auto-Pause Confidence</label>
          <span class="slider-badge" id="val-ctrl-thresh">80%</span>
        </div>
        <div class="slider-hint">80% recommended. Lower pauses earlier; higher pauses only on obvious failures.</div>
        <input type="range" id="ctrl-thresh" min="50" max="95" step="5" value="80" />
      </div>

      <div class="control-row">
        <div>
          <label for="ctrl-notify" class="label-with-icon"><ha-icon icon="mdi:cellphone-message"></ha-icon>Phone Push Notifications</label>
          <div class="slider-hint">Sends an instant alert with the snapshot photo to your phone on defects.</div>
        </div>
        <select id="ctrl-notify">
          <option value="none">Off (Dashboard Only)</option>
          <option value="notify.notify">All Mobile Apps</option>
        </select>
      </div>

      <hr class="section-divider" />
      <div class="section-label"><ha-icon icon="mdi:calendar-clock"></ha-icon>Inspection Schedule</div>

      <div class="control-row">
        <label for="ctrl-mode" class="label-with-icon"><ha-icon icon="mdi:clock-check-outline"></ha-icon>When to Check Your Print</label>
        <select id="ctrl-mode">
          <option value="both">Layers or Time (Recommended)</option>
          <option value="layers">By Layer Count Only</option>
          <option value="minutes">By Time Interval Only</option>
        </select>
      </div>

      <div class="slider-row">
        <div class="slider-head">
          <label for="ctrl-l1" class="label-with-icon"><ha-icon icon="mdi:numeric-1-box-multiple-outline"></ha-icon>Extra Checks on Layer 1</label>
          <span class="slider-badge" id="val-ctrl-l1">3 checks</span>
        </div>
        <div class="slider-hint">Catches peeling or bad bed adhesion early while Layer 1 is still printing.</div>
        <input type="range" id="ctrl-l1" min="0" max="5" step="1" value="3" />
      </div>

      <div class="slider-row" id="row-ctrl-layers">
        <div class="slider-head">
          <label for="ctrl-layers" class="label-with-icon"><ha-icon icon="mdi:layers-triple-outline"></ha-icon>Check Every… (Layers)</label>
          <span class="slider-badge" id="val-ctrl-layers">10 layers</span>
        </div>
        <div class="slider-hint">Inspects your print every time this many layers finish.</div>
        <input type="range" id="ctrl-layers" min="1" max="50" step="1" value="10" />
      </div>

      <div class="slider-row" id="row-ctrl-mins">
        <div class="slider-head">
          <label for="ctrl-mins" class="label-with-icon"><ha-icon icon="mdi:timer-outline"></ha-icon>Check Every… (Minutes)</label>
          <span class="slider-badge" id="val-ctrl-mins">5 min</span>
        </div>
        <div class="slider-hint">Inspects if this many minutes pass during a slow, large layer.</div>
        <input type="range" id="ctrl-mins" min="1" max="60" step="1" value="5" />
      </div>
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
  #timelapsesLoaded = false;
  #selectedVideoId = "";
  #pollTimer = null;

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
      sr.querySelectorAll("[data-tab]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const target = btn.dataset.tab;
          sr.querySelectorAll("[data-tab]").forEach((b) => {
            b.setAttribute("aria-selected", b.dataset.tab === target ? "true" : "false");
          });
          ["live", "stats", "settings"].forEach((pane) => {
            sr.getElementById(`pane-${pane}`).hidden = pane !== target;
          });
        });
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
      sr.getElementById("ctrl-notify").addEventListener("change", (e) => {
        if (this.#hass && this.#entityMap.notify) {
          this.#hass.callService("select", "select_option", {
            entity_id: this.#entityMap.notify,
            option: e.target.value,
          });
        }
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
      sr.getElementById("btn-refresh-timelapses").addEventListener("click", () => {
        this.#loadTimelapses();
      });
      sr.getElementById("btn-run-replay").addEventListener("click", () => {
        this.#startReplay();
      });
      bindNum("ctrl-l1", "l1");
      bindNum("ctrl-layers", "layers");
      bindNum("ctrl-mins", "mins");
      bindNum("ctrl-thresh", "thresh");
      bindNum("ctrl-keep", "keep");
    }
    this.#render();
  }

  disconnectedCallback() {
    if (this.#pollTimer) {
      clearInterval(this.#pollTimer);
      this.#pollTimer = null;
    }
  }

  async #loadTimelapses() {
    if (!this.#hass) return;
    const gallery = this.shadowRoot.getElementById("replay-gallery");
    const runBtn = this.shadowRoot.getElementById("btn-run-replay");
    try {
      const data = await this.#hass.callApi("GET", "bambu_ai_guard/timelapses");
      const list = Array.isArray(data?.timelapses) ? data.timelapses : [];
      if (list.length === 0) {
        gallery.innerHTML = `<div class="details-box">No previous print timelapses found in /media or printer SD card.</div>`;
        runBtn.disabled = true;
        return;
      }

      if (!this.#selectedVideoId || !list.some((x) => x.id === this.#selectedVideoId)) {
        this.#selectedVideoId = list[0].id;
      }
      runBtn.disabled = false;

      gallery.replaceChildren(
        ...list.slice(0, 20).map((item) => {
          const card = document.createElement("button");
          card.type = "button";
          card.className = "gallery-card";
          card.dataset.videoId = item.id;
          if (item.id === this.#selectedVideoId) {
            card.setAttribute("data-selected", "true");
          }

          if (item.thumb_url) {
            const img = document.createElement("img");
            img.className = "gallery-thumb";
            img.loading = "lazy";
            img.src = item.thumb_url;
            img.alt = item.label;
            card.append(img);
          } else {
            const ph = document.createElement("div");
            ph.className = "gallery-thumb";
            ph.style.display = "grid";
            ph.style.placeItems = "center";
            ph.style.color = "#aaa";
            ph.style.fontSize = "0.75rem";
            ph.textContent = "Printer SD Timelapse";
            card.append(ph);
          }

          const meta = document.createElement("div");
          meta.className = "gallery-meta";
          const t = document.createElement("div");
          t.className = "gallery-title";
          t.textContent = item.label;
          t.title = item.label;
          const s = document.createElement("div");
          s.className = "gallery-sub";
          s.textContent = item.size_mb ? `${item.size_mb} MB` : "SD Card";
          meta.append(t, s);
          card.append(meta);

          card.addEventListener("click", () => {
            this.#selectedVideoId = item.id;
            gallery.querySelectorAll(".gallery-card").forEach((el) => {
              el.setAttribute(
                "data-selected",
                el.dataset.videoId === item.id ? "true" : "false"
              );
            });
            runBtn.disabled = false;
          });
          return card;
        })
      );
    } catch (err) {
      gallery.innerHTML = `<div class="details-box">Could not load previous prints — restart Home Assistant to activate v1.5.1.</div>`;
    }
  }

  async #startReplay() {
    if (!this.#hass) return;
    const sr = this.shadowRoot;
    const videoId = this.#selectedVideoId;
    if (!videoId) return;

    const btn = sr.getElementById("btn-run-replay");
    const banner = sr.getElementById("replay-banner");
    btn.disabled = true;
    btn.textContent = "Simulating…";
    banner.hidden = false;
    banner.removeAttribute("data-state");
    banner.textContent = "Extracting timelapse layer frames and running Gemini Decisions API…";

    try {
      await this.#hass.callApi("POST", "bambu_ai_guard/simulate", {
        video_id: videoId,
      });
      if (this.#pollTimer) clearInterval(this.#pollTimer);
      this.#pollTimer = setInterval(() => this.#pollReplayProgress(), 1200);
      await this.#pollReplayProgress();
    } catch (err) {
      btn.disabled = false;
      btn.textContent = "Simulate Print";
      banner.setAttribute("data-state", "fail");
      banner.textContent = `Simulation error: ${err.message || err}`;
    }
  }

  async #pollReplayProgress() {
    if (!this.#hass) return;
    const sr = this.shadowRoot;
    try {
      const p = await this.#hass.callApi("GET", "bambu_ai_guard/simulate");
      const banner = sr.getElementById("replay-banner");
      const grid = sr.getElementById("replay-grid");
      const btn = sr.getElementById("btn-run-replay");

      banner.hidden = false;
      if (p.error) {
        banner.setAttribute("data-state", "fail");
        banner.textContent = `Simulation error: ${p.error}`;
      } else if (p.running) {
        banner.removeAttribute("data-state");
        banner.textContent = `Replaying ${p.video_name || "print"}: checked ${p.checked}/${p.total_checkpoints || "?"} checkpoints (total ${p.total_layers || "?"} layers)…`;
      } else if (p.would_pause) {
        banner.setAttribute("data-state", "fail");
        banner.textContent = `🚨 WOULD HAVE AUTO-PAUSED at Layer ${p.pause_layer}/${p.total_layers} — ${p.pause_reason}`;
      } else if (p.checked > 0) {
        banner.setAttribute("data-state", "ok");
        banner.textContent = `✅ Print Passed All ${p.checked} Checkpoints (${p.total_layers} layers) — 0 false positives!`;
      }

      if (Array.isArray(p.results)) {
        grid.replaceChildren(
          ...p.results.map((r) => {
            const card = document.createElement("div");
            card.className = "replay-step";
            if (r.would_pause) card.setAttribute("data-pause", "true");
            const img = document.createElement("img");
            img.src = r.image_data_url;
            img.alt = `Layer ${r.layer}`;
            const meta = document.createElement("div");
            meta.className = "replay-step-meta";
            const head = document.createElement("strong");
            head.textContent = `${r.would_pause ? "🚨 PAUSE" : r.status === "WARNING" ? "⚠️ WARN" : "✅ OK"} · Layer ${r.layer}/${r.total_layers}`;
            const sub = document.createElement("span");
            sub.style.color = "var(--z-ink-2)";
            sub.textContent = `Spaghetti ${r.spaghetti_pct}% · Warp ${r.warping_pct}% · Detach ${r.detachment_pct}%`;
            meta.append(head, sub);
            card.append(img, meta);
            return card;
          })
        );
      }

      if (!p.running) {
        btn.disabled = false;
        btn.textContent = "Simulate Print";
        if (this.#pollTimer) {
          clearInterval(this.#pollTimer);
          this.#pollTimer = null;
        }
      }
    } catch (_) {}
  }

  set hass(hass) {
    this.#hass = hass;
    if (!this.#timelapsesLoaded && hass) {
      this.#timelapsesLoaded = true;
      this.#loadTimelapses();
    }
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
      notify: this.#find("select", ["notify_target", "push_notifications", "notifications_push"]),
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
      sr.getElementById("kpi-checks").textContent = String(a.total_inspections ?? 0);
      sr.getElementById("kpi-failures").textContent = String(a.failures_detected ?? 0);
      sr.getElementById("kpi-latency").textContent = a.latency_ms ? `${a.latency_ms} ms` : "—";

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
    const notifySel = sr.getElementById("ctrl-notify");
    const notifyState = this.#entityMap.notify ? this.#hass.states[this.#entityMap.notify] : null;
    if (notifyState && Array.isArray(notifyState.attributes?.options)) {
      const opts = notifyState.attributes.options;
      const curKeys = Array.from(notifySel.options).map((o) => o.value).join(",");
      if (curKeys !== opts.join(",")) {
        notifySel.replaceChildren(
          ...opts.map((opt) => {
            const o = document.createElement("option");
            o.value = opt;
            o.textContent =
              opt === "none"
                ? "Off (Dashboard Only)"
                : opt === "notify.notify"
                ? "All Mobile Apps"
                : opt.replace(/^notify\./, "").replace(/^mobile_app_/, "Phone: ");
            return o;
          })
        );
      }
      if (document.activeElement !== notifySel && sr.activeElement !== notifySel) {
        notifySel.value = notifyState.state;
      }
    }
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
      sr.getElementById("kpi-prints").textContent = String(total);

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
