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

## CNN/RNN inference

ONNX Runtime supports local CNN/RNN-compatible models when `numpy` and `onnxruntime` are installed:

```sh
chimera-ai-workspace infer --family cnn --model ./model.onnx --input-npy ./input.npy --output ./result.json
chimera-ai-workspace infer --family rnn --model ./sequence.onnx --input-npy ./sequence.npy --output ./sequence-result.json
```

Models, tensors and datasets are user supplied. This is inference, not model training. Training requires a separately selected dataset, architecture, compute budget and output path.

The ISO packages the integration and runtime probes, not proprietary model weights or unavailable framework dependencies.
