cmake_minimum_required(VERSION 3.16)
project(chimera_ii_c VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(AURORA_BUILD "Build the Aurora Wayland userspace compositor" OFF)

add_library(chimera_core src/chimera.c)
target_include_directories(chimera_core PUBLIC include)
target_compile_options(chimera_core PRIVATE -Wall -Wextra -Wpedantic)

add_executable(chimera_server src/server.c)
target_link_libraries(chimera_server PRIVATE chimera_core pthread)
target_compile_options(chimera_server PRIVATE -Wall -Wextra -Wpedantic)

add_executable(test_chimera tests/test_chimera.c)
target_link_libraries(test_chimera PRIVATE chimera_core)
target_compile_options(test_chimera PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_test(NAME chimera_unit COMMAND test_chimera)

if(AURORA_BUILD)
    add_subdirectory(userspace/aurora/compositor)
endif()
