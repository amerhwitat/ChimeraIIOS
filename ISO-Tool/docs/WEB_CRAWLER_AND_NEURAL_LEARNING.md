# ISO-Tool Web Crawler and Neural Learning

The ISO-Tool implementation now includes a cross-language Knowledge & AI layer for repository documentation, build-system discovery, bounded web crawling, search, recurrent build-sequence learning and LLM/Transformer adapters.

Web content is untrusted evidence. The crawler respects robots.txt, uses bounded depth/page limits and records source URL, retrieval time and SHA-256. Commands learned from the Internet are never executed automatically. Existing package installation, compiler and ISO-build authorization remains authoritative.

The common GUI contract exposes 66 features, including Web Search, Crawl Website, Crawl Documentation, Build Knowledge Base, Train RNN, Train Transformer/LLM, AI Build Analysis, Installation/Build Plan generation, provenance/source inspection and Offline AI Mode.

Python, Java 17, C#/.NET 6 and C++20 contain language-native engines/adapters.

Normative crawler policy: urlRFC 9309 Robots Exclusion Protocolhttps://www.rfc-editor.org/rfc/rfc9309.html

PyTorch can be used by the Python implementation for `torch.nn.RNN` and Transformer backends when installed; the built-in recurrent scorer remains available for dependency-light operation. urlPyTorch RNN documentationhttps://docs.pytorch.org/docs/main/generated/torch.nn.RNN.html
