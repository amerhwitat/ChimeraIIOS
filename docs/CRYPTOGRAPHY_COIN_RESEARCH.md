# Chimera II OS — Cryptocurrency and Cryptography Research Integration

Chimera II OS treats cryptocurrency support as a cryptographic research and interoperability subsystem, not as an embedded wallet or autonomous financial agent.

## Research domains

- Bitcoin: UTXO transactions, SHA-256 block-header hashing, Merkle commitments, secp256k1 signatures.
- Ethereum: account transactions, Keccak-256, secp256k1 signatures, EIP-55 checksums.
- Litecoin/Dogecoin: Bitcoin-derived UTXO and proof-of-work families.
- Monero: privacy-oriented cryptographic protocol research.
- Solana: account/program model and Ed25519 signatures.
- General cryptography: SHA-2, SHA-3, Keccak, HMAC, HKDF, AEAD, Ed25519, X25519 and secp256k1 interoperability where supported by audited libraries.

## Python integration

The Python research track supplies deterministic test workloads, public metadata catalogs and Tkinter/ttk GUIs. The Python layer should use established cryptographic libraries rather than implementing production primitives from scratch.

## C8192/R8192 integration

Cryptographic operations can become ISA/emulator conformance workloads:

- wide-integer addition/subtraction;
- modular multiplication and reduction;
- SHA-family compression workloads;
- Keccak permutation workloads;
- Merkle-tree hashing;
- deterministic signature verification vectors.

These workloads are for benchmarking and conformance. They do not imply that the Chimera ISA itself is a certified cryptographic implementation.

## Security boundary

No Chimera component should add address-to-private-key recovery, seed-phrase guessing, credential harvesting, or unauthorized wallet access. Secret keys used in legitimate tests must be generated or supplied locally and excluded from repositories, logs and CI artifacts.

## Upstream technical references

The project tracks standards and open-source references separately, preserving their licenses and attribution. Bitcoin's reference material describes block-header SHA-256 hashing and secp256k1 public-key operations; Ethereum's EIP-55 specifies mixed-case checksum encoding.
