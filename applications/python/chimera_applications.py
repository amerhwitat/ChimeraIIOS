from dataclasses import dataclass
from pathlib import Path
import json
@dataclass(frozen=True)
class ApplicationDescriptor:
    id:str; category:str; upstream:str; spdx:str; platforms:tuple[str,...]; languages:tuple[str,...]; integration:str; sandbox:str

def load(path='applications/catalog.json'):
    return json.loads(Path(path).read_text(encoding='utf-8'))['applications']
def find(category, platform, path='applications/catalog.json'):
    return [x for x in load(path) if x['category']==category and platform in x['platforms']]
