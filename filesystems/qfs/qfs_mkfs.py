#!/usr/bin/env python3
"""Create or inspect a Chimera QFS v1 image."""
import argparse, os, struct, uuid
MAGIC=0x43484653
VERSION=1
DEFAULT_BLOCK=4096
MIN_BLOCK=4096
MAX_BLOCK=65536

def page_size():
    try: return os.sysconf("SC_PAGE_SIZE")
    except (AttributeError,ValueError): return 4096

def valid(n): return MIN_BLOCK <= n <= MAX_BLOCK and n & (n-1) == 0

def format_qfs(path,size,block,sector,force,allow_unsafe):
    if not valid(block): raise SystemExit("block size must be 4096, 8192, 16384, 32768, or 65536 bytes")
    if block > page_size() and not allow_unsafe:
        raise SystemExit(f"block size {block} exceeds host page size {page_size()}")
    if size < block*8: raise SystemExit("QFS image is too small")
    if os.path.exists(path) and not force: raise SystemExit(f"{path} exists; use --force")
    blocks=size//block
    data_start=max(8,blocks//1024)
    sb=struct.pack("<IIIIQQQQ16s",MAGIC,VERSION,block,sector,blocks,1,data_start,1,uuid.uuid4().bytes)
    sb += bytes(block-len(sb))
    with open(path,"w+b") as f:
        f.truncate(size); f.write(sb); f.flush(); os.fsync(f.fileno())
    print(f"QFS v{VERSION}: {path} block_size={block} blocks={blocks}")

def inspect(path):
    with open(path,"rb") as f: raw=f.read(4096)
    if len(raw)<56: raise SystemExit("not a QFS image")
    magic,version,block,sector,blocks,meta,data,root,uid=struct.unpack("<IIIIQQQQ16s",raw[:56])
    if magic!=MAGIC: raise SystemExit("invalid QFS magic")
    print({"version":version,"block_size":block,"sector_size":sector,"total_blocks":blocks,"metadata_start":meta,"data_start":data,"root_inode":root,"uuid":str(uuid.UUID(bytes=uid))})

ap=argparse.ArgumentParser()
ap.add_argument("path")
ap.add_argument("--size",type=int)
ap.add_argument("--block-size",type=int,default=DEFAULT_BLOCK)
ap.add_argument("--sector-size",type=int,default=512)
ap.add_argument("--force",action="store_true")
ap.add_argument("--inspect",action="store_true")
ap.add_argument("--allow-unsafe-page-size",action="store_true")
a=ap.parse_args()
if a.inspect: inspect(a.path)
elif not a.size: raise SystemExit("--size is required when creating a QFS image")
else: format_qfs(a.path,a.size,a.block_size,a.sector_size,a.force,a.allow_unsafe_page_size)
