from chimera_quantum import Circuit, bell_state, qft

def test_bell_state_is_normalized_and_entangled():
    state=bell_state(); assert abs(sum(abs(x)**2 for x in state)-1.0)<1e-12; assert abs(state[0]-2**-0.5)<1e-12; assert abs(state[3]-2**-0.5)<1e-12

def test_qft_of_basis_zero_is_uniform():
    out=qft([1,0,0,0]); assert all(abs(abs(x)-0.5)<1e-12 for x in out)
