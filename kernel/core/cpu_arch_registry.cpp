#include "chimera/cpu_arch_registry.h"
#include "cpu_arch_registry.generated.h"

namespace {
static int same(const char *a, const char *b) {
    if (!a || !b) return 0;
    while (*a && *b) { if (*a++ != *b++) return 0; }
    return *a == *b;
}
}
extern "C" uint32_t koronos_cpu_arch_count(void) {
    return KORONOS_CPU_ARCH_REGISTRY_COUNT;
}
extern "C" const koronos_cpu_arch_descriptor *koronos_cpu_arch_at(uint32_t index) {
    return index < KORONOS_CPU_ARCH_REGISTRY_COUNT ? &koronos_cpu_arch_registry[index] : 0;
}
extern "C" const koronos_cpu_arch_descriptor *koronos_cpu_arch_find(const char *id) {
    if (!id || !*id) return 0;
    for (uint32_t i = 0; i < KORONOS_CPU_ARCH_REGISTRY_COUNT; ++i)
        if (same(koronos_cpu_arch_registry[i].id, id)) return &koronos_cpu_arch_registry[i];
    return 0;
}
extern "C" const koronos_cpu_arch_descriptor *koronos_cpu_arch_current(void) {
#if defined(__x86_64__)
    return koronos_cpu_arch_find("x86-64");
#elif defined(__i386__)
    return koronos_cpu_arch_find("x86-32");
#elif defined(__aarch64__)
    return koronos_cpu_arch_find("aarch64");
#elif defined(__arm__)
    return koronos_cpu_arch_find("arm32");
#elif defined(__riscv) && (__riscv_xlen == 64)
    return koronos_cpu_arch_find("riscv64");
#elif defined(__riscv) && (__riscv_xlen == 32)
    return koronos_cpu_arch_find("riscv32");
#else
    return 0;
#endif
}
