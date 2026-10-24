#pragma once
#include <stdint.h>
#include <stddef.h>
#include "elf64.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_ELF_LOADER_ABI 2u
#define CHIMERA_ELF_BACKING_IMAGE 1u
#define CHIMERA_ELF_LOADER_MAX_SEGMENTS 16u
#define CHIMERA_ELF_USER_LIMIT 0x0000800000000000ull
#define CHIMERA_ELF_PAGE_SIZE 4096ull
#define CHIMERA_ELF_MAX_STACK_SIZE (16ull * 1024ull * 1024ull)
typedef struct chimera_elf_load_ops {
    void *(*create_address_space)(void *context);
    int (*map_pages)(void *context, void *address_space, uint64_t virtual_base,
                     uint64_t size, uint32_t elf_flags, void **kernel_alias);
    void (*destroy_address_space)(void *context, void *address_space);
    /* Optional metadata hook; a persistent image object lets VM describe clean ELF pages. */
    int (*set_backing)(void *context, void *address_space, uint64_t virtual_base,
                       uint64_t length, uint32_t backing_kind,
                       uint64_t backing_object, uint64_t backing_offset);
} chimera_elf_load_ops;
typedef struct chimera_loaded_elf {
    uint32_t abi, segment_count;
    void *address_space;
    uint64_t entry, user_stack_top, image_low, image_high, loaded_file_bytes;
} chimera_loaded_elf;
/* Loads ET_EXEC PT_LOAD segments, zeroes BSS, maps a non-executable stack.
   It prepares an image but does not itself switch to ring 3. */
int chimera_elf_load_user_image(const void *image, uint64_t image_size,
                                uint16_t expected_machine, uint64_t stack_top,
                                uint64_t stack_size, const chimera_elf_load_ops *ops,
                                void *context, chimera_loaded_elf *out);
#ifdef __cplusplus
}
#endif
