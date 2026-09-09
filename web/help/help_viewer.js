/* Minimal accessible viewer for the canonical ChimeraHelp API. */
(function () {
  "use strict";
  function render(container, result) {
    container.replaceChildren();
    (result.results || result.documents || []).forEach((doc) => {
      const item = document.createElement("article");
      item.className = "chimera-help-result";
      item.innerHTML = `<h3>${escapeHtml(doc.name || "")}${doc.section ? `(${escapeHtml(doc.section)})` : ""}</h3><p>${escapeHtml(doc.summary || doc.title || "")}</p><small>${escapeHtml(doc.namespace || "")}</small>`;
      container.appendChild(item);
    });
  }
  function escapeHtml(value) {
    return String(value).replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;", "'":"&#39;"}[c]));
  }
  window.ChimeraHelpViewer = { render };
})();
