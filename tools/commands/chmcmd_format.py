"""Chimera native command-object format (CHMCMD v1) codec.

This module is the single definition of the binary layout used by the builder
and validator. Each record now carries explicit descriptor sections for operands,
options, register effects and register-effect status. Empty descriptor arrays
are rejected at pack time and at parse time. This is a metadata/object format,
not an executable format, and it implies no conformance.
"""
from __future__ import annotations

import json
import struct

FILE_MAGIC = b"CHMCMD01"
FILE_VERSION = 1
RECORD_MAGIC = b"RECD"
FILE_HEADER = struct.Struct("<8sIII")
RECORD_HEADER = struct.Struct("<4sIHBB" + "H" * 12)
LEN = struct.Struct("<H")

ARCH_IDS = {
    "unbound": 0,
    "x86_64": 1,
    "aarch64": 2,
    "riscv64": 3,
    "chimera-cisc": 4,
    "chimera-risc": 5,
}
ARCH_NAMES = {value: key for key, value in ARCH_IDS.items()}
KIND_IDS = {"positional": 1, "optional": 2, "variadic": 3}
KIND_NAMES = {value: key for key, value in KIND_IDS.items()}
STATUS_NOT_IMPLEMENTED = 0
STATUS_NATIVE_PROVIDER = 1


class FormatError(Exception):
    """Raised when a CHMCMD file or record is malformed."""


def encode_text(value: str) -> bytes:
    return value.encode("utf-8")


def _length_prefixed(raw: bytes) -> bytes:
    if len(raw) > 0xFFFF:
        raise FormatError("descriptor exceeds 16-bit length field")
    return LEN.pack(len(raw)) + raw


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def _descriptor_section(descriptors: list, label: str) -> tuple[bytes, int]:
    if not isinstance(descriptors, list) or not descriptors:
        raise FormatError(f"{label} must be a non-empty list")
    for item in descriptors:
        if not isinstance(item, dict):
            raise FormatError(f"{label} entries must be objects")
    return b"".join(_length_prefixed(_json_bytes(item)) for item in descriptors), len(descriptors)


def pack_record(row: dict, reference_arch: str = "x86_64") -> bytes:
    name = encode_text(str(row["name"]))
    namespace = encode_text(str(row["namespace"]))
    implemented = row["implementation"] != "not_implemented"
    symbols = []
    reason = ""

    if implemented:
        details = row["implementation_details"]
        symbols = [
            str(details.get("function") or row["implementation"]),
            str(row["implementation"]),
        ]
        arch_id = ARCH_IDS[reference_arch]
    else:
        reason = str(row.get("implementation_reason") or "not implemented")
        arch_id = ARCH_IDS["unbound"]

    isa_targets = [encode_text(str(target)) for target in row["isa_targets"]]
    operand_bytes, operand_count = _descriptor_section(row["operands"], "operands")
    option_bytes, option_count = _descriptor_section(row["options"], "options")

    effects = row["effects_on_registers"]
    reg_status = row["register_effects_status"]
    if not isinstance(effects, dict) or not effects:
        raise FormatError("effects_on_registers must be a non-empty object")
    if not isinstance(reg_status, dict) or not reg_status:
        raise FormatError("register_effects_status must be a non-empty object")
    effects_bytes = _json_bytes(effects)
    reg_status_bytes = _json_bytes(reg_status)

    encoded_symbols = [encode_text(item) for item in symbols]
    exit_codes = encode_text(str(row["exit_codes"]))
    side_effects = encode_text(str(row["side_effects"]))
    reason_bytes = encode_text(reason)

    payload = b""
    payload += name + namespace
    for item in isa_targets:
        payload += _length_prefixed(item)
    payload += operand_bytes
    payload += option_bytes
    for item in encoded_symbols:
        payload += _length_prefixed(item)
    payload += exit_codes + side_effects + reason_bytes
    payload += effects_bytes + reg_status_bytes

    header = RECORD_HEADER.pack(
        RECORD_MAGIC,
        RECORD_HEADER.size + len(payload),
        arch_id,
        STATUS_NATIVE_PROVIDER if implemented else STATUS_NOT_IMPLEMENTED,
        int(row.get("permission_flags", 0)) & 0xFF,
        len(name), len(namespace), len(isa_targets), operand_count, option_count,
        len(encoded_symbols), len(exit_codes), len(side_effects), len(reason_bytes),
        len(effects_bytes), len(reg_status_bytes), 0,
    )
    return header + payload


def pack_file(records: list[dict], reference_arch: str = "x86_64") -> bytes:
    body = b"".join(pack_record(row, reference_arch) for row in records)
    return FILE_HEADER.pack(FILE_MAGIC, FILE_VERSION, len(records), 0) + body


def _take(payload: bytes, offset: int, length: int) -> tuple[bytes, int]:
    if length < 0 or offset + length > len(payload):
        raise FormatError("record payload is shorter than declared field lengths")
    return payload[offset:offset + length], offset + length


def _text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise FormatError("record field is not valid UTF-8") from exc


def _decoded_object(raw: bytes, label: str) -> dict:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise FormatError(f"invalid JSON in {label} section") from exc
    if not isinstance(value, dict) or not value:
        raise FormatError(f"{label} must be a non-empty object")
    return value


