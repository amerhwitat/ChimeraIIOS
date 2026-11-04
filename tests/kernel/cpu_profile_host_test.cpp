#include "chimera/koronos_abi.h"
#include "chimera/arch_backend.h"
#include <cstdio>
#include <cstring>
#include <cassert>
int main() {
    koronos_boot_context ctx{};
    ctx.cpu_class=KORONOS_CPU_CISC;
    ctx.cpu_mode=KORONOS_X86_LONG64;
    koronos_arch_init(&ctx);
    const koronos_cpu_features *f=koronos_get_cpu_features();
#if defined(__x86_64__) || defined(__i386__)
    assert(f->architecture==(sizeof(void*)==8?KORONOS_ARCH_X86_64:KORONOS_ARCH_X86));
    assert(f->vendor[0]!=0);
    assert(f->logical_cpus>=1);
    assert(f->family!=0);
    assert(f->stepping<=15);
    assert(f->physical_address_bits==0 || (f->physical_address_bits>=32 && f->physical_address_bits<=64));
    assert(f->virtual_address_bits==0 || (f->virtual_address_bits>=32 && f->virtual_address_bits<=64));
    if(f->max_extended_leaf>=0x80000004u) assert(f->brand[0]!=0);
    if(f->feature_flags&KORONOS_CPU_FEAT_AVX2) assert(f->feature_flags&KORONOS_CPU_FEAT_AVX);
    assert(ctx.detected_cores>=1);
    assert(koronos_arch_backend_count()==22u);
    const koronos_arch_backend *backend=koronos_arch_backend_lookup(f->architecture);
    assert(backend!=nullptr);
    assert(f->backend_status==backend->status);
    assert(f->entry_backend_present==backend->entry_stub_present);
    assert(f->interrupt_backend_present==backend->interrupt_backend_present);
    assert(f->syscall_backend_present==backend->syscall_backend_present);
    for(uint32_t i=0;i<koronos_arch_backend_count();++i) {
        const koronos_arch_backend *row=koronos_arch_backend_at(i);
        assert(row!=nullptr && row->name!=nullptr && row->interrupt_model!=nullptr && row->syscall_entry!=nullptr);
        for(uint32_t j=i+1;j<koronos_arch_backend_count();++j)
            assert(koronos_arch_backend_at(j)->architecture!=row->architecture);
    }
    std::printf("[cpu-profile] PASS arch=%u vendor=%s family=%u model=%u stepping=%u logical=%u apic-id=%u\n",
        f->architecture,f->vendor,f->family,f->model,f->stepping,f->logical_cpus,f->processor_id);
#else
    assert(f->architecture!=KORONOS_ARCH_UNKNOWN);
    std::puts("[cpu-profile] PASS non-x86 compile-time architecture identification");
#endif
    return 0;
}
