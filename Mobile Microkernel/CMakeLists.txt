cmake_minimum_required(VERSION 3.20)
project(ChimeraIIMobileMicrokernel LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(chimera_mobile_kernel STATIC
    src/kernel/mobile_kernel.cpp
)

target_include_directories(chimera_mobile_kernel PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(chimera_mobile_kernel PUBLIC cxx_std_20)
target_compile_options(chimera_mobile_kernel PRIVATE
    $<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/W4>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall;-Wextra;-Wpedantic>
)

option(CHIMERA_MOBILE_BUILD_TESTS "Build host-side mobile microkernel tests" ON)
if(CHIMERA_MOBILE_BUILD_TESTS)
    enable_testing()
    add_executable(chimera_mobile_kernel_smoke tests/smoke.cpp)
    target_link_libraries(chimera_mobile_kernel_smoke PRIVATE chimera_mobile_kernel)
    add_test(NAME chimera_mobile_kernel_smoke COMMAND chimera_mobile_kernel_smoke)

    add_executable(chimera_mobile_platform_contract tests/platform_contract.cpp)
    target_link_libraries(chimera_mobile_platform_contract PRIVATE chimera_mobile_kernel)
    add_test(NAME chimera_mobile_platform_contract COMMAND chimera_mobile_platform_contract)
endif()
