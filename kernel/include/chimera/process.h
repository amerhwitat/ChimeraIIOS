#pragma once
#include <stdint.h>
#include "elf64.h"
#ifdef __cplusplus
extern "C" {
#endif
#define CHIMERA_PROCESS_ABI 2u
#define CHIMERA_PROCESS_MAX 128u
/* Admission remains a validated load plan until scheduler-owned execution is complete. */
#define CHIMERA_PROCESS_LOAD_PLAN_ONLY 1u
typedef enum chimera_process_state {
    CHIMERA_PROCESS_EMPTY=0, CHIMERA_PROCESS_ADMITTED=1, CHIMERA_PROCESS_READY=2,
    CHIMERA_PROCESS_RUNNING=3, CHIMERA_PROCESS_BLOCKED=4,
    CHIMERA_PROCESS_EXITED=5, CHIMERA_PROCESS_FAULTED=6
} chimera_process_state;
typedef struct chimera_elf_load_segment {
    uint64_t file_offset,virtual_address,file_size,memory_size,flags,align;
} chimera_elf_load_segment;
typedef struct chimera_process_image {
    uint32_t pid,state,segment_count,reserved;
    uint64_t entry,user_stack_top,image_low,image_high;
    chimera_elf_load_segment segments[16];
    /* Runtime ownership is bound only after the transactional ELF loader succeeds.
       Kernel stack/context fields remain zero until a real scheduler owns them. */
    void *address_space;
    uint64_t address_space_root;
    uint64_t runtime_entry;
    uint64_t runtime_stack;
    uint64_t kernel_stack_base;
    uint64_t kernel_stack_top;
    uint64_t saved_rsp;
    uint64_t saved_rip;
    uint32_t parent_pid;
    int32_t exit_status;
} chimera_process_image;
int chimera_process_init(void);
int chimera_process_admit_elf(const void*,uint64_t,uint16_t,uint64_t,chimera_process_image*);
int chimera_process_bind_address_space(uint32_t pid,void *address_space,uint64_t root,
                                       uint64_t user_entry,uint64_t user_stack);
int chimera_process_clear_address_space(uint32_t pid,void *expected_address_space);
int chimera_process_get(uint32_t,chimera_process_image*);
int chimera_process_set_state(uint32_t,chimera_process_state);
uint32_t chimera_process_count(void);
#ifdef __cplusplus
}
#endif
