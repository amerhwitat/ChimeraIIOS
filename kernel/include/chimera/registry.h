#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
enum koronos_registry_type { KORONOS_REG_U32=1,KORONOS_REG_U64=2,KORONOS_REG_BOOL=3,KORONOS_REG_STRING=4,KORONOS_REG_BYTES=5 };
struct koronos_registry_view { const uint8_t *data; uint32_t size; uint32_t entry_count; uint64_t generation; };
uint32_t koronos_registry_crc32(const uint8_t*,uint32_t);
int koronos_registry_validate(const void*,uint32_t,struct koronos_registry_view*);
int koronos_registry_find(const struct koronos_registry_view*,const char*,uint8_t,const uint8_t**,uint32_t*);
int koronos_registry_read_u64(const struct koronos_registry_view*,const char*,uint64_t*);
int koronos_registry_read_bool(const struct koronos_registry_view*,const char*,uint8_t*);
#ifdef __cplusplus
}
#endif
