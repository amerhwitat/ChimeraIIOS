cmake_minimum_required(VERSION 3.16)
add_executable(chimera_kernel_sync_test
  kernel_sync_test.cpp
  ../../kernel/core/scheduler.cpp
  ../../kernel/core/thread.cpp
  ../../kernel/core/sync.cpp
  ../../kernel/core/timer.cpp
  ../../kernel/core/apc.cpp
  ../../kernel/core/dpc.cpp
  ../../kernel/core/hardware.cpp
  ../../kernel/core/nbit.cpp
)
target_include_directories(chimera_kernel_sync_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_kernel_sync_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_kernel_sync_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_kernel_sync COMMAND chimera_kernel_sync_test)

add_executable(chimera_hardware_nbit_test
  hardware_nbit_test.cpp
  ../../kernel/core/hardware.cpp
  ../../kernel/core/nbit.cpp
)
target_include_directories(chimera_hardware_nbit_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_hardware_nbit_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_hardware_nbit_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_hardware_nbit COMMAND chimera_hardware_nbit_test)

add_executable(chimera_firmware_device_test
  firmware_device_test.cpp
  ../../kernel/core/firmware.cpp
  ../../kernel/core/hardware.cpp
  ../../kernel/core/device.cpp
)
target_include_directories(chimera_firmware_device_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_firmware_device_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_firmware_device_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_firmware_device COMMAND chimera_firmware_device_test)

add_executable(chimera_platform_features_test
  platform_features_test.cpp
  platform_features_abi_stubs.cpp
  ../../kernel/core/platform_features.cpp
  ../../kernel/core/compat.cpp
)
target_include_directories(chimera_platform_features_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_platform_features_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_platform_features_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_platform_features COMMAND chimera_platform_features_test)
