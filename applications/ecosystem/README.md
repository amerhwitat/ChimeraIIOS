# Chimera II OS Application Ecosystem

Aurora exposes the user's repository portfolio through one application catalog. Each repository gets a stable application ID, source URL, launcher contract, package metadata, permissions profile, and optional offline payload.

Integration modes:
- **native**: compiled Chimera application
- **web**: Aurora opens the application in its embedded/web runtime
- **external-runtime**: Node/Python/Java/etc. launched through the Universal Execution API
- **source-package**: repository is available to the package/build system
- **remote-catalog**: metadata is registered without copying source into the OS

The catalog deliberately does not pretend that arbitrary GitHub source is a prebuilt native executable. A build profile must compile/package an application before the offline binary is placed into the ISO.
