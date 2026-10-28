# Apple/macOS extracted files: safe integration procedure

This procedure distinguishes **redistributable project inputs** from Apple's proprietary macOS SDK.

## Do not vendor the macOS SDK

Do not commit an extracted macOS SDK, Apple framework binaries, private headers, Xcode components, or SDK archives into either public OS repository, a generated ISO, or the website. Keep the SDK on an appropriately licensed macOS build host and follow Apple's applicable terms. A macOS SDK is not required to build the freestanding Koronos kernel or its BIOS/UEFI ISO. Building/signing native macOS applications is a separate macOS-host workflow.

## Copy only files you are authorized to redistribute

Use this workflow for project-owned source, artwork, documentation, or other assets whose license permits redistribution. Do not copy an entire extracted SDK tree into the repositories.

On a Linux/WSL terminal, set the actual source folder and the two local repository roots:

```bash
# EDIT these three paths to match your machine.
export EXTRACTED_DIR="/path/to/extracted/project-files"
export CHIMERA_REPO="/mnt/c/tmp/ChimeraIIOS"
export OCTAVIAN_REPO="/path/to/OctavianOS"

test -d "$EXTRACTED_DIR" || { echo "Source directory not found"; exit 1; }
git -C "$CHIMERA_REPO" rev-parse --show-toplevel
git -C "$OCTAVIAN_REPO" rev-parse --show-toplevel
```

First inspect the source and licenses. Then copy an explicit allowlist of approved project files into a dedicated staging directory in each repository; do not use a broad recursive copy of the extracted tree:

```bash
# Example allowlist: replace these paths with your actual, redistributable files.
FILES=(
  "README.md"
  "LICENSE"
  "assets/your-project-artwork.svg"
)

for repo in "$CHIMERA_REPO" "$OCTAVIAN_REPO"; do
  dest="$repo/third_party/extracted-project-assets"
  mkdir -p "$dest"
  for rel in "${FILES[@]}"; do
    src="$EXTRACTED_DIR/$rel"
    if [[ -f "$src" ]]; then
      mkdir -p "$dest/$(dirname "$rel")"
      install -m 0644 "$src" "$dest/$rel"
    else
      echo "SKIP (not present): $src"
    fi
  done
done
```

Review the copied files before staging:

```bash
git -C "$CHIMERA_REPO" status --short
git -C "$OCTAVIAN_REPO" status --short
find "$CHIMERA_REPO/third_party/extracted-project-assets" -type f -print
find "$OCTAVIAN_REPO/third_party/extracted-project-assets" -type f -print
```

For licensed local SDK use, keep it outside both Git worktrees, for example under `$HOME/SDKs`, and add only a local build setting or ignored environment variable pointing to it. Do not add SDK files to Git, release artifacts, ISO images, or web deployment artifacts. Never run `git add .` before checking the staged file list.

## Build and release

After integrating allowed files, run each repository's documented tests/build separately and inspect `git diff --check`. Do not claim that the files affect the OS until a build actually consumes them and a test verifies the result. Do not publish a release while Koronos production acceptance is failing.
