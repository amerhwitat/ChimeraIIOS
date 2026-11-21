Boot graph:
- koronos.target wants hardware.target and runtime.target.
- live.target wants live-initramfs.service and aurora.service.
- installer.target wants installer-image.service, installer-storage.service, and installer-ui.service.
- installer UI requires both installer image and storage discovery, allowing those prerequisites to run in parallel.
- Unrelated hardware services are intentionally parallel.
