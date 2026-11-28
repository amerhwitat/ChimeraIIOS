#include "init_common.h"

/* Native Live target: a ring-3 text console session. This is a freestanding
 * init payload, not a desktop shell; no graphical session is started. */
__attribute__((noreturn, used)) void _start(void) {
    init_int80();

    const long pid = init_getpid();
    if (pid <= 0) init_exit(1);

    /* Exercise the actual ring-3 -> Linux-ABI -> Koronos VFS path before
       announcing userspace readiness. A failure must not emit a ready marker. */
    char release[512] = {};
    const char release_expected[] = "NAME=\"Chimera II OS\"";
    const long release_fd = init_open("/etc/os-release", 0, 0);
    if (release_fd < 0) {
        init_writestr("LIVE: FAIL open /etc/os-release\n");
        init_exit(20);
    }
    const long release_bytes = init_read(release_fd, release, sizeof(release)-1);
    const long release_close = init_close(release_fd);
    if (release_bytes <= 0 || release_close != 0 ||
        !init_contains(release, release_bytes, release_expected,
                       (long)sizeof(release_expected)-1)) {
        init_writestr("LIVE: FAIL read/verify /etc/os-release\n");
        init_exit(21);
    }
    init_writestr("LIVE: initramfs /etc/os-release open/read/close PASS\n");

    const char tmp_path[] = "/tmp/koronos-live-selftest";
    const char tmp_payload[] = "Koronos tmpfs ring3 roundtrip";
    char tmp_readback[sizeof(tmp_payload)] = {};
    const long tmp_fd = init_open(tmp_path, 2|0x40|0x80, 0600); /* O_RDWR|O_CREAT|O_EXCL */
    if (tmp_fd < 0) {
        init_writestr("LIVE: FAIL create /tmp self-test file\n");
        init_exit(22);
    }
    const long tmp_written = init_write(tmp_fd, tmp_payload, (long)sizeof(tmp_payload)-1);
    const long tmp_seek = init_lseek(tmp_fd, 0, 0); /* SEEK_SET */
    const long tmp_read = init_read(tmp_fd, tmp_readback, (long)sizeof(tmp_payload)-1);
    const long tmp_close = init_close(tmp_fd);
    if (tmp_written != (long)sizeof(tmp_payload)-1 || tmp_seek != 0 ||
        tmp_read != (long)sizeof(tmp_payload)-1 || tmp_close != 0 ||
        !init_bytes_equal(tmp_payload, tmp_readback, (long)sizeof(tmp_payload)-1)) {
        init_writestr("LIVE: FAIL /tmp write/seek/read roundtrip\n");
        init_exit(23);
    }
    init_writestr("LIVE: /tmp write/seek/read roundtrip PASS\n");

    init_emit_readiness(pid);

    init_writestr("LIVE: native console session banner\n");
    init_writestr("LIVE: ring-3 text console active (no graphical session)\n");

    /* Exercise the mapped yield ABI without depending on preemption. */
    init_yield();
    init_writestr("LIVE: scheduler yield returned\n");

    /* Remain resident as PID 1; do not tear down this process after readiness. */
    init_pid1_wait();
}
