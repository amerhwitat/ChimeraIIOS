from pathlib import Path
ROOT=Path(__file__).parents[2]
def test_koronos_contract():
    assert 'KORONOS_READY' in (ROOT/'kernel/core/boot_entry.cpp').read_text()
    assert '_start' in (ROOT/'kernel/arch/x86_64/entry.asm').read_text()
    assert 'ENTRY(_start)' in (ROOT/'kernel/arch/x86_64/koronos.ld').read_text()
    assert 'chm_bootinfo_t' in (ROOT/'kernel/include/chimera/kernel_entry.h').read_text()
