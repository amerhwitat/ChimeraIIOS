# Optional hosted macOS SDK / portable Objective-C tooling.
# This never downloads or redistributes Apple's proprietary SDK.
add_custom_target(chimera_macos_compat_check
  COMMAND bash ${CMAKE_SOURCE_DIR}/tools/macos-compat/check-sdk.sh auto
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  COMMENT "Check licensed Apple SDK availability or portable Clang/GNUstep toolchain"
  VERBATIM
)
if(BUILD_TESTING AND Python3_Interpreter_FOUND)
  add_test(NAME chimera_macos_compat_contract
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/macos_compat/test_contract.py)
endif()
install(PROGRAMS
  tools/macos-compat/check-sdk.sh
  tools/macos-compat/build-app.sh
  tools/macos-compat/run-app.sh
  DESTINATION bin
)
install(FILES docs/MACOS_COMPATIBILITY.md
  DESTINATION share/chimera/compat
)
install(FILES tools/macos-compat/app-compatibility-manifest.json
  DESTINATION share/chimera/compat
)
