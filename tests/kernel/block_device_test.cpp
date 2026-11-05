#include "chimera/block_device.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

namespace {
uint8_t media[16u * 512u]{};
int reads = 0, writes = 0, flushes = 0;
int read_media(void *, uint64_t lba, uint32_t count, void *buffer) {
    ++reads;
    memcpy(buffer, media + lba * 512u, (size_t)count * 512u);
    return 0;
}
int write_media(void *, uint64_t lba, uint32_t count, const void *buffer) {
    ++writes;
    memcpy(media + lba * 512u, buffer, (size_t)count * 512u);
    return 0;
}
int flush_media(void *) { ++flushes; return 0; }
}

int main() {
    const chimera_block_ops ops{read_media, write_media, flush_media};
    uint32_t handle = 0;
    assert(chimera_block_register("host-test", 512u, 16u, 0u, &ops, nullptr, &handle) == 0);
    assert(handle != 0);
    chimera_block_info info{};
    assert(chimera_block_get_info(handle, &info) == 0);
    assert(info.abi == CHIMERA_BLOCK_ABI && info.sector_size == 512u);
    assert(info.sector_count == 16u && strcmp(info.name, "host-test") == 0);

    uint8_t input[512], output[512];
    memset(input, 0xA5, sizeof(input));
    memset(output, 0, sizeof(output));
    assert(chimera_block_write(handle, 3u, 1u, input) == 0);
    assert(chimera_block_read(handle, 3u, 1u, output) == 0);
    assert(memcmp(input, output, sizeof(input)) == 0);
    assert(chimera_block_read(handle, 16u, 1u, output) == CHM_BLOCK_EINVAL);
    assert(chimera_block_write(handle, 15u, 2u, input) == CHM_BLOCK_EINVAL);
    assert(chimera_block_flush(handle) == 0);
    assert(reads == 1 && writes == 1 && flushes == 1);

    uint32_t read_only = 0;
    const chimera_block_ops ro_ops{read_media, nullptr, nullptr};
    assert(chimera_block_register("readonly", 512u, 16u,
        CHIMERA_BLOCK_READ_ONLY, &ro_ops, nullptr, &read_only) == 0);
    assert(chimera_block_write(read_only, 0u, 1u, input) == CHM_BLOCK_ENOTSUP);
    assert(chimera_block_flush(read_only) == CHM_BLOCK_ENOTSUP);
    assert(chimera_block_unregister(read_only) == 0);
    assert(chimera_block_get_info(read_only, &info) == CHM_BLOCK_ENODEV);

    assert(chimera_block_unregister(handle) == 0);
    assert(chimera_block_read(handle, 0u, 1u, output) == CHM_BLOCK_ENODEV);
    assert(chimera_block_register("bad", 1000u, 1u, 0u, &ops, nullptr, &handle) == CHM_BLOCK_EINVAL);
    return 0;
}
