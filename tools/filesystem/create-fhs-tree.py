#!/usr/bin/env python3
import argparse,json,os
from pathlib import Path
DIRS={"boot":493,"dev":493,"etc":493,"home":493,"media":493,"mnt":493,"opt":493,"proc":493,"root":448,"run":493,"srv":493,"sys":493,"tmp":1023,"usr":493,"usr/bin":493,"usr/lib":493,"usr/libexec":493,"usr/local":493,"usr/local/bin":493,"usr/local/lib":493,"usr/local/sbin":493,"usr/local/share":493,"usr/sbin":493,"usr/share":493,"usr/src":493,"var":493,"var/cache":493,"var/lib":493,"var/local":493,"var/log":493,"var/opt":493,"run/lock":493,"var/spool":493,"var/tmp":1023}
LINKS={"bin":("usr/bin",),"sbin":("usr/sbin",),"lib":("usr/lib",),"var/run":("../run","/run"),"var/lock":("../run/lock","/run/lock")}
def create(root):
 root=Path(root).expanduser().resolve()
 protected={Path("/"),Path("/bin"),Path("/boot"),Path("/dev"),Path("/etc"),Path("/home"),Path("/lib"),Path("/lib64"),Path("/media"),Path("/mnt"),Path("/opt"),Path("/proc"),Path("/root"),Path("/run"),Path("/sbin"),Path("/srv"),Path("/sys"),Path("/tmp"),Path("/usr"),Path("/var")}
 unsafe={p for p in protected if p not in (Path("/"),Path("/tmp"),Path("/mnt"))}
 if root==Path("/") or any(root==p or p in root.parents for p in unsafe) or root in (Path("/tmp"),Path("/mnt")):raise ValueError("refusing to create FHS layout on or beneath a host system directory; use a dedicated staging root under /tmp or a separate build volume")
 root.mkdir(parents=True,exist_ok=True);made=[]
 for rel,mode in DIRS.items():
  p=root/rel
  if p.is_symlink():raise ValueError("refusing symlink in target root: "+rel)
  p.mkdir(parents=True,exist_ok=True)
  if not p.is_dir():raise ValueError("not a directory: "+rel)
  os.chmod(p,mode,follow_symlinks=False);made.append("/"+rel)
 for name,targets in LINKS.items():
  p=root/name
  if p.is_symlink():
   if os.readlink(p) not in targets:raise ValueError("unexpected FHS link: "+name)
  elif p.exists():
   if not p.is_dir():raise ValueError("refusing to replace non-directory "+name)
  else:p.symlink_to(targets[0])
 return {"root":str(root),"directories":made,"links":LINKS,"mount_points":["/dev","/proc","/sys","/run","/tmp"]}
def main():
 p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args();print(json.dumps(create(a.root),indent=2))
if __name__=="__main__":main()
