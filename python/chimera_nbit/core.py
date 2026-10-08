"""Typed, variable-width N-bit operations for Chimera II OS."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum
from math import gcd as _gcd
from typing import Union

class NBitError(ValueError): pass
class OverflowMode(str, Enum):
    WRAP="wrap"; TRAP="trap"; SATURATE="saturate"

def _width(n:int)->int:
    if not isinstance(n,int) or isinstance(n,bool) or n<1: raise NBitError("bit width must be a positive integer")
    return n
def mask(width:int)->int: return (1<<_width(width))-1
def signed_value(value:int,width:int)->int:
    value=int(value)&mask(width)
    return value-(1<<width) if value&(1<<(width-1)) else value
def _fit(value:int,width:int,signed:bool,mode:OverflowMode):
    width=_width(width); lo=-(1<<(width-1)) if signed else 0; hi=(1<<(width-1))-1 if signed else mask(width)
    overflow=not lo<=value<=hi
    if mode==OverflowMode.TRAP and overflow: raise OverflowError(f"{value} does not fit {'i' if signed else 'u'}{width}")
    if mode==OverflowMode.SATURATE: value=min(hi,max(lo,value))
    else: value=signed_value(value,width) if signed else value&mask(width)
    return value,overflow

@dataclass(frozen=True)
class NBitInt:
    value:int
    width:int
    signed:bool=False
    def __post_init__(self):
        _width(self.width)
        object.__setattr__(self,"value",signed_value(self.value,self.width) if self.signed else int(self.value)&mask(self.width))
    @property
    def bits(self): return self.value&mask(self.width)
    @property
    def type_name(self): return ("i" if self.signed else "u")+str(self.width)
    @property
    def hex(self): return "0x"+format(self.bits,f"0{(self.width+3)//4}x")
    def cast(self,width:int,signed:bool|None=None,mode:OverflowMode=OverflowMode.WRAP):
        s=self.signed if signed is None else signed
        v,_=_fit(self.value,width,s,OverflowMode(mode)); return NBitInt(v,width,s)
    def __int__(self): return self.value
    def __index__(self): return self.bits
    def __repr__(self): return f"NBitInt({self.value}, {self.width}, signed={self.signed})"

@dataclass(frozen=True)
class NBitFloat:
    value:Decimal
    precision:int=256
    def __post_init__(self):
        if not 2<=self.precision<=10000: raise NBitError("Decimal precision must be in 2..10000")
        object.__setattr__(self,"value",Decimal(str(self.value)))
    @property
    def type_name(self): return f"f{self.precision}"
    def __str__(self): return str(self.value)

@dataclass(frozen=True)
class NBitConstant:
    name:str
    value:Union[int,str,Decimal]
    type_name:str
    def resolve(self):
        if self.type_name.startswith(("i","u")) and self.type_name[1:].isdigit():
            return NBitInt(int(self.value,0) if isinstance(self.value,str) else int(self.value),int(self.type_name[1:]),self.type_name[0]=="i")
        if self.type_name.startswith("f"):
            return NBitFloat(Decimal(str(self.value)),int(self.type_name[1:]))
        raise NBitError(f"unsupported constant type {self.type_name}")

MASK=lambda width:NBitConstant("MASK",mask(width),f"u{width}")
ZERO=NBitConstant("ZERO",0,"u1"); ONE=NBitConstant("ONE",1,"u1")
PI=NBitConstant("PI","3.14159265358979323846264338327950288419716939937510","f256")
E=NBitConstant("E","2.71828182845904523536028747135266249775724709369995","f256")

def _v(x): return x.value if isinstance(x,NBitInt) else int(x)
def _widths(a,b,out_width):
    aw=a.width if isinstance(a,NBitInt) else max(1,_v(a).bit_length())
    bw=b.width if isinstance(b,NBitInt) else max(1,_v(b).bit_length())
    return aw,bw,out_width or max(aw,bw)
def _binary(op,a,b,out_width=None,signed=None,overflow=OverflowMode.WRAP):
    aw,bw,w=_widths(a,b,out_width); s=(a.signed if isinstance(a,NBitInt) else False) if signed is None else signed
    x=_v(a); y=_v(b)
    if isinstance(a,NBitInt) and a.signed: x=a.value
    if isinstance(b,NBitInt) and b.signed: y=b.value
    if op=="add": z=x+y
    elif op=="sub": z=x-y
    elif op=="mul": z=x*y
    elif op=="div":
        if y==0: raise ZeroDivisionError("N-bit integer division by zero")
        z=abs(x)//abs(y)*(-1 if (x<0)!=(y<0) else 1)
    elif op=="mod":
        if y==0: raise ZeroDivisionError("N-bit integer modulo by zero")
        q=abs(x)//abs(y)*(-1 if (x<0)!=(y<0) else 1); z=x-q*y
    elif op=="and": z=(x&mask(aw))&(y&mask(bw))
    elif op=="or": z=(x&mask(aw))|(y&mask(bw))
    elif op=="xor": z=(x&mask(aw))^(y&mask(bw))
    elif op=="shl":
        if y<0: raise NBitError("negative shift count")
        z=(x&mask(aw))<<y
    elif op=="shr":
        if y<0: raise NBitError("negative shift count")
        z=x>>y if s else (x&mask(aw))>>y
    else: raise NBitError(f"unknown binary op {op}")
    z,ov=_fit(z,w,s,OverflowMode(overflow)); return NBitInt(z,w,s),ov
def add(a,b,**kw): return _binary("add",a,b,**kw)[0]
def sub(a,b,**kw): return _binary("sub",a,b,**kw)[0]
def mul(a,b,**kw): return _binary("mul",a,b,**kw)[0]
def div(a,b,**kw): return _binary("div",a,b,**kw)[0]
def mod(a,b,**kw): return _binary("mod",a,b,**kw)[0]
def bit_and(a,b,**kw): return _binary("and",a,b,**kw)[0]
def bit_or(a,b,**kw): return _binary("or",a,b,**kw)[0]
def bit_xor(a,b,**kw): return _binary("xor",a,b,**kw)[0]
def shl(a,count,**kw): return _binary("shl",a,count,**kw)[0]
def shr(a,count,**kw): return _binary("shr",a,count,**kw)[0]
def bit_not(a,width=None,signed=None):
    w=width or (a.width if isinstance(a,NBitInt) else max(1,int(a).bit_length())); s=a.signed if isinstance(a,NBitInt) and signed is None else bool(signed)
    return NBitInt(~_v(a),w,s)
def rol(a,count,width=None):
    w=width or (a.width if isinstance(a,NBitInt) else max(1,int(a).bit_length())); n=int(count)%w; x=_v(a)&mask(w)
    return NBitInt(((x<<n)|(x>>(w-n if n else w)))&mask(w),w, a.signed if isinstance(a,NBitInt) else False)
def ror(a,count,width=None): return rol(a,-int(count),width)
def compare(a,b,op="eq"):
    x=_v(a); y=_v(b)
    if isinstance(a,NBitInt) and a.signed: x=a.value
    if isinstance(b,NBitInt) and b.signed: y=b.value
    ops={"eq":x==y,"ne":x!=y,"lt":x<y,"le":x<=y,"gt":x>y,"ge":x>=y}
    if op not in ops: raise NBitError(f"unknown comparison {op}")
    return ops[op]
def popcount(a,width=None): return (_v(a)&mask(width or (a.width if isinstance(a,NBitInt) else max(1,_v(a).bit_length())))).bit_count()
def clz(a,width=None):
    w=width or (a.width if isinstance(a,NBitInt) else max(1,_v(a).bit_length())); x=_v(a)&mask(w); return w-x.bit_length()
def ctz(a,width=None):
    w=width or (a.width if isinstance(a,NBitInt) else max(1,_v(a).bit_length())); x=_v(a)&mask(w)
    return w if x==0 else (x&-x).bit_length()-1
def gcd(a,b): return NBitInt(_gcd(abs(_v(a)),abs(_v(b))),max(1,(_gcd(abs(_v(a)),abs(_v(b))).bit_length())),False)
def lcm(a,b):
    x,y=_v(a),_v(b); z=0 if x==0 or y==0 else abs(x//_gcd(x,y)*y); return NBitInt(z,max(1,z.bit_length()),False)
def parse_int(value,width,signed=False,base=0): return NBitInt(int(value,base) if isinstance(value,str) else int(value),width,signed)
def format_value(value,base=16):
    if not isinstance(value,NBitInt): return format(value,"x" if base==16 else "b" if base==2 else "d")
    return value.hex if base==16 else format(value.bits,"b") if base==2 else str(value.value)

def _float(op,a,b=None,precision=None,c=None):
    p=precision or max(getattr(a,"precision",256),getattr(b,"precision",256) if b is not None else 2)
    with localcontext() as ctx:
        ctx.prec=p; x=Decimal(str(a.value if isinstance(a,NBitFloat) else a))
        y=Decimal(str(b.value if isinstance(b,NBitFloat) else b)) if b is not None else None
        if op=="add": z=x+y
        elif op=="sub": z=x-y
        elif op=="mul": z=x*y
        elif op=="div":
            if y==0: raise ZeroDivisionError("N-bit float division by zero")
            z=x/y
        elif op=="sqrt":
            if x<0: raise NBitError("sqrt domain error")
            z=x.sqrt()
        elif op=="fma":
            if c is None: raise NBitError("fma requires three operands")
            z=x*y+Decimal(str(c.value if isinstance(c,NBitFloat) else c))
        else: raise NBitError(op)
        return NBitFloat(z,p)
def fadd(a,b,precision=None): return _float("add",a,b,precision)
def fsub(a,b,precision=None): return _float("sub",a,b,precision)
def fmul(a,b,precision=None): return _float("mul",a,b,precision)
def fdiv(a,b,precision=None): return _float("div",a,b,precision)
def fsqrt(a,precision=None): return _float("sqrt",a,precision=precision)
def fma(a,b,c,precision=None): return _float("fma",a,b,precision,c)
