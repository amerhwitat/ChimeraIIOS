from __future__ import annotations
import shutil
from pathlib import Path
def detect_build_systems(root:Path)->list[str]:
    checks=[('cmake',root/'CMakeLists.txt'),('make',root/'Makefile'),('make',root/'makefile'),('meson',root/'meson.build'),('cargo',root/'Cargo.toml'),('npm',root/'package.json'),('maven',root/'pom.xml'),('gradle',root/'build.gradle'),('gradle',root/'build.gradle.kts'),('dotnet',root/'*.sln'),('dotnet',root/'*.csproj'),('autotools',root/'configure.ac')]; found=[]
    for name,marker in checks:
        exists=any(root.glob(marker.name)) if marker.name.startswith('*.') else marker.exists()
        if exists and name not in found:found.append(name)
    return found
def command_for(system:str,root:Path,build_dir:Path)->list[str]|None:
    if system=='cmake' and shutil.which('cmake'):return ['cmake','-S',str(root),'-B',str(build_dir)]
    if system=='make' and shutil.which('make'):return ['make','-C',str(root),'-j']
    if system=='meson' and shutil.which('meson'):return ['meson','setup',str(build_dir),str(root)]
    if system=='cargo' and shutil.which('cargo'):return ['cargo','build','--release','--manifest-path',str(root/'Cargo.toml')]
    if system=='npm' and shutil.which('npm'):return ['npm','install']
    if system=='maven' and shutil.which('mvn'):return ['mvn','-B','package']
    if system=='gradle' and shutil.which('gradle'):return ['gradle','build']
    if system=='dotnet' and shutil.which('dotnet'):return ['dotnet','build',str(root),'--configuration','Release']
    if system=='autotools' and shutil.which('sh'):return ['./configure']
    return None
