cmake_minimum_required(VERSION 3.20)
project(ChimeraBuildingBlocks LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

enable_testing()

function(chimera_contract_test target source include_dir)
  add_executable(${target} ${source})
  target_include_directories(${target} PRIVATE ${include_dir})
  add_test(NAME ${target} COMMAND ${target})
endfunction()

chimera_contract_test(chimera_boot_contract_test boot/boot_contract_tests.cpp ${CMAKE_CURRENT_SOURCE_DIR}/boot)
chimera_contract_test(chimera_memory_contract_test memory/memory_contract_tests.cpp ${CMAKE_CURRENT_SOURCE_DIR}/memory)
chimera_contract_test(chimera_scheduler_contract_test kernel/scheduler_tests.cpp ${CMAKE_CURRENT_SOURCE_DIR}/kernel)
chimera_contract_test(chimera_ipc_contract_test kernel/ipc_tests.cpp ${CMAKE_CURRENT_SOURCE_DIR}/kernel)
chimera_contract_test(chimera_registern_executor_test runtime/registern_executor_tests.cpp ${CMAKE_CURRENT_SOURCE_DIR}/runtime)
chimera_contract_test(chimera_mobile_hal_test "../Mobile Microkernel/tests/hal_contract.cpp" "${CMAKE_CURRENT_SOURCE_DIR}/../Mobile Microkernel/include")

add_executable(chimera_opcode_table_test tools/isa/core_opcode_table.cpp)
target_compile_definitions(chimera_opcode_table_test PRIVATE CHIMERA_OPCODE_TABLE_SELF_TEST)
add_test(NAME chimera_opcode_table_test COMMAND chimera_opcode_table_test)
