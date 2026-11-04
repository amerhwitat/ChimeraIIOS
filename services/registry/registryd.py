#!/usr/bin/env python3
"""Local-only CHMRG01 registry service with generation-checked, journaled writes."""
import base64
import grp
import json
import os
import pathlib
import re
import socket
import socketserver
import struct
import sys
import tempfile
import threading

ROOT = pathlib.Path(os.environ.get("CHIMERA_REGISTRY_ROOT", "/etc/chimera/registry"))
RUNTIME = pathlib.Path(os.environ.get("CHIMERA_RUNTIME_DIR", "/run/chimera"))
SOCKET = pathlib.Path(os.environ.get("CHIMERA_REGISTRY_SOCKET", str(RUNTIME / "registry.sock")))
ADMIN_GROUP = os.environ.get("CHIMERA_REGISTRY_GROUP", "chimera-admin")
TOOL = pathlib.Path(os.environ.get("CHIMERA_REGISTRY_TOOL", "/usr/lib/chimera/registry/registry_hive.py"))
HIVES = ("machine", "environment", "kernel")
REQUEST_LOCK = threading.RLock()
KEY_RE = re.compile(r"^[a-z0-9_-]+(?:[./][a-z0-9_-]+)*$")
PROTECTED = ("cpu.", "machine.identity.", "security.", "kernel.smp.", "kernel.memory.", "kernel.architecture.")
HIVE_PREFIXES = {"machine": ("machine.", "cpu.", "security."), "environment": ("environment.",), "kernel": ("kernel.",)}

def _encode_hive(data):
    tool_dir = str(TOOL.parent)
    if tool_dir not in sys.path:
        sys.path.insert(0, tool_dir)
    import registry_hive
    return registry_hive.encode(data)

def _read(hive):
    if hive not in HIVES:
        raise ValueError("unknown hive")
    path = ROOT / (hive + ".json")
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("hive") != hive or data.get("schema_version") != 1 or
            isinstance(data.get("generation"), bool) or
            not isinstance(data.get("generation"), int)):
        raise ValueError("invalid hive source")
    expected = _encode_hive(data)
    binary_path = ROOT / (hive + ".hive")
    if binary_path.exists():
        if binary_path.read_bytes() != expected:
            raise ValueError("binary hive/source integrity mismatch")
    else:
        _atomic(binary_path, expected)
    return data

def _peer_allowed(sock, write=False):
    if not hasattr(socket, "SO_PEERCRED"):
        return False
    pid, uid, gid = struct.unpack("3i", sock.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
    if uid == 0:
        return True
    if not write:
        return True
    try:
        admin_gid = grp.getgrnam(ADMIN_GROUP).gr_gid
        status = pathlib.Path("/proc") / str(pid) / "status"
        groups = set()
        for line in status.read_text().splitlines():
            if line.startswith("Groups:"):
                groups = {int(x) for x in line.split()[1:]}
                break
        return gid == admin_gid or admin_gid in groups
    except (KeyError, OSError, ValueError):
        return False

def _atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        dfd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)
    finally:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass

def _recover(hive):
    journal = ROOT / (hive + ".transaction.json")
    if not journal.exists():
        return
    tx = json.loads(journal.read_text(encoding="utf-8"))
    if tx.get("hive") != hive:
        raise ValueError("transaction journal hive mismatch")
    source = base64.b64decode(tx["source"], validate=True)
    binary = base64.b64decode(tx["binary"], validate=True)
    data = json.loads(source.decode("utf-8"))
    if data.get("hive") != hive or _encode_hive(data) != binary:
        raise ValueError("transaction journal source/binary integrity mismatch")
    _atomic(ROOT / (hive + ".json"), source)
    _atomic(ROOT / (hive + ".hive"), binary)
    journal.unlink()
    dfd = os.open(str(ROOT), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)

def _commit(hive, data):
    source = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    binary = _encode_hive(data)
    ROOT.mkdir(parents=True, exist_ok=True)
    journal = {
        "hive": hive,
        "source": base64.b64encode(source).decode("ascii"),
        "binary": base64.b64encode(binary).decode("ascii")
    }
    _atomic(ROOT / (hive + ".transaction.json"),
            (json.dumps(journal, separators=(",", ":")) + "\n").encode())
    _recover(hive)

