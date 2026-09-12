from chimera_md import norm,dot,project,contract_2d

def test_norm_and_dot_128d():
    x=[1.0]*128; assert abs(norm(x)-128**0.5)<1e-12; assert dot(x,x)==128.0

def test_observer_projection(): assert project([3.0,4.0,5.0],[1.0,1.0,1.0])==[2.0,3.0,4.0]
def test_matrix_contraction(): assert contract_2d([[1,2],[3,4]],[[5,6],[7,8]])==[[19,22],[43,50]]
