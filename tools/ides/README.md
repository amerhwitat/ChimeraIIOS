# IDE manager

Run bash tools/ides/ide-manager.sh list to see supported editors.
Install the open-source VS Code distribution with
bash tools/ides/ide-manager.sh install vscodium, then verify with
bash tools/ides/ide-manager.sh verify.

The manager uses Flatpak, winget or Homebrew already installed on the host. It does not
mirror proprietary VS Code binaries or silently install extensions. VS Code itself remains
available through Microsoft's official download page and retains its product license.
