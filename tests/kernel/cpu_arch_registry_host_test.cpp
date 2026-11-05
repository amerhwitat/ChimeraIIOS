#include "chimera/cpu_arch_registry.h"
#include <assert.h>
#include <string.h>
int main(void) {
    /* Keep this test coupled to the public API, not the generated header's
       private implementation macro. The explicit inventory assertion below
       is the reviewed expected count for this source revision. */
    assert(koronos_cpu_arch_count() == 104u);
    const koronos_cpu_arch_descriptor *x = koronos_cpu_arch_find("x86-64");
    const koronos_cpu_arch_descriptor *x32 = koronos_cpu_arch_find("x86-32");
    const koronos_cpu_arch_descriptor *arm = koronos_cpu_arch_find("aarch64");
    const koronos_cpu_arch_descriptor *arm32 = koronos_cpu_arch_find("arm32");
    const koronos_cpu_arch_descriptor *rv = koronos_cpu_arch_find("riscv64");
    const koronos_cpu_arch_descriptor *rv32 = koronos_cpu_arch_find("riscv32");
    const koronos_cpu_arch_descriptor *gpu = koronos_cpu_arch_find("nvidia-ptx");
    const koronos_cpu_arch_descriptor *wasm = koronos_cpu_arch_find("wasm32");
    assert(x && x->native_kernel && x->kernel_arch == CHIMERA_ARCH_X86_64 && x->detection_method == 2u);
    assert(x32 && x32->kernel_arch == CHIMERA_ARCH_X86_32 && !x32->native_kernel && x32->detection_method == 2u);
    assert(arm && arm->kernel_arch == CHIMERA_ARCH_AARCH64 && !arm->native_kernel && arm->detection_method == 1u);
    assert(arm32 && arm32->kernel_arch == CHIMERA_ARCH_ARM32 && !arm32->native_kernel);
    assert(rv && rv->kernel_arch == CHIMERA_ARCH_RISCV64 && !rv->native_kernel && rv->detection_method == 1u);
    assert(rv32 && rv32->kernel_arch == CHIMERA_ARCH_RISCV32 && !rv32->native_kernel);
    assert(gpu && gpu->target_kind == 2u && gpu->kernel_arch == 0u);
    assert(wasm && wasm->target_kind == 2u && wasm->kernel_arch == 0u);
    assert(!koronos_cpu_arch_find("not-a-real-isa"));
    assert(koronos_cpu_arch_at(koronos_cpu_arch_count()) == 0);
    const koronos_cpu_arch_descriptor *current = koronos_cpu_arch_current();
#if defined(__x86_64__)
    assert(current && strcmp(current->id, "x86-64") == 0);
#endif
    return 0;
}
