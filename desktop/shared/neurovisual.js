/* Chimera / Octavian Neurovisual adaptive desktop layer.
 * Deterministic presentation adapter: accepts normalized 14-axis model outputs,
 * smooths them recurrently, and maps them to CSS tokens. It is not an LLM,
 * CNN, consciousness detector, quantum simulator, or scientific measurement.
 */
(() => {
  "use strict";
  const AXES = Object.freeze([
    "x", "y", "z", "time", "perspective", "energy", "interaction",
    "identity", "material", "information", "stochasticity", "agency",
    "semantic", "integration"
  ]);
  const clamp = (v, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, Number.isFinite(Number(v)) ? Number(v) : 0.5));
  const initial = Object.fromEntries(AXES.map(k => [k, 0.5]));
  initial.time = (new Date().getHours() / 23);
  initial.agency = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0.12 : 0.55;
  initial.semantic = 0.72;
  let state = { ...initial };
  let smoothed = { ...initial };
  let frame = 0;
  const palettes = {
    aurora: { hue: 184, saturation: 76 },
    marine: { hue: 211, saturation: 78 },
    focus: { hue: 268, saturation: 68 },
    calm: { hue: 166, saturation: 54 },
    explore: { hue: 194, saturation: 84 }
  };
  let identity = document.documentElement.dataset.neurovisual || "aurora";
  function normalize(input) {
    const next = { ...state };
    if (Array.isArray(input)) AXES.forEach((k, i) => { if (i < input.length) next[k] = clamp(input[i]); });
    else if (input && typeof input === "object") AXES.forEach(k => { if (k in input) next[k] = clamp(input[k]); });
    return next;
  }
  function project() {
    const s = smoothed;
    const p = palettes[identity] || palettes.aurora;
    const semanticHue = p.hue + (s.semantic - 0.5) * 54 + (s.perspective - 0.5) * 20;
    const opacity = 0.48 + s.material * 0.34;
    const blur = 10 + s.material * 22;
    const motion = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 0.15 + s.agency * 0.85;
    const density = 0.82 + s.information * 0.34;
    const brightness = 0.82 + s.energy * 0.36;
    const parallax = 1 + s.perspective * 5;
    const glow = 0.08 + s.integration * 0.22;
    const root = document.documentElement;
    const vars = {
      "--nv-accent": `hsl(${Math.round(semanticHue)} ${Math.round(p.saturation)}% 66%)`,
      "--nv-accent-soft": `hsl(${Math.round(semanticHue)} ${Math.round(p.saturation)}% 66% / .18)`,
      "--nv-glass-alpha": opacity.toFixed(3),
      "--nv-glass-blur": blur.toFixed(1) + "px",
      "--nv-motion": motion.toFixed(3),
      "--nv-density": density.toFixed(3),
      "--nv-brightness": brightness.toFixed(3),
      "--nv-parallax": parallax.toFixed(2) + "px",
      "--nv-glow": glow.toFixed(3),
      "--nv-noise": (s.stochasticity * 0.018).toFixed(4)
    };
    Object.entries(vars).forEach(([key, value]) => root.style.setProperty(key, value));
    root.dataset.neurovisualIdentity = identity;
    root.dataset.neurovisualFrame = String(++frame);
  }
  function update(input, options = {}) {
    state = normalize(input);
    const alpha = clamp(options.alpha ?? 0.18, 0.02, 0.8);
    AXES.forEach(k => { smoothed[k] += (state[k] - smoothed[k]) * alpha; });
    if (typeof options.identity === "string" && options.identity in palettes) identity = options.identity;
    project();
    window.dispatchEvent(new CustomEvent("chimera-neurovisual-updated", { detail: { state: { ...smoothed }, identity } }));
  }
  function setIdentity(value) {
    if (value in palettes) { identity = value; update({}); }
  }
  const style = document.createElement("style");
  style.textContent = `
    :root { --nv-accent: hsl(184 76% 66%); --nv-glass-alpha: .68; --nv-glass-blur: 22px; --nv-motion: .55; --nv-density: 1; --nv-brightness: 1; --nv-parallax: 3px; --nv-glow: .18; }
    body { filter: brightness(var(--nv-brightness)); }
    button:focus-visible, a:focus-visible { outline: 2px solid var(--nv-accent) !important; outline-offset: 3px; }
    .dock, .taskbar, .topbar, .menu-bar, .menubar, .panel, .window, .start-menu, .launcher, .control-center, .widget {
      backdrop-filter: blur(var(--nv-glass-blur)) saturate(1.25);
      -webkit-backdrop-filter: blur(var(--nv-glass-blur)) saturate(1.25);
      border-color: color-mix(in srgb, var(--nv-accent) 28%, transparent) !important;
    }
    .dock, .taskbar, .topbar, .menu-bar, .menubar { box-shadow: 0 8px 32px color-mix(in srgb, var(--nv-accent) calc(var(--nv-glow) * 100%), transparent); }
    button:hover, [role="button"]:hover, .app:hover { border-color: var(--nv-accent) !important; }
    .active, [aria-current="page"], [aria-pressed="true"] { accent-color: var(--nv-accent); }
    .dock, .taskbar, .panel, .window, .start-menu, .launcher, .widget { transition-duration: calc(180ms * var(--nv-motion)); }
    body::before { content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0; opacity: var(--nv-noise); background-image: radial-gradient(var(--nv-accent) .5px, transparent .5px); background-size: 5px 5px; mix-blend-mode: screen; }
  `;
  (document.head || document.documentElement).appendChild(style);
  window.ChimeraNeurovisual = Object.freeze({
    axes: AXES, update, setIdentity,
    getState: () => ({ ...smoothed }),
    getIdentity: () => identity,
    reset: () => { state = { ...initial }; smoothed = { ...initial }; update({}); }
  });
  const pointer = event => {
    const rect = document.documentElement.getBoundingClientRect();
    update({
      x: clamp(event.clientX / Math.max(1, rect.width)),
      y: clamp(event.clientY / Math.max(1, rect.height)),
      perspective: clamp(0.35 + (event.clientX / Math.max(1, rect.width)) * 0.3)
    }, { alpha: 0.12 });
  };
  if (!matchMedia("(prefers-reduced-motion: reduce)").matches) window.addEventListener("pointermove", pointer, { passive: true });
  window.addEventListener("chimera-neurovisual-input", event => {
    const detail = event.detail || {};
    update(detail.state || detail, { alpha: detail.alpha, identity: detail.identity });
  });
  update({}, { identity });
})();
