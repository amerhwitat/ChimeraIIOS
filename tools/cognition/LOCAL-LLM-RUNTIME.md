# Local LLM inference for command and ISA discovery

The default router remains offline and deterministic. To enable inference, run a model server that you installed and validated yourself, bound to loopback only. For example, with a local GGUF model and a compatible llama.cpp build:

```sh
llama-server --model /absolute/path/to/your-model.gguf --host 127.0.0.1 --port 8080
```

Then, in another terminal:

```sh
export CHIMERA_LLM_BASE_URL=http://127.0.0.1:8080/v1
export CHIMERA_LLM_MODEL=local-model
python3 tools/commands/command_candidate_router.py "list files" --limit 10 --llm
python3 tools/isa/isa_candidate_router.py "riscv add" --limit 10 --llm
```

The OS does not download model weights. The endpoint is restricted to loopback HTTP, uses short timeouts, and sends at most 100 ranked candidates to the model. The model can reorder only allowlisted candidate IDs. Invalid JSON, unknown IDs, endpoint errors, or timeouts fall back to deterministic ranking. A model response cannot run a command, install a provider, define instruction semantics, or promote an ISA entry to executable/conformance-tested.

This adapter supplies inference integration; it is not itself a trained RNN/LLM and does not include trained weights. Use a model with a license and architecture suitable for your deployment.
