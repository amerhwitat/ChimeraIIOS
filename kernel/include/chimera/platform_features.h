#ifndef CHIMERA_PLATFORM_FEATURES_H
#define CHIMERA_PLATFORM_FEATURES_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Stable platform-feature ABI shared by Koronos, Kore, drivers and Aurora. */
#define CHIMERA_PLATFORM_FEATURE_ABI 1u
#define CHIMERA_MAX_PLATFORM_OBJECTS 256u

typedef enum chimera_platform_state {
    CHM_PLATFORM_OFFLINE = 0,
    CHM_PLATFORM_DISCOVERING = 1,
    CHM_PLATFORM_READY = 2,
    CHM_PLATFORM_DEGRADED = 3,
    CHM_PLATFORM_PANIC = 4
} chimera_platform_state;

/* Platform capabilities. Keep these values stable for persisted profiles. */
enum chimera_platform_feature_bits {
    CHM_FEAT_OBJECTS          = 1ull << 0,
    CHM_FEAT_PROCESSES        = 1ull << 1,
    CHM_FEAT_THREADS          = 1ull << 2,
    CHM_FEAT_VMEM             = 1ull << 3,
    CHM_FEAT_PAGECACHE        = 1ull << 4,
    CHM_FEAT_VFS              = 1ull << 5,
    CHM_FEAT_BLOCK_IO         = 1ull << 6,
    CHM_FEAT_DMA_IOMMU       = 1ull << 7,
    CHM_FEAT_PNP              = 1ull << 8,
    CHM_FEAT_HOTPLUG          = 1ull << 9,
    CHM_FEAT_NET_IP           = 1ull << 10,
    CHM_FEAT_NET_SOCKETS      = 1ull << 11,
    CHM_FEAT_NET_ZEROCOPY     = 1ull << 12,
    CHM_FEAT_SECURITY         = 1ull << 13,
    CHM_FEAT_TPM              = 1ull << 14,
    CHM_FEAT_DRM_KMS          = 1ull << 15,
    CHM_FEAT_USB_HID          = 1ull << 16,
    CHM_FEAT_AUDIO            = 1ull << 17,
    CHM_FEAT_POWER            = 1ull << 18,
    CHM_FEAT_VIRTUALIZATION   = 1ull << 19,
    CHM_FEAT_DIAGNOSTICS      = 1ull << 20,
    CHM_FEAT_AURORA_COMP      = 1ull << 21,
    CHM_FEAT_AURORA_WM        = 1ull << 22,
    CHM_FEAT_AURORA_CLIP      = 1ull << 23,
    CHM_FEAT_AURORA_ACCESS    = 1ull << 24,
    CHM_FEAT_COMPAT_POSIX     = 1ull << 25,
    CHM_FEAT_COMPAT_NT        = 1ull << 26,
    CHM_FEAT_COMPAT_DARWIN    = 1ull << 27,
    CHM_FEAT_COMPAT_DOS       = 1ull << 28
};

typedef struct chimera_memory_region {
    uint64_t base;
    uint64_t length;
    uint32_t flags;
    uint32_t type;
} chimera_memory_region;

typedef struct chimera_io_request {
    uint64_t id;
    uint64_t buffer;
    uint64_t length;
    uint64_t offset;
    uint32_t opcode;
    uint32_t flags;
    int32_t status;
} chimera_io_request;

typedef struct chimera_security_subject {
    uint64_t subject_id;
    uint64_t capabilities;
    uint32_t uid;
    uint32_t gid;
    uint32_t integrity;
    uint32_t flags;
} chimera_security_subject;

typedef struct chimera_net_endpoint {
    uint8_t address[16];
    uint16_t port;
    uint16_t family;
    uint32_t protocol;
    uint32_t flags;
} chimera_net_endpoint;

typedef struct chimera_display_target {
    uint32_t id;
    uint32_t width;
    uint32_t height;
    uint32_t refresh_millihz;
    uint32_t format;
    uint32_t flags;
} chimera_display_target;

typedef struct chimera_power_state {
    uint32_t ac_online;
    uint32_t battery_percent;
    uint32_t thermal_millidegrees;
    uint32_t sleep_state;
    uint64_t monotonic_ns;
} chimera_power_state;

typedef struct chimera_platform_snapshot {
    uint32_t abi;
    uint32_t state;
    uint64_t features;
    uint32_t memory_regions;
    uint32_t devices;
    uint32_t drivers;
    uint32_t displays;
    uint32_t sockets;
    uint32_t security_subjects;
} chimera_platform_snapshot;

int chimera_platform_init(uint64_t requested_features);
int chimera_platform_probe(void);
uint64_t chimera_platform_features(void);
uint32_t chimera_platform_state_get(void);
int chimera_platform_has(uint64_t feature);
int chimera_platform_get_snapshot(chimera_platform_snapshot *out);

int chimera_memory_register_region(uint64_t base, uint64_t length, uint32_t type, uint32_t flags);
uint32_t chimera_memory_region_count(void);
const chimera_memory_region *chimera_memory_region_at(uint32_t index);

int chimera_io_submit(chimera_io_request *request);
int chimera_io_complete(uint64_t request_id, int32_t status);
uint32_t chimera_io_pending(void);

int chimera_security_check(const chimera_security_subject *subject, uint64_t requested_capability);
int chimera_security_set_subject(const chimera_security_subject *subject);
int chimera_security_get_subject(uint64_t subject_id, chimera_security_subject *out);

int chimera_net_register_endpoint(const chimera_net_endpoint *endpoint);
int chimera_net_remove_endpoint(uint16_t family, uint16_t port);
uint32_t chimera_net_endpoint_count(void);

int chimera_display_register(const chimera_display_target *target);
uint32_t chimera_display_count(void);
const chimera_display_target *chimera_display_target_at(uint32_t index);

int chimera_power_update(const chimera_power_state *state);
int chimera_power_snapshot(chimera_power_state *out);

#ifdef __cplusplus
}
#endif

#endif
