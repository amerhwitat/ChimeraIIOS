#!/usr/bin/env python3
"""Plan and stage optional enterprise services for a Chimera rootfs.

Safe defaults: plan-only, no automatic service enablement, no remote shell execution.
Package payloads are extracted into --rootfs where supported; host package managers
are never allowed to install files directly into the running host from this tool.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shlex, shutil, subprocess, sys, tarfile, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "installer/services/enterprise-services.json"
MANAGERS = ("apt-get", "dnf", "yum", "zypper", "pacman", "apk", "brew", "snap")

def manager():
    for name in MANAGERS:
        if shutil.which(name):
            return name
    return None

def run(args, cwd=None):
    print("+", " ".join(map(str,args)), flush=True)
    return subprocess.run(args, cwd=cwd, check=False).returncode

def package_stage(pm, packages, rootfs, cache):
    """Download and extract packages without installing them into the host OS."""
    cache.mkdir(parents=True, exist_ok=True)
    rootfs.mkdir(parents=True, exist_ok=True)
    if pm == "apt-get" and shutil.which("apt-get") and shutil.which("dpkg-deb"):
        for package in packages:
            rc=run(["apt-get","download",package],cwd=cache)
            if rc: return rc
        debs=list(cache.glob("*.deb"))
        if not debs: return 1
        for deb in debs:
            if run(["dpkg-deb","-x",str(deb),str(rootfs)]): return 1
        return 0
    if pm in ("dnf","yum") and shutil.which("rpm2cpio") and shutil.which("cpio"):
        fetcher=pm
        if shutil.which("dnf") and pm=="yum": fetcher="dnf"
        for package in packages:
            if run([fetcher,"download","--destdir",str(cache),package]): return 1
        for rpm in cache.glob("*.rpm"):
            p=subprocess.Popen(["rpm2cpio",str(rpm)],stdout=subprocess.PIPE)
            assert p.stdout is not None
            with (rootfs/".package-extract.cpio").open("wb") as f:
                shutil.copyfileobj(p.stdout,f)
            if p.wait()!=0: return 1
            if run(["cpio","-idm","--no-absolute-filenames"],cwd=rootfs): return 1
            (rootfs/".package-extract.cpio").unlink(missing_ok=True)
        return 0
    # Other package managers do not have a uniform safe rootfs extraction API.
    # Do not install into the host as a fallback.
    print(f"manager {pm} detected, but safe rootfs staging is unavailable for it",file=sys.stderr)
    return 2

def verified_source_stage(service, archive_path, expected_sha256, rootfs, cache, execution_mode):
    if not archive_path or not expected_sha256 or len(expected_sha256)!=64:
        return 2, "source fallback requires a supplied archive and 64-character SHA-256 digest"
    archive=Path(archive_path).resolve()
    if not archive.is_file(): return 2, "source archive does not exist"
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest.lower()!=expected_sha256.lower(): return 2, "source archive SHA-256 mismatch"
    cache.mkdir(parents=True,exist_ok=True); rootfs.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chimera-source-",dir=cache) as td:
        build=Path(td)
        try:
            with tarfile.open(archive,"r:*") as tf:
                members=tf.getmembers()
                for m in members:
                    p=Path(m.name)
                    if p.is_absolute() or ".." in p.parts or m.issym() or m.islnk() or m.isdev():
                        return 2, "unsafe archive member rejected"
                tf.extractall(build,members=members)
        except (tarfile.TarError,OSError) as exc:
            return 2, f"cannot unpack verified source: {exc}"
        roots=[x for x in build.iterdir()]
        cwd=roots[0] if len(roots)==1 and roots[0].is_dir() else build
        env=os.environ.copy(); env.update({"DESTDIR":str(rootfs.resolve()),"PREFIX":"/usr","CMAKE_INSTALL_PREFIX":"/usr"})
        if execution_mode=="native":
            cc=os.environ.get("CHIMERA_CC") or shutil.which("chimera-cc")
            cxx=os.environ.get("CHIMERA_CXX") or shutil.which("chimera-c++")
            if not cc: return 2, "native mode requires CHIMERA_CC or chimera-cc; compatibility binaries are not relabeled native"
            env["CC"]=cc
            if cxx: env["CXX"]=cxx
            env["CHIMERA_EXECUTION_MODE"]="native"
        else:
            env["CHIMERA_EXECUTION_MODE"]="compatibility"
        svc=service
        for command in svc.get("source",{}).get("build",[]):
            argv=shlex.split(command)
            if not argv: continue
            try: result=subprocess.run(argv,cwd=cwd,env=env,check=False)
            except OSError as exc: return 2, f"source build tool unavailable: {exc}"
            if result.returncode: return result.returncode, f"source build command failed: {command}"
        return 0, "verified source build commands completed with DESTDIR staging; review package ABI and service config before enabling"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,default=CATALOG)
    p.add_argument("--rootfs",type=Path,default=ROOT/"build/rootfs")
    p.add_argument("--cache",type=Path,default=ROOT/"build/package-cache")
    p.add_argument("--service",action="append",default=[])
    p.add_argument("--profile",action="append",default=[])
    p.add_argument("--package-manager",choices=MANAGERS)
    p.add_argument("--execution-mode",choices=("auto","native","compatibility"),default="auto",
                   help="native requires the Chimera compiler and verified source; compatibility stages platform packages")
    p.add_argument("--source-archive",action="append",default=[],metavar="SERVICE=PATH")
    p.add_argument("--source-sha256",action="append",default=[],metavar="SERVICE=HEX")
    p.add_argument("--apply",action="store_true",help="download and stage selected package payloads")
    p.add_argument("--enable",action="store_true",help="write requested boot-target enablement intent after review")
    a=p.parse_args()
    catalog=json.loads(a.catalog.read_text(encoding="utf-8"))
    services={x["id"]:x for x in catalog["services"]}
    selected=set(a.service)
    for profile in a.profile:
        if profile not in {x["id"] for x in catalog["profiles"]}:
            p.error(f"unknown profile: {profile}")
        selected.update(next(x["services"] for x in catalog["profiles"] if x["id"]==profile))
    if not selected:
        print(json.dumps({"services":[{"id":x["id"],"label":x["label"],"profile":x["profile"],"boot_target":x["boot_target"]} for x in catalog["services"]],"profiles":catalog["profiles"]},indent=2))
        return 0
    unknown={sid for sid in selected if sid not in services}
    if unknown: p.error("unknown service IDs: "+", ".join(sorted(unknown)))
    detected=([a.package_manager] if a.package_manager else []) + [x for x in MANAGERS if shutil.which(x) and x != a.package_manager]
    source_archives=dict(x.split("=",1) for x in a.source_archive if "=" in x)
    source_hashes=dict(x.split("=",1) for x in a.source_sha256 if "=" in x)
    native_compiler=bool(os.environ.get("CHIMERA_CC") or shutil.which("chimera-cc"))
    execution_mode=a.execution_mode
    if execution_mode=="auto":
        execution_mode="native" if native_compiler and selected.issubset(source_archives.keys()) else "compatibility"
    pm=detected[0] if detected else None
    plan={"schema":"CHIMERA-ENTERPRISE-INSTALL-PLAN-1","package_manager":pm,"package_manager_candidates":detected,
          "execution_mode":execution_mode,"rootfs":str(a.rootfs),
          "apply":a.apply,"user_review_confirmed":a.enable,"services":[],"enabled_targets":[]}
    for sid in sorted(selected):
        svc=services[sid]
        item={"id":sid,"label":svc["label"],"boot_target":svc["boot_target"],"packages":{},
              "staging":"not-requested","native_policy":svc.get("native","prefer-native-package"),
              "compatibility":svc.get("compatibility",[]),"attempts":[]}
        if a.apply:
            if execution_mode=="native":
                if sid not in source_archives:
                    item["error"]="native mode requires a verified source archive for this service; package payloads are compatibility binaries"
                    plan["services"].append(item); print(json.dumps(plan,indent=2)); return 2
                rc, detail=verified_source_stage(svc,source_archives[sid],source_hashes.get(sid),a.rootfs,a.cache,"native")
                item["attempts"].append({"method":"chimera-native-source-build","result":"staged" if rc==0 else "failed","detail":detail})
                if rc:
                    item["error"]=detail; plan["services"].append(item); print(json.dumps(plan,indent=2)); return 2
                item["selected_package_manager"]="chimera-native-source-build"; item["staging"]=detail
            elif not detected and sid not in source_archives:
                item["error"]="no package manager detected; verified source archive fallback was not supplied"; plan["services"].append(item); print(json.dumps(plan,indent=2)); return 2
            if execution_mode!="native":
                success=False
                for candidate in detected:
                    packages=(svc.get("packages") or {}).get(candidate,[])
                    item["packages"][candidate]=packages
                    if not packages:
                        item["attempts"].append({"manager":candidate,"result":"no-package-mapping"}); continue
                    rc=package_stage(candidate,packages,a.rootfs,a.cache)
                    item["attempts"].append({"manager":candidate,"result":"staged" if rc==0 else "failed","exit_code":rc})
                    if rc==0:
                        item["selected_package_manager"]=candidate
                        item["staging"]="package payloads extracted; dependency resolution, service configuration and ABI conversion still require rootfs integration"
                        success=True; break
                if not success and sid in source_archives:
                    rc, detail=verified_source_stage(svc,source_archives[sid],source_hashes.get(sid),a.rootfs,a.cache,"compatibility")
                    item["attempts"].append({"method":"verified-source-build","result":"staged" if rc==0 else "failed","detail":detail})
                    if rc==0:
                        item["selected_package_manager"]="verified-source-build"
                        item["staging"]=detail
                        success=True
                if not success:
                    item["error"]="all available package staging adapters failed; provide --source-archive SERVICE=PATH and --source-sha256 SERVICE=HEX for verified source fallback"
                    plan["services"].append(item); print(json.dumps(plan,indent=2)); return 2
        plan["services"].append(item)
        if a.enable: plan["enabled_targets"].append(svc["boot_target"])
    out=a.rootfs/"etc/chimera/enterprise-services.plan.json"
    if a.apply:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(plan,indent=2)+"\n",encoding="utf-8")
        tool_dir=a.rootfs/"usr/lib/chimera/tools"; tool_dir.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/"tools/services/chimera_enterprise_targets.py",tool_dir/"chimera_enterprise_targets.py")
        os.chmod(tool_dir/"chimera_enterprise_targets.py",0o755)
        if a.enable and plan["enabled_targets"]:
            unit_src=ROOT/"services/chimera-native/units/chimera-enterprise-services.service"
            unit_dst=a.rootfs/"usr/lib/systemd/system/chimera-enterprise-services.service"
            unit_dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(unit_src,unit_dst)
            wants=a.rootfs/"etc/systemd/system/multi-user.target.wants"
            wants.mkdir(parents=True,exist_ok=True)
            link=wants/"chimera-enterprise-services.service"
            if link.exists() or link.is_symlink(): link.unlink()
            link.symlink_to("../../../../usr/lib/systemd/system/chimera-enterprise-services.service")
    print(json.dumps(plan,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
