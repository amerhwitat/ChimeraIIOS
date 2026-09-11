from __future__ import annotations
import json, shutil
from pathlib import Path
MANIFESTS={'python':('requirements.txt','pyproject.toml','setup.py','setup.cfg'),'nodejs':('package.json','package-lock.json','npm-shrinkwrap.json'),'rust':('Cargo.toml','Cargo.lock'),'java':('pom.xml','build.gradle','build.gradle.kts'),'dotnet':('*.csproj','*.fsproj','*.sln'),'go':('go.mod','go.sum'),'cmake':('CMakeLists.txt',),'make':('Makefile','makefile','GNUmakefile')}
PACKAGE_MANAGERS={'apt':('apt-get','apt'),'dnf':('dnf',),'zypper':('zypper',),'pacman':('pacman',),'apk':('apk',),'xbps':('xbps-install',),'portage':('emerge',),'homebrew':('brew',),'flatpak':('flatpak',),'snap':('snap',),'winget':('winget',),'chocolatey':('choco',),'scoop':('scoop',)}
def _present(root:Path,patterns:tuple[str,...])->bool:return any(root.glob(pattern) for pattern in patterns)
def _manager_report()->dict:return {name:{'available':any(shutil.which(binary) for binary in binaries),'binaries':binaries} for name,binaries in PACKAGE_MANAGERS.items()}
def discover_applications(root:Path,target:str='auto')->dict:
    root=Path(root).resolve(); discovered=[]
    for app,patterns in MANIFESTS.items():
        if _present(root,patterns): discovered.append({'id':app,'classification':'recommended' if app in {'cmake','make'} else 'optional','evidence':list(patterns)})
    if (root/'README.md').exists() or (root/'README').exists(): discovered.append({'id':'documentation','classification':'required','evidence':['README']})
    result={'target':target,'root':str(root),'discovered':discovered,'package_managers':_manager_report(),'install_authorized':False,'install_command':None}; (root/'applications.json').write_text(json.dumps(result,indent=2),encoding='utf-8'); return result
def authorize_package_install(result:dict,manager:str,packages:list[str],yes:bool=False)->dict:
    if not yes: raise PermissionError('Package installation requires explicit authorization (--yes).')
    info=result['package_managers'].get(manager)
    if not info or not info['available']: raise RuntimeError(f'Package manager is unavailable: {manager}')
    commands={'apt':['apt-get','install','--no-install-recommends'],'dnf':['dnf','install'],'zypper':['zypper','install'],'pacman':['pacman','-S'],'apk':['apk','add'],'xbps':['xbps-install','-y'],'portage':['emerge'],'homebrew':['brew','install'],'flatpak':['flatpak','install'],'snap':['snap','install'],'winget':['winget','install'],'chocolatey':['choco','install','-y'],'scoop':['scoop','install']}; result=dict(result); result['install_authorized']=True; result['install_command']=commands[manager]+packages; return result
