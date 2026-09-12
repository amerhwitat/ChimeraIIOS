#ifndef CHM_QUANTUM_H
#define CHM_QUANTUM_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef struct chm_qc_state chm_qc_state;
chm_qc_state* chm_qc_create(size_t qubits);
void chm_qc_destroy(chm_qc_state* state);
int chm_qc_h(chm_qc_state* state,size_t target);
int chm_qc_cx(chm_qc_state* state,size_t control,size_t target);
int chm_qc_measure(chm_qc_state* state,unsigned long long seed,unsigned long long* bits);
#ifdef __cplusplus
}
#endif
#endif
