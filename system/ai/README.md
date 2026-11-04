# Chimera AI Workspace

Local-first desktop AI integration for the Aurora and Marine desktops.

## Resource library

Select the directories you want indexed:

```sh
chimera-ai-workspace scan --root ~/Projects --root ~/Documents
```

The default JSON database stores metadata and SHA-256 hashes only. To opt in to storing small supported text files for retrieval, add `--include-text`. Hidden directories/files, credentials, tokens, private keys, browser profiles and caches are excluded. Nothing is uploaded.

## Local LLM chat

Install and configure a local Ollama model or llama.cpp model, then run:

```sh
chimera-ai-workspace chat --model <local-model>
```

For Ollama, `<local-model>` is the local model name. For llama.cpp, it is a local model file path; select the backend with `--backend llama.cpp`. The interactive chat retrieves matching excerpts from the local JSON database and supplies them as context. It is retrieval-augmented inference, not fine-tuning or automatic weight training. If the database contains metadata only, run the explicit `scan --include-text` command first.

The desktop launcher opens this local chat workflow. If no model backend or model is configured, it reports the missing local prerequisite rather than downloading one.

### Model configuration

For an already-installed Ollama model, create `~/.config/chimera-ai/config.json`:

```json
{
  "backend": "ollama",
  "model": "llama3.2:latest"
}
```

For llama.cpp, set `"backend": "llama.cpp"` and set `"model"` to the path of an existing local GGUF file. The CLI checks the local model inventory/file before launching, so it will not implicitly download model weights.

## CNN/RNN inference

ONNX Runtime supports local CNN/RNN-compatible models when `numpy` and `onnxruntime` are installed:

```sh
chimera-ai-workspace infer --family cnn --model ./model.onnx --input-npy ./input.npy --output ./result.json
chimera-ai-workspace infer --family rnn --model ./sequence.onnx --input-npy ./sequence.npy --output ./sequence-result.json
```

Models, tensors and datasets are user supplied. This is inference, not model training. Training requires a separately selected dataset, architecture, compute budget and output path.

The ISO packages the integration and runtime probes, not proprietary model weights or unavailable framework dependencies.


## Curated hardware and systems knowledge database

The ISO now stages `/usr/share/chimera/ai/hardware-systems-knowledge.json`, its JSON Schema, an append/validate/search utility, and an advisory character-RNN checkpoint trained from the database during the ISO build. The initial database combines the repository's 104 architecture descriptors with curated, source-attributed entries covering processor architectures, ABI and interrupt models, compilers, assemblers, linkers, programming languages, firmware, bus and device drivers, DMA/IOMMU, storage, networking, graphics, kernel engineering, and ML deployment.

Local RAG chat retrieves matching records and includes their primary-documentation URLs in the evidence context. Retrieved content is data, not instructions; it cannot authorize privileged actions, execute code, or promote an inventory row to a supported hardware target.

### Search and append knowledge

```sh
chimera-ai-knowledge validate --database /usr/share/chimera/ai/hardware-systems-knowledge.json
chimera-ai-knowledge search --database /usr/share/chimera/ai/hardware-systems-knowledge.json --query "RISC-V trap interrupt ABI"
chimera-ai-knowledge append \
  --database ~/.local/share/chimera-ai/knowledge.json \
  --base /usr/share/chimera/ai/hardware-systems-knowledge.json \
  --input my-reviewed-record.json
```

An appended record must have a unique stable ID, domain, title, summary, tags, verification status, and at least one `source_ids` value already present in the database source registry. The append tool validates provenance, rejects duplicate IDs, hashes the record and writes atomically. The user overlay is kept separate from the read-only ISO database. For a new source, add its bibliographic record through a reviewed database update before appending entries that cite it.

### Model status and training boundaries

- **RNN:** the ISO builder trains a small vanilla character-level RNN on the curated knowledge entries, holds out a deterministic evaluation split, records corpus SHA-256/loss/held-out score, and validates checkpoint round-trip. It is an advisory text-pattern model, not an LLM and not an authoritative ISA/driver classifier.
- **CNN:** not trained or bundled. A reproducible CNN training run needs an explicitly licensed, labelled dataset and a defined task/metrics; no such dataset is part of this change.
- **LLM:** local Ollama or llama.cpp inference remains a separately installed model. The JSON database supplies retrieval context; it does not fine-tune LLM weights. No LLM weights are redistributed by this ISO payload.
- **Training is not runtime acceptance:** build-time model generation and RAG availability do not prove a running Koronos userspace process, a hardware driver, or a production-ready target architecture.
