#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "chimera/swap.h"

static uint8_t disk[KORONOS_SWAP_MAX_SLOTS * KORONOS_SWAP_PAGE_SIZE];
static int fail_read = 0, fail_write = 0;
static int callback_lock_probe() {
    // Backend callbacks must not run while the swap metadata spinlock is held.
    koronos_swap_snapshot snapshot{};
    return koronos_swap_get_snapshot(&snapshot);
}
static int rd(void *, uint64_t off, void *buf, uint32_t len) {
    if (callback_lock_probe() != 0 || fail_read || off > sizeof(disk) || len > sizeof(disk) - off) return -1;
    memcpy(buf, disk + off, len); return 0;
}
static int wr(void *, uint64_t off, const void *buf, uint32_t len) {
    if (callback_lock_probe() != 0 || fail_write || off > sizeof(disk) || len > sizeof(disk) - off) return -1;
    memcpy(disk + off, buf, len); return 0;
}
#define CHECK(x) do { if (!(x)) { fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #x); return 1; } } while (0)
int main(void) {
    koronos_swap_backend b{KORONOS_SWAP_ABI, KORONOS_SWAP_PAGE_SIZE, sizeof(disk), rd, wr, nullptr};
    CHECK(koronos_swap_init(nullptr) != 0);
    CHECK(koronos_swap_init(&b) == 0);
    CHECK(koronos_swap_self_test() == 0);
    uint8_t in[KORONOS_SWAP_PAGE_SIZE], out[KORONOS_SWAP_PAGE_SIZE];
    for (uint32_t i=0;i<sizeof(in);++i) in[i]=(uint8_t)((i*37u+11u)&0xffu);
    uint32_t slot=KORONOS_SWAP_SLOT_INVALID;
    CHECK(koronos_swap_store(in,&slot)==0 && slot==0);
    CHECK(koronos_swap_init(&b)!=0); // never discard owned swap slots by reinitializing
    memset(out,0,sizeof(out)); CHECK(koronos_swap_load(slot,out)==0);
    CHECK(memcmp(in,out,sizeof(in))==0);
    CHECK(koronos_swap_release(slot)==0);
    CHECK(koronos_swap_load(slot,out)!=0);
    fail_write=1; CHECK(koronos_swap_store(in,&slot)!=0); fail_write=0;
    CHECK(koronos_swap_store(in,&slot)==0);
    disk[(uint64_t)slot*KORONOS_SWAP_PAGE_SIZE+7u]^=0x80u;
    CHECK(koronos_swap_load(slot,out)!=0);
    koronos_swap_snapshot s{}; CHECK(koronos_swap_get_snapshot(&s)==0);
    CHECK(s.checksum_failures==1 && s.used_slots==1 && s.writes==2 && s.reads==1);
    CHECK(koronos_swap_release(slot)==0);

    // Explicitly test capacity exhaustion and repeated reuse with a tiny
    // backend; capacity is the validated device extent, not the host buffer.
    koronos_swap_backend tiny=b;
    tiny.capacity_bytes=2u*KORONOS_SWAP_PAGE_SIZE;
    CHECK(koronos_swap_init(&tiny)==0);
    uint32_t a=KORONOS_SWAP_SLOT_INVALID, z=KORONOS_SWAP_SLOT_INVALID, extra=KORONOS_SWAP_SLOT_INVALID;
    CHECK(koronos_swap_store(in,&a)==0 && a==0);
    CHECK(koronos_swap_store(in,&z)==0 && z==1);
    CHECK(koronos_swap_store(in,&extra)!=0);
    CHECK(koronos_swap_release(a)==0 && koronos_swap_release(z)==0);
    for (uint32_t cycle=0; cycle<8; ++cycle) {
        CHECK(koronos_swap_store(in,&a)==0);
        CHECK(koronos_swap_load(a,out)==0 && memcmp(in,out,sizeof(in))==0);
        CHECK(koronos_swap_release(a)==0);
    }
    CHECK(koronos_swap_get_snapshot(&s)==0 && s.used_slots==0 && s.writes==10 && s.reads==8);
    puts("Koronos swap backend tests passed");
    return 0;
}
