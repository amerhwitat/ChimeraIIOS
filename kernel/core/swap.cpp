#include <stdint.h>
#include <stddef.h>
#include "chimera/swap.h"

namespace {
constexpr uint32_t WORD_BITS = 32u;
static koronos_swap_backend g_backend{};
static uint32_t g_bitmap[KORONOS_SWAP_MAX_SLOTS / WORD_BITS]{};
static uint32_t g_checksums[KORONOS_SWAP_MAX_SLOTS]{};
static uint32_t g_slots = 0;
static uint32_t g_used = 0;
static uint32_t g_ready = 0;
static volatile uint32_t g_lock = 0;
static uint64_t g_writes = 0, g_reads = 0, g_checksum_failures = 0, g_io_failures = 0;
static void lock() { while (__sync_lock_test_and_set(&g_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&g_lock); }
static bool bit(uint32_t slot) { return (g_bitmap[slot / WORD_BITS] & (1u << (slot % WORD_BITS))) != 0; }
static void set_bit(uint32_t slot) { g_bitmap[slot / WORD_BITS] |= (1u << (slot % WORD_BITS)); }
static void clear_bit(uint32_t slot) { g_bitmap[slot / WORD_BITS] &= ~(1u << (slot % WORD_BITS)); }
static uint32_t checksum(const uint8_t *data, uint32_t size) {
    uint32_t crc = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < size; ++i) {
        crc ^= data[i];
        for (uint32_t b = 0; b < 8u; ++b)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}
static bool slot_offset(uint32_t slot, uint64_t *offset) {
    if (!offset || slot >= g_slots || slot > UINT64_MAX / KORONOS_SWAP_PAGE_SIZE) return false;
    *offset = static_cast<uint64_t>(slot) * KORONOS_SWAP_PAGE_SIZE;
    return *offset <= g_backend.capacity_bytes &&
           KORONOS_SWAP_PAGE_SIZE <= g_backend.capacity_bytes - *offset;
}
}

extern "C" int koronos_swap_init(const koronos_swap_backend *backend) {
    lock();
    g_ready = 0; g_slots = 0; g_used = 0;
    for (uint32_t i = 0; i < KORONOS_SWAP_MAX_SLOTS / WORD_BITS; ++i) g_bitmap[i] = 0;
    for (uint32_t i = 0; i < KORONOS_SWAP_MAX_SLOTS; ++i) g_checksums[i] = 0;
    g_writes = g_reads = g_checksum_failures = g_io_failures = 0;
    if (!backend || backend->abi != KORONOS_SWAP_ABI ||
        backend->page_size != KORONOS_SWAP_PAGE_SIZE || !backend->read || !backend->write ||
        backend->capacity_bytes < KORONOS_SWAP_PAGE_SIZE) {
        unlock(); return -1;
    }
    uint64_t slots64 = backend->capacity_bytes / KORONOS_SWAP_PAGE_SIZE;
    if (slots64 > KORONOS_SWAP_MAX_SLOTS) slots64 = KORONOS_SWAP_MAX_SLOTS;
    g_backend = *backend;
    g_slots = static_cast<uint32_t>(slots64);
    g_ready = g_slots != 0;
    unlock();
    return g_ready ? 0 : -2;
}

extern "C" int koronos_swap_store(const void *page, uint32_t *slot_out) {
    if (!page || !slot_out) return -1;
    lock();
    if (!g_ready) { unlock(); return -2; }
    uint32_t slot = 0;
    while (slot < g_slots && bit(slot)) ++slot;
    if (slot == g_slots) { unlock(); return -3; }
    uint64_t offset = 0;
    if (!slot_offset(slot, &offset)) { unlock(); return -4; }
    // Reserve the slot before I/O so concurrent writers cannot alias it.
    set_bit(slot); ++g_used;
    const uint32_t sum = checksum(static_cast<const uint8_t *>(page), KORONOS_SWAP_PAGE_SIZE);
    if (g_backend.write(g_backend.context, offset, page, KORONOS_SWAP_PAGE_SIZE) != 0) {
        clear_bit(slot); --g_used; ++g_io_failures; unlock(); return -5;
    }
    g_checksums[slot] = sum;
    ++g_writes; *slot_out = slot;
    unlock();
    return 0;
}

extern "C" int koronos_swap_load(uint32_t slot, void *page_out) {
    if (!page_out) return -1;
    lock();
    if (!g_ready) { unlock(); return -2; }
    if (slot >= g_slots || !bit(slot)) { unlock(); return -3; }
    uint64_t offset = 0;
    if (!slot_offset(slot, &offset)) { unlock(); return -4; }
    if (g_backend.read(g_backend.context, offset, page_out, KORONOS_SWAP_PAGE_SIZE) != 0) {
        ++g_io_failures; unlock(); return -5;
    }
    if (checksum(static_cast<const uint8_t *>(page_out), KORONOS_SWAP_PAGE_SIZE) != g_checksums[slot]) {
        ++g_checksum_failures; unlock(); return -6;
    }
    ++g_reads;
    unlock();
    return 0;
}

extern "C" int koronos_swap_release(uint32_t slot) {
    lock();
    if (!g_ready) { unlock(); return -1; }
    if (slot >= g_slots || !bit(slot)) { unlock(); return -2; }
    clear_bit(slot); g_checksums[slot] = 0; --g_used;
    unlock();
    return 0;
}

extern "C" int koronos_swap_get_snapshot(koronos_swap_snapshot *out) {
    if (!out) return -1;
    lock();
    out->abi = KORONOS_SWAP_ABI; out->initialized = g_ready; out->slot_count = g_slots;
    out->used_slots = g_used; out->page_size = KORONOS_SWAP_PAGE_SIZE; out->reserved = 0;
    out->capacity_bytes = static_cast<uint64_t>(g_slots) * KORONOS_SWAP_PAGE_SIZE;
    out->writes = g_writes; out->reads = g_reads;
    out->checksum_failures = g_checksum_failures; out->io_failures = g_io_failures;
    unlock();
    return 0;
}

extern "C" int koronos_swap_self_test(void) {
    koronos_swap_snapshot snapshot{};
    if (koronos_swap_get_snapshot(&snapshot) != 0) return -1;
    if (!snapshot.initialized) return -2;
    if (snapshot.page_size != KORONOS_SWAP_PAGE_SIZE ||
        snapshot.slot_count == 0 || snapshot.used_slots > snapshot.slot_count) return -3;
    return 0;
}
