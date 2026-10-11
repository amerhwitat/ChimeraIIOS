# ISA candidate mapping and learning corpus

The canonical source of ISA inventory is `isa/isa_database.json`. The inventory is intentionally broader than the implemented decoder set. A catalog row is not evidence that an encoder, decoder, simulator, compiler backend, or physical processor implementation exists.

## Deterministic baseline

Run from the repository root:

```sh
python3 tools/isa/chimera_isa_mapper.py --source-architecture riscv64 --mnemonic ADD --operands 'x1,x2,x3' --json
python3 -m unittest discover -s tests/isa -v
```

The mapper performs exact-mnemonic retrieval against recorded instruction forms, includes both native Chimera targets, emits explicit negative matches, and appends a JSONL observation to `data/isa/mapping_observations.jsonl` unless `--no-record` is supplied. It does not claim to be a trained RNN/LLM. A future model can provide optional ranking scores with `--model-scores scores.json`; scores only affect ordering and cannot convert an absent encoding into verified support.

## Required RNN/LLM training data

Retain each candidate, including negative matches, alongside database version, source ISA, operands, source references, architecture status, model version/score, deterministic validation outcome, and eventual human/conformance labels. Split train/validation/test data by architecture family and source-document version to reduce leakage. Do not treat model-generated suggestions as labels. Keep raw user source code and prompts out of the corpus unless explicitly chosen for training.

## Mapping result classes

- `verified-form-candidate`: an exact mnemonic form is present; still requires operand, feature, privilege, and backend validation.
- `native-target-unverified`: native Chimera target included for research; no matching native form recorded.
- `no-exact-form`: no exact mnemonic form is cataloged; semantic lowering or emulation requires a separately validated rule.

No candidate list authorizes execution. A target can be marked executable only after a concrete encoder/decoder or lowering backend, feature/profile gates, runtime/ABI support, and conformance tests pass. Preserve provenance and all failures so future models can learn which mappings were rejected and why.
