#!/usr/bin/env python3
"""Aurora Application Center: safe catalog discovery for apps and source projects."""
from __future__ import annotations
import json, os, pathlib, tkinter as tk, urllib.parse, webbrowser
from tkinter import messagebox, ttk

ROOT = pathlib.Path(os.environ.get("CHIMERA_ROOT", "/usr/share/chimera"))
APP_CATALOG = ROOT / "appcenter" / "catalog" / "apps.json"
REPOSITORY_CATALOG = ROOT / "applications" / "ecosystem" / "repos.json"


def load_json(path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def safe_web_url(value):
    parsed = urllib.parse.urlparse(value or "")
    return value if parsed.scheme == "https" and parsed.netloc else None


def load_entries(app_catalog=APP_CATALOG, repository_catalog=REPOSITORY_CATALOG):
    """Normalize metadata for display only; never execute catalog-provided commands."""
    entries = []
    try:
        for app in load_json(app_catalog).get("apps", []):
            entries.append({
                "id": app.get("id", ""), "name": app.get("name", app.get("id", "Unnamed app")),
                "category": app.get("category", "Other"), "provider": app.get("provider", "unknown"),
                "status": app.get("availability", "catalog-only"),
                "url": app.get("homepage") or app.get("source") or "",
                "license": app.get("license", "Not recorded"), "kind": "Application",
                "description": app.get("description", "Catalog entry only; installation and target compatibility are not verified.")
            })
    except (OSError, json.JSONDecodeError) as exc:
        entries.append({"id":"catalog-error","name":"Application catalog unavailable","category":"Diagnostics",
                        "provider":"none","status":"unavailable","url":"","license":"n/a","kind":"Diagnostic",
                        "description":str(exc)})
    try:
        for repo in load_json(repository_catalog).get("source_repositories", []):
            entries.append({
                "id": repo.get("id", repo.get("name", "repository")), "name": repo.get("name", "Unnamed repository"),
                "category": repo.get("category", "Source repositories"), "provider": repo.get("integration", "source"),
                "status": "source-reference", "url": repo.get("url", ""),
                "license": repo.get("license", "Review upstream license"), "kind": "Repository",
                "description": repo.get("description", "Upstream project reference; this action does not install it.")
            })
    except (OSError, json.JSONDecodeError):
        pass
    return entries


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aurora Application Center")
        self.geometry("1040x680")
        self.minsize(780, 500)
        self.entries = load_entries()
        self.by_id = {entry["id"]: entry for entry in self.entries}
        ttk.Label(self, text="Aurora • Application Center", font=("TkDefaultFont", 16, "bold")).pack(pady=(12, 3))
        ttk.Label(self, text="Discover desktop applications and upstream projects. Listings do not prove installation or native support.").pack(pady=(0, 10))
        filters = ttk.Frame(self); filters.pack(fill="x", padx=14)
        ttk.Label(filters, text="Search").pack(side="left")
        self.query = tk.StringVar()
        ttk.Entry(filters, textvariable=self.query).pack(side="left", fill="x", expand=True, padx=(6, 12))
        self.category = tk.StringVar(value="All")
        ttk.Label(filters, text="Category").pack(side="left")
        self.category_box = ttk.Combobox(filters, textvariable=self.category, state="readonly", width=22)
        self.category_box.pack(side="left", padx=(6, 0))
        body = ttk.Panedwindow(self, orient="horizontal"); body.pack(fill="both", expand=True, padx=14, pady=12)
        left = ttk.Frame(body); right = ttk.Frame(body, padding=(12, 0, 0, 0))
        body.add(left, weight=3); body.add(right, weight=2)
        self.tree = ttk.Treeview(left, columns=("category", "provider", "status"), show="tree headings", selectmode="browse")
        for col, width in (("category", 140), ("provider", 115), ("status", 130)):
            self.tree.heading(col, text=col.title()); self.tree.column(col, width=width, stretch=(col == "category"))
        self.tree.column("#0", width=210); self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _event: self.open_project())
        ttk.Label(right, text="Application details", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")
        self.detail_name = ttk.Label(right, text="Select an entry", font=("TkDefaultFont", 11, "bold"), wraplength=320)
        self.detail_name.pack(anchor="w", pady=(10, 5))
        self.detail_text = tk.Text(right, height=14, wrap="word", state="disabled"); self.detail_text.pack(fill="both", expand=True)
        buttons = ttk.Frame(right); buttons.pack(fill="x", pady=10)
        ttk.Button(buttons, text="Open Official Website", command=self.open_project).pack(side="left")
        ttk.Button(buttons, text="Refresh", command=self.refresh).pack(side="right")
        ttk.Label(self, text="Safety: this interface never runs third-party code or installs applications. Use a verified package provider.").pack(anchor="w", padx=14, pady=(0, 10))
        self.query.trace_add("write", lambda *_: self.populate())
        self.category_box.bind("<<ComboboxSelected>>", lambda _event: self.populate())
        self.refresh()

    def refresh(self):
        self.entries = load_entries()
        self.by_id = {entry["id"]: entry for entry in self.entries}
        categories = sorted({entry["category"] for entry in self.entries}, key=str.casefold)
        self.category_box["values"] = ["All", *categories]
        if self.category.get() not in self.category_box["values"]: self.category.set("All")
        self.populate()

    def populate(self):
        self.tree.delete(*self.tree.get_children())
        query, category = self.query.get().casefold().strip(), self.category.get()
        for entry in self.entries:
            text = " ".join(str(entry.get(k, "")) for k in ("id","name","category","provider","status","license","description")).casefold()
            if query and query not in text: continue
            if category != "All" and entry["category"] != category: continue
            # Treeview item IDs must be unique even if an upstream catalog reuses an identifier.
            iid = entry["id"]
            if self.tree.exists(iid): iid = f'{entry["kind"].lower()}-{iid}'
            entry["_tree_iid"] = iid
            self.tree.insert("", "end", iid=iid, text=entry["name"], values=(entry["category"],entry["provider"],entry["status"]))

    def on_select(self, _event=None):
        selected = self.tree.selection()
        if not selected: return
        entry = next((item for item in self.entries if item.get("_tree_iid", item["id"]) == selected[0]), None)
        if not entry: return
        self.detail_name.configure(text=entry["name"])
        details = (f'Type: {entry["kind"]}\nCategory: {entry["category"]}\nProvider: {entry["provider"]}\n'
                   f'Status: {entry["status"]}\nLicense: {entry["license"]}\nWebsite: {entry["url"] or "Not recorded"}\n\n'
                   f'{entry["description"]}\n\nThis listing does not mean the application is installed, ported, or launch-verified on ChimeraIIOS.')
        self.detail_text.configure(state="normal"); self.detail_text.delete("1.0","end")
        self.detail_text.insert("1.0",details); self.detail_text.configure(state="disabled")

    def open_project(self):
        selected = self.tree.selection()
        if not selected: messagebox.showinfo("Application Center","Select an entry first."); return
        entry = next((item for item in self.entries if item.get("_tree_iid", item["id"]) == selected[0]), {})
        url = safe_web_url(entry.get("url",""))
        if not url: messagebox.showwarning("Website unavailable","This entry has no valid HTTPS website."); return
        try:
            if not webbrowser.open(url,new=2): messagebox.showwarning("Open website",f"Could not open browser. Visit:\n{url}")
        except Exception as exc: messagebox.showerror("Open website",str(exc))


if __name__ == "__main__":
    App().mainloop()
