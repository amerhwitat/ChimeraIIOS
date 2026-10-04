#include "chimera/interrupt.h"
#include "chimera/syscall.h"

extern "C" int chimera_interrupt_init(void) {
    return 0;
}

extern "C" int chimera_syscall_init(void) {
    return 0;
}
