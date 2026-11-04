# Chimera AI Workspace

This is a local-first integration point for CNN, RNN and LLM workflows.

- Run `chimera-ai-workspace status` to detect installed local runtimes.
- Index only directories you explicitly select:
  `chimera-ai-workspace scan --root ~/Projects --root ~/Documents`.
- The default JSON database stores file metadata and SHA-256 hashes, not file contents.
- Add `--include-text` only when you deliberately want small supported text files copied into the JSON database.
- Credentials, private keys, hidden directories, browser profiles, caches and common secret filenames are excluded.
- Nothing is uploaded. The tool does not train models or alter model weights.

CNN/RNN training needs a real dataset and a supported framework; LLM inference needs compatible model weights and a backend such as llama.cpp or Ollama. The ISO packages the integration and probes, not unlicensed model weights or claims that unavailable frameworks are installed.

The AI Workspace launcher is available from both Aurora and Marine desktop application menus.
