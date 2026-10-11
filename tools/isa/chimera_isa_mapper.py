#!/usr/bin/env python3
"""Evidence-first ISA candidate mapper for Chimera II OS.

This tool is a deterministic retrieval baseline and dataset collector, not a trained
RNN/LLM and not an instruction emulator. Optional model scores may reorder candidates,
but never upgrade evidence or execution support.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "isa" / "isa_database.json"
DEFAULT_DATASET = ROOT / "data" / "isa" / "mapping_observations.jsonl"
ARCH_FIELDS = ("id", "class", "family", "word_bits", "status", "encoding_model", "source_ref", "verified_form_count")
INS_FIELDS = ("architecture", "mnemonic", "form_id", "operands", "syntax", "length_bits", "value_bits", "mask_bits")
NATIVE = ("chimera-c8192", "chimera-r8192")


def load_database(path: pathlib.Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("architectures", "instructions", "sources"):
        if not isinstance(data.get(key), list):
            raise ValueError(f"ISA database missing list: {key}")
    return data


def rows_to_dicts(rows: list[list[Any]], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    return [dict(zip(fields, row)) for row in rows if isinstance(row, list)]


def build_mapping(db: dict[str, Any], source_arch: str, mnemonic: str,
                  operands: str = "", model_scores: dict[str, Any] | None = None) -> dict[str, Any]:
    architectures = rows_to_dicts(db["architectures"], ARCH_FIELDS)
    instructions = rows_to_dicts(db["instructions"], INS_FIELDS)
    by_id = {a["id"]: a for a in architectures}
    if source_arch not in by_id:
        raise ValueError(f"unknown source architecture: {source_arch}")
    source_forms = [i for i in instructions if i["architecture"] == source_arch
                    and i["mnemonic"].casefold() == mnemonic.casefold()]
    # Exact mnemonic/semantic-name retrieval only. No fabricated cross-ISA equivalence.
    target_rows = []
    for arch in architectures:
        forms = [i for i in instructions if i["architecture"] == arch["id"]
                 and i["mnemonic"].casefold() == mnemonic.casefold()]
        score = 1.0 if forms else 0.0
        model_score = None
        if isinstance(model_scores, dict):
            raw = model_scores.get(arch["id"])
            if isinstance(raw, (int, float)) and 0 <= raw <= 1:
                model_score = float(raw)
                # Model score is a tie-break/ranking signal, not evidence.
                score = score * 0.8 + model_score * 0.2
        if forms:
            status = "verified-form-candidate"
            reason = "Exact mnemonic form exists in the database; operand/profile/encoding validation is still required."
        elif arch["id"] in NATIVE:
            status = "native-target-unverified"
            reason = "Native Chimera target retained for mapping research; no exact instruction form exists for this mnemonic."
        else:
            status = "no-exact-form"
            reason = "No exact mnemonic form is currently recorded; semantic lowering or emulation needs a separately validated rule."
        target_rows.append({
            "architecture": arch["id"], "class": arch["class"], "family": arch["family"],
            "architecture_status": arch["status"], "verified_form_count": arch["verified_form_count"],
            "source_ref": arch["source_ref"], "status": status, "reason": reason,
            "forms": forms, "model_score": model_score, "ranking_score": round(score, 6)
        })
    target_rows.sort(key=lambda r: (-r["ranking_score"], r["architecture"]))
    source = by_id[source_arch]
    record = {
        "schema": "CHM-ISA-MAP-OBS-1",
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "database_version": db.get("version"),
        "source": {"architecture": source_arch, "mnemonic": mnemonic, "operands": operands,
                   "architecture_status": source["status"], "source_ref": source["source_ref"],
                   "recorded_forms": source_forms},
        "targets": target_rows,
        "native_chimera_targets": [r for r in target_rows if r["architecture"] in NATIVE],
        "decision": "candidate-list-only",
        "execution_allowed": False,
        "policy": "AI ranking is advisory; execute only after a validated backend, feature/profile checks, operand validation, and conformance tests."
    }
    return record


def append_jsonl(path: pathlib.Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=pathlib.Path, default=DEFAULT_DB)
    parser.add_argument("--source-architecture", required=True)
    parser.add_argument("--mnemonic", required=True)
    parser.add_argument("--operands", default="")
    parser.add_argument("--model-scores", type=pathlib.Path,
                        help="Optional JSON object mapping target architecture IDs to scores in [0,1].")
    parser.add_argument("--dataset", type=pathlib.Path, default=DEFAULT_DATASET)
    parser.add_argument("--no-record", action="store_true", help="Do not append this observation to the JSONL dataset.")
    parser.add_argument("--json", action="store_true", help="Print the full machine-readable mapping.")
    args = parser.parse_args(argv)
    try:
        db = load_database(args.database)
        scores = json.loads(args.model_scores.read_text(encoding="utf-8")) if args.model_scores else None
        result = build_mapping(db, args.source_architecture, args.mnemonic, args.operands, scores)
        if not args.no_record:
            append_jsonl(args.dataset, result)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"{args.source_architecture}:{args.mnemonic} -> {len(result['targets'])} ISA candidates")
            for target in result["targets"][:20]:
                print(f"{target['architecture']:<20} {target['status']:<27} forms={len(target['forms'])} model={target['model_score']}")
            print("Execution: NOT authorized by candidate ranking. Validate a concrete backend first.")
            if not args.no_record:
                print(f"Recorded dataset observation: {args.dataset}")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"isa-map: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
