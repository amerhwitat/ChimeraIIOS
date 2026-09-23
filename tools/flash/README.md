# Chimera II Flash Tool

The flash tool is a safety-gated orchestration layer around platform-supported device tools. Android integration uses adb and fastboot. Android Platform-Tools documentation identifies fastboot as the tool for flashing system images. Chimera does not automate unlocking or bypass device security.

A future device profile may implement exact partition maps, image names, AVB metadata, rollback indexes and recovery steps. Until such a profile is validated, generic flashing refuses to write.

Required manifest fields: schema, device, images, security.
