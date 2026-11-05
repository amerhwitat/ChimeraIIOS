#include "chimera/qfs_probe.h"

namespace {
uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
uint64_t le64(const uint8_t *p) {
    return (uint64_t)le32(p) | ((uint64_t)le32(p + 4) << 32);
}
uint32_t gcd32(uint32_t a, uint32_t b) {
    while (b) { const uint32_t r = a % b; a = b; b = r; }
    return a;
}
}

/* The on-disk v1 header is serialized little-endian and occupies 64 bytes.
 * Read one logical sector only; never trust geometry until it is validated. */
extern "C" int chimera_qfs_probe(uint32_t handle, chimera_qfs_probe_info *out) {
    if (!out) return CHM_BLOCK_EINVAL;
    chimera_block_info device{};
    if (chimera_block_get_info(handle, &device) != 0) return CHM_BLOCK_ENODEV;
    if (device.sector_size < 512u || device.sector_size > 65536u ||
        (device.sector_size & (device.sector_size - 1u)) ||
        !device.sector_count) return CHM_BLOCK_EINVAL;

    static uint8_t sector[65536];
    if (chimera_block_read(handle, 0u, 1u, sector) != 0) return CHM_BLOCK_EIO;
    if (le32(sector) != CHIMERA_QFS_MAGIC) return CHM_BLOCK_ENOTSUP;
    const uint32_t version = le32(sector + 4);
    const uint32_t block_size = le32(sector + 8);
    const uint32_t sector_size = le32(sector + 12);
    const uint64_t total_blocks = le64(sector + 16);
    const uint64_t metadata_start = le64(sector + 24);
    const uint64_t data_start = le64(sector + 32);
    const uint64_t root_inode = le64(sector + 40);

    if (version != CHIMERA_QFS_VERSION ||
        !chimera_qfs_valid_block_size(block_size) ||
        sector_size != device.sector_size ||
        block_size < sector_size || block_size % sector_size ||
        !total_blocks || total_blocks > UINT64_MAX / block_size ||
        total_blocks * block_size > device.sector_count * (uint64_t)device.sector_size ||
        metadata_start != 1u || data_start <= metadata_start ||
        data_start >= total_blocks || !root_inode)
        return CHM_BLOCK_EINVAL;

    uint8_t uuid_nonzero = 0;
    for (uint32_t i = 0; i < 16u; ++i) uuid_nonzero |= sector[48u + i];
    if (!uuid_nonzero) return CHM_BLOCK_EINVAL;

    out->abi = CHIMERA_QFS_PROBE_ABI;
    out->block_size = block_size;
    out->sector_size = sector_size;
    out->total_blocks = total_blocks;
    out->metadata_start = metadata_start;
    out->data_start = data_start;
    out->root_inode = root_inode;
    for (uint32_t i = 0; i < 16u; ++i) out->uuid[i] = sector[48u + i];
    return 0;
}
