#!/usr/bin/env python3
"""Static contract checks for the native Koronos ring-3 target consoles."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

kernel = read("kernel/core/koronos.cpp")
syscall = read("kernel/core/syscall.cpp")
compat = read("kernel/core/compat.cpp")
common = read("kernel/targets/init_common.h")
live = read("kernel/targets/live_init.c")
installer = read("kernel/targets/installer_init.c")
recovery = read("kernel/targets/recovery_init.c")
target_launch = read("kernel/core/target_launch.cpp")

assert "koronos_console_read_user" in kernel
assert "koronos_console_try_getchar" in kernel
assert 'sti; hlt; cli' in kernel
assert "case CHM_SYS_READ:" in syscall
assert "koronos_console_read_user(address, length)" in syscall
assert "case 0: return 8;" in compat  # Linux x86-64 read -> CHM_SYS_READ
assert "#define LINUX_X86_64_SYS_READ 0" in common
assert "static long init_read_line(" in common
# Every target prompt must outlive the bootstrap deadline. Keep PIT IRQ0 active
# because the current ring-3 console uses timer wakeups while polling PS/2 input.
readiness = target_launch.split("ready_seen=1;", 1)[1].split("return 1;", 1)[0]
assert "koronos_user_timeout_disarm_keep_timer();" in readiness
assert "if (active_target == TARGET_LIVE)" not in readiness

for source, prompt in ((live, "chimera> "), (installer, "installer> "), (recovery, "recovery> ")):
    assert prompt in source
    assert "init_read_line(line" in source
    assert 'init_text_equal(line, "help")' in source
    assert 'init_text_equal(line, "exit")' in source
    assert "init_emit_readiness(pid)" in source

assert "no disk writes performed" in installer
assert "no disks are writable" in installer
assert "read-only" in recovery
assert "repair not available" in recovery
assert "VFS, external ELF execution and graphics are not yet enabled" in live
print("Koronos live, installer and recovery ring-3 console contracts validated.")
