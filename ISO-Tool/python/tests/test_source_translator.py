from pathlib import Path
from iso_tool.source_translator import translate

def test_translate_all_targets(tmp_path: Path):
    root=tmp_path/'src'; root.mkdir(); (root/'sample.py').write_text('import json\nclass Sample: pass\ndef run(x): return x\n',encoding='utf-8')
    out=tmp_path/'generated'; manifest=translate(root,out)
    assert len(manifest['modules']) == 1
    assert (out/'c'/'sample.c').exists()
    assert (out/'cpp'/'sample.cpp').exists()
    assert (out/'csharp'/'sample.cs').exists()
    assert (out/'java'/'sample.java').exists()
    assert (out/'parity-manifest.json').exists()
