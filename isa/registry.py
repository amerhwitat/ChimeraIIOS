"""Chimera II universal ISA and CPU compatibility registry.

The registry is a declarative compatibility manifest. It does not claim that
all historical instruction encodings are manually reimplemented locally.
Foreign targets are decoded and lowered into canonical Chimera micro-ops or
executed by an emulation/JIT boundary when available.
"""

ISA_TARGETS = [
    {"name":"chimera-r8192","family":"Chimera","width":8192,"execution":"native","encoding":"fixed-64","bus_profile":"chimera-r8192","toolchains":["gnu-binutils","gcc","llvm"]},
    {"name":"chimera-c8192","family":"Chimera","width":8192,"execution":"native","encoding":"variable-64-4096","bus_profile":"chimera-c8192","toolchains":["gnu-binutils","gcc","llvm"]},
    {"name":"x86-64","family":"x86","width":64,"execution":"translated","encoding":"variable","bus_profile":"x86-64","toolchains":["gnu-binutils","gcc","llvm","nasm","yasm","msvc","masm","qemu"]},
    {"name":"aarch64","family":"ARM","width":64,"execution":"translated","encoding":"fixed-32","bus_profile":"aarch64","toolchains":["gnu-binutils","gcc","llvm","msvc","arm-keil","iar","qemu"]},
    {"name":"riscv64","family":"RISC-V","width":64,"execution":"translated","encoding":"variable","bus_profile":"riscv64","toolchains":["gnu-binutils","gcc","llvm","iar","qemu"]},
    {"name":"riscv32","family":"RISC-V","width":32,"execution":"translated","encoding":"variable","bus_profile":"riscv64","toolchains":["gnu-binutils","gcc","llvm","iar","qemu"]},
    {"name":"power64","family":"POWER","width":64,"execution":"translated","encoding":"fixed-32","bus_profile":"power64","toolchains":["gnu-binutils","gcc","llvm","ibm-xl-family","qemu"]},
    {"name":"mips64","family":"MIPS","width":64,"execution":"translated","encoding":"fixed-32","bus_profile":"mips64","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"sparc64","family":"SPARC","width":64,"execution":"translated","encoding":"fixed-32","bus_profile":"sparc64","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"s390x","family":"IBM Z","width":64,"execution":"translated","encoding":"variable","bus_profile":"s390x","toolchains":["gnu-binutils","gcc","llvm","ibm-xl-family","qemu"]},
    {"name":"loongarch64","family":"LoongArch","width":64,"execution":"translated","encoding":"variable","bus_profile":"loongarch64","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"m68k","family":"Motorola 68k","width":32,"execution":"emulated","encoding":"variable","bus_profile":"m68k","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"alpha","family":"DEC Alpha","width":64,"execution":"emulated","encoding":"fixed-32","bus_profile":"alpha","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"parisc64","family":"PA-RISC","width":64,"execution":"emulated","encoding":"fixed-32","bus_profile":"parisc64","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"sh4","family":"SuperH","width":32,"execution":"emulated","encoding":"fixed-16-32","bus_profile":"sh4","toolchains":["gnu-binutils","gcc","llvm","iar","qemu"]},
    {"name":"itanium","family":"Itanium","width":64,"execution":"emulated","encoding":"bundle-128","bus_profile":"itanium","toolchains":["gnu-binutils","llvm"]},
    {"name":"avr","family":"AVR","width":8,"execution":"emulated","encoding":"variable","bus_profile":"avr","toolchains":["gnu-binutils","gcc","llvm","iar","qemu"]},
    {"name":"xtensa","family":"Xtensa","width":32,"execution":"emulated","encoding":"variable","bus_profile":"xtensa","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"or1k","family":"OpenRISC","width":32,"execution":"emulated","encoding":"fixed-32","bus_profile":"or1k","toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"wasm32","family":"WebAssembly","width":32,"execution":"imported","encoding":"stack-bytecode","bus_profile":None,"toolchains":["llvm","gnu-binutils"]},
    {"name":"bpf","family":"eBPF","width":64,"execution":"imported","encoding":"fixed-64","bus_profile":None,"toolchains":["llvm","gnu-binutils"]},
    {"name":"amdgpu","family":"AMD GPU","width":64,"execution":"imported","encoding":"fixed-32","bus_profile":None,"toolchains":["llvm"]},
    {"name":"nvptx","family":"NVIDIA PTX","width":64,"execution":"imported","encoding":"variable","bus_profile":None,"toolchains":["llvm"]},
    {"name":"hexagon","family":"Qualcomm Hexagon","width":32,"execution":"emulated","encoding":"packet","bus_profile":None,"toolchains":["llvm","qemu"]},
    {"name":"msp430","family":"TI MSP430","width":16,"execution":"emulated","encoding":"variable","bus_profile":None,"toolchains":["gnu-binutils","gcc","llvm","iar"]},
    {"name":"csky","family":"C-SKY","width":32,"execution":"translated","encoding":"variable","bus_profile":None,"toolchains":["gnu-binutils","gcc","llvm"]},
    {"name":"microblaze","family":"AMD/Xilinx MicroBlaze","width":32,"execution":"emulated","encoding":"variable","bus_profile":None,"toolchains":["gnu-binutils","gcc","llvm","qemu"]},
    {"name":"rx","family":"Renesas RX","width":32,"execution":"emulated","encoding":"variable","bus_profile":None,"toolchains":["gnu-binutils","gcc","iar","qemu"]},
    {"name":"tricore","family":"Infineon TriCore","width":32,"execution":"emulated","encoding":"variable","bus_profile":None,"toolchains":["gnu-binutils","qemu"]},
]


def find_target(name: str):
    return next((target for target in ISA_TARGETS if target["name"] == name), None)


def validate_registry() -> None:
    names = [target["name"] for target in ISA_TARGETS]
    if len(names) != len(set(names)):
        raise ValueError("duplicate ISA target name")
    allowed = {"native", "translated", "emulated", "imported"}
    for target in ISA_TARGETS:
        if target["execution"] not in allowed:
            raise ValueError(f"unsupported execution mode: {target['execution']}")
        if target["width"] <= 0:
            raise ValueError(f"invalid register width: {target['name']}")
        if not target["toolchains"]:
            raise ValueError(f"missing toolchain metadata: {target['name']}")


if __name__ == "__main__":
    validate_registry()
    print(f"validated {len(ISA_TARGETS)} ISA targets")
