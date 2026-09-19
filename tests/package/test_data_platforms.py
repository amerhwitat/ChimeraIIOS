import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from package.providers.data_platforms import discover, manager_commands

rows=discover()
assert any(x['name']=='postgresql' for x in rows)
assert isinstance(manager_commands(), dict)
print('data platform package metadata: ok')
