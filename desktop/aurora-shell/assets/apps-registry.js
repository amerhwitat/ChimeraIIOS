/* Aurora Registry Editor — never writes without the native Aegis/registry bridge. */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el, row } = A;
  const HIVE_FILES = {
    machine: ["file:///opt/aurora/repo/system/registry/machine.defaults.json", "file:///opt/aurora/repo/vendor/chimera-ii-os/source/system/registry/machine.defaults.json"],
    environment: ["file:///opt/aurora/repo/system/registry/environment.defaults.json", "file:///opt/aurora/repo/vendor/chimera-ii-os/source/system/registry/environment.defaults.json"],
    kernel: ["file:///opt/aurora/repo/system/registry/kernel.defaults.json", "file:///opt/aurora/repo/vendor/chimera-ii-os/source/system/registry/kernel.defaults.json"]
  };
  const state = { hive: "machine", generation: 0, entries: [], editable: false, query: "" };
  const bridge = () => window.chimeraRegistry || null;

  async function loadHive() {
    const api = bridge();
    if (api && typeof api.read === "function") {
      const result = await api.read(state.hive);
      state.generation = result.generation;
      state.entries = result.entries || [];
      state.editable = typeof api.set === "function" && typeof api.delete === "function";
      return;
    }
    let result = null;
    for (const source of HIVE_FILES[state.hive]) {
      try {
        const response = await fetch(source, { cache: "no-store" });
        if (response.ok) { result = await response.json(); break; }
      } catch (_) { /* try the vendored source snapshot */ }
    }
    if (!result) throw new Error("Registry defaults are not available in this image");
    state.generation = result.generation || 0;
    state.entries = result.entries || [];
    state.editable = false;
  }

  function parseValue(type, raw) {
    if (type === "bool") { if (raw === true || raw === "true") return true; if (raw === false || raw === "false") return false; throw new Error("Enter true or false"); }
    if (type === "u32" || type === "u64") {
      if (!/^(0|[1-9][0-9]*)$/.test(String(raw))) throw new Error("Enter a non-negative integer");
      const n = Number(raw);
      const max = type === "u32" ? 0xffffffff : Number.MAX_SAFE_INTEGER;
      if (!Number.isSafeInteger(n) || n > max) throw new Error("Integer is outside the safe editor range");
      return n;
    }
    if (type === "bytes") {
      const s = String(raw).replace(/\s/g, "");
      if (s.length % 2 || !/^[0-9a-f]*$/i.test(s)) throw new Error("Bytes must be even-length hexadecimal");
      return s.toLowerCase();
    }
    return String(raw);
  }

  function render(body) {
    const wrap = el("div", "content registry-editor");
    const title = el("h2", "", "Registry Editor");
    const note = el("p", "status", "Machine, Environment and Kernel hives · typed values · generation-safe updates");
    const toolbar = el("div", "row");
    const select = el("select");
    ["machine", "environment", "kernel"].forEach((name) => {
      const option = el("option", "", name[0].toUpperCase() + name.slice(1));
      option.value = name;
      select.appendChild(option);
    });
    select.value = state.hive;
    const search = el("input");
    search.type = "search";
    search.placeholder = "Filter registry keys…";
    search.value = state.query;
    const reload = el("button", "", "Reload");
    reload.type = "button";
    toolbar.append(select, search, reload);
    const status = el("div", "status", "Loading registry…");
    const list = el("div", "listing");
    const editor = el("div", "content");
    const add = el("button", "", "＋ Add entry");
    add.type = "button";
    add.disabled = !state.editable;
    wrap.append(title, note, toolbar, status, list, add, editor);
    body.appendChild(wrap);

    function setStatus(message, error) {
      status.textContent = message;
      status.setAttribute("aria-live", "polite");
      status.dataset.state = error ? "error" : "normal";
    }
    async function refresh() {
      list.replaceChildren();
      add.disabled = true;
      setStatus("Loading " + state.hive + " hive…");
      try {
        await loadHive();
        add.disabled = !state.editable;
        setStatus(state.editable
          ? "Connected to the protected registry service · generation " + state.generation
          : "Read-only preview · native registry IPC bridge is not installed");
        draw();
      } catch (error) {
        setStatus(error.message || String(error), true);
      }
    }
    function draw() {
      list.replaceChildren();
      const matches = state.entries.filter((item) =>
        item.path.toLowerCase().includes(state.query.toLowerCase()));
      const head = el("div", "row head");
      ["Key", "Type", "Value", "Actions"].forEach((v) => head.appendChild(el("span", "", v)));
      list.appendChild(head);
      matches.forEach((item) => {
        const line = el("div", "row");
        line.append(el("span", "", item.path), el("span", "", item.type),
          el("span", "", item.type === "bytes" ? String(item.value).slice(0, 48) : String(item.value)));
        const actions = el("span", "row");
        const edit = el("button", "", "Edit");
        edit.type = "button";
        edit.disabled = !state.editable;
        edit.addEventListener("click", () => editEntry(item));
        const remove = el("button", "", "Delete");
        remove.type = "button";
        remove.disabled = !state.editable;
        remove.addEventListener("click", () => deleteEntry(item));
        actions.append(edit, remove);
        line.appendChild(actions);
        list.appendChild(line);
      });
      if (!matches.length) list.appendChild(el("p", "status", "No matching registry entries."));
    }
    async function editEntry(item) {
      const raw = window.prompt("New value for " + item.path, String(item.value));
      if (raw === null) return;
      await saveEntry(item.path, item.type, raw);
    }
    async function saveEntry(path, type, raw) {
      try {
        const value = parseValue(type, raw);
        const result = await bridge().set({
          hive: state.hive, path, type, value, generation: state.generation
        });
        state.generation = result.generation;
        await refresh();
        setStatus("Saved " + path + " · generation " + state.generation);
      } catch (error) {
        setStatus(error.message || String(error), true);
        if (/generation conflict/i.test(error.message || "")) await refresh();
      }
    }
    async function deleteEntry(item) {
      if (!window.confirm("Delete registry entry " + item.path + "?")) return;
      try {
        const result = await bridge().delete({
          hive: state.hive, path: item.path, generation: state.generation
        });
        state.generation = result.generation;
        await refresh();
      } catch (error) {
        setStatus(error.message || String(error), true);
      }
    }
    add.addEventListener("click", async () => {
      const path = window.prompt("Registry key path (lowercase, e.g. environment.locale)");
      if (!path) return;
      const type = window.prompt("Type: string, bool, u32, u64 or bytes", "string");
      if (!type) return;
      const raw = window.prompt("Initial value", "");
      if (raw === null) return;
      await saveEntry(path, type, raw);
    });
    select.addEventListener("change", async () => {
      state.hive = select.value;
      await refresh();
    });
    search.addEventListener("input", () => {
      state.query = search.value;
      draw();
    });
    reload.addEventListener("click", refresh);
    refresh();
  }

  A.registerApp({
    id: "registry-editor",
    name: "Registry Editor",
    glyph: "🗝",
    render
  });
})();