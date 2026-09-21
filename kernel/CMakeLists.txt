add_custom_target(koronos-x86_64
  COMMAND ${CMAKE_COMMAND} -E env bash "${CMAKE_CURRENT_SOURCE_DIR}/build-koronos.sh"
  WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
  BYPRODUCTS "${CMAKE_SOURCE_DIR}/build/koronos/x86_64/koronos.elf"
  COMMENT "Build freestanding Koronos ELF64 kernel"
)
add_custom_target(koronos-validate
  COMMAND ${Python3_EXECUTABLE} "${CMAKE_SOURCE_DIR}/tools/koronos/validate_elf.py" "${CMAKE_SOURCE_DIR}/build/koronos/x86_64/koronos.elf"
  DEPENDS koronos-x86_64
  COMMENT "Validate Koronos ELF64 image"
)