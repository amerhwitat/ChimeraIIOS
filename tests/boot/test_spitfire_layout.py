from pathlib import Path
import re
ROOT = Path(__file__).parents[2]
def test_spitfire_sources_exist():
    for name in ('sf0_mbr.asm','sf1_longmode.asm','sf2_loader.cpp','sf2_loader.h','spitfire.ld'):
        assert (ROOT/'boot/spitfire'/name).exists()
def test_sf0_has_signature_and_int13_extensions():
    text=(ROOT/'boot/spitfire/sf0_mbr.asm').read_text()
    assert 'int 0x13' in text and '0x42' in text and '0xAA55' in text
    assert re.search(r'times\s+510-\(\$-\$\$\)', text)
