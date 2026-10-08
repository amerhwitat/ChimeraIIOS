# Chimera II watchdog service (userspace process supervisor).
add_executable(chimera-watchdog chimera_watchdog.cpp)
target_compile_features(chimera-watchdog PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera-watchdog PRIVATE -Wall -Wextra -Wpedantic)
endif()
install(TARGETS chimera-watchdog RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
install(FILES "${CMAKE_CURRENT_SOURCE_DIR}/README.md"
  DESTINATION "${CMAKE_INSTALL_DATADIR}/chimera/services/watchdog")
