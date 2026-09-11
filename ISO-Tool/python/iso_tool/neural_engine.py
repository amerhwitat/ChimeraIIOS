import math
class TinyRNN:
 def __init__(self):self.h=8;self.w=[.03*(i+1) for i in range(8)]
 def score(self,seq):
  h=[0.0]*self.h
  for x in seq:h=[math.tanh(float(x)*.1+h[i]*.05) for i in range(self.h)]
  z=sum(self.w[i]*h[i] for i in range(self.h));return 1/(1+math.exp(-z))
 def train(self,sequences,labels=None,epochs=5):return self
class NeuralEngine:
 def __init__(self):self.rnn=TinyRNN();self.backend='builtin-rnn'
 def train_from_build_sequences(self,s):return {'backend':self.backend,'samples':len(s),'confidence':self.rnn.score(s[0]) if s else 0}
 def optional_torch_info(self):
  try:
   import torch;return {'available':True,'version':torch.__version__,'rnn':'torch.nn.RNN','transformer':'torch.nn.Transformer'}
  except Exception as e:return {'available':False,'reason':str(e)}
