#ifndef CHIMERA_QUANTUM_H
#define CHIMERA_QUANTUM_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct { double re; double im; } chm_complex_t;
typedef struct { size_t qubits; size_t count; chm_complex_t *amplitudes; } chm_state_t;
int chm_state_init(chm_state_t *state, size_t qubits);
void chm_state_free(chm_state_t *state);
int chm_hadamard(chm_state_t *state, size_t target);
double chm_probability_sum(const chm_state_t *state);
#ifdef __cplusplus
}
#endif
#endif
