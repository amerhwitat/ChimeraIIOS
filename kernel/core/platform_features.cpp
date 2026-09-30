#include "chimera/platform_features.h"
#include <stddef.h>

namespace {
static uint64_t g_requested = 0;
static uint64_t g_features = 0;
static uint32_t g_state = CHM_PLATFORM_COLD;

static chimera_memory_region g_memory[CHIMERA_MAX_PLATFORM_OBJECTS];
static uint32_t g_memory_count = 0;
static chimera_io_request g_io[CHIMERA_MAX_PLATFORM_OBJECTS];
static uint32_t g_io_count = 0;
static chimera_security_subject g_subjects[CHIMERA_MAX_PLATFORM_OBJECTS];
static uint32_t g_subject_count = 0;
static chimera_net_endpoint g_endpoints[CHIMERA_MAX_PLATFORM_OBJECTS];
static uint32_t g_endpoint_count = 0;
static chimera_display_target g_displays[CHIMERA_MAX_PLATFORM_OBJECTS];
static uint32_t g_display_count = 0;
static chimera_power_state g_power = {0, 0, 0, 0, 0};

static void zero(void *p, size_t n) {
    unsigned char *b = static_cast<unsigned char *>(p);
    for (size_t i = 0; i < n; ++i) b[i] = 0;
}

static uint64_t native_features() {
    return CHM_FEAT_OBJECTS | CHM_FEAT_PROCESSES | CHM_FEAT_THREADS |
           CHM_FEAT_VMEM | CHM_FEAT_PAGECACHE | CHM_FEAT_VFS |
           CHM_FEAT_BLOCK_IO | CHM_FEAT_DMA_IOMMU | CHM_FEAT_PNP |
           CHM_FEAT_HOTPLUG | CHM_FEAT_NET_IP | CHM_FEAT_NET_SOCKETS |
           CHM_FEAT_NET_ZEROCOPY | CHM_FEAT_SECURITY | CHM_FEAT_TPM |
           CHM_FEAT_DRM_KMS | CHM_FEAT_USB_HID | CHM_FEAT_AUDIO |
           CHM_FEAT_POWER | CHM_FEAT_VIRTUALIZATION | CHM_FEAT_DIAGNOSTICS |
           CHM_FEAT_AURORA_COMP | CHM_FEAT_AURORA_WM | CHM_FEAT_AURORA_CLIP |
           CHM_FEAT_AURORA_ACCESS | CHM_FEAT_COMPAT_POSIX |
           CHM_FEAT_COMPAT_NT | CHM_FEAT_COMPAT_DARWIN | CHM_FEAT_COMPAT_DOS;
}
}

extern "C" int chimera_platform_init(uint64_t requested_features) {
    g_requested = requested_features;
    g_features = native_features() & (requested_features ? requested_features : native_features());
    g_state = CHM_PLATFORM_DISCOVERING;
    return 0;
}

extern "C" int chimera_platform_probe(void) {
    if (g_state == CHM_PLATFORM_COLD) chimera_platform_init(0);
    g_state = CHM_PLATFORM_READY;
    return 0;
}

extern "C" uint64_t chimera_platform_features(void) { return g_features; }
extern "C" uint32_t chimera_platform_state(void) { return g_state; }
extern "C" int chimera_platform_has(uint64_t feature) { return (g_features & feature) == feature; }

extern "C" int chimera_platform_get_snapshot(chimera_platform_snapshot *out) {
    if (!out) return -1;
    zero(out, sizeof(*out));
    out->abi = CHIMERA_PLATFORM_FEATURE_ABI;
    out->state = g_state;
    out->features = g_features;
    out->memory_regions = g_memory_count;
    out->devices = 0;
    out->drivers = 0;
    out->displays = g_display_count;
    out->sockets = g_endpoint_count;
    out->security_subjects = g_subject_count;
    return 0;
}

