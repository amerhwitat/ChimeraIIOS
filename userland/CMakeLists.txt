add_library(chimera_shell STATIC
  shell/chimera_shell.cpp
)
target_include_directories(chimera_shell PUBLIC
  ${CMAKE_CURRENT_SOURCE_DIR}/shell
)
add_executable(chimera-shell shell/main.cpp)
target_link_libraries(chimera-shell PRIVATE chimera_shell)
target_compile_features(chimera_shell PUBLIC cxx_std_20)
target_compile_features(chimera-shell PRIVATE cxx_std_20)
add_executable(chimera-utils commands/chimera_utils.cpp)
target_compile_features(chimera-utils PRIVATE cxx_std_20)
add_executable(aurora-launcher ../desktop/aurora/aurora-launcher.cpp)
target_compile_features(aurora-launcher PRIVATE cxx_std_20)
install(TARGETS chimera-shell chimera-utils aurora-launcher RUNTIME DESTINATION bin)

add_executable(chmctl commands/chmctl.cpp)
add_executable(chm-diagnostics commands/chimera_diagnostics.cpp)
add_executable(chmhelp commands/chmhelp.cpp)
add_executable(aurora-settings ../desktop/aurora/apps/aurora_settings.cpp)
foreach(chm_target chmctl chm-diagnostics chmhelp aurora-settings)
  target_compile_features(${chm_target} PRIVATE cxx_std_20)
endforeach()
install(TARGETS chmctl chm-diagnostics chmhelp aurora-settings RUNTIME DESTINATION bin)
install(DIRECTORY ../man/ DESTINATION share/man/man1 FILES_MATCHING PATTERN "*.1")
