# Windows PE/COFF compatibility targets.
# This directory is intentionally a normal CMake subdirectory so the targets
# are visible to the top-level Chimera II OS build and can be selected with
# `cmake --build ... --target chimera-win-pe`.
set(CHIMERA_WIN_PE_SOURCES
  pe_loader.cpp
)

add_library(chimera-win-pe STATIC ${CHIMERA_WIN_PE_SOURCES})
target_include_directories(chimera-win-pe PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_features(chimera-win-pe PUBLIC cxx_std_17)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(chimera-win-pe PRIVATE -Wall -Wextra -Wpedantic)
endif()

add_executable(chimera-pe-inspect pe_inspect.cpp)
target_link_libraries(chimera-pe-inspect PRIVATE chimera-win-pe)
target_compile_features(chimera-pe-inspect PRIVATE cxx_std_17)

install(TARGETS chimera-win-pe
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)
install(TARGETS chimera-pe-inspect
  RUNTIME DESTINATION bin
)
