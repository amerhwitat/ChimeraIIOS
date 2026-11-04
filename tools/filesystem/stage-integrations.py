#!/usr/bin/env python3
import argparse,importlib.util,json,os,shutil
from pathlib import Path
def copy(src,dst,mode=420):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);os.chmod(dst,mode)
def stage(source,root):
 source=Path(source).resolve();root=Path(root).resolve()
 spec=importlib.util.spec_from_file_location("fhs",source/"tools/filesystem/create-fhs-tree.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.create(root)
 groups=[
 (["services/registry/registryd.py","services/registry/registry-editor-api.py","tools/registry/registry_hive.py"],"usr/lib/chimera/registry",493),
 (["services/network/smb-browse.py","services/network/directoryctl.py","services/network/directory-discovery.py","services/network/network-discoveryd.py"],"usr/lib/chimera/network",493),
 (["services/storage/mount-image.py"],"usr/lib/chimera/storage",493),
 (["desktop/aurora/registry-editor.html"],"usr/share/chimera/aurora",420),
 (["desktop/aurora/chimera-registry-editor.desktop"],"usr/share/applications",420),
 (["system/registry/machine.defaults.json","system/registry/environment.defaults.json","system/registry/kernel.defaults.json","system/registry/registry-editor-policy.json"],"etc/chimera/registry",420),
 (["services/registry/registryd.service.json","services/registry/registry-editor.service.json","services/network/smbd.service.json","services/network/smb-browse.service.json","services/network/directory-discovery.service.json","services/storage/mount-image.service.json"],"usr/lib/chimera/services",420),
 (["services/network/network-stack.json"],"usr/share/chimera/network",420),
 (["system/filesystem/fhs-layout.json"],"usr/share/chimera/filesystem",420),
 (["services/systemd/chimera-registryd.service"],"usr/lib/systemd/system",420),
 (["services/systemd/chimera-registry-editor.service"],"usr/lib/systemd/user",420)
 ]
 copied=[]
 for names,dest,mode in groups:
  for name in names:
   src=source/name
   if not src.is_file():raise FileNotFoundError(src)
   copy(src,root/dest/src.name,mode);copied.append("/"+dest+"/"+src.name)
 cfg=root/"etc/chimera/registry";cfg.mkdir(parents=True,exist_ok=True)
 spec=importlib.util.spec_from_file_location("registry_hive",root/"usr/lib/chimera/registry/registry_hive.py");h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 for name in ("machine","environment","kernel"):
  data=json.loads((cfg/(name+".defaults.json")).read_text())
  (cfg/(name+".json")).write_text(json.dumps(data,indent=2,sort_keys=True)+"\n")
  (cfg/(name+".hive")).write_bytes(h.encode(data))
 os.chmod(cfg,488)
 return {"root":str(root),"copied":copied,"hives":["machine","environment","kernel"]}
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--root",required=True);a=p.parse_args();print(json.dumps(stage(a.source,a.root),indent=2))
if __name__=="__main__":main()
