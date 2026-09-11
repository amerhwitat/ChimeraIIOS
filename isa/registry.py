"""Chimera II universal ISA target registry.

Declarative compatibility metadata for native Chimera execution and
foreign-ISA translation/emulation/import. This registry deliberately does
not claim that every historical instruction encoding is locally implemented.
Backends lower verified source instructions into canonical Chimera micro-ops.
"""

ISA_TARGETS = [
    {"name":"chimera-r8192","family":"Chimera","width":8192,"execution":"native","encoding":"fixed-64","privilege":["machine","supervisor","user"],"features":["integer","atomic","vector","tensor","crypto","memory","control","system"]},
    {"name":"chimera-c8192","family":"Chimera","width":8192,"execution":"native","encoding":"variable-64-4096","privilege":["machine","supervisor","user"],"features":["integer","atomic","vector","tensor","crypto","memory","control","system"]},
    {"name":"x86-64","family":"x86","width":64,"execution":"translated","encoding":"variable","privilege":["ring0","ring3"],"features":["integer","atomic","simd","avx","crypto","virtualization","system","memory"]},
    {"name":"aarch64","family":"ARM","width":64,"execution":"translated","encoding":"fixed-32","privilege":["el0","el1","el2","el3"],"features":["integer","atomic","simd","sve","crypto","virtualization","system","memory"]},
    {"name":"riscv64","family":"RISC-V","width":64,"execution":"translated","encoding":"variable","privilege":["u","s","m"],"features":["integer","atomic","vector","crypto","compressed","custom","system","memory"]},
    {"name":"power64","family":"POWER","width":64,"execution":"translated","encoding":"fixed-32","privilege":["problem","supervisor","hypervisor"],"features":["integer","atomic","vector","crypto","virtualization","system","memory"]},
    {"name":"mips64","family":"MIPS","width":64,"execution":"translated","encoding":"fixed-32","privilege":["user","supervisor","kernel"],"features":["integer","atomic","simd","system","memory"]},
    {"name":"sparc64","family":"SPARC","width":64,"execution":"translated","encoding":"fixed-32","privilege":["user","supervisor","hypervisor"],"features":["integer","atomic","simd","system","memory"]},
    {"name":"s390x","family":"IBM Z","width":64,"execution":"translated","encoding":"variable","privilege":["problem","supervisor"],"features":["integer","atomic","vector","crypto","decimal","system","memory"]},
    {"name":"m68k","family":"Motorola 68k","width":32,"execution":"emulated","encoding":"variable","privilege":["user","supervisor"],"features":["integer","system","memory"]},
    {"name":"alpha","family":"DEC Alpha","width":64,"execution":"emulated","encoding":"fixed-32","privilege":["user","kernel"],"features":["integer","atomic","vector","system","memory"]},
    {"name":"parisc64","family":"PA-RISC","width":64,"execution":"emulated","encoding":"fixed-32","privilege":["user","kernel"],"features":["integer","atomic","system","memory"]},
    {"name":"sh4","family":"SuperH","width":32,"execution":"emulated","encoding":"fixed-16-32","privilege":["user","privileged"],"features":["integer","atomic","simd","system","memory"]},
    {"name":"itanium","family":"Itanium","width":64,"execution":"emulated","encoding":"bundle-128","privilege":["user","kernel"],"features":["integer","predication","vector","speculation","system","memory"]},
    {"name":"avr","family":"AVR","width":8,"execution":"emulated","encoding":"variable","privilege":["application"],"features":["integer","atomic","io","system"]},
    {"name":"xtensa","family":"Xtensa","width":32,"execution":"emulated","encoding":"variable","privilege":["user","privileged"],"features":["integer","atomic","simd","custom","system","memory"]},
    {"name":"wasm32","family":"WebAssembly","width":32,"execution":"imported","encoding":"stack-bytecode","privilege":["sandbox"],"features":["integer","atomic","simd","reference","sandbox"]},
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
        if not target["features"]:
            raise ValueError(f"missing feature metadata: {target['name']}")


if __name__ == "__main__":
    validate_registry()
    print(f"validated {len(ISA_TARGETS)} ISA targets")
