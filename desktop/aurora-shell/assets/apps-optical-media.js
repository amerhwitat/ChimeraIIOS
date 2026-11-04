/* Optical image manager — file selection and privileged mount use native IPC only. */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el } = A;
  A.registerApp({
    id: "optical-media",
    name: "Optical Media",
    glyph: "💿",
    render(body) {
      const wrap = el("div", "content");
      wrap.appendChild(el("h2", "", "ISO / DVD Images"));
      wrap.appendChild(el("p", "status", "Images are mounted read-only through the authorized udisks2 loop-device service."));
      const status = el("p", "status", "No image selected.");
      const choose = el("button", "", "Choose ISO image"); choose.type = "button";
      const unmount = el("button", "", "Unmount selected image"); unmount.type = "button";
      let device = null;
      choose.addEventListener("click", async () => {
        const api = window.chimeraStorage;
        if (!api || typeof api.selectIso !== "function" || typeof api.mountIso !== "function") {
          status.textContent = "Native storage bridge unavailable. The live edition requires udisks2 and its image-mount helper.";
          return;
        }
        try {
          const selected = await api.selectIso();
          const path = selected && selected.path;
          if (!path) return;
          const result = await api.mountIso(path);
          device = result.device;
          status.textContent = result.mount || ("Mounted read-only on " + device);
        } catch (e) { status.textContent = e.message || String(e); }
      });
      unmount.addEventListener("click", async () => {
        const api = window.chimeraStorage;
        if (!device || !api || typeof api.unmountIso !== "function") return;
        try { await api.unmountIso(device); device = null; status.textContent = "Image unmounted."; }
        catch (e) { status.textContent = e.message || String(e); }
      });
      wrap.append(choose, unmount, status);
      body.appendChild(wrap);
    }
  });
})();