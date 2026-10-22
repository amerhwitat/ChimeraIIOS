#include "chimera/block.h"
#include <stdio.h>
#include <string.h>

struct Disk { unsigned char bytes[8 * 512]; unsigned flushes; };
static int read_disk(void *ctx, uint64_t lba, uint32_t count, void *buffer) {
    Disk *d = static_cast<Disk *>(ctx);
    memcpy(buffer, d->bytes + lba * 512, count * 512);
    return 0;
}
static int write_disk(void *ctx, uint64_t lba, uint32_t count, const void *buffer) {
    Disk *d = static_cast<Disk *>(ctx);
    memcpy(d->bytes + lba * 512, buffer, count * 512);
    return 0;
}
static int flush_disk(void *ctx) { ++static_cast<Disk *>(ctx)->flushes; return 0; }
static int fail_read(void *, uint64_t, uint32_t, void *) { return -1; }
static int fail_write(void *, uint64_t, uint32_t, const void *) { return -1; }
static int fail(const char *m) { fprintf(stderr, "FAIL: %s\n", m); return 1; }

int main() {
    Disk disk{};
    const chimera_block_ops ops{read_disk, write_disk, flush_disk};
    const chimera_block_device dev{7, 512, 8, &ops, &disk};
    unsigned char in[512], out[512];
    memset(in, 0xA5, sizeof(in));
    if (chimera_block_register(&dev) != CHIMERA_BLOCK_OK) return fail("register");
    if (chimera_block_register(&dev) != CHIMERA_BLOCK_EINVAL) return fail("duplicate id");
    if (chimera_block_device_count() != 1) return fail("count");
    if (chimera_block_write(7, 2, 1, in) != CHIMERA_BLOCK_OK) return fail("write");
    memset(out, 0, sizeof(out));
    if (chimera_block_read(7, 2, 1, out) != CHIMERA_BLOCK_OK) return fail("read");
    if (memcmp(in, out, sizeof(in)) != 0) return fail("round trip");
    if (chimera_block_read(7, 8, 1, out) != CHIMERA_BLOCK_ERANGE) return fail("end bound");
    if (chimera_block_read(7, 7, 2, out) != CHIMERA_BLOCK_ERANGE) return fail("cross-boundary");
    if (chimera_block_read(7, 0, 0, out) != CHIMERA_BLOCK_EINVAL) return fail("zero length");
    if (chimera_block_read(99, 0, 1, out) != CHIMERA_BLOCK_ENODEV) return fail("unknown device");
    if (chimera_block_flush(7) != CHIMERA_BLOCK_OK || disk.flushes != 1) return fail("flush");
    if (chimera_block_unregister(7) != CHIMERA_BLOCK_OK) return fail("unregister");
    if (chimera_block_read(7, 0, 1, out) != CHIMERA_BLOCK_ENODEV) return fail("unregistered device");

    const chimera_block_device bad_256{8, 256, 8, &ops, &disk};
    const chimera_block_device bad_768{8, 768, 8, &ops, &disk};
    const chimera_block_device bad_8192{8, 8192, 8, &ops, &disk};
    if (chimera_block_register(&bad_256) != CHIMERA_BLOCK_EINVAL) return fail("sector size below supported minimum");
    if (chimera_block_register(&bad_768) != CHIMERA_BLOCK_EINVAL) return fail("non-power-of-two sector size");
    if (chimera_block_register(&bad_8192) != CHIMERA_BLOCK_EINVAL) return fail("sector size above supported maximum");

    const chimera_block_ops no_flush_ops{read_disk, write_disk, nullptr};
    const chimera_block_device no_flush{8, 512, 8, &no_flush_ops, &disk};
    if (chimera_block_register(&no_flush) != CHIMERA_BLOCK_OK) return fail("register device without flush");
    if (chimera_block_flush(8) != CHIMERA_BLOCK_ENOTSUP) return fail("missing flush reports unsupported");
    if (chimera_block_unregister(8) != CHIMERA_BLOCK_OK) return fail("unregister device without flush");

    const chimera_block_ops failing_ops{fail_read, fail_write, flush_disk};
    const chimera_block_device failing{9, 512, 8, &failing_ops, &disk};
    if (chimera_block_register(&failing) != CHIMERA_BLOCK_OK) return fail("register failing transport");
    if (chimera_block_read(9, 0, 1, out) != CHIMERA_BLOCK_EIO) return fail("read transport error maps to EIO");
    if (chimera_block_write(9, 0, 1, in) != CHIMERA_BLOCK_EIO) return fail("write transport error maps to EIO");
    if (chimera_block_unregister(9) != CHIMERA_BLOCK_OK) return fail("unregister failing transport");

    puts("PASS: block API enforces registration, sector geometry, bounded I/O, transport errors, flush capability, and unregister contracts");
    return 0;
}
