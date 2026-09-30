# Aurora Media Stack

Aurora exposes one media integration layer while permitting multiple open-source playback engines.

The initial registry covers VLC, mpv, Audacious, MPlayer, FFplay/FFmpeg, and Kodi. Upstream source remains authoritative: Chimera records a pinned revision, license notices, dependency/license review, and SHA-256 for each generated binary package.

Third-party binaries are not silently copied into the repository. CI/build hosts fetch the selected upstream revision, build it for the target, generate notices and hashes, and stage results under `build/media/<target>/<player>/`.

No proprietary player, codec, firmware, Microsoft/Apple binary, or copyrighted sound recording is bundled merely because it is supported by an upstream player.

See `config/aurora/media-players.json` for the registry and `config/aurora/media-associations.json` for default MIME routing.
