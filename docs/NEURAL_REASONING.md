# Deep Reasoning and Multidimensional Cognition

The neural layer is designed as a reasoning substrate, not a claim of consciousness.

For evidence values `e_i in [0,1]` with non-negative weights `w_i`:

`S = sum(w_i e_i) / sum(w_i)`

A disagreement-aware confidence estimate uses weighted spread:

`V = sum(w_i (e_i-S)^2) / sum(w_i)`

`C = clamp(S (1-sqrt(V)), 0, 1)`

For geometry, a point `x` viewed from observer origin `o` is separated from perspective by:

`r = x - o`, `p = P r`

An affine transformation is `x' = A x + b`.

For tensor contraction:

`C_ik = sum_j A_ij B_jk`.

The 128D profile uses the same mathematical primitives at dimension 128 and is explicitly labeled experimental/semantic. It is not presented as an established physical dimension.

A response pipeline should keep: raw evidence -> normalized features -> observer transform -> reasoning score -> confidence -> explanation -> optional speech.

This makes the system inspectable and reduces the chance that a change in presentation is mistaken for a change in underlying geometry.
