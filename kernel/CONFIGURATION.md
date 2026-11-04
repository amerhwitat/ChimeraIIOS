# Kernel customization

Kernel hive keys are limited to non-security-critical tunables. Kconfig controls build inclusion and architecture selection. CPU capability and online-CPU state always come from hardware/firmware and AP acknowledgements; registry values cannot invent features, widen address limits, change syscall ABI or promote a backend. Unknown keys default to reject.
