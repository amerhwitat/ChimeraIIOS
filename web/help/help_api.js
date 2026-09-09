/* Unified Help API adapter shared by Web Terminal and Aurora. */
(function (global) {
  "use strict";
  const base = "/api/help";
  async function request(path, params) {
    const q = new URLSearchParams(params || {});
    const url = q.toString() ? `${base}/${path}?${q}` : `${base}/${path}`;
    const response = await fetch(url, { credentials: "same-origin", method: "GET" });
    if (!response.ok) throw new Error(`help request failed: ${response.status}`);
    return response.json();
  }
  global.ChimeraHelp = Object.freeze({
    search: (q, namespace, section) => request("search", { q, namespace, section }),
    page: (id) => request(`page/${encodeURIComponent(id)}`),
    sources: () => request("sources"),
    status: () => request("status")
  });
})(window);
