add_library(chimera_shell STATIC
  shell/chimera_shell.cpp
)
target_include_directories(chimera_shell PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/shell
  ${CMAKE_CURRENT_SOURCE_DIR}/../desktop/aurora/i18n
)
add_library(aurora_utf STATIC
  ../desktop/aurora/i18n/aurora_utf.cpp
  ../desktop/aurora/i18n/aurora_emoji.cpp
  ../desktop/aurora/icons/chimera_icons.cpp
)
target_include_directories(aurora_utf PUBLIC
  ../desktop/aurora/i18n
  ../desktop/aurora/icons
)
target_compile_features(aurora_utf PUBLIC cxx_std_20)
add_executable(chimera-shell shell/main.cpp)
target_link_libraries(chimera-shell PRIVATE chimera_shell aurora_utf)
target_compile_features(chimera_shell PUBLIC cxx_std_20)
target_compile_features(chimera-shell PRIVATE cxx_std_20)
add_executable(chimera-utils commands/chimera_utils.cpp)
target_compile_features(chimera-utils PRIVATE cxx_std_20)
add_executable(aurora-launcher ../desktop/aurora/aurora-launcher.cpp)
target_compile_features(aurora-launcher PRIVATE cxx_std_20)
install(TARGETS chimera-shell chimera-utils aurora-launcher aurora_utf RUNTIME DESTINATION bin ARCHIVE DESTINATION lib)
add_executable(chmctl commands/chmctl.cpp)
add_executable(chm-diagnostics commands/chimera_diagnostics.cpp)
add_executable(chmhelp commands/chmhelp.cpp)
add_executable(chm-utf8 commands/chm-utf8.cpp)
add_executable(aurora-settings ../desktop/aurora/apps/aurora_settings.cpp)
foreach(chm_target chmctl chm-diagnostics chmhelp chm-utf8 aurora-settings)
  target_link_libraries(${chm_target} PRIVATE aurora_utf)
  target_compile_features(${chm_target} PRIVATE cxx_std_20)
endforeach()
install(TARGETS chmctl chm-diagnostics chmhelp chm-utf8 aurora-settings RUNTIME DESTINATION bin)
install(DIRECTORY ../man/ DESTINATION share/man/man1 FILES_MATCHING PATTERN "*.1")
install(DIRECTORY ../desktop/aurora/icons DESTINATION share/chimera/aurora)
