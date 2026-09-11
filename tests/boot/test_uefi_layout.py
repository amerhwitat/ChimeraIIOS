from pathlib import Path
ROOT=Path(__file__).parents[2]
def test_uefi_contract():
    h=(ROOT/'boot/spitfire/sfu_uefi.h').read_text()
    c=(ROOT/'boot/spitfire/sfu_uefi.c').read_text()
    assert 'efi_main' in h and 'efi_main' in c
    assert 'BOOTX64.EFI' in (ROOT/'boot/spitfire/efi/README.md').read_text()
