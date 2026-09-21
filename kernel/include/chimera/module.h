#pragma once
#include <stdint.h>
#define KORONOS_MODULE_ABI 0x00010000u
struct koronos_module_header {
 uint32_t magic;
 uint16_t abi_major;
 uint16_t abi_minor;
 uint32_t flags;
 uint64_t init;
 uint64_t exit;
};
#define KORONOS_MODULE_MAGIC 0x4B4D4F44u
