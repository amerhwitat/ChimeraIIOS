#include <stdint.h>
#ifndef CHIMERA_NBIT_IMAGE_BITS
#define CHIMERA_NBIT_IMAGE_BITS 64
#endif
extern "C" __attribute__((used,section(".chimera.nbit"),aligned(4)))
const struct { uint32_t magic; uint32_t version; uint32_t mode_bits; uint32_t execution_class; } chimera_nbit_image_note =
 {0x43484E42u,1u,CHIMERA_NBIT_IMAGE_BITS,(CHIMERA_NBIT_IMAGE_BITS==64u)?0u:1u};
