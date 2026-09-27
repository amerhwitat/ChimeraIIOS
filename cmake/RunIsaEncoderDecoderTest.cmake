# CTest wrapper: regenerate the canonical ISA metadata before executing the
# encoder/decoder test. This makes the test independent of stale build-tree
# isa_bitfields.json files left by an older CMake configure/build.

if(NOT DEFINED CHIMERA_ISA_JSON OR NOT DEFINED CHIMERA_SOURCE_DIR OR
   NOT DEFINED CHIMERA_ENCODER_TEST)
  message(FATAL_ERROR "Missing ISA encoder test wrapper arguments")
endif()

if(NOT DEFINED CHIMERA_PYTHON_EXECUTABLE OR
   CHIMERA_PYTHON_EXECUTABLE STREQUAL "")
  find_program(CHIMERA_PYTHON_EXECUTABLE NAMES python3 python)
endif()
if(NOT CHIMERA_PYTHON_EXECUTABLE)
  message(FATAL_ERROR "Python 3 is required to regenerate ISA metadata")
endif()

execute_process(
  COMMAND "${CHIMERA_PYTHON_EXECUTABLE}"
          "${CHIMERA_SOURCE_DIR}/tools/isa/generate_isa_bitfields.py"
          --output "${CHIMERA_ISA_JSON}"
  WORKING_DIRECTORY "${CHIMERA_SOURCE_DIR}"
  RESULT_VARIABLE GENERATE_RESULT
  OUTPUT_VARIABLE GENERATE_OUTPUT
  ERROR_VARIABLE GENERATE_ERROR
  COMMAND_ECHO STDOUT
)

if(NOT GENERATE_RESULT EQUAL 0)
  message(FATAL_ERROR
    "ISA metadata generation failed (exit ${GENERATE_RESULT})\n"
    "Python: [${CHIMERA_PYTHON_EXECUTABLE}]\n"
    "Source: [${CHIMERA_SOURCE_DIR}]\n"
    "Output: [${CHIMERA_ISA_JSON}]\n"
    "${GENERATE_OUTPUT}\n${GENERATE_ERROR}")
endif()

execute_process(
  COMMAND "${CHIMERA_ENCODER_TEST}" "${CHIMERA_ISA_JSON}"
  WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}"
  RESULT_VARIABLE TEST_RESULT
  OUTPUT_VARIABLE TEST_OUTPUT
  ERROR_VARIABLE TEST_ERROR
)

if(NOT TEST_RESULT EQUAL 0)
  message(FATAL_ERROR
    "chimera_isa_encoder_decoder failed (exit ${TEST_RESULT})\n"
    "${TEST_OUTPUT}\n${TEST_ERROR}")
endif()

message(STATUS "${TEST_OUTPUT}")
