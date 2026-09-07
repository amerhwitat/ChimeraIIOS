cmake_minimum_required(VERSION 3.16)

project(aurora_compositor VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(aurora_compositor
    src/main.cpp
    src/compositor.cpp
)

target_include_directories(aurora_compositor PRIVATE include)
target_compile_options(aurora_compositor PRIVATE -Wall -Wextra -Wpedantic)

find_package(PkgConfig QUIET)

if(PkgConfig_FOUND)
    pkg_check_modules(WAYLAND_SERVER QUIET wayland-server)
endif()

if(WAYLAND_SERVER_FOUND)
    target_compile_definitions(aurora_compositor PRIVATE AURORA_HAS_WAYLAND=1)
    target_include_directories(aurora_compositor PRIVATE ${WAYLAND_SERVER_INCLUDE_DIRS})
    target_link_directories(aurora_compositor PRIVATE ${WAYLAND_SERVER_LIBRARY_DIRS})
    target_link_libraries(aurora_compositor PRIVATE ${WAYLAND_SERVER_LIBRARIES})
else()
    message(STATUS "Aurora: wayland-server development package not found; building lifecycle stub")
endif()

install(TARGETS aurora_compositor RUNTIME DESTINATION bin)
