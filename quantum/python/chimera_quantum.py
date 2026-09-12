from __future__ import annotations
import cmath, math
from dataclasses import dataclass

@dataclass
class Circuit:
    qubits: int
    ops: list
    def __init__(self, qubits: int):
        self.qubits, self.ops = qubits, []
    def h(self, q): self.ops.append(('h', q)); return self
    def cx(self, c, t): self.ops.append(('cx', c, t)); return self

def _apply_single(state, q, matrix):
    n = int(math.log2(len(state))); bit = 1 << (n - 1 - q); out = state[:]
    for i in range(len(state)):
        if not i & bit:
            j=i|bit; a,b=state[i],state[j]
            out[i]=matrix[0][0]*a+matrix[0][1]*b
            out[j]=matrix[1][0]*a+matrix[1][1]*b
    return out

def _apply_cx(state,c,t):
    n=int(math.log2(len(state))); cb=1<<(n-1-c); tb=1<<(n-1-t); out=state[:]
    for i in range(len(state)):
        if i&cb and not i&tb:
            j=i|tb; out[i],out[j]=state[j],state[i]
    return out

def simulate(circuit:Circuit):
    state=[0j]*(1<<circuit.qubits); state[0]=1+0j
    for op in circuit.ops:
        if op[0]=='h': state=_apply_single(state,op[1],((1/math.sqrt(2),1/math.sqrt(2)),(1/math.sqrt(2),-1/math.sqrt(2))))
        elif op[0]=='cx': state=_apply_cx(state,op[1],op[2])
        else: raise ValueError(op[0])
    return state

def bell_state(): return simulate(Circuit(2).h(0).cx(0,1))
def qft(state):
    n=len(state); return [sum(state[x]*cmath.exp(2j*math.pi*k*x/n) for x in range(n))/math.sqrt(n) for k in range(n)]
