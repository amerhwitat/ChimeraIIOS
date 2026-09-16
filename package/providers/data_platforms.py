"""Safe metadata for open-source database and data-platform packages."""
from dataclasses import dataclass
import platform, shutil

@dataclass(frozen=True)
class DataPackage:
    name: str
    command: str
    ecosystem: str
    platform: str

PACKAGES = [
    DataPackage("postgresql","postgresql","sql","all"),
    DataPackage("mariadb","mariadb-server","sql","all"),
    DataPackage("sqlite","sqlite3","sql","all"),
    DataPackage("duckdb","duckdb","sql","all"),
    DataPackage("cassandra","cassandra","nosql","all"),
    DataPackage("hadoop","hadoop","hadoop","all"),
    DataPackage("hive","hive","hadoop","all"),
    DataPackage("spark","spark","hadoop","all"),
    DataPackage("openstack-client","python3-openstackclient","openstack","all"),
]

def discover():
    system=platform.system().lower()
    return [{"name":p.name,"command":p.command,"ecosystem":p.ecosystem,"installed":bool(shutil.which(p.command.split()[0])),"platform":system} for p in PACKAGES]


def manager_commands():
    """Return provider commands only; callers must still request confirmation."""
    system=platform.system().lower()
    if system=="linux":
        return {"apt":["apt","install"],"dnf":["dnf","install"],"pacman":["pacman","-S"],"zypper":["zypper","install"],"apk":["apk","add"]}
    if system=="windows": return {"winget":["winget","install"]}
    if system=="darwin": return {"brew":["brew","install"]}
    return {}
