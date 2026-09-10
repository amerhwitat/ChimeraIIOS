# Chimera II Crypto Upstreams and Provenance

**Status:** research/provenance catalogue — 2026-09-10

This document records public standards and open-source implementations reviewed for the Chimera II cryptocurrency interoperability layer. It is a reference and provenance record, not a claim that third-party projects are part of Chimera II or that their source has been copied.

## Design boundary

Chimera II crypto tooling supports legitimate cryptographic operations on material already possessed by the operator:

- private-key -> public-key -> address derivation;
- Bitcoin and Ethereum address syntax/checksum validation;
- BIP-32/BIP-39/BIP-44 deterministic derivation from legitimately possessed seed/key material;
- deterministic published test vectors;
- cryptographic benchmarking on synthetic/test data;
- ISA/emulator experiments for hashing, elliptic-curve and wide-integer operations.

It does **not** implement or restore public-address -> private-key search, guessing, inference, wallet targeting, or brute-force recovery.

## Standards and primary specifications

| Reference | Relevance | Chimera use |
|---|---|---|
| [BIP-32](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki) | Hierarchical deterministic key derivation over secp256k1 | Conformance/test-vector reference |
| [ERC-55 / EIP-55](https://eips.ethereum.org/EIPS/eip-55) | Ethereum mixed-case address checksum | Address validation/encoding reference |
| [ERC-1191](https://eips.ethereum.org/EIPS/eip-1191) | Optional chain-ID-aware Ethereum checksum | Network-aware validation research |

BIP-32 specifies secp256k1 point multiplication, serialization and extended-key derivation. The specification also publishes deterministic test vectors. ERC-55 specifies Keccak-256-based mixed-case checksum encoding. ERC-1191 extends the checksum scheme for selected chain IDs.

## Reviewed open-source implementations

| Project | Language | License observed | Review purpose | Integration policy |
|---|---|---|---|---|
| [bitcoinjs/bip32](https://github.com/bitcoinjs/bip32) | TypeScript/JS | MIT | BIP-32 API and test approach | Reference; no source copied without provenance |
| [bitcoinjs/bitcoinjs-lib](https://github.com/bitcoinjs/bitcoinjs-lib) | TypeScript/JS | MIT | Bitcoin/BIP39/BIP44 ecosystem patterns | Reference/dependency candidate |
| [paulmillr/scure-bip32](https://github.com/paulmillr/scure-bip32) | TypeScript/JS | MIT | Minimal/audited BIP-32 implementation and supply-chain practices | Reference/dependency candidate |
| [paulmillr/scure-bip39](https://github.com/paulmillr/scure-bip39) | TypeScript/JS | MIT | BIP-39 mnemonic handling and test practices | Reference/dependency candidate |
| [bitcoin-core/secp256k1](https://github.com/bitcoin-core/secp256k1) | C | MIT | High-assurance secp256k1 primitives | Reference/dependency candidate for native implementations |
| [dan-da/hd-wallet-derive](https://github.com/dan-da/hd-wallet-derive) | PHP | MIT | Multi-coin HD derivation and interoperability ideas | Reference only |
| [cryptocoinjs/hdkey](https://github.com/cryptocoinjs/hdkey) | JavaScript | MIT | HD-key API patterns | Reference only |
| [richardkiss/pycoin](https://github.com/richardkiss/pycoin) | Python | project license must be checked before reuse | Bitcoin/Python interoperability research | Reference only until license audit |

The listed projects are independent projects. Chimera II does not imply endorsement, affiliation, authorship, or ownership.

## License/provenance rules

1. Prefer standards-compatible independent implementations when a clean-room implementation is sufficient.
2. If third-party source is incorporated, retain the upstream copyright and license notices and record the exact upstream project, version/commit, files, and modifications.
3. Do not copy source merely because it is publicly visible.
4. Do not vendor proprietary, confidential, credential-bearing, or undocumented material.
5. Dependencies retain their own licenses; the Chimera II root GPL license does not relicense third-party components.
6. License metadata from Git hosting is a useful signal but is not legal advice. A repository's dependencies and embedded assets require separate review.

## GitHub and GitLab discovery

GitHub repository/code search and GitLab blob search were used to discover comparable public implementations. GitLab's API documents `scope=blobs` for filename/content search and its semantic search facilities; GitHub documents repository and license metadata APIs. These facilities are discovery mechanisms, not permission to copy code.

- GitHub repository API: https://docs.github.com/en/rest/repos/repos
- GitHub license API: https://docs.github.com/en/rest/licenses/licenses
- GitLab search API: https://docs.gitlab.com/api/search/

## Security and testing policy

Crypto changes should include:

- published deterministic test vectors;
- malformed-input tests;
- checksum negative tests;
- cross-implementation comparison tests;
- fuzz/property tests where practical;
- constant-time/security-sensitive primitive review;
- dependency/license/SBOM review;
- secret-material redaction and no-secret logging;
- reproducible build information where available.

## Chimera II ISA mapping

Suitable primitives can be mapped into the C8192/R8192 research ISA without changing the wallet safety boundary:

- wide integer add/subtract/compare;
- modular reduction and multiplication;
- SHA-2/SHA-3/Keccak hashing;
- secp256k1 point operations through explicitly defined accelerator contracts;
- deterministic HMAC/PBKDF2-style derivation;
- serialization/base encoding;
- vector/tensor operations for benchmark workloads.

The ISA specification must distinguish architectural instructions from library-level operations and must provide deterministic conformance vectors before claiming parity.

## Search snapshot

This catalogue was expanded on 2026-09-10 using current public GitHub/GitLab documentation and current public repositories. Re-run the discovery process before adopting a dependency, because repositories, licenses, releases, and security status can change.

## Related Chimera repositories

- https://github.com/amerhwitat/ChimeraIIOS
- https://github.com/amerhwitat/eth-key-check
- https://github.com/amerhwitat/bruteforce
- https://github.com/amerhwitat/keygen
- https://github.com/amerhwitat/CPU4096
- https://github.com/amerhwitat/CPU4096Simulator
