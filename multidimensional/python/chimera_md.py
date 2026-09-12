import math

def norm(x): return math.sqrt(sum(v*v for v in x))
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def project(x,observer): return [a-b for a,b in zip(x,observer)]
def contract_2d(a,b): return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]
