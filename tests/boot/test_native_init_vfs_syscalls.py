from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_linux_lseek_translation_and_descriptor_permissions_are_wired():
    compat = (ROOT / "kernel/core/compat.cpp").read_text()
    syscall = (ROOT / "kernel/core/syscall.cpp").read_text()
    abi = (ROOT / "kernel/include/chimera/syscall.h").read_text()
    assert "case 8: return 7; // lseek" in compat
    assert "CHM_SYS_SEEK = 7" in abi
    assert "case CHM_SYS_SEEK:" in syscall
    assert "entry.readable" in syscall
    assert "entry.writable" in syscall
    assert "seek_initramfs_file" in syscall


def test_live_init_checks_filesystem_before_readiness():
    init = (ROOT / "kernel/targets/live_init.c").read_text()
    build = (ROOT / "tools/build-live-boot-binaries.sh").read_text()
    assert 'init_open("/etc/os-release", 0, 0)' in init
    assert "init_read(release_fd" in init
    assert "init_close(release_fd)" in init
    assert "init_open(tmp_path, 2|0x40|0x80, 0600)" in init
    assert "init_lseek(tmp_fd, 0, 0)" in init
    assert "init_read(tmp_fd" in init
    assert "LIVE: /tmp write/seek/read roundtrip PASS" in init
    assert 'init_emit_readiness(pid);' in init
    assert init.index('init_writestr("LIVE: /tmp write/seek/read roundtrip PASS\\n");') < init.index("init_emit_readiness(pid);")
    assert 'cat > "$INIT/etc/os-release"' in build
    assert 'find . -print0 | cpio --null -o -H newc' in build


def test_ring3_linux_syscall_helpers_use_linux_x86_64_numbers():
    common = (ROOT / "kernel/targets/init_common.h").read_text()
    assert "#define LINUX_X86_64_SYS_READ 0" in common
    assert "#define LINUX_X86_64_SYS_OPEN 2" in common
    assert "#define LINUX_X86_64_SYS_CLOSE 3" in common
    assert "#define LINUX_X86_64_SYS_LSEEK 8" in common
    assert "init_syscall3(LINUX_X86_64_SYS_CLOSE, fd, 0, 0)" in common

def test_single_cpu_boot_does_not_wait_for_a_nonexistent_ap():
    smp = (ROOT / "kernel/core/smp.cpp").read_text()
    header = (ROOT / "kernel/include/chimera/smp.h").read_text()
    harness = (ROOT / "tools/boot/run-qemu-live-vfs.py").read_text()
    assert "logical_processor_count() < 2u" in smp
    assert "KORONOS_SMP_SELFTEST_SKIPPED" in smp
    assert "KORONOS_SMP_SELFTEST_SKIPPED" in header
    assert '"-smp", "1"' in harness
    grub = (ROOT / "boot/iso/grub.cfg").read_text()
    assert "terminal_input serial console" in grub
