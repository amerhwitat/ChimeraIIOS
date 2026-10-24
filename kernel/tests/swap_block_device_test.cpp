#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "chimera/block_device.h"
#include "chimera/swap.h"

static uint8_t disk[8u * KORONOS_SWAP_PAGE_SIZE];
static int flush_fail = 0;
static int device_present = 1;
static uint32_t flush_calls = 0;
static int read_device(void *, uint64_t offset, void *buffer, uint64_t length) {
    if (!buffer || offset > sizeof(disk) || length > sizeof(disk) - offset) return -1;
    memcpy(buffer, disk + offset, static_cast<size_t>(length)); return 0;
}
static int write_device(void *, uint64_t offset, const void *buffer, uint64_t length) {
    if (!buffer || offset > sizeof(disk) || length > sizeof(disk) - offset) return -1;
    memcpy(disk + offset, buffer, static_cast<size_t>(length)); return 0;
}
static int flush_device(void *) { ++flush_calls; return flush_fail ? -1 : 0; }
static int present_device(void *) { return device_present; }
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)

int main(void) {
    chimera_block_device device{
        CHIMERA_BLOCK_DEVICE_ABI, 512u, sizeof(disk), 0u, nullptr,
        read_device, write_device, flush_device, present_device
    };
    koronos_swap_snapshot snapshot{};
    CHECK(koronos_swap_get_snapshot(&snapshot) == 0 && snapshot.initialized == 0u);

    CHECK(koronos_swap_init_block_extent(&device, 1u, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    CHECK(koronos_swap_get_snapshot(&snapshot) == 0 && snapshot.initialized == 0u);

    device.logical_block_size = 8192u;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.logical_block_size = 512u;
    CHECK(koronos_swap_get_snapshot(&snapshot) == 0 && snapshot.initialized == 0u);

    device.flags = CHIMERA_BLOCK_READ_ONLY;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.flags = 0u;

    device_present = 0;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device_present = 1;

    auto saved_flush = device.flush;
    device.flush = nullptr;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.flush = saved_flush;

    auto saved_write = device.write;
    device.write = nullptr;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.write = saved_write;

    auto saved_read = device.read;
    device.read = nullptr;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.read = saved_read;

    device.abi = 0u;
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);
    device.abi = CHIMERA_BLOCK_DEVICE_ABI;

    CHECK(koronos_swap_init_block_extent(&device, sizeof(disk), KORONOS_SWAP_PAGE_SIZE) != 0);
    CHECK(koronos_swap_get_snapshot(&snapshot) == 0 && snapshot.initialized == 0u);
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) == 0);

    uint8_t input[KORONOS_SWAP_PAGE_SIZE], output[KORONOS_SWAP_PAGE_SIZE];
    for (uint32_t i = 0; i < sizeof(input); ++i) input[i] = static_cast<uint8_t>((i * 19u + 3u) & 0xffu);
    uint32_t slot = KORONOS_SWAP_SLOT_INVALID;
    flush_fail = 1;
    CHECK(koronos_swap_store(input, &slot) != 0);
    CHECK(koronos_swap_get_snapshot(&snapshot) == 0 && snapshot.used_slots == 0u && snapshot.io_failures == 1u);
    flush_fail = 0;
    CHECK(koronos_swap_store(input, &slot) == 0 && slot == 0u);
    CHECK(memcmp(disk + KORONOS_SWAP_PAGE_SIZE, input, sizeof(input)) == 0);
    memset(output, 0, sizeof(output));
    CHECK(koronos_swap_load(slot, output) == 0 && memcmp(input, output, sizeof(input)) == 0);
    CHECK(koronos_swap_release(slot) == 0);
    CHECK(flush_calls == 2u);
    CHECK(koronos_swap_init_block_extent(&device, KORONOS_SWAP_PAGE_SIZE, 3u * KORONOS_SWAP_PAGE_SIZE) != 0);

    puts("Koronos block-device swap adapter tests passed");
    return 0;
}
