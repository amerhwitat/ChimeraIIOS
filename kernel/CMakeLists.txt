add_custom_target(koronos-x86_64
  COMMAND ${CMAKE_COMMAND} -E env bash "${CMAKE_CURRENT_SOURCE_DIR}/build-koronos.sh"
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  BYPRODUCTS "${CMAKE_SOURCE_DIR}/build/koronos/x86_64/koronos.elf"
  COMMENT "Build freestanding Koronos ELF64 microkernel with scheduler, IPC and N-bit runtime"
)
add_custom_target(koronos-microkernel-validate
  COMMAND ${CMAKE_COMMAND} -E env bash "${CMAKE_CURRENT_SOURCE_DIR}/build-koronos.sh"
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  COMMENT "Build and validate Koronos microkernel IPC/capability ABI"
)
add_custom_target(koronos-validate
  COMMAND ${Python3_EXECUTABLE} "${CMAKE_SOURCE_DIR}/tools/koronos/validate_elf.py" "${CMAKE_SOURCE_DIR}/build/koronos/x86_64/koronos.elf"
  DEPENDS koronos-x86_64
  COMMENT "Validate Koronos ELF64 image and microkernel foundation"
)
\nadd_library(chimera_watchdog_core STATIC core/watchdog.cpp)\ntarget_include_directories(chimera_watchdog_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)\ntarget_compile_features(chimera_watchdog_core PRIVATE cxx_std_20)\n
add_library(chimera_watchdog_core STATIC core/watchdog.cpp)
target_include_directories(chimera_watchdog_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_compile_features(chimera_watchdog_core PRIVATE cxx_std_20)
