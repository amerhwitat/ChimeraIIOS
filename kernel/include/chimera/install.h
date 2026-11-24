#pragma once
#include <stdint.h>
#include "chimera/block.h"
#include "chimera/vfs.h"
#ifdef __cplusplus
extern "C" {
#endif

/* Durable installer/recovery state on a dedicated GPT partition.
 *
 * The journal is two copies of a 2048-byte record in partition 1. It stores
 * the before/after superblock, inode, and file bytes so recovery can repair a
 * torn write and roll back a pending transaction without trusting fixed
 * marker sectors. */

#define KORONOS_JOURNAL_MAGIC "KORONOSJ2\x00\x00\x00\x00\x00\x00"
#define KORONOS_JOURNAL_VERSION 2u
#define KORONOS_JOURNAL_RECORD_SECTORS 4u
#define KORONOS_JOURNAL_MIRROR_SECTORS 4u
#define KORONOS_JOURNAL_PAYLOAD_MAX 256u

typedef enum koronos_journal_state {
    KORONOS_JOURNAL_EMPTY = 0u,
    KORONOS_JOURNAL_COMMITTED = 1u,
    KORONOS_JOURNAL_PENDING = 2u,
    KORONOS_JOURNAL_ROLLED_BACK = 3u
} koronos_journal_state_t;

typedef enum koronos_install_phase {
    KORONOS_PHASE_NONE = 0u,
    KORONOS_PHASE_INSTALLER = 1u,
    KORONOS_PHASE_INSTALLED = 2u,
    KORONOS_PHASE_RECOVERY = 3u,
    KORONOS_PHASE_VERIFY = 4u,
    KORONOS_PHASE_LIVE = 5u
} koronos_install_phase_t;

typedef struct koronos_journal_record {
    uint8_t magic[16];
    uint32_t version;
    uint32_t state;
    uint64_t transaction;
    uint64_t root_digest;
    uint64_t before_digest;
    uint64_t after_digest;
    uint32_t next_phase;
    uint32_t target_inode;
    char target_name[64];
    uint8_t before_inode[64];
    uint8_t after_inode[64];
    uint8_t before_superblock[512];
    uint8_t after_superblock[512];
    uint8_t before_content[256];
    uint8_t after_content[256];
    uint32_t content_length;
    uint32_t sequence;
    uint8_t reserved[244];
    uint32_t checksum;
} koronos_journal_record_t;

typedef struct koronos_install_status {
    uint32_t phase;
    uint32_t partition_count;
    uint64_t root_start;
    uint64_t root_sectors;
    uint64_t journal_start;
    uint64_t journal_sectors;
    uint32_t mount_state;
    uint32_t journal_state;
    uint64_t transaction;
    uint64_t bytes_written;
    uint64_t bytes_read;
    uint64_t root_digest;
    uint64_t restored_bytes;
    uint32_t rollback;
    uint32_t fsck_pass;
    uint32_t handoff;
} koronos_install_status_t;

extern const uint8_t koronos_root_type_guid[16];
extern const uint8_t koronos_journal_type_guid[16];

const koronos_install_status_t *koronos_install_status(void);
koronos_install_phase_t koronos_install_selected_phase(void);

int koronos_install_run_phase(koronos_install_phase_t phase);
int koronos_installer_run(void);
int koronos_installed_run(void);
int koronos_recovery_run(void);
int koronos_verify_run(void);
int koronos_live_run(void);

/* Kernel-side handoff used by the native SYSCALL path. Copies a measured
 * token into a validated ring-3 buffer. */
int koronos_vfs_handoff_user(uint64_t address, uint64_t length);

#ifdef __cplusplus
}
#endif
