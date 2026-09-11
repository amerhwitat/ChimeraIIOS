# GitHub → Compile/Link → ISO

ISO-Tool accepts a GitHub URL or local repository, checks out the selected source, then runs the compile/link entry point. GNU C++ and MSVC use separate build directories and their generated executables/libraries are staged separately.

The Chimera II OS repository additionally provides `tools/build/main.py` as its single repository-local CMake build entry point. It records the generated executable, library, boot-image and related artifacts in `build/chimera-build-artifacts.json`.

Interactive ISO-Tool flow: select repository → choose output directory → compile/link → stage artifacts → ISO mastering.
