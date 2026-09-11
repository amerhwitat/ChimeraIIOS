# Document-aware AI ISO pipeline

The ISO-Tool integration scans repository documentation, source and build metadata before compilation. It creates a knowledge index, deterministic precedence graph, optional local RNN/LLM recommendations, compiler artifacts, canonical staging tree and final ISO.

AI recommendations never replace mandatory dependency ordering and never execute arbitrary downloaded scripts. A local llama.cpp-compatible CLI may be used with an explicitly configured GGUF model. llama.cpp provides local LLM inference in C/C++ and supports CPU/GPU backends.

Internet research is advisory and recorded in `tools/internet_solution_policy.json`; xorriso is the preferred ISO mastering backend, while CMake remains the build/dependency authority.
