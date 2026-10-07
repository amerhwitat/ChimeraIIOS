#include <stdint.h>
#include "../../kernel/include/chimera/koronos_abi.h"

static void jasper_progress(){
    volatile uint16_t *v=(volatile uint16_t*)0xB8000;
    const char *label="JASPER  [##########----------]  35%  Boot policy manager";
    for(uint32_t i=0;i<80;i++) v[160+i]=0x0700|' ';
    for(uint32_t i=0;label[i] && i<80;i++) v[160+i]=0x0F00|(uint8_t)label[i];
}

extern "C" void jasper_main() {
    jasper_progress();
    // Jasper is the deterministic boot-policy stage. The native chain is:
    // Spit Fire -> Jasper -> GRUB -> Koronos.
    // The GRUB stage is selected by the boot medium adapter; Koronos receives
    // the final Multiboot2/Chimera boot context.
    volatile uint64_t *handoff = (volatile uint64_t *)0x0000000000007F00ull;
    handoff[0] = 0x4A41535045524F53ull; // "JASPEROS"
    handoff[1] = KORONOS_ABI_VERSION;
    handoff[2] = 3; // next stage: GRUB
    handoff[3] = 4; // final kernel: Koronos
    for (;;) __asm__ volatile("hlt");
}
