#!/usr/bin/env python3
"""Small deterministic RNN security scorer.

This is an optional local ML layer, not a self-modifying LLM. It scores feature sequences
and can consume a signed model artifact. Model updates are data-only and must be verified
before activation; the daemon never downloads/execut es model code.
"""
from __future__ import annotations
import json, math
from pathlib import Path

def sigmoid(x): return 1/(1+math.exp(-max(-40,min(40,x))))
class RNN:
    def __init__(self, model):
        self.Wx=model["Wx"]; self.Wh=model["Wh"]; self.b=model["b"]; self.wy=model["wy"]; self.by=model["by"]
    def score(self, seq):
        h=[0.0]*len(self.Wh)
        for x in seq:
            z=[]
            for i in range(len(h)):
                z.append(math.tanh(sum(self.Wx[i][j]*x[j] for j in range(len(x))) + sum(self.Wh[i][j]*h[j] for j in range(len(h))) + self.b[i]))
            h=z
        return sigmoid(sum(self.wy[i]*h[i] for i in range(len(h)))+self.by)
def load(path): return RNN(json.loads(Path(path).read_text()))
