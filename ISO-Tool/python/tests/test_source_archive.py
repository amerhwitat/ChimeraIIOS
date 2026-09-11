from pathlib import Path
import hashlib, zipfile
from iso_tool.github_source import classify_source, is_source_reference
from iso_tool.source_archive import extract_archive, sha256_file

def test_classify_direct_zip_archive(tmp_path):
    archive=tmp_path/'sample.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('project/CMakeLists.txt','cmake_minimum_required(VERSION 3.20)')
    assert classify_source(str(archive))=='archive'; assert is_source_reference(str(archive))
def test_extract_archive_rejects_path_traversal(tmp_path):
    archive=tmp_path/'unsafe.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('../escape.txt','unsafe')
    try:extract_archive(archive,tmp_path/'out')
    except ValueError as exc:assert 'traversal' in str(exc).lower()
    else:raise AssertionError('unsafe archive was accepted')
def test_sha256_matches_file(tmp_path):
    p=tmp_path/'x.bin';p.write_bytes(b'chimera');assert sha256_file(p)==hashlib.sha256(b'chimera').hexdigest()
