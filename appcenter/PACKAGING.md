# Native application packaging and support contract

The catalog describes discoverable applications. The runtime support manifest separately records whether a native package exists and which gates are unfinished. **There are currently no native packages claimed by this manifest.**

## Required before an app can be marked supported

1. Confirm license, source provenance, source revision and a software bill of materials.
2. Build for each declared target architecture using a supported runtime and ABI.
3. Declare dependencies with version ranges and fail closed if a required dependency is absent.
4. Declare permissions, default-deny sensitive access, and enforce filesystem, network and device sandbox boundaries.
5. Produce a signed package manifest and verify its signature before installation.
6. Implement transactional install, update, rollback and uninstall; do not execute arbitrary catalog-supplied shell scripts.
7. Run actual launch, crash, permission-denial and lifecycle tests on every claimed OS/architecture target.
8. Record the test artifact, commit, target, exit status and logs in CI. A host build or browser preview is not a native launch test.

## Manifest schema

`package-manifest.schema.json` defines the future native package contract. It is a schema only; no app should be marked `supported` until a concrete package validates against it and its launch/lifecycle evidence passes.

## Current browser prototypes

Paint Studio, Media Deck, Document Desk, Snake Arcade, Vector Studio, Sheet Desk, File Toolkit and Code Workbench are browser applications. Their native package availability is false, native launch tests are not run, and native install/update/rollback/uninstall are not implemented. The browser CI smoke tests validate only browser behavior.
