cmake_minimum_required(VERSION 3.16)
project(chimera_native_toolchain LANGUAGES C CXX)

add_library(chimera_nbit INTERFACE)
target_include_directories(chimera_nbit INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/../../lib>
    $<INSTALL_INTERFACE:include>
)
target_compile_features(chimera_nbit INTERFACE cxx_std_17)

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../lib/chimera-nbit/
        DESTINATION include/chimera-nbit FILES_MATCHING PATTERN "*.hpp")
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../sdk/python/
        DESTINATION lib/chimera/python)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../sdk/java/
        DESTINATION share/chimera/sdk/java)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/../../sdk/rust/
        DESTINATION share/chimera/sdk/rust)
install(FILES architectures.json languages.json README.md
        DESTINATION share/chimera/toolchain)
install(PROGRAMS chimera-ncc chimera-rustc chimera-python chimera-javac
        chimera-zig chimera-go chimera-fortran chimera-swift
        DESTINATION bin)
