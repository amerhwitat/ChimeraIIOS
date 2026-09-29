add_subdirectory(pe)
install(FILES ${CMAKE_SOURCE_DIR}/system/windows/compatibility-manifest.json DESTINATION share/chimera/windows)
install(PROGRAMS ${CMAKE_SOURCE_DIR}/tools/runtime/chimera-pe.py DESTINATION bin)
