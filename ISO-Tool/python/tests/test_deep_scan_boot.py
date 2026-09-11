from pathlib import Path
import tempfile
from iso_tool.tree_scanner import scan_tree
from iso_tool.builtin_boot_assembler import assemble_spit_fire

def test_recursive_tree_and_language_counts():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'src'/'nested').mkdir(parents=True);(root/'src'/'nested'/'main.cpp').write_text('int main(){}');(root/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)')
        result=scan_tree(root)
        assert result['summary']['files']==2
        assert result['summary']['languages']['C++']==1
        assert 'src/nested/main.cpp' in str(result['tree'])

def test_builtin_spit_fire_is_boot_sector():
    with tempfile.TemporaryDirectory() as td:
        out=assemble_spit_fire(Path(td)/'first_stage.bin');data=out.read_bytes();assert len(data)==512;assert data[-2:]==b'\x55\xAA'
