#include "chimera/fat_probe.h"

namespace {
uint16_t le16(const uint8_t *p) {
    return (uint16_t)p[0] | ((uint16_t)p[1] << 8);
}
uint32_t le32(const uint8_t *p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
volatile uint32_t fat_probe_lock = 0;
uint8_t boot[4096];

int probe_impl(uint32_t handle, chimera_fat_probe_info *out) {
    if (!out) return CHM_BLOCK_EINVAL;
    chimera_block_info dev{};
    if (chimera_block_get_info(handle, &dev) != 0) return CHM_BLOCK_ENODEV;
    if (dev.sector_size < 512u || dev.sector_size > sizeof(boot) ||
        (dev.sector_size & (dev.sector_size - 1u))) return CHM_BLOCK_EINVAL;
    if (chimera_block_read(handle, 0, 1, boot) != 0) return CHM_BLOCK_EIO;
    if (boot[510] != 0x55 || boot[511] != 0xaa) return CHM_BLOCK_ENOTSUP;

    chimera_fat_probe_info result{};
    result.abi = CHIMERA_FAT_PROBE_ABI;
    result.sector_size = dev.sector_size;

    if (boot[3]=='E' && boot[4]=='X' && boot[5]=='F' && boot[6]=='A' &&
        boot[7]=='T' && boot[8]==' ' && boot[9]==' ' && boot[10]==' ') {
        const uint64_t volume_length =
            (uint64_t)le32(boot + 72) | ((uint64_t)le32(boot + 76) << 32);
        const uint32_t fat_offset = le32(boot + 80);
        const uint32_t fat_length = le32(boot + 84);
        const uint32_t heap_offset = le32(boot + 88);
        const uint32_t clusters = le32(boot + 92);
        const uint32_t root = le32(boot + 96);
        const uint8_t sector_shift = boot[108];
        const uint8_t cluster_shift = boot[109];
        if (sector_shift < 9 || sector_shift > 12 ||
            (1u << sector_shift) != dev.sector_size ||
            cluster_shift > 25u - sector_shift ||
            !volume_length || volume_length > dev.sector_count ||
            !fat_offset || !fat_length || !clusters || root < 2u ||
            (uint64_t)root >= (uint64_t)clusters + 2u || fat_offset >= heap_offset ||
            (uint64_t)fat_offset + fat_length > heap_offset ||
            heap_offset >= volume_length ||
            (uint64_t)heap_offset + ((uint64_t)clusters << cluster_shift) > volume_length ||
            (uint64_t)fat_length * dev.sector_size < ((uint64_t)clusters + 2u) * 4u)
            return CHM_BLOCK_EINVAL;
        result.kind = CHM_EXFAT;
        result.sectors_per_cluster = 1u << cluster_shift;
        result.total_sectors = volume_length;
        result.fat_start_sector = fat_offset;
        result.data_start_sector = heap_offset;
        result.cluster_count = clusters;
        result.root_cluster = root;
        *out = result;
        return 0;
    }

    const uint32_t bytes_per_sector = le16(boot + 11);
    const uint32_t sectors_per_cluster = boot[13];
    const uint32_t reserved = le16(boot + 14);
    const uint32_t fats = boot[16];
    const uint32_t root_entries = le16(boot + 17);
    const uint32_t total16 = le16(boot + 19);
    const uint32_t fat16 = le16(boot + 22);
    const uint32_t total32 = le32(boot + 32);
    const uint32_t fat32 = le32(boot + 36);
    const uint32_t total = total16 ? total16 : total32;
    const uint32_t fat_size = fat16 ? fat16 : fat32;
    if (bytes_per_sector != dev.sector_size ||
        bytes_per_sector < 512u || bytes_per_sector > 4096u ||
        !sectors_per_cluster || sectors_per_cluster > 128u ||
        (sectors_per_cluster & (sectors_per_cluster - 1u)) ||
        !reserved || (fats != 1u && fats != 2u) ||
        !total || !fat_size || total > dev.sector_count)
        return CHM_BLOCK_EINVAL;

    const uint64_t root_dir_sectors =
        ((uint64_t)root_entries * 32u + bytes_per_sector - 1u) / bytes_per_sector;
    const uint64_t fat_start = reserved;
    const uint64_t data_start = fat_start + (uint64_t)fats * fat_size + root_dir_sectors;
    if (data_start >= total) return CHM_BLOCK_EINVAL;
    const uint64_t clusters = (total - data_start) / sectors_per_cluster;
    const uint64_t fat_bytes = (uint64_t)fat_size * bytes_per_sector;
    uint32_t kind = clusters < 4085u ? CHM_FAT12 :
                    clusters < 65525u ? CHM_FAT16 : CHM_FAT32;
    if (kind == CHM_FAT32) {
        if (root_entries || fat16 || !fat32) return CHM_BLOCK_EINVAL;
        const uint32_t root = le32(boot + 44) & 0x0fffffffu;
        if (root < 2u || root >= clusters + 2u ||
            fat_bytes < ((clusters + 2u) * 4u))
            return CHM_BLOCK_EINVAL;
        result.root_cluster = root;
    } else {
        if (!root_entries || !fat16 ||
            fat_bytes < ((clusters + 2u) * (kind == CHM_FAT12 ? 3u : 4u) + 1u) / 2u)
            return CHM_BLOCK_EINVAL;
        result.root_cluster = 0;
    }
    result.kind = kind;
    result.sectors_per_cluster = sectors_per_cluster;
    result.total_sectors = total;
    result.fat_start_sector = fat_start;
    result.data_start_sector = data_start;
    result.cluster_count = clusters;
    *out = result;
    return 0;
}
}

extern "C" int chimera_fat_probe(uint32_t handle, chimera_fat_probe_info *out) {
    while (__sync_lock_test_and_set(&fat_probe_lock, 1u)) {}
    const int rc = probe_impl(handle, out);
    __sync_lock_release(&fat_probe_lock);
    return rc;
}
