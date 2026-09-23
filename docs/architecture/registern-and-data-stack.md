# RegisterN, parallel execution and data stack

## CPU

Chimera Bit Mode is a logical ISA whose registers use runtime-selected RegisterN widths. It is not constrained to 8192 bits. A host CPU executes Chimera instructions through a canonical micro-op layer. CISC and RISC hosts therefore share the same architectural semantics without pretending their physical registers have Chimera width.

Logical Chimera cores and threads are scheduled over detected physical CPUs and hardware threads. NUMA, affinity and accelerator information are reserved for the Koronos scheduler policy layer.

## Native tools

The native toolchain identifies CHIMERA-BIT machine metadata and emits/reads 16-byte canonical instruction records. Symbol, relocation and control-flow metadata are designed for debugger and reverse-engineering workflows.

## Data

Nucleus-facing services implement an ER + MDM semantic model with OLTP/OLAP/HTAP execution profiles. Row storage, column storage, MVCC/WAL, vectorized analytics, CDC and MDM golden-record workflows are separate layers.

## Apache ecosystem

Apache projects are integrated as source-first optional userland services. Koronos remains freestanding; Apache runtimes cannot become kernel dependencies. Each integration must record upstream version, license, checksum and build recipe.
