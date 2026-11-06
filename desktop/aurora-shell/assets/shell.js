/* Aurora Desktop Shell — window manager, icon grid, context menus, shortcuts.
 * No framework, no network access, persists to localStorage only.
 */
(function () {
  "use strict";

  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
  const el = (tag, cls, text) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  };

  const PROFILES = {
    jasper: { name: "Jasper", skin: "Windows 12", glyph: "⊞", family: "windows" },
    gates: { name: "Gates", skin: "macOS", glyph: "", family: "mac" },
    aurora: { name: "Aurora", skin: "Linux 7.x", glyph: "◉", family: "linux" },
    marine: { name: "Marine", skin: "Windows 10", glyph: "≋", family: "windows" }
  };

  const SHORTCUTS = {
    windows: [
      ["Ctrl+Alt+T", "Terminal"], ["Super", "Start menu"], ["Super+E", "Files"],
      ["Super+I", "Settings"], ["Super+D", "Show desktop"], ["Super+Tab", "Window overview"],
      ["Alt+Tab", "Switch window"], ["Alt+F4", "Close window"], ["F2", "Rename icon"],
      ["Delete", "Remove icon"], ["Win+←/→", "Snap window"], ["F5", "Refresh"]
    ],
    mac: [
      ["Ctrl+Alt+T", "Terminal"], ["Cmd+Space", "Spotlight"], ["Cmd+Q", "Close window"],
      ["Cmd+W", "Close window"], ["Cmd+Tab", "Switch window"], ["Ctrl+↑", "Mission control"],
      ["F2", "Rename icon"], ["Cmd+Delete", "Remove icon"], ["F5", "Refresh"]
    ],
    linux: [
      ["Ctrl+Alt+T", "Terminal"], ["Super", "Activities"], ["Super+E", "Files"],
      ["Super+I", "Settings"], ["Super+D", "Show desktop"], ["Alt+Tab", "Switch window"],
      ["Alt+F4", "Close window"], ["F2", "Rename icon"], ["Super+←/→", "Tile window"],
      ["F5", "Refresh"]
    ]
  };

  const state = {
    profile: "aurora",
    wallpaper: "",
    iconSize: 56,
    selected: null,
    windows: [],
    zIndex: 100,
    apps: [],
    panels: [],
    wallpaperList: [],
    windowsSeq: 0
  };

  // ------------------------------------------------------------------ storage
  function load(key, fallback) {
    try {
      const raw = localStorage.getItem("aurora." + key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (err) {
      return fallback;
    }
  }
  function save(key, value) {
    try { localStorage.setItem("aurora." + key, JSON.stringify(value)); } catch (err) { /* private mode */ }
  }

  const DEFAULT_DESKTOP = [
    { id: "files", name: "Files", glyph: "🗂", tile: ["#4ea3ff", "#1558b0"], app: "files" },
    { id: "terminal", name: "Terminal", glyph: "⌨", tile: ["#3a3f4b", "#12151c"], app: "terminal" },
    { id: "voiceconnect", name: "VoiceConnect", glyph: "🎙", tile: ["#31d17c", "#0b7a45"], app: "voiceconnect" },
    { id: "network", name: "Network Applications", glyph: "🌐", tile: ["#54b6ff", "#0b5aa8"], app: "network" },
    { id: "settings", name: "Settings", glyph: "⚙", tile: ["#8b93a5", "#3b4250"], app: "settings" },
    { id: "system", name: "System Panel", glyph: "📊", tile: ["#ff9f43", "#b45c00"], app: "system" },
    { id: "media", name: "Media Deck", glyph: "🎬", tile: ["#ff6b8b", "#8c1030"], app: "media" },
    { id: "store", name: "App Center", glyph: "🛍", tile: ["#a06bff", "#4d1ba3"], app: "store" },
    { id: "about", name: "About", glyph: "ℹ", tile: ["#5bc0de", "#12627d"], app: "about" },
    { id: "docs", name: "Documentation", glyph: "📘", tile: ["#6c8cff", "#22318f"], app: "docs" }
  ];

  const ICON_SYMBOLS = Object.freeze({
    files: "file-manager",
    terminal: "terminal",
    voiceconnect: "voiceconnect",
    network: "network",
    settings: "settings",
    system: "system-monitor",
    media: "aurora-media-player",
    store: "store",
    about: "about",
    docs: "docs"
  });

  function appGlyphNode(glyph, symbolId) {
    const node = el("span", "glyph", glyph || "▣");
    if (!symbolId) return node;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.classList.add("app-symbol");
    svg.setAttribute("viewBox", "0 0 64 64");
    svg.setAttribute("aria-hidden", "true");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", "../app-icons/catalog.svg#app-" + symbolId);
    svg.appendChild(use);
    node.replaceChildren(svg);
    return node;
  }

  // ------------------------------------------------------------------ helpers
  function toast(message, ms) {
    const node = $("#toast");
    node.textContent = message;
    node.classList.add("show");
    clearTimeout(node._t);
    node._t = setTimeout(() => node.classList.remove("show"), ms || 2600);
  }

  function applyProfile(name, persist) {
    if (!PROFILES[name]) name = "aurora";
    state.profile = name;
    document.documentElement.dataset.profile = name;
    if (persist !== false) save("profile", name);
    const brand = $("#mbBrand");
    if (brand) brand.textContent = PROFILES[name].name;
    const glyph = $("#mbGlyph");
    if (glyph) glyph.textContent = PROFILES[name].glyph || "◉";
    renderDock();
    renderTaskbar();
    document.dispatchEvent(new CustomEvent("aurora:profile", { detail: name }));
  }

  function applyWallpaper(url, persist) {
    state.wallpaper = url;
    const wp = $("#wallpaper");
    if (wp) wp.style.backgroundImage = url ? 'url("' + url + '")' : "none";
    if (persist !== false) save("wallpaper", url);
  }

  function applyIconSize(size, persist) {
    state.iconSize = size;
    document.documentElement.style.setProperty("--icon-size", size + "px");
    if (persist !== false) save("iconSize", size);
  }

  async function loadWallpapers() {
    const candidates = ["../../wallpapers/index.json", "../wallpapers/index.json", "wallpapers/index.json"];
    for (const url of candidates) {
      try {
        const response = await fetch(url);
        if (!response.ok) continue;
        const list = await response.json();
        const base = url.replace(/index\.json$/, "");
        state.wallpaperList = list.map((item) => ({
          name: item.name || "Artwork",
          url: base + (item.file || item.url || "")
        }));
        return;
      } catch (err) { /* try next */ }
    }
    state.wallpaperList = [];
  }

  // ------------------------------------------------------------------ icons
  function desktopIcons() {
    return load("icons", DEFAULT_DESKTOP);
  }
  function setDesktopIcons(list) {
    save("icons", list);
    renderIcons();
  }

  function renderIcons() {
    const host = $("#desktopIcons");
    if (!host) return;
    host.replaceChildren();
    for (const icon of desktopIcons()) {
      host.appendChild(iconNode(icon));
    }
  }

  function iconNode(icon) {
    const node = el("div", "icon");
    node.dataset.iconId = icon.id;
    node.tabIndex = 0;
    const glyph = appGlyphNode(icon.glyph, ICON_SYMBOLS[icon.id]);
    glyph.style.setProperty("--tile-a", (icon.tile && icon.tile[0]) || "#2f7cf6");
    glyph.style.setProperty("--tile-b", (icon.tile && icon.tile[1]) || "#134a9e");
    const label = el("div", "label", icon.name);
    node.append(glyph, label);

    node.addEventListener("click", (event) => {
      event.stopPropagation();
      const wasSelected = state.selected === icon.id;
      select(icon.id);
      if (wasSelected) startRename(node, icon);
    });
    node.addEventListener("dblclick", (event) => {
      event.stopPropagation();
      openApp(icon.app, { title: icon.name });
    });
    node.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      event.stopPropagation();
      select(icon.id);
      showContextMenu(event.clientX, event.clientY, iconMenu(icon));
    });
    node.addEventListener("keydown", (event) => {
      if (event.key === "Enter") openApp(icon.app, { title: icon.name });
      if (event.key === "F2") startRename(node, icon);
    });
    return node;
  }

  function select(id) {
    state.selected = id;
    $$("#desktopIcons .icon").forEach((node) => node.classList.toggle("selected", node.dataset.iconId === id));
  }

  function startRename(node, icon) {
    const label = node.querySelector(".label");
    if (!label || label.querySelector("input")) return;
    const original = icon.name;
    const input = document.createElement("input");
    input.type = "text";
    input.value = original;
    input.maxLength = 48;
    label.textContent = "";
    label.appendChild(input);
    input.focus();
    input.select();

    const commit = (keep) => {
      const value = (input.value || "").trim();
      label.textContent = keep && value ? value : original;
      if (keep && value && value !== original) {
        const list = desktopIcons().map((item) => item.id === icon.id ? Object.assign({}, item, { name: value }) : item);
        setDesktopIcons(list);
        toast("Renamed to “" + value + "”");
      }
    };
    input.addEventListener("blur", () => commit(true));
    input.addEventListener("keydown", (event) => {
      event.stopPropagation();
      if (event.key === "Enter") { event.preventDefault(); commit(true); }
      if (event.key === "Escape") { event.preventDefault(); commit(false); }
    });
  }

  // ------------------------------------------------------------------ menus
  function showContextMenu(x, y, items) {
    const menu = $("#ctxMenu");
    if (!menu) return;
    menu.replaceChildren();
    for (const item of items) {
      if (item === "-") { menu.appendChild(el("div", "sep")); continue; }
      const button = el("button", "item" + (item.danger ? " danger" : ""));
      button.type = "button";
      button.append(el("span", "ic", item.icon || " "), el("span", "", item.label));
      if (item.hint) button.append(el("span", "hint", item.hint));
      button.addEventListener("click", () => {
        hideContextMenu();
        if (typeof item.run === "function") item.run();
      });
      menu.appendChild(button);
    }
    menu.classList.add("open");
    const rect = menu.getBoundingClientRect();
    menu.style.left = Math.min(x, window.innerWidth - rect.width - 8) + "px";
    menu.style.top = Math.min(y, window.innerHeight - rect.height - 8) + "px";
  }
  function hideContextMenu() {
    const menu = $("#ctxMenu");
    if (menu) menu.classList.remove("open");
  }

  function desktopMenu() {
    return [
      { label: "New Folder", icon: "📁", run: () => createFolder() },
      { label: "Open Terminal", icon: "⌨", hint: "Ctrl+Alt+T", run: () => openApp("terminal") },
      "-",
      { label: "Change Background…", icon: "🖼", run: () => openApp("settings", { section: "appearance" }) },
      { label: "Display Settings…", icon: "🖥", run: () => openApp("settings", { section: "display" }) },
      { label: "Sort Icons", icon: "⇅", run: () => { setDesktopIcons(desktopIcons().slice().sort((a, b) => a.name.localeCompare(b.name))); toast("Icons sorted"); } },
      "-",
      { label: "Show Shortcuts", icon: "⌘", run: () => shortcutsDialog() },
      { label: "Desktop Properties", icon: "⚙", hint: "Alt+Enter", run: () => desktopProperties() }
    ];
  }

  function iconMenu(icon) {
    return [
      { label: "Open", icon: "↗", hint: "Enter", run: () => openApp(icon.app, { title: icon.name }) },
      { label: "Open in New Window", icon: "❐", run: () => openApp(icon.app, { title: icon.name, forceNew: true }) },
      "-",
      { label: "Rename", icon: "✎", hint: "F2", run: () => {
          const node = $("#desktopIcons .icon[data-icon-id='" + icon.id + "']");
          if (node) startRename(node, icon);
        } },
      { label: "Properties", icon: "ⓘ", hint: "Alt+Enter", run: () => iconProperties(icon) },
      "-",
      { label: "Remove from Desktop", icon: "🗑", danger: true, hint: "Del", run: () => {
          setDesktopIcons(desktopIcons().filter((item) => item.id !== icon.id));
          toast("Removed from desktop");
        } }
    ];
  }

  function createFolder() {
    const list = desktopIcons();
    let n = 1;
    while (list.some((item) => item.name === "New Folder" + (n > 1 ? " " + n : ""))) n++;
    const name = "New Folder" + (n > 1 ? " " + n : "");
    const folder = { id: "folder-" + Date.now(), name: name, glyph: "📁", tile: ["#ffca6b", "#b07b00"], app: "files", folder: true };
    setDesktopIcons(list.concat([folder]));
    const node = $("#desktopIcons .icon[data-icon-id='" + folder.id + "']");
    if (node) { select(folder.id); startRename(node, folder); }
  }

  // ------------------------------------------------------------------ dialogs
  function dialog(title, contentNodes, footerNodes, opts) {
    const layer = $("#dialogLayer");
    const box = el("div", "dialog");
    const header = el("header");
    const close = el("button", "btn ghost small", "✕");
    close.addEventListener("click", () => box.remove());
    header.append(el("span", "", title), el("span", "spacer"), close);
    const content = el("div", "content");
    (contentNodes || []).forEach((node) => content.appendChild(node));
    box.append(header, content);
    if (footerNodes && footerNodes.length) {
      const footer = el("footer");
      footerNodes.forEach((node) => footer.appendChild(node));
      box.append(footer);
    }
    box.style.left = "50%";
    box.style.top = (opts && opts.top) || "18%";
    box.style.transform = "translateX(-50%)";
    layer.appendChild(box);
    return box;
  }

  function row(key, value) {
    const line = el("div", "row");
    line.append(el("span", "k", key), el("span", "v", String(value)));
    return line;
  }

  function desktopProperties() {
    const icons = desktopIcons();
    const content = [
      row("Desktop profile", PROFILES[state.profile].name + " (" + PROFILES[state.profile].skin + ")"),
      row("Wallpaper", state.wallpaper ? state.wallpaper.split("/").pop() : "default"),
      row("Icon size", state.iconSize + " px"),
      row("Desktop items", icons.length),
      row("Screen", window.screen.width + " × " + window.screen.height + " @ " + (window.devicePixelRatio || 1) + "x"),
      row("Engine", "Aurora Shell 2.0 (WebKit2GTK kiosk)"),
      row("User agent", navigator.userAgent)
    ];
    const ok = el("button", "btn primary", "Close");
    const box = dialog("Desktop Properties", content, [ok]);
    ok.addEventListener("click", () => box.remove());
  }

  function iconProperties(icon) {
    const content = [
      row("Name", icon.name),
      row("Type", icon.folder ? "Folder" : "Application shortcut"),
      row("Target", icon.app),
      row("Identifier", icon.id),
      row("Icon glyph", icon.glyph),
      row("Location", "/opt/aurora/desktop/aurora-shell"),
      row("Permissions", "read-only image · writable overlay")
    ];
    const rename = el("button", "btn", "Rename…");
    rename.addEventListener("click", () => {
      box.remove();
      const node = $("#desktopIcons .icon[data-icon-id='" + icon.id + "']");
      if (node) startRename(node, icon);
    });
    const ok = el("button", "btn primary", "Close");
    const box = dialog("“" + icon.name + "” Properties", content, [rename, ok]);
    ok.addEventListener("click", () => box.remove());
  }

  function shortcutsDialog() {
    const family = PROFILES[state.profile].family;
    const list = SHORTCUTS[family] || SHORTCUTS.linux;
    const content = list.map(([keys, action]) => row(keys, action));
    content.push(row("All profiles", "Ctrl+Alt+T terminal · F2 rename · F5 refresh · Alt+F4 close"));
    const ok = el("button", "btn primary", "Close");
    const box = dialog("Keyboard shortcuts — " + PROFILES[state.profile].name, content, [ok]);
    ok.addEventListener("click", () => box.remove());
  }

  // ------------------------------------------------------------------ windows
  function nextRect(offset) {
    const base = 120 + (offset || 0) * 28;
    return { x: Math.min(base, window.innerWidth - 620), y: Math.min(base, window.innerHeight - 420), w: 760, h: 520 };
  }

  function openWindow(opts) {
    if (!opts.forceNew) {
      const existing = state.windows.find((win) => win.app === opts.app);
      if (existing) { focusWindow(existing.id); return existing; }
    }
    const rect = opts.rect || nextRect(state.windowsSeq % 6);
    const id = "win-" + (++state.windowsSeq);
    const node = el("section", "window focused");
    node.dataset.winId = id;
    node.style.left = rect.x + "px";
    node.style.top = rect.y + "px";
    node.style.width = rect.w + "px";
    node.style.height = rect.h + "px";
    node.style.zIndex = ++state.zIndex;

    const bar = el("div", "titlebar");
    const lights = el("div", "lights");
    const closeBtn = el("button", "close", ""); closeBtn.title = "Close";
    const minBtn = el("button", "min", ""); minBtn.title = "Minimise";
    const maxBtn = el("button", "max", ""); maxBtn.title = "Maximise";
    lights.append(closeBtn, minBtn, maxBtn);
    const title = el("div", "title", opts.title || opts.app);
    const ctl = el("div", "winctl");
    const cMin = el("button", "", "—"); cMin.title = "Minimise";
    const cMax = el("button", "", "□"); cMax.title = "Maximise";
    const cClose = el("button", "close", "✕"); cClose.title = "Close";
    ctl.append(cMin, cMax, cClose);
    bar.append(lights, title, ctl);

    const body = el("div", "body");
    const grip = el("div", "resize");
    node.append(bar, body, grip);
    $("#windows").appendChild(node);

    const record = { id: id, app: opts.app, title: opts.title || opts.app, node: node, body: body, minimized: false, maximized: false, rect: rect };
    state.windows.push(record);

    const close = () => closeWindow(id);
    closeBtn.addEventListener("click", close);
    cClose.addEventListener("click", close);
    minBtn.addEventListener("click", () => minimizeWindow(id));
    cMin.addEventListener("click", () => minimizeWindow(id));
    maxBtn.addEventListener("click", () => toggleMaximize(id));
    cMax.addEventListener("click", () => toggleMaximize(id));

    node.addEventListener("mousedown", () => focusWindow(id), true);
    makeDraggable(node, bar, record);
    makeResizable(node, grip, record);
    bar.addEventListener("dblclick", () => toggleMaximize(id));

    node.addEventListener("contextmenu", (event) => {
      event.preventDefault();
      showContextMenu(event.clientX, event.clientY, [
        { label: "Minimise", icon: "—", run: () => minimizeWindow(id) },
        { label: "Maximise", icon: "□", run: () => toggleMaximize(id) },
        { label: "Properties", icon: "ⓘ", run: () => windowProperties(record) },
        "-",
        { label: "Close", icon: "✕", danger: true, run: close }
      ]);
    });

    const app = state.apps.find((a) => a.id === opts.app);
    if (app && typeof app.render === "function") {
      try {
        app.render(body, { win: record, opts: opts, shell: api });
      } catch (err) {
        body.appendChild(el("div", "content", "Application failed to render: " + err.message));
      }
    } else {
      body.appendChild(el("div", "content", (opts.title || opts.app) + " — no renderer registered."));
    }

    focusWindow(id);
    renderTaskbar();
    return record;
  }

  function windowProperties(record) {
    const content = [
      row("Title", record.title),
      row("Application", record.app),
      row("Position", Math.round(record.node.offsetLeft) + ", " + Math.round(record.node.offsetTop)),
      row("Size", Math.round(record.node.offsetWidth) + " × " + Math.round(record.node.offsetHeight)),
      row("State", record.minimized ? "minimised" : record.maximized ? "maximised" : "normal")
    ];
    const ok = el("button", "btn primary", "Close");
    const box = dialog("Window Properties", content, [ok]);
    ok.addEventListener("click", () => box.remove());
  }

  function focusWindow(id) {
    const record = state.windows.find((win) => win.id === id);
    if (!record) return;
    state.windows.forEach((win) => {
      const focused = win.id === id;
      win.node.classList.toggle("focused", focused);
      if (focused) win.node.style.zIndex = ++state.zIndex;
    });
    if (record.minimized) { record.minimized = false; record.node.classList.remove("minimized"); }
    renderTaskbar();
  }

  function closeWindow(id) {
    const index = state.windows.findIndex((win) => win.id === id);
    if (index < 0) return;
    state.windows[index].node.remove();
    state.windows.splice(index, 1);
    renderTaskbar();
    renderOverview();
  }

  function minimizeWindow(id) {
    const record = state.windows.find((win) => win.id === id);
    if (!record) return;
    record.minimized = true;
    record.node.classList.add("minimized");
    renderTaskbar();
  }

  function toggleMaximize(id) {
    const record = state.windows.find((win) => win.id === id);
    if (!record) return;
    record.maximized = !record.maximized;
    if (record.maximized) {
      record.prev = { left: record.node.style.left, top: record.node.style.top, width: record.node.style.width, height: record.node.style.height };
      const top = state.profile === "gates" || state.profile === "aurora" ? "var(--menubar-h)" : "0px";
      record.node.style.left = "0px";
      record.node.style.top = "calc(" + top + ")";
      record.node.style.width = "100%";
      record.node.style.height = "calc(100% - " + top + " - " + (state.profile === "jasper" || state.profile === "marine" ? "var(--taskbar-h)" : "0px") + ")";
      record.node.classList.add("maximized");
    } else {
      const prev = record.prev || {};
      record.node.style.left = prev.left || "120px";
      record.node.style.top = prev.top || "120px";
      record.node.style.width = prev.width || "760px";
      record.node.style.height = prev.height || "520px";
      record.node.classList.remove("maximized");
    }
  }

  function snap(id, side) {
    const record = state.windows.find((win) => win.id === id);
    if (!record) return;
    const menubar = state.profile === "gates" || state.profile === "aurora" ? 28 : 0;
    const taskbar = state.profile === "jasper" || state.profile === "marine" ? 58 : 0;
    record.node.style.top = menubar + "px";
    record.node.style.height = (window.innerHeight - menubar - taskbar) + "px";
    record.node.style.left = side === "right" ? "50%" : "0px";
    record.node.style.width = "50%";
  }

  function makeDraggable(node, handle, record) {
    let startX = 0, startY = 0, originX = 0, originY = 0, dragging = false;
    handle.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) return;
      if (record.maximized) return;
      dragging = true;
      startX = event.clientX; startY = event.clientY;
      originX = node.offsetLeft; originY = node.offsetTop;
      document.body.style.cursor = "grabbing";
      event.preventDefault();
    });
    window.addEventListener("mousemove", (event) => {
      if (!dragging) return;
      const x = originX + event.clientX - startX;
      const y = Math.max(0, originY + event.clientY - startY);
      node.style.left = Math.max(-node.offsetWidth + 80, Math.min(x, window.innerWidth - 80)) + "px";
      node.style.top = y + "px";
    });
    window.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      document.body.style.cursor = "";
    });
  }

  function makeResizable(node, grip, record) {
    let startX = 0, startY = 0, startW = 0, startH = 0, resizing = false;
    grip.addEventListener("mousedown", (event) => {
      resizing = true;
      startX = event.clientX; startY = event.clientY;
      startW = node.offsetWidth; startH = node.offsetHeight;
      event.preventDefault();
      event.stopPropagation();
    });
    window.addEventListener("mousemove", (event) => {
      if (!resizing) return;
      node.style.width = Math.max(320, startW + event.clientX - startX) + "px";
      node.style.height = Math.max(180, startH + event.clientY - startY) + "px";
    });
    window.addEventListener("mouseup", () => { resizing = false; });
  }

  // ------------------------------------------------------------------ chrome
  function renderTaskbar() {
    const tasks = $("#tbTasks");
    if (!tasks) return;
    const icons = desktopIcons();
    tasks.replaceChildren();
    for (const record of state.windows) {
      const icon = icons.find((item) => item.app === record.app);
      const button = el("button", "tb-task" + (record.minimized ? "" : " active"));
      button.type = "button";
      button.append(el("span", "", icon ? icon.glyph : "▣"), el("span", "", record.title));
      button.addEventListener("click", () => {
        if (record.minimized) { focusWindow(record.id); } else { minimizeWindow(record.id); }
      });
      tasks.appendChild(button);
    }
  }

  function renderDock() {
    const dock = $("#dock");
    if (!dock) return;
    dock.replaceChildren();
    const pinned = desktopIcons().slice(0, 8);
    for (const icon of pinned) {
      const button = el("button", "dock-btn" + (state.windows.some((win) => win.app === icon.app) ? " running" : ""), icon.glyph);
      button.type = "button";
      button.title = icon.name;
      button.addEventListener("click", () => openApp(icon.app, { title: icon.name }));
      button.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        showContextMenu(event.clientX, event.clientY, iconMenu(icon));
      });
      dock.appendChild(button);
    }
    dock.appendChild(el("div", "dock-sep"));
    const start = el("button", "dock-btn", "⊞");
    start.type = "button";
    start.title = "Launcher";
    start.addEventListener("click", toggleStart);
    dock.appendChild(start);
  }

  function renderLauncher() {
    const appsHost = $("#smApps");
    const panelsHost = $("#smPanels");
    if (!appsHost || !panelsHost) return;
    appsHost.replaceChildren();
    panelsHost.replaceChildren();
    const icons = desktopIcons();
    for (const icon of icons) {
      appsHost.appendChild(launcherButton(icon.glyph, icon.name, () => { hideStart(); openApp(icon.app, { title: icon.name }); }, ICON_SYMBOLS[icon.id]));
    }
    for (const panel of state.panels) {
      panelsHost.appendChild(launcherButton(panel.glyph || "▤", panel.name, () => {
        hideStart();
        openApp("network", { title: panel.name, panel: panel.id });
      }));
    }
  }

  function launcherButton(glyph, name, onClick, symbolId) {
    const button = el("button", "sm-app");
    button.type = "button";
    const icon = appGlyphNode(glyph, symbolId);
    button.append(icon, el("span", "", name));
    button.addEventListener("click", onClick);
    return button;
  }

  function toggleStart(force) {
    const menu = $("#startMenu");
    if (!menu) return;
    const open = force != null ? force : !menu.classList.contains("open");
    menu.classList.toggle("open", open);
    if (open) {
      renderLauncher();
      const search = $("#smSearch");
      if (search) { search.value = ""; setTimeout(() => search.focus(), 30); }
    }
  }
  function hideStart() { toggleStart(false); }

  function renderOverview() {
    const grid = $("#ovGrid");
    if (!grid) return;
    grid.replaceChildren();
    for (const record of state.windows) {
      const card = el("div", "ov-card");
      card.append(el("div", "t", record.title), el("div", "p", record.app + " · " + (record.minimized ? "minimised" : "open")));
      card.addEventListener("click", () => { toggleOverview(false); focusWindow(record.id); });
      grid.appendChild(card);
    }
    if (!state.windows.length) grid.appendChild(el("div", "p", "No open windows."));
  }

  function toggleOverview(force) {
    const overview = $("#overview");
    if (!overview) return;
    const open = force != null ? force : !overview.classList.contains("open");
    overview.classList.toggle("open", open);
    document.documentElement.dataset.overview = open ? "on" : "off";
    if (open) renderOverview();
  }

  // ------------------------------------------------------------------ apps
  function openApp(appId, opts) {
    const app = state.apps.find((item) => item.id === appId);
    if (!app) { toast("Unknown application: " + appId); return null; }
    return openWindow(Object.assign({ app: appId, title: app.name }, opts || {}));
  }

  // ------------------------------------------------------------------ shortcuts
  function shortcutHandler(event) {
    const key = event.key;
    const ctrl = event.ctrlKey || event.metaKey;
    const family = PROFILES[state.profile].family;

    if (event.ctrlKey && event.altKey && (key === "t" || key === "T")) {
      event.preventDefault(); openApp("terminal"); return;
    }
    if (event.metaKey && family === "mac" && key === " ") {
      event.preventDefault(); toggleStart(true); return;
    }
    if (event.metaKey && (key === "d" || key === "D") && family !== "mac") {
      event.preventDefault(); state.windows.forEach((win) => minimizeWindow(win.id)); return;
    }
    if (event.metaKey && (key === "e" || key === "E")) {
      event.preventDefault(); openApp("files"); return;
    }
    if (event.metaKey && (key === "i" || key === "I")) {
      event.preventDefault(); openApp("settings"); return;
    }
    if (event.metaKey && (key === "Tab" || key === "`")) {
      event.preventDefault(); cycleWindows(event.shiftKey ? -1 : 1); return;
    }
    if (event.altKey && key === "Tab") {
      event.preventDefault(); cycleWindows(event.shiftKey ? -1 : 1); return;
    }
    if ((family === "mac" ? event.metaKey : event.altKey) && (key === "q" || key === "Q") && family === "mac") {
      event.preventDefault(); const top = topWindow(); if (top) closeWindow(top.id); return;
    }
    if (event.altKey && key === "F4") {
      event.preventDefault(); const top = topWindow(); if (top) closeWindow(top.id); return;
    }
    if (family === "mac" && event.metaKey && (key === "w" || key === "W")) {
      event.preventDefault(); const top = topWindow(); if (top) closeWindow(top.id); return;
    }
    if (event.metaKey && (key === "ArrowLeft" || key === "ArrowRight")) {
      const top = topWindow();
      if (top) { event.preventDefault(); snap(top.id, key === "ArrowLeft" ? "left" : "right"); }
      return;
    }
    if (family === "mac" && event.ctrlKey && key === "ArrowUp") {
      event.preventDefault(); toggleOverview(); return;
    }
    if (event.metaKey && (key === "Tab" || key === "t") && family !== "mac") { /* handled above */ }
    if (event.key === "F2" && state.selected) {
      event.preventDefault();
      const icon = desktopIcons().find((item) => item.id === state.selected);
      const node = $("#desktopIcons .icon[data-icon-id='" + state.selected + "']");
      if (icon && node) startRename(node, icon);
      return;
    }
    if ((key === "Delete" || key === "Backspace") && state.selected && document.activeElement === document.body) {
      event.preventDefault();
      setDesktopIcons(desktopIcons().filter((item) => item.id !== state.selected));
      state.selected = null;
      toast("Removed from desktop");
      return;
    }
    if (key === "F5") { event.preventDefault(); location.reload(); return; }
    if (key === "Escape") { hideContextMenu(); hideStart(); toggleOverview(false); return; }
    if (key === "F1") { event.preventDefault(); shortcutsDialog(); return; }
    if (event.altKey && key === "Enter" && state.selected) {
      event.preventDefault();
      const icon = desktopIcons().find((item) => item.id === state.selected);
      if (icon) iconProperties(icon);
      return;
    }
    if (event.altKey && key === "Enter" && !state.selected) { event.preventDefault(); desktopProperties(); }
  }

  function topWindow() {
    const focused = state.windows.find((win) => win.node.classList.contains("focused"));
    return focused || state.windows[state.windows.length - 1];
  }

  function cycleWindows(direction) {
    if (state.windows.length < 2) return;
    const current = topWindow();
    const index = state.windows.indexOf(current);
    const next = state.windows[(index + direction + state.windows.length) % state.windows.length];
    if (next) focusWindow(next.id);
  }

  // ------------------------------------------------------------------ wiring
  function wire() {
    document.addEventListener("contextmenu", (event) => {
      if (event.target.closest(".window") || event.target.closest("#startMenu") || event.target.closest("#ctxMenu")) return;
      event.preventDefault();
      showContextMenu(event.clientX, event.clientY, desktopMenu());
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest("#ctxMenu")) hideContextMenu();
      if (!event.target.closest("#startMenu") && !event.target.closest("#tbStart") && !event.target.closest("#dock")) hideStart();
      if (event.target.closest("#desktop")) select(null);
    });
    document.addEventListener("keydown", shortcutHandler);

    const start = $("#tbStart");
    if (start) start.addEventListener("click", (event) => { event.stopPropagation(); toggleStart(); });
    const search = $("#tbSearch");
    if (search) search.addEventListener("click", (event) => { event.stopPropagation(); toggleStart(true); });
    const smSearch = $("#smSearch");
    if (smSearch) {
      smSearch.addEventListener("input", () => {
        const query = smSearch.value.trim().toLowerCase();
        $$("#startMenu .sm-app").forEach((node) => {
          node.style.display = node.textContent.toLowerCase().includes(query) ? "" : "none";
        });
      });
    }
    const quick = $("#mbQuick");
    if (quick) quick.addEventListener("click", () => openApp("settings", { section: "system" }));
    const net = $("#tbTrayNet");
    if (net) net.addEventListener("click", () => openApp("network"));
    const voice = $("#tbTrayVoice");
    if (voice) voice.addEventListener("click", () => openApp("voiceconnect"));
    const mbVoice = $("#mbVoice");
    if (mbVoice) mbVoice.addEventListener("click", () => openApp("voiceconnect"));
    const mbQuick = $("#mbQuick");
    if (mbQuick) mbQuick.addEventListener("click", () => openApp("settings"));

    $$("#mbMenus button").forEach((button) => {
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        const rect = button.getBoundingClientRect();
        const menu = button.dataset.menu;
        const items = menu === "app" ? desktopMenu()
          : menu === "window" ? state.windows.map((win) => ({ label: win.title, icon: "▣", run: () => focusWindow(win.id) }))
          : menu === "help" ? [{ label: "Keyboard shortcuts", icon: "⌘", run: shortcutsDialog }, { label: "About this image", icon: "ℹ", run: () => openApp("about") }]
          : desktopMenu();
        showContextMenu(rect.left, rect.bottom + 4, items.length ? items : [{ label: "No items", run: () => {} }]);
      });
    });
  }

  function startClock() {
    const tick = () => {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const clock = $("#mbClock");
      if (clock) clock.textContent = hh + ":" + mm;
      const tb = $("#tbClock");
      if (tb) tb.innerHTML = hh + ":" + mm + "<br><small>" + String(now.getMonth() + 1).padStart(2, "0") + "/" + String(now.getDate()).padStart(2, "0") + "/" + now.getFullYear() + "</small>";
    };
    tick();
    setInterval(tick, 15000);
  }

  // ------------------------------------------------------------------ public API
  const api = {
    state: state,
    profiles: PROFILES,
    shortcuts: SHORTCUTS,
    openApp: openApp,
    openWindow: openWindow,
    closeWindow: closeWindow,
    focusWindow: focusWindow,
    toast: toast,
    dialog: dialog,
    row: row,
    el: el,
    applyProfile: applyProfile,
    applyWallpaper: applyWallpaper,
    applyIconSize: applyIconSize,
    desktopIcons: desktopIcons,
    setDesktopIcons: setDesktopIcons,
    renderIcons: renderIcons,
    renderDock: renderDock,
    renderTaskbar: renderTaskbar,
    loadWallpapers: loadWallpapers,
    save: save,
    load: load,
    toggleStart: toggleStart,
    toggleOverview: toggleOverview
  };

  function registerApp(app) {
    state.apps = state.apps.filter((item) => item.id !== app.id).concat([app]);
  }
  function registerPanel(panel) {
    state.panels = state.panels.filter((item) => item.id !== panel.id).concat([panel]);
  }
  api.registerApp = registerApp;
  api.registerPanel = registerPanel;

  function boot() {
    const params = new URLSearchParams(location.search);
    const requested = params.get("profile") || load("profile", "aurora");
    applyProfile(requested, false);
    applyIconSize(load("iconSize", 56), false);
    applyWallpaper(load("wallpaper", ""), false);
    wire();
    startClock();
    renderIcons();
    renderDock();
    renderTaskbar();
    loadWallpapers().then(() => {
      if (!state.wallpaper && state.wallpaperList.length) applyWallpaper(state.wallpaperList[0].url, false);
      document.dispatchEvent(new CustomEvent("aurora:wallpapers", { detail: state.wallpaperList }));
    });
    // First-run hint, once per browser profile.
    if (!load("welcomed", false)) {
      save("welcomed", true);
      setTimeout(() => toast("Right-click the desktop for properties and settings", 4200), 900);
    }
    document.dispatchEvent(new CustomEvent("aurora:ready", { detail: api }));
  }

  window.Aurora = api;
  api.boot = boot;
})();
