from __future__ import annotations
from pathlib import Path
import struct
def _rel8(buf,pos,target):buf[pos]=(target-(pos+1))&0xff
def _rel16(buf,pos,target):buf[pos:pos+2]=struct.pack('<h',target-(pos+2))
def assemble_spit_fire(output:Path)->Path:
    b=bytearray();labels={};fix=[]
    def mark(n):labels[n]=len(b)
    def op(*x):b.extend(x)
    def j8(opcode,label):op(opcode,0);fix.append((len(b)-1,label,'8'))
    def j16(opcode,label):op(opcode,0,0);fix.append((len(b)-2,label,'16'))
    op(0xFA,0x31,0xC0,0x8E,0xD8,0x8E,0xC0,0x8E,0xD0,0xBC,0x00,0x7C,0xFB)
    mark('print');op(0xBE,0,0);fix.append((len(b)-2,'msg','abs16'));op(0xAC,0x84,0xC0);j8(0x74,'menu');op(0xB4,0x0E,0xCD,0x10);j16(0xE9,'print')
    mark('menu');op(0x30,0xE4,0xCD,0x16,0x3C,0x31);j8(0x74,'primary');op(0x3C,0x32);j8(0x74,'fallback');j16(0xE9,'menu');mark('primary');j16(0xE9,'fallback')
    mark('fallback');op(0xBE,0,0);fix.append((len(b)-2,'fallback_msg','abs16'));mark('fprint');op(0xAC,0x84,0xC0);j8(0x74,'halt');op(0xB4,0x0E,0xCD,0x10);j16(0xE9,'fprint');mark('halt');op(0xFA,0xF4);j16(0xE9,'halt')
    mark('msg');b.extend(b'\r\nISO-Tool BIOS: 1=primary  2=fallback\r\n\0');mark('fallback_msg');b.extend(b'\r\nPrimary unavailable; fallback selected.\r\n\0')
    for pos,label,width in fix:
        if width=='8':_rel8(b,pos,labels[label])
        elif width=='16':_rel16(b,pos,labels[label])
        else:b[pos:pos+2]=struct.pack('<H',labels[label]+0x7C00)
    if len(b)>510:raise ValueError(f'Spit Fire bootstrap exceeds one sector: {len(b)} bytes')
    b.extend(b'\0'*(510-len(b)));b.extend(b'\x55\xAA');output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(b);return output
