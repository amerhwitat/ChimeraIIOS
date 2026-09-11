from pathlib import Path

ROOT = Path(__file__).parents[2]

def test_boot_abi_headers_are_versioned():
    boot = (ROOT / 'boot/include/chimera/bootinfo.h').read_text()
    cpu = (ROOT / 'boot/include/chimera/cpu_profile.h').read_text()
    flags = (ROOT / 'boot/include/chimera/boot_flags.h').read_text()
    assert 'CHM_BOOTINFO_MAGIC' in boot
    assert 'CHM_BOOTINFO_VERSION 4u' in boot
    assert 'chm_cpu_profile_t' in cpu
    for name in ('CHM_BOOT_BIOS', 'CHM_BOOT_UEFI', 'CHM_BOOT_MULTIBOOT2'):
        assert name in flags

def test_bootinfo_contains_handoff_state():
    text = (ROOT / 'boot/include/chimera/bootinfo.h').read_text()
    for name in ('memory_map', 'acpi_rsdp', 'efi_system_table', 'initrd_addr', 'cmdline_addr', 'tpm_pcr_digest'):
        assert name in text