def unpack_record(data: bytes) -> dict:
    if len(data) < RECORD_HEADER.size:
        raise FormatError("truncated record header")

    (magic, record_len, arch_id, impl_status, permission_flags,
     name_len, namespace_len, isa_count, operand_count, option_count,
     symbol_count, exit_code_len, side_effect_len, reason_len,
     effects_len, reg_status_len, reserved) = RECORD_HEADER.unpack_from(data, 0)

    if magic != RECORD_MAGIC:
        raise FormatError("bad record magic")
    if record_len != len(data):
        raise FormatError("record length does not match stored bytes")
    if reserved != 0:
        raise FormatError("reserved record field is nonzero")
    if arch_id not in ARCH_NAMES:
        raise FormatError(f"unknown architecture id: {arch_id}")
    if impl_status not in (STATUS_NOT_IMPLEMENTED, STATUS_NATIVE_PROVIDER):
        raise FormatError(f"unknown implementation status: {impl_status}")
    if impl_status == STATUS_NATIVE_PROVIDER and (symbol_count == 0 or reason_len != 0):
        raise FormatError("implemented record must have symbols and no reason")
    if impl_status == STATUS_NOT_IMPLEMENTED and (symbol_count != 0 or reason_len == 0):
        raise FormatError("unimplemented record must have a reason and no symbols")
    if operand_count == 0 or option_count == 0:
        raise FormatError("record has empty operand or option descriptors")
    if effects_len == 0 or reg_status_len == 0:
        raise FormatError("record has no register effect descriptors")

    payload = data[RECORD_HEADER.size:]
    offset = 0
    raw, offset = _take(payload, offset, name_len)
    name = _text(raw)
    raw, offset = _take(payload, offset, namespace_len)
    namespace = _text(raw)

    isa_targets = []
    for _ in range(isa_count):
        raw, offset = _take(payload, offset, LEN.size)
        (length,) = LEN.unpack(raw)
        raw, offset = _take(payload, offset, length)
        isa_targets.append(_text(raw))

    operands = []
    for _ in range(operand_count):
        raw, offset = _take(payload, offset, LEN.size)
        (length,) = LEN.unpack(raw)
        raw, offset = _take(payload, offset, length)
        value = _decoded_object(raw, "operand")
        if "name" not in value or "type" not in value:
            raise FormatError("operand descriptor lacks name or type")
        operands.append(value)

    options = []
    for _ in range(option_count):
        raw, offset = _take(payload, offset, LEN.size)
        (length,) = LEN.unpack(raw)
        raw, offset = _take(payload, offset, length)
        value = _decoded_object(raw, "option")
        if "name" not in value or "form" not in value:
            raise FormatError("option descriptor lacks name or form")
        options.append(value)

    symbols = []
    for _ in range(symbol_count):
        raw, offset = _take(payload, offset, LEN.size)
        (length,) = LEN.unpack(raw)
        raw, offset = _take(payload, offset, length)
        symbols.append(_text(raw))

    raw, offset = _take(payload, offset, exit_code_len)
    exit_codes = _text(raw)
    raw, offset = _take(payload, offset, side_effect_len)
    side_effects = _text(raw)
    raw, offset = _take(payload, offset, reason_len)
    reason = _text(raw)

    raw, offset = _take(payload, offset, effects_len)
    effects = _decoded_object(raw, "effects_on_registers")
    raw, offset = _take(payload, offset, reg_status_len)
    reg_status = _decoded_object(raw, "register_effects_status")

    if offset != len(payload):
        raise FormatError("record has trailing payload bytes")

    return {
        "name": name,
        "namespace": namespace,
        "arch_id": arch_id,
        "arch": ARCH_NAMES[arch_id],
        "isa_targets": isa_targets,
        "operands": operands,
        "options": options,
        "implementation": (symbols[1] if impl_status == STATUS_NATIVE_PROVIDER
                           else "not_implemented"),
        "symbols": symbols,
        "implementation_reason": reason,
        "effects_on_registers": effects,
        "register_effects_status": reg_status,
        "exit_codes": exit_codes,
        "side_effects": side_effects,
        "permission_flags": permission_flags,
    }


def unpack_file(data: bytes) -> tuple[dict, list[dict]]:
    if len(data) < FILE_HEADER.size:
        raise FormatError("file is shorter than CHMCMD header")
    magic, version, record_count, reserved = FILE_HEADER.unpack_from(data, 0)
    if magic != FILE_MAGIC:
        raise FormatError("bad CHMCMD magic")
    if version != FILE_VERSION:
        raise FormatError(f"unsupported CHMCMD version: {version}")
    if reserved != 0:
        raise FormatError("reserved file field is nonzero")

    offset = FILE_HEADER.size
    records = []
    seen = set()
    for _ in range(record_count):
        if offset + RECORD_HEADER.size > len(data):
            raise FormatError("truncated record header")
        (_, record_len, *_) = RECORD_HEADER.unpack_from(data, offset)
        if record_len < RECORD_HEADER.size or offset + record_len > len(data):
            raise FormatError("record length exceeds file size")
        record = unpack_record(data[offset:offset + record_len])
        if record["name"] in seen:
            raise FormatError(f"duplicate command record: {record['name']}")
        seen.add(record["name"])
        records.append(record)
        offset += record_len

    if offset != len(data):
        raise FormatError("file has trailing bytes after declared records")

    return {
        "magic": FILE_MAGIC.decode("ascii"),
        "version": version,
        "record_count": record_count,
    }, records
