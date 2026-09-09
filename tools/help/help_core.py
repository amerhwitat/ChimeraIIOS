#!/usr/bin/env python3
"""Dependency-free unified Chimera II help index/resolver."""
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Optional

@dataclass(frozen=True)
class HelpDocument:
    id: str
    namespace: str
    name: str
    section: str = ""
    title: str = ""
    synopsis: str = ""
    summary: str = ""
    aliases: list[str] = field(default_factory=list)
    content: str = ""
    source_uri: str = ""
    source_version: str = ""
    license: str = ""
    availability: str = "local"

class HelpDatabase:
    def __init__(self, path=None):
        self.path = path
        self._documents = {}

    def add(self, document: HelpDocument):
        self._documents[document.id] = document

    def get(self, document_id: str) -> Optional[HelpDocument]:
        return self._documents.get(document_id)

    def all(self):
        return list(self._documents.values())

    def search(self, query: str, namespace: str | None = None):
        q = query.casefold().strip()
        if not q:
            return []
        docs = self.all()
        if namespace:
            docs = [d for d in docs if d.namespace.casefold() == namespace.casefold()]
        return [d for d in docs if q in " ".join((d.name, d.title, d.synopsis, d.summary, d.content)).casefold()]

class HelpResolver:
    def __init__(self, database: HelpDatabase):
        self.db = database

    def resolve(self, page: str, name: str | None = None):
        namespace = None
        section = page if name is not None else None
        target = name if name is not None else page
        if name is None and ":" in page:
            namespace, target = page.split(":", 1)
        docs = self.db.all()
        if namespace:
            docs = [d for d in docs if d.namespace.casefold() == namespace.casefold()]
        if section:
            docs = [d for d in docs if d.section.casefold() == section.casefold()]
        t = target.casefold()
        exact = [d for d in docs if d.name.casefold() == t]
        if not exact:
            exact = [d for d in docs if any(a.casefold() == t for a in d.aliases)]
        if not exact:
            return None
        return sorted(exact, key=lambda d: (d.namespace, d.section, d.id))[0]

    def search(self, query: str, namespace: str | None = None):
        return self.db.search(query, namespace)

def load_legacy_catalog(db: HelpDatabase, catalog):
    raw = json.loads(Path(catalog).read_text(encoding="utf-8"))
    count = 0
    for name, value in raw.get("entries", {}).items():
        namespace = "chimera" if value.get("family") == "chimera" or name.startswith("chimera") else "linux"
        db.add(HelpDocument(id=f"{namespace}:{name}:1", namespace=namespace, name=name,
                            section="1", title=name, synopsis=value.get("synopsis", ""),
                            summary=value.get("summary", ""), aliases=value.get("aliases", []),
                            source_uri=str(catalog), source_version=raw.get("schema", "unknown")))
        count += 1
    return count
