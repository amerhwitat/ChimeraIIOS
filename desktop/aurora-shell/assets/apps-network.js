/* Network Applications panel: every network-facing surface found in the repos,
 * grouped into categories, searchable and launchable from icons on the desktop.
 */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el, row } = A;

  const CATEGORY_META = {
    all: { label: "All", glyph: "🌐" },
    connectivity: { label: "Connectivity", glyph: "🔌" },
    monitoring: { label: "Monitoring", glyph: "📈" },
    transfer: { label: "Transfer", glyph: "⇅" },
    remote: { label: "Remote access", glyph: "🖥" },
    security: { label: "Security", glyph: "🛡" },
    p2p: { label: "Peer-to-peer", glyph: "🕸" },
    cloud: { label: "Cloud fabric", glyph: "☁" },
    communication: { label: "Communication", glyph: "🎙" },
    emulation: { label: "Emulation & media", glyph: "🕹" },
    other: { label: "Other", glyph: "▤" }
  };

  const state = { entries: [], category: "all", query: "", loaded: false };

  const FALLBACK = [
    { id: "network-hub", name: "Network Hub", category: "connectivity", glyph: "🌐", description: "Network control surface from the Chimera II web UI." },
    { id: "network-monitor", name: "Network Monitor", category: "monitoring", glyph: "📈", description: "Interface and traffic monitor." },
    { id: "network-fabric", name: "Network Fabric", category: "cloud", glyph: "☁", description: "Cloud fabric client and route manager." },
    { id: "p2p", name: "P2P Services", category: "p2p", glyph: "🕸", description: "Peer-to-peer discovery and transfer." },
    { id: "voiceconnect", name: "VoiceConnect", category: "communication", glyph: "🎙", description: "Voice, video and messaging client." }
  ];

  async function ensureCatalog() {
    if (state.loaded) return state.entries;
    for (const url of ["data/network-apps.json", "../data/network-apps.json"]) {
      try {
        const response = await fetch(url);
        if (!response.ok) continue;
        const data = await response.json();
        state.entries = Array.isArray(data.apps) ? data.apps : [];
        state.loaded = true;
        return state.entries;
      } catch (err) { /* next */ }
    }
    state.entries = FALLBACK;
    state.loaded = true;
    return state.entries;
  }

  function categoriesOf(entries) {
    const seen = new Set(entries.map((entry) => entry.category || "other"));
    return ["all"].concat(Array.from(seen).sort());
  }

  function card(entry) {
    const button = el("button", "card");
    button.type = "button";
    const glyph = el("span", "glyph", entry.glyph || (CATEGORY_META[entry.category] || {}).glyph || "▤");
    glyph.style.setProperty("--tile-a", entry.tile ? entry.tile[0] : "#2f7cf6");
    glyph.style.setProperty("--tile-b", entry.tile ? entry.tile[1] : "#134a9e");
    const text = el("span");
    text.append(
      el("div", "name", entry.name),
      el("div", "meta", (CATEGORY_META[entry.category] || CATEGORY_META.other).label + (entry.path ? " · " + entry.path : ""))
    );
    button.append(glyph, text);
    button.addEventListener("click", () => details(entry));
    button.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      A.openApp("network", { panel: entry.category, title: entry.name });
    });
    return button;
  }

  function details(entry) {
    const content = [
      row("Application", entry.name),
      row("Category", (CATEGORY_META[entry.category] || CATEGORY_META.other).label),
      row("Source path", entry.path || "bundled panel"),
      row("Description", entry.description || "Network application discovered in the repository."),
      row("Entry point", entry.entry || entry.path || "panel"),
      row("Package", entry.repo || "ChimeraIIOS")
    ];
    if (entry.url) content.push(row("URL", entry.url));
    if (entry.requires) content.push(row("Requires", entry.requires));
    const open = el("button", "btn primary", "Open");
    open.addEventListener("click", () => {
      box.remove();
      A.toast(entry.name + " — launched from the bundled catalogue");
    });
    const copy = el("button", "btn", "Copy path");
    copy.addEventListener("click", () => {
      const value = entry.entry || entry.path || entry.name;
      if (navigator.clipboard) navigator.clipboard.writeText(value).then(() => A.toast("Copied: " + value));
      else A.toast(value);
    });
    const close = el("button", "btn ghost", "Close");
    const box = A.dialog(entry.name, content, [copy, open, close]);
    close.addEventListener("click", () => box.remove());
  }

  function render(body, ctx) {
    ensureCatalog().then((entries) => {
      const wrap = el("div", "na");
      const toolbar = el("div", "toolbar");
      const search = document.createElement("input");
      search.type = "search";
      search.placeholder = "Search network applications…";
      search.value = state.query;
      const select = document.createElement("select");
      categoriesOf(entries).forEach((category) => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = (CATEGORY_META[category] || { label: category }).label;
        select.appendChild(option);
      });
      select.value = state.category;
      const count = el("span", "badge", entries.length + " entries");
      toolbar.append(search, select, count);

      const grid = el("div", "grid");
      const status = el("div", "status");
      const paint = () => {
        const query = state.query.trim().toLowerCase();
        const rows = entries.filter((entry) =>
          (state.category === "all" || entry.category === state.category) &&
          (!query || [entry.name, entry.category, entry.description, entry.path].join(" ").toLowerCase().includes(query)));
        grid.replaceChildren();
        rows.forEach((entry) => grid.appendChild(card(entry)));
        if (!rows.length) grid.appendChild(el("div", "status", "No network applications match this filter."));
        status.textContent = rows.length + " of " + entries.length + " network applications · catalogue generated from the repository tree";
      };
      search.addEventListener("input", () => { state.query = search.value; paint(); });
      select.addEventListener("change", () => { state.category = select.value; paint(); });
      paint();

      wrap.append(toolbar, grid, status);
      body.replaceChildren(wrap);
    });
    if (ctx && ctx.opts && ctx.opts.panel) state.category = ctx.opts.panel;
  }

  A.registerApp({ id: "network", name: "Network Applications", glyph: "🌐", render });

  // Register the panel set and mirror every panel as a desktop icon.
  const PANELS = ["connectivity", "monitoring", "transfer", "remote", "security", "p2p", "cloud", "communication"];
  PANELS.forEach((id) => A.registerPanel({ id, name: (CATEGORY_META[id] || { label: id }).label, glyph: (CATEGORY_META[id] || {}).glyph || "▤", category: id }));

  document.addEventListener("aurora:ready", () => {
    const icons = A.desktopIcons();
    const wanted = PANELS.map((id, index) => ({
      id: "panel-" + id,
      name: "Network · " + (CATEGORY_META[id] || { label: id }).label,
      glyph: (CATEGORY_META[id] || {}).glyph || "▤",
      tile: ["#54b6ff", "#0b5aa8"],
      app: "network",
      panel: id,
      order: 40 + index
    }));
    let changed = false;
    wanted.forEach((icon) => {
      if (!icons.some((item) => item.id === icon.id)) { icons.push(icon); changed = true; }
    });
    if (changed) A.setDesktopIcons(icons);
  });
})();
