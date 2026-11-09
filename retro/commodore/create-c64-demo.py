#!/usr/bin/env python3
"""Create an original Commodore 64 BASIC V2 PRG."""
from pathlib import Path
import argparse

def build_program(message="CHIMERA C64 RETRO KIT"):
    text=message.encode("ascii","strict")
    if len(text)>200: raise ValueError("BASIC line too long")
    load=0x0801
    body=bytes([0x99])+b'"'+text+b'"'+b"\x00"
    line_size=2+2+len(body)
    next_line=load+line_size
    line=next_line.to_bytes(2,"little")+(10).to_bytes(2,"little")+body
    return load.to_bytes(2,"little")+line+b"\x00\x00"

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--message",default="CHIMERA C64 RETRO KIT")
    a=p.parse_args(); data=build_program(a.message)
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(data)
    print(f"created {a.output} ({len(data)} bytes)")
if __name__=="__main__": main()
