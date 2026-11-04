(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const bridge = (name) => window[name] || null;
  const say = (id, message, bad = false) => {
    const node = $(id); if (!node) return;
    node.textContent = message; node.dataset.state = bad ? "error" : "normal";
  };
  const make = (tag, value, cls) => {
    const node = document.createElement(tag);
    if (value !== undefined) node.textContent = String(value);
    if (cls) node.className = cls;
    return node;
  };
  const reg = {hive:"machine",generation:0,entries:[]};
  const registryAvailable = !!bridge("chimeraRegistry");
  const networkAvailable = !!bridge("chimeraNetwork");
  const storageAvailable = !!bridge("chimeraStorage");
  ["systemRegistryAdd","systemRegistryReload"].forEach(id => { if ($(id)) $(id).disabled = !registryAvailable; });
  ["systemSmbDiscover","systemSmbBrowse","systemRealmStatus","systemRealmJoin","systemLdapSearch"].forEach(id => { if ($(id)) $(id).disabled = !networkAvailable; });
  ["systemIsoMount","systemOpticalDeviceMount","systemOpticalUnmount"].forEach(id => { if ($(id)) $(id).disabled = !storageAvailable; });
  const hiveSelect = $("systemHive");
  const search = $("systemRegistrySearch");
  const list = $("systemRegistryRows");

  function parseValue(type, raw) {
    if (type === "bool") {
      if (raw === true || raw === "true") return true;
      if (raw === false || raw === "false") return false;
      throw new Error("Use true or false");
    }
    if (type === "u32" || type === "u64") {
      if (!/^(0|[1-9][0-9]*)$/.test(String(raw))) throw new Error("Enter a non-negative integer");
      const n = Number(raw);
      const max = type === "u32" ? 0xffffffff : Number.MAX_SAFE_INTEGER;
      if (!Number.isSafeInteger(n) || n > max) throw new Error("Integer exceeds the safe editor range");
      return n;
    }
    if (type === "bytes") {
      const hex = String(raw).replace(/\s/g, "");
      if (hex.length % 2 || !/^[0-9a-f]*$/i.test(hex)) throw new Error("Bytes must be even-length hexadecimal");
      return hex.toLowerCase();
    }
    return String(raw);
  }

  async function loadRegistry() {
    const api = bridge("chimeraRegistry");
    if (!api || typeof api.read !== "function") {
      say("systemRegistryStatus", "Native registry service unavailable. This public/web preview is read-only.");
      return;
    }
    try {
      const result = await api.read(reg.hive);
      reg.generation = result.generation;
      reg.entries = result.entries || [];
      say("systemRegistryStatus", "Connected · " + reg.hive + " hive · generation " + reg.generation);
      drawRegistry();
    } catch (e) { say("systemRegistryStatus", e.message || String(e), true); }
  }

  function drawRegistry() {
    list.replaceChildren();
    const query = (search.value || "").toLowerCase();
    const rows = reg.entries.filter(x => x.path.toLowerCase().includes(query));
    rows.forEach(item => {
      const row = make("tr");
      row.append(make("td", item.path), make("td", item.type), make("td", item.type === "bytes" ? String(item.value).slice(0, 64) : item.value));
      const actions = make("td");
      const edit = make("button", "Edit", "system-action");
      edit.addEventListener("click", async () => {
        const raw = window.prompt("New value for " + item.path, String(item.value));
        if (raw !== null) await writeEntry(item.path, item.type, raw);
      });
      const del = make("button", "Delete", "system-action danger");
      del.addEventListener("click", async () => {
        if (!window.confirm("Delete " + item.path + "?")) return;
        try {
          const result = await bridge("chimeraRegistry").delete({hive:reg.hive,path:item.path,generation:reg.generation});
          reg.generation = result.generation; await loadRegistry();
        } catch (e) { say("systemRegistryStatus", e.message || String(e), true); }
      });
      actions.append(edit, del); row.append(actions); list.append(row);
    });
    if (!rows.length) {
      const row = make("tr"); const cell = make("td", "No matching entries.");
      cell.colSpan = 4; row.append(cell); list.append(row);
    }
  }

  async function writeEntry(path, type, raw) {
    try {
      const value = parseValue(type, raw);
      const result = await bridge("chimeraRegistry").set({
        hive:reg.hive,path,type,value,generation:reg.generation
      });
      reg.generation = result.generation;
      await loadRegistry();
      say("systemRegistryStatus", "Saved " + path + " · generation " + reg.generation);
    } catch (e) {
      say("systemRegistryStatus", e.message || String(e), true);
      if (/generation conflict/i.test(e.message || "")) await loadRegistry();
    }
  }

  if (hiveSelect) hiveSelect.addEventListener("change", () => { reg.hive = hiveSelect.value; loadRegistry(); });
  if (search) search.addEventListener("input", drawRegistry);
  $("systemRegistryReload")?.addEventListener("click", loadRegistry);
  $("systemRegistryAdd")?.addEventListener("click", async () => {
    const path = $("systemRegistryPath").value.trim();
    const type = $("systemRegistryType").value;
    const raw = $("systemRegistryValue").value;
    if (!path) { say("systemRegistryStatus", "Enter a registry path.", true); return; }
    await writeEntry(path, type, raw);
  });

  const network = bridge("chimeraNetwork");
  $("systemSmbDiscover")?.addEventListener("click", async () => {
    const out = $("systemSmbResults"); out.replaceChildren();
    if (!network || !network.discoverSmb) { say("systemSmbStatus", "Native network bridge unavailable.", true); return; }
    say("systemSmbStatus", "Discovering Windows hosts on the local link…");
    try {
      const result = await network.discoverSmb();
      for (const server of result.servers || []) {
        const host = server.host || server.address;
        const row = make("button", (server.name || host) + " · " + host, "system-server");
        row.addEventListener("click", () => { $("systemSmbHost").value = host; $("systemSmbBrowse").click(); });
        out.append(row);
      }
      say("systemSmbStatus", (result.servers || []).length + " candidate host(s) found; select one to enumerate SMB shares.");
    } catch (e) { say("systemSmbStatus", e.message || String(e), true); }
  });
  $("systemSmbBrowse")?.addEventListener("click", async () => {
    const out = $("systemSmbResults"); out.replaceChildren();
    if (!network || !network.browseSmb) { say("systemSmbStatus", "Native network bridge unavailable.", true); return; }
    try {
      const result = await network.browseSmb($("systemSmbHost").value.trim());
      for (const share of result.shares || []) out.append(make("p", share.name + " — " + (share.comment || "")));
      say("systemSmbStatus", result.authenticated ? "Kerberos-authenticated SMB session." : (result.error || "SMB authentication failed."), !result.authenticated);
    } catch (e) { say("systemSmbStatus", e.message || String(e), true); }
  });

  $("systemRealmStatus")?.addEventListener("click", async () => {
    if (!network || !network.realmStatus) { say("systemRealmStatusText", "Native directory bridge unavailable.", true); return; }
    try { const result = await network.realmStatus(); say("systemRealmStatusText", result.stdout || result.stderr || "No joined realm reported."); }
    catch (e) { say("systemRealmStatusText", e.message || String(e), true); }
  });
  $("systemRealmJoin")?.addEventListener("click", async () => {
    if (!network || !network.joinDomain) { say("systemRealmStatusText", "Native directory bridge unavailable.", true); return; }
    const domain = $("systemRealmDomain").value.trim(), user = $("systemRealmUser").value.trim();
    if (!domain || !window.confirm("Join Active Directory domain " + domain + " using the current Kerberos ticket?")) return;
    try {
      const result = await network.joinDomain(domain, user);
      say("systemRealmStatusText", result.stdout || result.stderr || "Domain join command completed.");
    } catch (e) { say("systemRealmStatusText", e.message || String(e), true); }
  });
  $("systemLdapSearch")?.addEventListener("click", async () => {
    if (!network || !network.ldapSearch) { say("systemLdapStatus", "Native directory bridge unavailable.", true); return; }
    try {
      const result = await network.ldapSearch($("systemLdapUri").value.trim(), $("systemLdapBase").value.trim(), $("systemLdapFilter").value.trim());
      $("systemLdapResults").textContent = result.stdout || result.stderr || JSON.stringify(result, null, 2);
      say("systemLdapStatus", result.returncode === 0 ? "LDAP query completed with TLS validation and GSSAPI." : "LDAP query failed.", result.returncode !== 0);
    } catch (e) { say("systemLdapStatus", e.message || String(e), true); }
  });

  let opticalDevice = null;
  const storage = bridge("chimeraStorage");
  $("systemIsoMount")?.addEventListener("click", async () => {
    if (!storage || !storage.selectIso || !storage.mountIso) { say("systemOpticalStatus", "Native storage bridge unavailable.", true); return; }
    try {
      const path = await storage.selectIso(); if (!path) return;
      const result = await storage.mountIso(path); opticalDevice = result.device;
      say("systemOpticalStatus", result.mount || ("Mounted read-only on " + opticalDevice));
    } catch (e) { say("systemOpticalStatus", e.message || String(e), true); }
  });
  $("systemOpticalDeviceMount")?.addEventListener("click", async () => {
    if (!storage || !storage.mountOpticalDrive) { say("systemOpticalStatus", "Native optical bridge unavailable.", true); return; }
    try {
      const result = await storage.mountOpticalDrive($("systemOpticalDevice").value.trim() || "/dev/sr0");
      opticalDevice = result.device; say("systemOpticalStatus", result.mount || ("Mounted read-only from " + opticalDevice));
    } catch (e) { say("systemOpticalStatus", e.message || String(e), true); }
  });
  $("systemOpticalUnmount")?.addEventListener("click", async () => {
    if (!storage || !storage.unmountIso || !opticalDevice) return;
    try { await storage.unmountIso(opticalDevice); opticalDevice = null; say("systemOpticalStatus", "Optical media unmounted."); }
    catch (e) { say("systemOpticalStatus", e.message || String(e), true); }
  });
  loadRegistry();
})();