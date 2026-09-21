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
add_executable(aurora-launcher ../desktop/aurora/aurora-launcher.cpp)
target_compile_features(aurora-launcher PRIVATE cxx_std_20)
install(TARGETS chimera-shell aurora-launcher RUNTIME DESTINATION bin)
