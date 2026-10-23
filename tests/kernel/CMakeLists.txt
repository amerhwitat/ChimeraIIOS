add_executable(chimera_service_runtime_test
  service_runtime_test.cpp
  ../../kernel/core/service.cpp
)
target_include_directories(chimera_service_runtime_test PRIVATE ${CMAKE_SOURCE_DIR}/kernel/include)
target_compile_features(chimera_service_runtime_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_service_runtime_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_service_runtime COMMAND chimera_service_runtime_test)

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


add_executable(chimera_scheduler_runtime_test
  scheduler_runtime_test.cpp
  ../../kernel/core/scheduler.cpp
)
target_include_directories(chimera_scheduler_runtime_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_scheduler_runtime_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_scheduler_runtime_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_scheduler_runtime COMMAND chimera_scheduler_runtime_test)

add_executable(chimera_elf64_admission_test
  elf64_admission_test.cpp
  ../../kernel/core/elf64.cpp
  ../../kernel/core/process.cpp
)
target_include_directories(chimera_elf64_admission_test PRIVATE
  ${CMAKE_SOURCE_DIR}/kernel/include
)
target_compile_features(chimera_elf64_admission_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_elf64_admission_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_elf64_admission COMMAND chimera_elf64_admission_test)

add_executable(chimera_vfs_test
  ../../kernel/tests/vfs_test.cpp
  ../../kernel/core/vfs.cpp
)
target_include_directories(chimera_vfs_test PRIVATE ${CMAKE_SOURCE_DIR}/kernel/include)
target_compile_features(chimera_vfs_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_vfs_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_vfs COMMAND chimera_vfs_test)

add_executable(chimera_block_device_iso9660_test
  ../../kernel/tests/block_device_iso9660_test.cpp
  ../../kernel/core/block_device.cpp
  ../../kernel/core/iso9660.cpp
  ../../kernel/core/vfs.cpp
)
target_include_directories(chimera_block_device_iso9660_test PRIVATE ${CMAKE_SOURCE_DIR}/kernel/include)
target_compile_features(chimera_block_device_iso9660_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_block_device_iso9660_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_block_device_iso9660 COMMAND chimera_block_device_iso9660_test)


add_executable(chimera_tmpfs_test
  ../../kernel/tests/tmpfs_test.cpp
  ../../kernel/core/tmpfs.cpp
  ../../kernel/core/vfs.cpp
)
target_include_directories(chimera_tmpfs_test PRIVATE ${CMAKE_SOURCE_DIR}/kernel/include)
target_compile_features(chimera_tmpfs_test PRIVATE cxx_std_20)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera_tmpfs_test PRIVATE -Wall -Wextra -Wpedantic)
endif()
add_test(NAME chimera_tmpfs COMMAND chimera_tmpfs_test)

if(Python3_Interpreter_FOUND)
  add_test(NAME chimera_production_closeout_daps
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tools/tests/test_production_closeout_daps.py)
endif()