def _handle(req, writable):
    op = req.get("op")
    hive = req.get("hive", "")
    if op == "list":
        result = []
        for name in HIVES:
            _recover(name)
            data = _read(name)
            result.append({"hive": name, "generation": data["generation"],
                           "entries": data["entries"]})
        return {"ok": True, "hives": result}
    if hive not in HIVES:
        raise ValueError("unknown hive")
    _recover(hive)
    data = _read(hive)
    if op == "read":
        return {"ok": True, "hive": hive, "generation": data["generation"],
                "entries": data["entries"]}
    if op not in ("set", "delete"):
        raise ValueError("unsupported operation")
    if not writable:
        raise PermissionError("registry-admin group required")
    if isinstance(req.get("generation"), bool) or not isinstance(req.get("generation"), int) or req.get("generation") != data["generation"]:
        raise RuntimeError("generation conflict; reload before editing")
    key = req.get("path", "")
    if not isinstance(key, str) or not KEY_RE.fullmatch(key) or len(key) > 255:
        raise ValueError("invalid registry key")
    normalized_key = key.replace("/", ".")
    if not any(normalized_key.startswith(prefix) for prefix in HIVE_PREFIXES[hive]):
        raise ValueError("registry key is outside the selected hive namespace")
    if any(normalized_key.startswith(prefix) for prefix in PROTECTED):
        raise PermissionError("hardware, security and boot-critical keys are immutable here")
    entries = data["entries"]
    found = next((e for e in entries if e["path"] == key), None)
    if op == "delete":
        if found is None:
            raise KeyError("registry key not found")
        entries.remove(found)
    else:
        typ, value = req.get("type"), req.get("value")
        if typ not in ("u32", "u64", "bool", "string", "bytes"):
            raise ValueError("unsupported value type")
        if typ == "bool" and not isinstance(value, bool):
            raise ValueError("boolean value required")
        if typ in ("u32", "u64"):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("integer value required")
            maximum = (1 << (32 if typ == "u32" else 64)) - 1
            if value < 0 or value > maximum:
                raise ValueError("integer out of range")
        if typ == "string" and (not isinstance(value, str) or len(value.encode()) > 1 << 20):
            raise ValueError("invalid string")
        if typ == "bytes" and (not isinstance(value, str) or len(value) > 2 << 20):
            raise ValueError("bytes must be hex text")
        item = {"path": key, "type": typ, "value": value}
        if found is None:
            if len(entries) >= 4096:
                raise ValueError("hive entry limit reached")
            entries.append(item)
        else:
            found.update(item)
    data["generation"] += 1
    _commit(hive, data)
    return {"ok": True, "hive": hive, "generation": data["generation"]}

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            writable = _peer_allowed(self.request, write=True)
            readable = _peer_allowed(self.request, write=False)
            raw = self.rfile.readline(2 << 20)
            if not raw or len(raw) >= 2 << 20:
                raise ValueError("request too large")
            req = json.loads(raw)
            if not isinstance(req, dict):
                raise ValueError("request must be an object")
            op = req.get("op")
            if op in ("list", "read") and not readable:
                raise PermissionError("local peer access denied")
            with REQUEST_LOCK:
                response = _handle(req, writable)
        except PermissionError as exc:
            response = {"ok": False, "error": "permission-denied", "message": str(exc)}
        except Exception as exc:
            response = {"ok": False, "error": "request-failed", "message": str(exc)}
        self.wfile.write((json.dumps(response, separators=(",", ":")) + "\n").encode())

class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for hive in HIVES:
        _recover(hive)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    try:
        SOCKET.unlink()
    except FileNotFoundError:
        pass
    with Server(str(SOCKET), Handler) as server:
        gid = grp.getgrnam(ADMIN_GROUP).gr_gid
        os.chown(SOCKET, 0, gid)
        os.chmod(SOCKET, 0o660)
        server.serve_forever()

if __name__ == "__main__":
    main()
