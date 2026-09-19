#!/usr/bin/env python3
"""Provider-neutral Chimera package manager with data-platform metadata.

The package manager discovers through explicit adapters and never bypasses
vendor licensing, signatures, authentication, or platform restrictions.
"""
import argparse, json, platform, shutil, subprocess
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from providers.data_platforms import discover as discover_data, manager_commands
except ImportError:
    from package.providers.data_platforms import discover as discover_data, manager_commands

@dataclass
class Package:
    name: str
    version: str
    source: str
    platform: str
    install_hint: str
    signed: bool = False

class Backend:
    name='backend'
    def search(self, query): return []
    def install(self, package): raise RuntimeError(f'{self.name}: explicit adapter required')

class LinuxBackend(Backend):
    name='linux'
    def search(self, query):
        out=[]
        if shutil.which('apt-cache'):
            p=subprocess.run(['apt-cache','search',query],text=True,capture_output=True,check=False)
            for line in p.stdout.splitlines()[:20]:
                if ' - ' in line:
                    n,_=line.split(' - ',1); out.append(Package(n,'repo',self.name,platform.system(),'apt install '+n))
        if shutil.which('dnf'):
            p=subprocess.run(['dnf','repoquery','--qf','%{name}\t%{version}',query],text=True,capture_output=True,check=False)
            for line in p.stdout.splitlines()[:20]:
                parts=line.split('\t',1)
                if parts: out.append(Package(parts[0],parts[1] if len(parts)>1 else 'repo',self.name,platform.system(),'dnf install '+parts[0]))
        return out

class RegistryBackend(Backend):
    def __init__(self,name,source,platform_name): self.name=name; self.source=source; self.platform_name=platform_name
    def search(self,query): return [Package(query,'remote','catalog',self.platform_name,'external-provider-required',False)]

BACKENDS={'linux':LinuxBackend(), 'windows':RegistryBackend('windows-store','Microsoft Store / WinGet-compatible provider','Windows'), 'macos':RegistryBackend('macos','App Store / signed package provider','Darwin')}

def search(query):
    result=[]
    for backend in BACKENDS.values(): result.extend(backend.search(query))
    return result

def main():
    ap=argparse.ArgumentParser(prog='chimera-pkg')
    sub=ap.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('search'); s.add_argument('query')
    i=sub.add_parser('install'); i.add_argument('package'); i.add_argument('--source',choices=list(BACKENDS),default='linux'); i.add_argument('--yes',action='store_true')
    sub.add_parser('sources')
    sub.add_parser('data')
    args=ap.parse_args()
    if args.cmd=='sources':
        print(json.dumps({'backends':{k:v.name for k,v in BACKENDS.items()},'native_managers':manager_commands()},indent=2)); return
    if args.cmd=='data':
        print(json.dumps(discover_data(),indent=2)); return
    if args.cmd=='search':
        print(json.dumps([asdict(x) for x in search(args.query)],indent=2)); return
    pkg=Package(args.package,'unknown',args.source,platform.system(),'explicit-provider-required')
    if not args.yes:
        print(json.dumps({'action':'install','package':asdict(pkg),'dry_run':True,'message':'re-run with --yes after reviewing the provider and package metadata'},indent=2)); return
    print(json.dumps({'action':'install','package':asdict(pkg),'status':'provider-specific installation required'},indent=2))

if __name__=='__main__': main()
