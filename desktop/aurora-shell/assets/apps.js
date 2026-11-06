/* Core applications for the Aurora desktop shell. */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el, row } = A;

  const SYSTEM_INFO = {
    product: "Aurora Desktop Shell",
    version: "2.0.0",
    shell: "WebKit2GTK kiosk · X11",
    kernel: "Linux 6.12 (live image)",
    native: "Koronos microkernel sources ship in /opt/aurora/repo/kernel (not in the boot path)",
    profiles: "Jasper (Windows 12) · Gates (macOS) · Aurora (Linux 7.x) · Marine (Windows 10)"
  };

  // ------------------------------------------------------------------ Files
  A.registerApp({
    id: "files",
    name: "Files",
    glyph: "🗂",
    render(body) {
      const wrap = el("div", "files");
      const sidebar = el("div", "sidebar");
      const listing = el("div", "listing");
      const places = [
        { name: "Home", path: "/home/live", glyph: "🏠" },
        { name: "Desktop payload", path: "/opt/aurora/desktop", glyph: "🧩" },
        { name: "Artwork", path: "/opt/aurora/wallpapers", glyph: "🖼" },
        { name: "Source snapshot", path: "/opt/aurora/repo", glyph: "📦" },
        { name: "Reports", path: "/opt/aurora/reports", glyph: "📄" },
        { name: "System", path: "/usr/share/backgrounds", glyph: "🖥" }
      ];
      const entries = [
        { name: "desktop", type: "folder", size: "—", modified: "image" },
        { name: "wallpapers", type: "folder", size: "—", modified: "image" },
        { name: "repo", type: "folder", size: "—", modified: "image" },
        { name: "PROJECT.md", type: "file", size: "1.4 KB", modified: "build" },
        { name: "README.txt", type: "file", size: "0.6 KB", modified: "build" },
        { name: "build-report.json", type: "file", size: "12 KB", modified: "build" }
      ];
      places.forEach((place, index) => {
        const entry = el("div", "entry" + (index === 0 ? " active" : ""), place.glyph + "  " + place.name);
        entry.title = place.path;
        entry.addEventListener("click", () => {
          wrap.querySelectorAll(".entry").forEach((node) => node.classList.remove("active"));
          entry.classList.add("active");
        });
        sidebar.appendChild(entry);
      });
      const head = el("div", "row head");
      ["", "Name", "Size", "Modified"].forEach((text) => head.appendChild(el("span", "", text)));
      listing.appendChild(head);
      entries.forEach((item) => {
        const line = el("div", "row");
        line.append(el("span", "", item.type === "folder" ? "📁" : "📄"),
          el("span", "", item.name), el("span", "", item.size), el("span", "", item.modified));
        line.addEventListener("dblclick", () => A.toast("Opening " + item.name + " (image is read-only in this live session)"));
        listing.appendChild(line);
      });
      wrap.append(sidebar, listing);
      body.appendChild(wrap);
    }
  });

  // ------------------------------------------------------------------ Terminal
  A.registerApp({
    id: "terminal",
    name: "Terminal",
    glyph: "⌨",
    render(body) {
      const term = el("div", "term");
      const history = el("div");
      const line = el("div", "line");
      const prompt = el("span", "prompt", "live@aurora:~$ ");
      const input = document.createElement("input");
      input.type = "text";
      input.setAttribute("aria-label", "command");
      line.append(prompt, input);
      term.append(history, line);
      body.appendChild(term);
      setTimeout(() => input.focus(), 60);

      const print = (text) => {
        const out = el("div", "line", text);
        history.appendChild(out);
        term.scrollTop = term.scrollHeight;
      };
      print("Aurora shell — commands: help, uname, whoami, date, ls, cat PROJECT, profile, wallpaper, clear");
      input.addEventListener("keydown", (event) => {
        event.stopPropagation();
        if (event.key !== "Enter") return;
        const command = input.value.trim();
        input.value = "";
        print("live@aurora:~$ " + command);
        const [name, ...args] = command.split(/\s+/);
        switch (name) {
          case "": break;
          case "help":
            print("help uname whoami date ls cat profile wallpaper clear");
            break;
          case "uname":
            print("Linux aurora 6.12.107-amd64 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux (live image)");
            break;
          case "whoami": print("live (uid 1000, passwordless sudo)"); break;
          case "date": print(new Date().toString()); break;
          case "ls": print("desktop  wallpapers  repo  PROJECT.md  README.txt  build-report.json"); break;
          case "cat": print(args[0] === "PROJECT" ? "See /opt/aurora/PROJECT.md — upstream repo, branch, commit and build date." : "cat: " + (args[0] || "") + ": permission denied (live image)"); break;
          case "profile": print("active desktop profile: " + A.state.profile); break;
          case "wallpaper": print(A.state.wallpaper || "default"); break;
          case "clear": history.replaceChildren(); break;
          default: print(name + ": command not found — try 'help'");
        }
        term.scrollTop = term.scrollHeight;
      });
    }
  });

  // ------------------------------------------------------------------ Settings
  A.registerApp({
    id: "settings",
    name: "Settings",
    glyph: "⚙",
    render(body, ctx) {
      const wrap = el("div", "settings");
      const nav = el("div", "nav");
      const panel = el("div", "panel");
      const sections = ["appearance", "display", "system", "shortcuts", "about"];
      const labels = { appearance: "Appearance", display: "Display & icons", system: "System", shortcuts: "Keyboard shortcuts", about: "About" };

      const render = (section) => {
        panel.replaceChildren();
        panel.dataset.section = section;
        if (section === "appearance") {
          panel.appendChild(el("h3", "", "Desktop profile"));
          Object.entries(A.profiles).forEach(([id, profile]) => {
            const card = el("button", "profile-card");
            card.type = "button";
            card.setAttribute("aria-pressed", String(A.state.profile === id));
            const glyph = el("span", "glyph", profile.glyph || "◉");
            const text = el("span");
            text.append(el("div", "", profile.name), el("div", "p", profile.skin));
            card.append(glyph, text);
            card.addEventListener("click", () => {
              A.applyProfile(id);
              A.toast("Desktop profile: " + profile.name + " (" + profile.skin + ")");
              render("appearance");
            });
            panel.appendChild(card);
          });
          panel.appendChild(el("h3", "", "Wallpaper"));
          const swatches = el("div", "swatches");
          A.state.wallpaperList.forEach((item) => {
            const swatch = el("button", "swatch");
            swatch.type = "button";
            swatch.title = item.name;
            swatch.style.backgroundImage = 'url("' + item.url + '")';
            swatch.setAttribute("aria-pressed", String(A.state.wallpaper === item.url));
            swatch.addEventListener("click", () => { A.applyWallpaper(item.url); A.toast("Wallpaper: " + item.name); render("appearance"); });
            swatches.appendChild(swatch);
          });
          panel.appendChild(swatches);
        } else if (section === "display") {
          panel.appendChild(el("h3", "", "Icon size"));
          const seg = el("div", "seg");
          [44, 56, 68, 80].forEach((size) => {
            const button = el("button", "btn small", size + " px");
            button.type = "button";
            button.setAttribute("aria-pressed", String(A.state.iconSize === size));
            button.addEventListener("click", () => { A.applyIconSize(size); render("display"); });
            seg.appendChild(button);
          });
          panel.appendChild(seg);
          const info = el("div");
          [["Resolution", window.screen.width + " × " + window.screen.height],
            ["Device pixel ratio", window.devicePixelRatio || 1],
            ["Renderer", "WebKit2GTK (software rendering)"]].forEach(([k, v]) => info.appendChild(row(k, v)));
          panel.appendChild(el("h3", "", "Display"));
          panel.appendChild(info);
        } else if (section === "system") {
          panel.appendChild(el("h3", "", "System"));
          Object.entries(SYSTEM_INFO).forEach(([k, v]) => panel.appendChild(row(k, v)));
          const buttons = el("div");
          buttons.style.display = "flex";
          buttons.style.gap = "8px";
          buttons.style.marginTop = "12px";
          const reset = el("button", "btn", "Reset desktop layout");
          reset.addEventListener("click", () => { A.save("icons", null); location.reload(); });
          const reboot = el("button", "btn danger", "Restart session");
          reboot.addEventListener("click", () => location.reload());
          buttons.append(reset, reboot);
          panel.appendChild(buttons);
        } else if (section === "shortcuts") {
          panel.appendChild(el("h3", "", "Shortcuts for " + A.profiles[A.state.profile].name));
          const family = A.profiles[A.state.profile].family;
          (A.shortcuts[family] || A.shortcuts.linux).forEach(([keys, action]) => panel.appendChild(row(keys, action)));
        } else {
          panel.appendChild(el("h3", "", "Aurora Desktop Shell"));
          panel.appendChild(row("Version", SYSTEM_INFO.version));
          panel.appendChild(row("Licence", "GPL-3.0 (see /opt/aurora/repo/LICENSE)"));
          panel.appendChild(row("Upstream", "github.com/amerhwitat/ChimeraIIOS"));
          panel.appendChild(row("Artwork", A.state.wallpaperList.length + " bundled backgrounds"));
        }
      };

      sections.forEach((section, index) => {
        const button = el("button", "", labels[section]);
        button.type = "button";
        if (index === 0) button.classList.add("active");
        button.addEventListener("click", () => {
          nav.querySelectorAll("button").forEach((node) => node.classList.remove("active"));
          button.classList.add("active");
          render(section);
        });
        nav.appendChild(button);
      });
      wrap.append(nav, panel);
      body.appendChild(wrap);

      const start = (ctx && ctx.opts && ctx.opts.section) || "appearance";
      render(start);
    }
  });

  // ------------------------------------------------------------------ System panel
  A.registerApp({
    id: "system",
    name: "System Panel",
    glyph: "📊",
    render(body) {
      const wrap = el("div", "settings");
      const nav = el("div", "nav");
      const panel = el("div", "panel");
      panel.appendChild(el("h3", "", "Runtime status"));
      panel.appendChild(row("Kernel", "Linux 6.12.107-amd64 (live)"));
      panel.appendChild(row("Native microkernel", "Koronos sources present, not in boot path"));
      panel.appendChild(row("Session", "aurora-session.service (systemd)"));
      panel.appendChild(row("Display server", "X11 · software rendering"));
      panel.appendChild(row("Profile", A.profiles[A.state.profile].name));
      panel.appendChild(row("Bundled apps", A.state.apps.length));
      panel.appendChild(row("Network panels", A.state.panels.length));
      nav.appendChild(el("div", "entry active", "Overview"));
      wrap.append(nav, panel);
      body.appendChild(wrap);
    }
  });

  // ------------------------------------------------------------------ Media deck
  A.registerApp({
    id: "media",
    name: "Media Deck",
    glyph: "🎬",
    render(body) {
      const wrap = el("div", "content");
      wrap.appendChild(el("h3", "", "Media Deck"));
      wrap.appendChild(el("p", "", "Playback surface for the project's Init.mp4 boot film and bundled artwork. The live image stages Init.mp4 as the authoritative media source."));
      const bar = el("div");
      bar.style.display = "flex";
      bar.style.gap = "8px";
      bar.style.marginTop = "12px";
      const play = el("button", "btn primary", "▶ Play Intro film");
      play.addEventListener("click", () => A.toast("Init.mp4 is staged read-only in the image media directory"));
      const gallery = el("button", "btn", "Open wallpaper folder");
      gallery.addEventListener("click", () => A.openApp("files"));
      bar.append(play, gallery);
      wrap.appendChild(bar);
      body.appendChild(wrap);
    }
  });

  // ------------------------------------------------------------------ App center
  A.registerApp({
    id: "store",
    name: "App Center",
    glyph: "🛍",
    render(body) {
      const grid = el("div", "na");
      const toolbar = el("div", "toolbar");
      toolbar.appendChild(el("strong", "", "Installed applications and panels"));
      const area = el("div", "grid");
      A.state.apps.filter((app) => app.id !== "store").forEach((app) => {
        const card = el("button", "card");
        card.type = "button";
        const glyph = el("span", "glyph", app.glyph || "▣");
        const text = el("span");
        text.append(el("div", "name", app.name), el("div", "meta", "local · preinstalled"));
        card.append(glyph, text);
        card.addEventListener("click", () => A.openApp(app.id, { forceNew: true }));
        area.appendChild(card);
      });
      A.state.panels.forEach((panel) => {
        const card = el("button", "card");
        card.type = "button";
        const glyph = el("span", "glyph", panel.glyph || "▤");
        const text = el("span");
        text.append(el("div", "name", panel.name), el("div", "meta", "panel · network"));
        card.append(glyph, text);
        card.addEventListener("click", () => A.openApp("network", { panel: panel.id, title: panel.name }));
        area.appendChild(card);
      });
      grid.append(toolbar, area, el("div", "status", "Everything listed is bundled with the image; no store downloads are required."));
      body.appendChild(grid);
    }
  });

  // ------------------------------------------------------------------ About / docs
  A.registerApp({
    id: "about",
    name: "About",
    glyph: "ℹ",
    render(body) {
      const wrap = el("div", "content");
      wrap.appendChild(el("h3", "", "Aurora Desktop · Chimera II OS / OctavianOS"));
      Object.entries(SYSTEM_INFO).forEach(([k, v]) => wrap.appendChild(row(k, v)));
      wrap.appendChild(row("Scope", "Linux live image with the project's userland; native Koronos boot remains gated"));
      body.appendChild(wrap);
    }
  });

  A.registerApp({
    id: "docs",
    name: "Documentation",
    glyph: "📘",
    render(body) {
      const wrap = el("div", "content");
      wrap.appendChild(el("h3", "", "Documentation"));
      ["README.txt", "PROJECT.md", "live-image/README.md", "userspace/README.md", "kernel/README.md"].forEach((name) => {
        wrap.appendChild(row(name, "/opt/aurora/repo/" + name));
      });
      wrap.appendChild(el("p", "", "The verbatim source snapshot ships with the image, so documentation stays readable offline."));
      body.appendChild(wrap);
    }
  });
})();
