# Open-source source staging

`fetch_sources.py` downloads only from explicitly allowlisted HTTPS origins, applies a size limit and optionally verifies SHA-256. It writes to a caller-selected staging directory and never executes the result.

Build commands in `build_manifest.json` are descriptive metadata. The fetcher does not run them; an explicit user or CI job must choose the appropriate sandbox/toolchain and execute a selected command.
