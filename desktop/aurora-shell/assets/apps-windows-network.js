/* SMB and directory browser — requires the native, policy-checked service bridge. */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el } = A;
  A.registerApp({
    id: "windows-network",
    name: "Windows Network",
    glyph: "🖧",
    render(body) {
      const wrap = el("div", "content");
      wrap.appendChild(el("h2", "", "Windows Network & Directory"));
      wrap.appendChild(el("p", "status", "SMB2/3 browsing and GVFS share opening · Active Directory · LDAP over TLS"));
      const api = () => window.chimeraNetwork || null;
      const host = el("input"); host.placeholder = "SMB server (files.example.org)";
      const browse = el("button", "", "Browse shares"); browse.type = "button";
      const openHost = el("button", "", "Open computer in File Manager"); openHost.type = "button";
      const discover = el("button", "", "Discover Microsoft network"); discover.type = "button";
      const shares = el("div", "listing");
      openHost.addEventListener("click", async () => {
        if (!host.value || !api() || typeof api().openSmb !== "function") return;
        try { await api().openSmb(host.value, ""); }
        catch (e) { shares.appendChild(el("p", "status", e.message || String(e))); }
      });
      discover.addEventListener("click", async () => {
        shares.replaceChildren();
        if (!api() || typeof api().discoverSmb !== "function") {
          shares.appendChild(el("p", "status", "Network discovery bridge is unavailable; install Avahi and enable local-link discovery."));
          return;
        }
        try {
          const result = await api().discoverSmb();
          (result.servers || []).forEach((server) => {
            const line = el("div", "row");
            line.append(el("span", "", server.name), el("span", "", server.host || server.address),
              el("span", "", server.address + ":" + server.port));
            line.addEventListener("dblclick", () => { host.value = server.host || server.address; browse.click(); });
            shares.appendChild(line);
          });
          if (!result.servers?.length) shares.appendChild(el("p", "status", "No SMB services announced on this local link."));
        } catch (e) { shares.appendChild(el("p", "status", e.message || String(e))); }
      });
      browse.addEventListener("click", async () => {
        shares.replaceChildren();
        if (!api() || typeof api().browseSmb !== "function") {
          shares.appendChild(el("p", "status", "SMB browsing bridge is unavailable; install Samba client tools and the native network IPC adapter."));
          return;
        }
        try {
          const result = await api().browseSmb(host.value);
          (result.shares || []).forEach((share) => {
            const line = el("div", "row", share.name + " — " + (share.comment || ""));
            line.tabIndex = 0;
            line.setAttribute("role", "button");
            const open = async () => {
              if (typeof api().openSmb !== "function") {
                shares.appendChild(el("p", "status", "GVFS share opening is unavailable."));
                return;
              }
              try { await api().openSmb(host.value, share.name); }
              catch (error) { shares.appendChild(el("p", "status", error.message || String(error))); }
            };
            line.addEventListener("dblclick", open);
            line.addEventListener("keydown", (event) => {
              if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); }
            });
            shares.appendChild(line);
          });
          if (!result.shares?.length) shares.appendChild(el("p", "status", "No disk shares returned."));
        } catch (e) { shares.appendChild(el("p", "status", e.message || String(e))); }
      });
      wrap.append(el("h3", "", "Microsoft network"), discover, host, browse, openHost, shares);

      const domain = el("input"); domain.placeholder = "Active Directory DNS domain";
      const user = el("input"); user.placeholder = "Administrator account (optional)";
      const checkDomain = el("button", "", "Check domain membership"); checkDomain.type = "button";
      const join = el("button", "", "Join domain using Kerberos ticket"); join.type = "button";
      const domainStatus = el("p", "status", "Domain join requires an existing Kerberos ticket (kinit) and administrator authorization.");
      checkDomain.addEventListener("click", async () => {
        if (!api() || typeof api().realmStatus !== "function") { domainStatus.textContent = "Directory service bridge unavailable."; return; }
        try { domainStatus.textContent = JSON.stringify(await api().realmStatus()); }
        catch (e) { domainStatus.textContent = e.message || String(e); }
      });
      join.addEventListener("click", async () => {
        if (!api() || typeof api().joinDomain !== "function") {
          domainStatus.textContent = "Directory service bridge unavailable; use the administrator-controlled realmd/SSSD integration.";
          return;
        }
        if (!window.confirm("Request an Active Directory join for " + domain.value + "?")) return;
        try { domainStatus.textContent = JSON.stringify(await api().joinDomain(domain.value, user.value)); }
        catch (e) { domainStatus.textContent = e.message || String(e); }
      });
      wrap.append(el("h3", "", "Active Directory"), domain, user, checkDomain, join, domainStatus);

      const uri = el("input"); uri.placeholder = "ldaps://dc.example.org";
      const base = el("input"); base.placeholder = "Base DN: dc=example,dc=org";
      const filter = el("input"); filter.placeholder = "LDAP filter: (objectClass=computer)";
      const query = el("button", "", "Search directory"); query.type = "button";
      const results = el("pre");
      query.addEventListener("click", async () => {
        if (!api() || typeof api().ldapSearch !== "function") {
          results.textContent = "LDAP bridge unavailable. The system integration requires TLS validation and Kerberos GSSAPI.";
          return;
        }
        try { results.textContent = JSON.stringify(await api().ldapSearch(uri.value, base.value, filter.value), null, 2); }
        catch (e) { results.textContent = e.message || String(e); }
      });
      wrap.append(el("h3", "", "LDAP directory"), uri, base, filter, query, results);
      body.appendChild(wrap);
    }
  });
})();