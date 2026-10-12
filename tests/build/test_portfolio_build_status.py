from pathlib import Path

from tools.portfolio import build_portfolio


def test_missing_build_tool_is_reported_as_failure(tmp_path, monkeypatch):
    source = tmp_path / 'src'
    source.mkdir()
    (source / 'CMakeLists.txt').write_text('project(test)\n', encoding='utf-8')
    monkeypatch.setattr(build_portfolio.shutil, 'which', lambda _name: None)
    result = build_portfolio.build_one('test-repo', source, tmp_path / 'out', [])
    assert result['status'] == 'build-failed'
    assert result['failures'][0]['reason'] == 'missing-tool'


def test_python_only_project_is_not_mislabeled_as_compiled(tmp_path, monkeypatch):
    source = tmp_path / 'src'
    source.mkdir()
    (source / 'example.py').write_text('value = 1\n', encoding='utf-8')
    monkeypatch.setattr(build_portfolio.shutil, 'which', lambda _name: None)
    result = build_portfolio.build_one('test-repo', source, tmp_path / 'out', [])
    assert result['status'] == 'syntax-checked'
    assert result['status'] != 'built'
    assert result['python_files_checked'] == 1