extern "C" int chimera_memory_register_region(uint64_t base, uint64_t length, uint32_t type, uint32_t flags) {
    if (!length || g_memory_count >= CHIMERA_MAX_PLATFORM_OBJECTS) return -1;
    chimera_memory_region &r = g_memory[g_memory_count++];
    r.base = base; r.length = length; r.type = type; r.flags = flags;
    return 0;
}
extern "C" uint32_t chimera_memory_region_count(void) { return g_memory_count; }
extern "C" const chimera_memory_region *chimera_memory_region(uint32_t index) {
    return index < g_memory_count ? &g_memory[index] : 0;
}

extern "C" int chimera_io_submit(chimera_io_request *request) {
    if (!request || !request->length || g_io_count >= CHIMERA_MAX_PLATFORM_OBJECTS) return -1;
    g_io[g_io_count] = *request;
    g_io[g_io_count].id = (uint64_t)(g_io_count + 1u);
    g_io[g_io_count].status = -115;
    request->id = g_io[g_io_count].id;
    request->status = -115;
    ++g_io_count;
    return 0;
}
extern "C" int chimera_io_complete(uint64_t request_id, int32_t status) {
    for (uint32_t i = 0; i < g_io_count; ++i) if (g_io[i].id == request_id) {
        g_io[i].status = status;
        return 0;
    }
    return -1;
}
extern "C" uint32_t chimera_io_pending(void) {
    uint32_t n = 0;
    for (uint32_t i = 0; i < g_io_count; ++i) if (g_io[i].status == -115) ++n;
    return n;
}

extern "C" int chimera_security_check(const chimera_security_subject *subject, uint64_t requested_capability) {
    if (!subject) return -1;
    return (subject->capabilities & requested_capability) == requested_capability ? 0 : -13;
}
extern "C" int chimera_security_set_subject(const chimera_security_subject *subject) {
    if (!subject || !subject->subject_id) return -1;
    for (uint32_t i = 0; i < g_subject_count; ++i) if (g_subjects[i].subject_id == subject->subject_id) {
        g_subjects[i] = *subject; return 0;
    }
    if (g_subject_count >= CHIMERA_MAX_PLATFORM_OBJECTS) return -1;
    g_subjects[g_subject_count++] = *subject;
    return 0;
}
extern "C" int chimera_security_get_subject(uint64_t subject_id, chimera_security_subject *out) {
    if (!out) return -1;
    for (uint32_t i = 0; i < g_subject_count; ++i) if (g_subjects[i].subject_id == subject_id) {
        *out = g_subjects[i]; return 0;
    }
    return -1;
}

extern "C" int chimera_net_register_endpoint(const chimera_net_endpoint *endpoint) {
    if (!endpoint || !endpoint->port || g_endpoint_count >= CHIMERA_MAX_PLATFORM_OBJECTS) return -1;
    g_endpoints[g_endpoint_count++] = *endpoint;
    return 0;
}
extern "C" int chimera_net_remove_endpoint(uint16_t family, uint16_t port) {
    for (uint32_t i = 0; i < g_endpoint_count; ++i) if (g_endpoints[i].family == family && g_endpoints[i].port == port) {
        g_endpoints[i] = g_endpoints[--g_endpoint_count]; return 0;
    }
    return -1;
}
extern "C" uint32_t chimera_net_endpoint_count(void) { return g_endpoint_count; }

extern "C" int chimera_display_register(const chimera_display_target *target) {
    if (!target || !target->width || !target->height || g_display_count >= CHIMERA_MAX_PLATFORM_OBJECTS) return -1;
    g_displays[g_display_count++] = *target;
    return 0;
}
extern "C" uint32_t chimera_display_count(void) { return g_display_count; }
extern "C" const chimera_display_target *chimera_display_target_at(uint32_t index) {
    return index < g_display_count ? &g_displays[index] : 0;
}

extern "C" int chimera_power_update(const chimera_power_state *state) {
    if (!state) return -1;
    g_power = *state;
    return 0;
}
extern "C" int chimera_power_snapshot(chimera_power_state *out) {
    if (!out) return -1;
    *out = g_power;
    return 0;
}
