#!/usr/bin/env python3
"""Feature-probed GPU toolchain selector for Chimera native and compatibility shells.

This tool compiles source only. It never executes a GPU binary on the CPU and does
not claim a device runtime is available just because a compiler is installed.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
BACKENDS={
 "vulkan":{"tools":["glslc","glslangValidator"],"kind":"shader"},
 "cuda":{"tools":["nvcc"],"kind":"cuda"},
 "rocm-hip":{"tools":["hipcc"],"kind":"hip"},
 "opencl":{"tools":["clang"],"kind":"opencl"},
}
RUNTIMES={"vulkan":["vulkaninfo"],"cuda":["nvidia-smi"],"rocm-hip":["rocminfo"],"opencl":["clinfo"]}
def inventory():
    rows=[]
    for name,spec in BACKENDS.items():
        compiler=next((shutil.which(t) for t in spec["tools"] if shutil.which(t)),None)
        runtime=next((shutil.which(t) for t in RUNTIMES[name] if shutil.which(t)),None)
        rows.append({"backend":name,"compiler":compiler,"runtime_probe":runtime,
                     "compile_available":bool(compiler),"runtime_probe_available":bool(runtime),
                     "execution":"requires device/runtime validation" if compiler else "unavailable"})
    return {"schema":"CHIMERA-GPU-TOOLCHAIN-1","backends":rows}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory",action="store_true")
    p.add_argument("--backend",choices=sorted(BACKENDS))
    p.add_argument("--source",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--arch",help="vendor-specific architecture, e.g. sm_90 or gfx1100")
    a=p.parse_args()
    if a.inventory or not a.backend:
        print(json.dumps(inventory(),indent=2))
        if a.inventory:return 0
        if not a.backend:return 0
    if not a.source or not a.output:p.error("--backend requires --source and --output")
    spec=BACKENDS[a.backend]
    tool=next((shutil.which(t) for t in spec["tools"] if shutil.which(t)),None)
    if not tool:
        print(f"GPU backend unavailable: no compiler from {spec['tools']}",file=sys.stderr);return 2
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.backend=="vulkan":
        if Path(tool).name=="glslc": cmd=[tool,str(a.source),"-o",str(a.output)]
        else: cmd=[tool,"-V",str(a.source),"-o",str(a.output)]
    elif a.backend=="cuda":
        if a.arch and not a.arch.startswith("sm_"):p.error("CUDA --arch must use sm_NN notation")
        cmd=[tool]+(["--gpu-architecture="+a.arch] if a.arch else [])+["-c",str(a.source),"-o",str(a.output)]
    elif a.backend=="rocm-hip":
        if a.arch and not a.arch.startswith("gfx"):p.error("HIP --arch must use gfx notation")
        cmd=[tool]+(["--offload-arch="+a.arch] if a.arch else [])+["-c",str(a.source),"-o",str(a.output)]
    else:
        cmd=[tool,"-x","cl","-cl-std=CL2.0","-c",str(a.source),"-o",str(a.output)]
    result=subprocess.run(cmd,check=False)
    if result.returncode:return result.returncode
    print(json.dumps({"compiled":str(a.output),"backend":a.backend,"compiler":tool,
                      "device_execution_verified":False,"runtime_probe":next((shutil.which(t) for t in RUNTIMES[a.backend] if shutil.which(t)),None)},indent=2))
    return 0
if __name__=="__main__":raise SystemExit(main())
