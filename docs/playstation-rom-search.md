# Chimera II OS — Deep PlayStation ROM/ISO Search

Chimera II OS now includes a discovery-only web search utility for PSX through PS5 resources.

The utility queries public search engines and prioritizes public-domain, open-source, homebrew, Creative Commons, demos, and preservation/reference terms.

Examples:

    CHIMERA_ROM_PLATFORM=PSX chimera-rom-search.sh public domain homebrew
    CHIMERA_ROM_PLATFORM=PS2 chimera-rom-search.sh open source demo
    CHIMERA_ROM_PLATFORM=PS4 chimera-rom-search.sh SDK sample
    CHIMERA_ROM_SEARCH_MAX=100 CHIMERA_ROM_SEARCH_OUT=/tmp/ps-search.tsv chimera-rom-search.sh PSX PS2 PS3 homebrew

## Rights boundary

The search tool is discovery-only. It does not automatically download commercial ROMs/ISOs, proprietary BIOS, firmware, or copyrighted game assets.

For commercial games, including Final Fantasy, use legally obtained/user-owned dumps and verify rights and hashes before import.

Internet Archive entries require an item-by-item rights check; Internet Archive states that it does not guarantee the copyright status of uploaded material.

For PSX, PCSX-Redux provides an open-source OpenBIOS alternative to a retail BIOS.

Before import, verify copyright/license, redistribution permission, region/version, hashes, and emulator/firmware requirements.

Search results are displayed as URLs only. No arbitrary web page is executed, no downloaded ROM is mounted automatically, and no result is trusted merely because it appears in a search engine.
