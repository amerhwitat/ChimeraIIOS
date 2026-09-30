# Chimera II free-font collection

Chimera uses a source-first font registry for UI text, Arabic/Hebrew RTL text, Latin/Greek/Cyrillic LTR text, complex scripts, emoji and last-resort Unicode fallback.

The registry does not imply that every upstream font binary is copied into Git. Font packages are fetched from authoritative upstream sources, pinned, license-checked and hashed before being bundled into an ISO.

Generated font packages are staged under build/fonts/<target>/ with source revision, license, filename and SHA-256 metadata.
