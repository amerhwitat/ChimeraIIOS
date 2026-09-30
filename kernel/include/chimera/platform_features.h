#ifndef CHIMERA_PLATFORM_FEATURES_H
#define CHIMERA_PLATFORM_FEATURES_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum chimera_platform_state {
    CHM_PLATFORM_OFFLINE = 0,
    CHM_PLATFORM_DISCOVERING = 1,
    CHM_PLATFORM_READY = 2,
    CHM_PLATFORM_DEGRADED = 3,
    CHM_PLATFORM_PANIC = 4
} chimera_platform_state;

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

#ifdef __cplusplus
}
#endif

#endif
