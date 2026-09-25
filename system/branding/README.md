# Chimera II OS background policy

The Aurora Wayland Glass artwork is the default visual identity across the boot chain, installer and Aurora desktop. CHIMERA_AURORA_ASSET selects a replacement at build time.

After installation, chimera-background set IMAGE changes runtime artwork and records the selected image in /etc/chimera/background.conf. Bootloader/ISO artwork is immutable after an ISO is mastered; rebuilding the ISO with the same variable changes GRUB/Jasper/Spit Fire/installer artwork.
