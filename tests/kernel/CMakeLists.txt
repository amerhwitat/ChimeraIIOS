cmake_minimum_required(VERSION 3.16)
add_executable(chimera_kernel_sync_test
  kernel_sync_test.cpp
  ../../kernel/core/scheduler.cpp
  ../../kernel/core/thread.cpp
  ../../kernel/core/sync.cpp
  ../../kernel/core/timer.cpp
  ../../kernel/core/apc.cpp
  ../../kernel/core/dpc.cpp
)
target_include_directories(chimera_kernel_sync_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_kernel_sync_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_kernel_sync_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_kernel_sync COMMAND chimera_kernel_sync_test)
