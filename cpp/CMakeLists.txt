cmake_minimum_required(VERSION 3.16)
project(ChimeraIINative LANGUAGES C CXX ASM)

# The repository root owns the canonical source CMake model. This file is a
# native build entry point that can be configured independently by IDEs/tools.
set(CHIMERA_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." CACHE PATH "Chimera II OS repository root")

if(NOT EXISTS "${CHIMERA_ROOT}/CMakeLists.txt")
  message(FATAL_ERROR "Cannot locate repository CMakeLists.txt")
endif()

message(STATUS "Chimera II OS native build root: ${CHIMERA_ROOT}")
message(STATUS "Use the repository-root CMakeLists.txt for the complete test matrix.")

add_custom_target(chimera_native_configure ALL
  COMMAND ${CMAKE_COMMAND} -S "${CHIMERA_ROOT}" -B "${CMAKE_BINARY_DIR}/root" -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
  COMMENT "Configuring canonical Chimera II OS CMake build"
)
add_custom_target(chimera_native_build
  COMMAND ${CMAKE_COMMAND} --build "${CMAKE_BINARY_DIR}/root" --parallel
  DEPENDS chimera_native_configure
  COMMENT "Building canonical Chimera II OS C/C++ targets"
)
