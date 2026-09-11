from pathlib import Path
import json
ROOT=Path(__file__).parents[2]
def test_iso_layout_manifest():
    data=json.loads((ROOT/'boot/iso/iso-layout.json').read_text())
    assert data['filesystem']=='ISO9660'
    assert 'boot/spitfire' in data['directories']
    assert data['boot']['standard_efi_path']=='EFI/BOOT/BOOTX64.EFI'
def test_iso_builder_is_structured():
    text=(ROOT/'boot/iso/build-iso.sh').read_text()
    for token in ('prepare-layout.sh','validate-iso.py','grub-mkrescue','SHA256'):
        assert token in text
