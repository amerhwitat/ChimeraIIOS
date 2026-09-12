"""Minimal authenticated-ready Chimera P2P framing reference.

This module intentionally provides framing, hashing and sequence validation;
trust/authentication is supplied by the deployment transport or identity layer.
"""
from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Envelope:
    node_id: str
    kind: str
    sequence: int
    payload: Any
    version: int = 1
    capabilities: list[str] = field(default_factory=list)

    def encode(self) -> bytes:
        raw = json.dumps(self.payload, sort_keys=True, separators=(",", ":")).encode()
        msg = {
            "version": self.version, "type": self.kind, "node_id": self.node_id,
            "sequence": self.sequence, "capabilities": self.capabilities,
            "payload_hash": hashlib.sha256(raw).hexdigest(), "payload": self.payload,
        }
        return (json.dumps(msg, sort_keys=True, separators=(",", ":")) + "\n").encode()

def decode(line: bytes) -> dict[str, Any]:
    msg = json.loads(line)
    raw = json.dumps(msg["payload"], sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(raw).hexdigest() != msg["payload_hash"]:
        raise ValueError("payload integrity check failed")
    return msg
