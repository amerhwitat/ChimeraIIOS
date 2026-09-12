from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json

class ServiceState(str, Enum):
    INACTIVE='inactive'; STARTING='starting'; ACTIVE='active'; STOPPING='stopping'; FAILED='failed'

@dataclass(frozen=True)
class ServiceDescriptor:
    id: str
    platform: str
    backend: str
    capabilities: tuple[str,...]

def load_registry(path: str|Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding='utf-8'))['services']

def resolve(service_id: str, platform: str, path: str|Path='services/service_registry.json') -> ServiceDescriptor:
    for item in load_registry(path):
        if item['id']==service_id and platform in item['platforms']:
            return ServiceDescriptor(service_id, platform, item['backends'].get(platform, 'compatibility'), tuple(item['capabilities']))
    raise KeyError(f'unsupported service/platform: {service_id}/{platform}')

def can_transition(old: ServiceState, new: ServiceState) -> bool:
    return (old,new) in {(ServiceState.INACTIVE,ServiceState.STARTING),(ServiceState.STARTING,ServiceState.ACTIVE),(ServiceState.STARTING,ServiceState.FAILED),(ServiceState.ACTIVE,ServiceState.STOPPING),(ServiceState.STOPPING,ServiceState.INACTIVE),(ServiceState.FAILED,ServiceState.STARTING)}
