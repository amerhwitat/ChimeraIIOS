#pragma once
#include "koronos_abi.h"
#ifdef __cplusplus
extern "C" {
#endif
enum koronos_backend_status {
 KORONOS_BACKEND_REFERENCE_ONLY=0,
 KORONOS_BACKEND_PARTIAL=1,
 KORONOS_BACKEND_PORT_SKELETON=2
};
struct koronos_arch_backend {
 uint32_t architecture;
 uint32_t family;
 uint32_t status;
 uint8_t entry_stub_present;
 uint8_t interrupt_backend_present;
 uint8_t syscall_backend_present;
 uint8_t reserved;
 const char *name;
 const char *interrupt_model;
 const char *syscall_entry;
};
const struct koronos_arch_backend *koronos_arch_backend_lookup(uint32_t architecture);
uint32_t koronos_arch_backend_count(void);
const struct koronos_arch_backend *koronos_arch_backend_at(uint32_t index);
#ifdef __cplusplus
}
#endif
