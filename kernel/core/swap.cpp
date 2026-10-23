#include <stdint.h>
#include <stddef.h>
#include "chimera/swap.h"

namespace {
enum SlotState : uint8_t { SLOT_FREE = 0, SLOT_WRITING = 1, SLOT_USED = 2, SLOT_READING = 3 };
static koronos_swap_backend g_backend{};
static uint8_t g_states[KORONOS_SWAP_MAX_SLOTS]{};
static uint32_t g_checksums[KORONOS_SWAP_MAX_SLOTS]{};
static uint32_t g_slots = 0;
static uint32_t g_used = 0;
static uint32_t g_ready = 0;
static uint32_t g_active_ops = 0;
static volatile uint32_t g_lock = 0;
static uint64_t g_writes = 0, g_reads = 0, g_checksum_failures = 0, g_io_failures = 0;
static void lock() { while (__sync_lock_test_and_set(&g_lock, 1u)) {} }
static void unlock() { __sync_lock_release(&g_lock); }
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
    // Never replace/reset backend metadata while an operation is outside the
    // lock performing potentially blocking storage I/O.
    if (g_active_ops != 0 || (g_ready && g_used != 0u)) { unlock(); return -3; }
    if (!backend || backend->abi != KORONOS_SWAP_ABI ||
        backend->page_size != KORONOS_SWAP_PAGE_SIZE || !backend->read || !backend->write ||
        backend->capacity_bytes < KORONOS_SWAP_PAGE_SIZE) {
        unlock(); return -1;
    }
    uint64_t slots64 = backend->capacity_bytes / KORONOS_SWAP_PAGE_SIZE;
    if (slots64 > KORONOS_SWAP_MAX_SLOTS) slots64 = KORONOS_SWAP_MAX_SLOTS;
    if (slots64 == 0) { unlock(); return -2; }
    g_ready = 0;
    g_slots = 0; g_used = 0;
    for (uint32_t i = 0; i < KORONOS_SWAP_MAX_SLOTS; ++i) {
        g_states[i] = SLOT_FREE;
        g_checksums[i] = 0;
    }
    g_writes = g_reads = g_checksum_failures = g_io_failures = 0;
    g_backend = *backend;
    g_slots = static_cast<uint32_t>(slots64);
    g_ready = 1;
    unlock();
    return 0;
}

extern "C" int koronos_swap_store(const void *page, uint32_t *slot_out) {
    if (!page || !slot_out) return -1;
    lock();
    if (!g_ready) { unlock(); return -2; }
    uint32_t slot = 0;
    while (slot < g_slots && g_states[slot] != SLOT_FREE) ++slot;
    if (slot == g_slots) { unlock(); return -3; }
    uint64_t offset = 0;
    if (!slot_offset(slot, &offset)) { unlock(); return -4; }
    // Reserve under lock, then release the spinlock before backend I/O.
    g_states[slot] = SLOT_WRITING;
    ++g_used; ++g_active_ops;
    const koronos_swap_backend backend = g_backend;
    unlock();

    const uint32_t sum = checksum(static_cast<const uint8_t *>(page), KORONOS_SWAP_PAGE_SIZE);
    const int io_rc = backend.write(backend.context, offset, page, KORONOS_SWAP_PAGE_SIZE);

    lock();
    --g_active_ops;
    if (io_rc != 0) {
        g_states[slot] = SLOT_FREE; --g_used;
        ++g_io_failures;
        unlock(); return -5;
    }
    g_checksums[slot] = sum;
    g_states[slot] = SLOT_USED;
    ++g_writes; *slot_out = slot;
    unlock();
    return 0;
}

extern "C" int koronos_swap_load(uint32_t slot, void *page_out) {
    if (!page_out) return -1;
    lock();
    if (!g_ready) { unlock(); return -2; }
    if (slot >= g_slots || g_states[slot] != SLOT_USED) { unlock(); return -3; }
    uint64_t offset = 0;
    if (!slot_offset(slot, &offset)) { unlock(); return -4; }
    g_states[slot] = SLOT_READING; ++g_active_ops;
    const koronos_swap_backend backend = g_backend;
    const uint32_t expected_sum = g_checksums[slot];
    unlock();

    const int io_rc = backend.read(backend.context, offset, page_out, KORONOS_SWAP_PAGE_SIZE);
    const bool checksum_ok = io_rc == 0 &&
        checksum(static_cast<const uint8_t *>(page_out), KORONOS_SWAP_PAGE_SIZE) == expected_sum;

    lock();
    --g_active_ops;
    g_states[slot] = SLOT_USED;
    if (io_rc != 0) { ++g_io_failures; unlock(); return -5; }
    if (!checksum_ok) { ++g_checksum_failures; unlock(); return -6; }
    ++g_reads;
    unlock();
    return 0;
}

extern "C" int koronos_swap_release(uint32_t slot) {
    lock();
    if (!g_ready) { unlock(); return -1; }
    if (slot >= g_slots || g_states[slot] == SLOT_FREE) { unlock(); return -2; }
    // A writer/reader owns this slot until its I/O completes. The caller must
    // retry rather than releasing storage which is currently in flight.
    if (g_states[slot] != SLOT_USED) { unlock(); return -3; }
    g_states[slot] = SLOT_FREE; g_checksums[slot] = 0; --g_used;
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
