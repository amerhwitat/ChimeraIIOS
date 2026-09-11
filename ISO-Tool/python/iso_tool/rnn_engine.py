from __future__ import annotations
import math
class SequenceRNN:
 def __init__(self,input_size=8,hidden_size=16):
  self.input_size=input_size;self.hidden_size=hidden_size;self.wh=[[0.0]*input_size for _ in range(hidden_size)];self.uh=[[0.0]*hidden_size for _ in range(hidden_size)];self.b=[0.0]*hidden_size
 def step(self,x,state=None):
  s=state or [0.0]*self.hidden_size;return [math.tanh(sum(self.wh[i][j]*x[j] for j in range(min(len(x),self.input_size)))+sum(self.uh[i][j]*s[j] for j in range(self.hidden_size))+self.b[i]) for i in range(self.hidden_size)]
 def score_sequence(self,vectors):
  s=None
  for x in vectors:s=self.step(x,s)
  return sum(s)/len(s) if s else 0.0
