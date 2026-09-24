# Chimera II OS modular build entry point.
cmake_minimum_required(VERSION 3.16)
project(ChimeraIIOS VERSION 2.8.0 LANGUAGES C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
include(GNUInstallDirs)
include(CTest)
find_package(Python3 COMPONENTS Interpreter QUIET)
include(${CMAKE_SOURCE_DIR}/cmake/ChimeraPackaging.cmake)
include(${CMAKE_SOURCE_DIR}/cmake/ChimeraExistingGraph.cmake)
include(${CMAKE_SOURCE_DIR}/cmake/ChimeraNextGen.cmake)
add_subdirectory(kernel)
add_subdirectory(userland)
add_subdirectory(installer)
add_subdirectory(sdk)
add_subdirectory(tools/chimera-asm)

add_library(chimera_registern STATIC
  arch/registern/RegisterN.cpp
  arch/registern/ChimeraCorePool.cpp
  arch/registern/HostIsaBackend.cpp
)
target_include_directories(chimera_registern PUBLIC ${CMAKE_SOURCE_DIR}/arch/registern)
target_compile_features(chimera_registern PUBLIC cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_registern PRIVATE -Wall -Wextra -Wpedantic)
endif()
install(TARGETS chimera_registern ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(DIRECTORY arch/registern DESTINATION share/chimera/arch)
install(DIRECTORY tools/chimera-asm DESTINATION share/chimera/tools)
install(FILES system/database/chimera-data-architecture.json DESTINATION share/chimera/database)
install(DIRECTORY system/database/sql DESTINATION share/chimera/database)
install(FILES system/database/schema/chimera_mdm.sql DESTINATION share/chimera/database/schema)
install(DIRECTORY services/apache DESTINATION share/chimera/services)
install(DIRECTORY web/runtime DESTINATION share/chimera/web)
install(PROGRAMS services/chimera-web/chimera_web.py DESTINATION share/chimera/web)
install(FILES system/security/chimera_web_policy.json system/containers/podman_profile.json DESTINATION share/chimera/config)
install(FILES system/containers/quadlet/chimera-web.container DESTINATION share/chimera/quadlet)

# Apache ecosystem package ingestion and verification tools
install(FILES platform/systemd/chimera-web.service DESTINATION ${CMAKE_INSTALL_LIBDIR}/systemd/system)
install(PROGRAMS tools/web/init-chimera-web-token.sh DESTINATION bin)
install(FILES services/chimera-web/README.md DESTINATION share/chimera/web)
install(PROGRAMS services/apache/install-apache-ecosystem.sh services/apache/verify-apache-package.sh DESTINATION bin)
install(PROGRAMS services/apache/apache-sync.py DESTINATION bin)
install(FILES services/apache/apache-projects.json services/apache/README.md DESTINATION share/chimera/apache)
install(FILES system/security/apache-sandbox.json DESTINATION share/chimera/config)

# Native C/C++/ASM compiler and linker drivers.
install(PROGRAMS
  tools/toolchain/chimera-cc
  tools/toolchain/chimera-cxx
  tools/toolchain/chimera-gas
  tools/toolchain/chimera-ld
  tools/toolchain/install-native-toolchain.sh
  DESTINATION bin
)
install(FILES toolchains/chimera-native-toolchain.json DESTINATION share/chimera/toolchains)

# Boot/ISO assets: keep source artwork and boot contracts available to the installed system.
install(DIRECTORY boot/splash DESTINATION share/chimera/boot)
install(DIRECTORY desktop/aurora/assets DESTINATION share/chimera/aurora)
install(FILES boot/boot_protocol.json boot/boot-artwork-manifest.json boot/iso/grub.cfg boot/iso/grub-theme.txt DESTINATION share/chimera/boot)
install(FILES installer/installation_phases.json installer/installer_profiles.json installer/chimera-installer-plan.json DESTINATION share/chimera/installer)

# Mobile edition and safety-gated device tooling.
install(DIRECTORY mobile DESTINATION share/chimera/mobile)
install(PROGRAMS tools/flash/chimera-flash mobile/android/build-mobile.sh mobile/ios/build-mobile.sh DESTINATION bin)
install(FILES tools/flash/flash-manifest.example.json tools/flash/README.md DESTINATION share/chimera/flash)
