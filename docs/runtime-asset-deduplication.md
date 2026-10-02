# Chimera II OS Runtime Asset Deduplication

## Canonical-source policy

Aurora artwork and shared UI media have one canonical copy. Other runtime stages reference that copy with relative symbolic links in the Git repository.

Canonical priority:

1. `desktop/aurora/assets/`
2. `desktop/aurora/`
3. shared `assets/`
4. installer
5. recovery
6. mobile

Boot-critical firmware, kernels, initramfs images, disk images and ISO payloads remain regular files. They are never replaced by symlinks by the automatic artwork workflow.

## Build staging

When a runtime tree is copied to a staging directory on the same filesystem, use:

```bash
tools/link-runtime-assets.sh \
  --source desktop/aurora/assets \
  --dest /path/to/staging/aurora/assets \
  --mode auto
```

`auto` attempts hard links first and falls back to a normal copy when source and destination are on different filesystems. `soft` creates relative symlinks and `hard` requires hard links.

## Repository cleanup

The automatic GitHub Actions job runs on `main` changes affecting runtime trees. It validates symlinks and commits only when duplicate UI/static payloads are replaced by canonical links.

For local WSL cleanup:

```bash
bash tools/deduplicate-ui-artwork.sh
bash tools/deduplicate-assets.sh --runtime --dry-run
```

Do not use `--all` as part of an ISO build. Repository-wide source deduplication can alter intentionally separate entry points; use it only after reviewing its dry-run output.

## ISO behavior

The ISO builder may follow repository symlinks while staging files. Boot-critical files remain regular files, so GRUB/UEFI/BIOS boot paths do not depend on filesystem symlink support.
