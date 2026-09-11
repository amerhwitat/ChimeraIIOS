from __future__ import annotations
import shutil
from pathlib import Path
def detect_build_systems(root:Path)->list[str]:
    checks=[('cmake','CMakeLists.txt'),('make','Makefile'),('make','makefile'),('meson','meson.build'),('cargo','Cargo.toml'),('npm','package.json'),('maven','pom.xml'),('gradle','build.gradle'),('gradle','build.gradle.kts'),('dotnet','.sln'),('dotnet','.csproj'),('autotools','configure.ac'),('autotools','configure')];found=[]
    for name,marker in checks:
        exists=(root/marker).exists() if not marker.startswith('.') else any(root.glob('*'+marker))
        if exists and name not in found:found.append(name)
    return found
def command_for(system:str,root:Path,build_dir:Path,compiler:str='auto')->list[str]|None:
    if system=='cmake' and shutil.which('cmake'):
        if compiler in ('gnu','gcc') and shutil.which('ninja'):return ['cmake','-S',str(root),'-B',str(build_dir),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release']
        if compiler in ('gnu','gcc') and shutil.which('mingw32-make'):return ['cmake','-S',str(root),'-B',str(build_dir),'-G','MinGW Makefiles','-DCMAKE_BUILD_TYPE=Release']
        if compiler in ('msvc','cl'):return ['cmake','-S',str(root),'-B',str(build_dir),'-G','Visual Studio 17 2022','-A','x64']
        return ['cmake','-S',str(root),'-B',str(build_dir)]
    if system=='make' and shutil.which('make'):return ['make','-C',str(root),'-j']
    if system=='meson' and shutil.which('meson'):return ['meson','setup',str(build_dir),str(root)]
    if system=='cargo' and shutil.which('cargo'):return ['cargo','build','--release','--manifest-path',str(root/'Cargo.toml')]
    if system=='npm' and shutil.which('npm'):return ['npm','ci','--ignore-scripts'] if (root/'package-lock.json').exists() else ['npm','install','--ignore-scripts']
    if system=='maven' and shutil.which('mvn'):return ['mvn','-B','package','-DskipTests']
    if system=='gradle' and shutil.which('gradle'):return ['gradle','build','-x','test']
    if system=='dotnet' and shutil.which('dotnet'):return ['dotnet','build',str(root),'--configuration','Release']
    if system=='autotools' and shutil.which('sh'):return ['sh','./configure']
    return None
