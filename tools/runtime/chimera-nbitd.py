#!/usr/bin/env python3
"""Local Unix-socket daemon for Chimera software N-bit reference arithmetic.

The daemon is a software service, not a hardware driver or guest ISA emulator.
Requests are newline-delimited JSON objects with op=info or op=calculate.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import stat
import sys
from pathlib import Path

MAX_REQUEST_BYTES = 65536
MIN_BITS = 8
MAX_BITS = 65536
OPERATIONS = {"add", "sub", "and", "or", "xor", "shl", "shr"}


def _width(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("width must be an integer")
    if value < MIN_BITS or value > MAX_BITS or value % 8:
        raise ValueError("width must be byte-aligned and in 8..65536")
    return value


def _calculate(operation: object, lhs: object, rhs: object, width: int) -> int:
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise ValueError("unsupported operation")
    if isinstance(lhs, bool) or not isinstance(lhs, int) or isinstance(rhs, bool) or not isinstance(rhs, int):
        raise ValueError("lhs and rhs must be integers")
    mask = (1 << width) - 1
    a, b = lhs & mask, rhs & mask
    if operation == "add":
        value = a + b
    elif operation == "sub":
        value = a - b
    elif operation == "and":
        value = a & b
    elif operation == "or":
        value = a | b
    elif operation == "xor":
        value = a ^ b
    elif operation == "shl":
        value = a << b if b < width else 0
    else:
        value = a >> b if b < width else 0
    return value & mask


def handle_request(request: object) -> dict:
    if not isinstance(request, dict):
        raise ValueError("request must be a JSON object")
    operation = request.get("op")
    if operation == "info":
        width = _width(request.get("width", 8192))
        return {
            "ok": True, "schema": "CHIMERA-NBITD-1", "width_bits": width,
            "execution": "software-reference", "hardware_native": False,
            "guest_isa_execution": False,
        }
    if operation == "calculate":
        width = _width(request.get("width", 8192))
        result = _calculate(request.get("operation"), request.get("lhs"),
                            request.get("rhs"), width)
        return {"ok": True, "width_bits": width, "result": hex(result),
                "execution": "software-reference", "hardware_native": False}
    raise ValueError("op must be 'info' or 'calculate'")


def serve(connection: socket.socket) -> None:
    stream = connection.makefile("rb")
    try:
        raw = stream.readline(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            response = {"ok": False, "error": "request too large"}
        elif not raw:
            response = {"ok": False, "error": "empty request"}
        else:
            try:
                response = handle_request(json.loads(raw.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                response = {"ok": False, "error": str(exc)}
        connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
    finally:
        stream.close()
        connection.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path, default=Path("/run/chimera/nbitd.sock"))
    parser.add_argument("--check", action="store_true", help="validate configuration and exit")
    args = parser.parse_args(argv)
    if args.check:
        print(json.dumps(handle_request({"op": "info"}), indent=2))
        return 0
    path = args.socket
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        mode = path.lstat().st_mode
        if not stat.S_ISSOCK(mode):
            raise SystemExit(f"refusing to replace non-socket path: {path}")
        path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(path))
    os.chmod(path, 0o660)
    server.listen(16)
    stopped = False

    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
        server.close()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopped:
            try:
                conn, _ = server.accept()
            except OSError:
                if stopped:
                    break
                raise
            serve(conn)
    finally:
        server.close()
        try:
            path.unlink()
        except FileNotFoundError:
            pass
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"chimera-nbitd: {exc}", file=sys.stderr)
        raise SystemExit(2)
