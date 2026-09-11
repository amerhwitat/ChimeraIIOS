from iso_tool.application_discovery import discover_applications

def test_discovers_node_and_python_applications(tmp_path):
    (tmp_path/'package.json').write_text('{"name":"demo"}',encoding='utf-8');(tmp_path/'requirements.txt').write_text('requests\n',encoding='utf-8');result=discover_applications(tmp_path);ids={item['id'] for item in result['discovered']};assert 'nodejs' in ids;assert 'python' in ids;assert result['install_authorized'] is False

def test_package_install_requires_explicit_authorization(tmp_path):
    result=discover_applications(tmp_path);assert result['install_authorized'] is False;assert result['install_command'] is None
