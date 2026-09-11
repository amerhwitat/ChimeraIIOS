# Contract inventory

| Area | Contract | Test |
|---|---|---|
| Boot | `boot/boot_info.hpp` | `boot/boot_contract_tests.cpp` |
| Memory/DMA | `memory/memory_contract.hpp` | `memory/memory_contract_tests.cpp` |
| Scheduler | `kernel/scheduler_contract.hpp` | `kernel/scheduler_tests.cpp` |
| IPC/capabilities | `kernel/ipc_contract.hpp` | `kernel/ipc_tests.cpp` |
| RegisterN | `runtime/registern_runtime.hpp` | `runtime/registern_contract_tests.cpp` and executor smoke test |
| Mobile HAL | `Mobile Microkernel/include/chimera/mobile/hal_contract.hpp` | `Mobile Microkernel/tests/hal_contract.cpp` |
| ISA metadata | `tools/isa/core_opcode_table.cpp` | `tools/isa/core_opcode_table_test.cpp` |

These are contract-level tests. Hardware-level validation remains separate.
