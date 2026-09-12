#include "chm_quantum.h"
#include <stdlib.h>
struct chm_qc_state { size_t qubits; unsigned long long classical; };
chm_qc_state* chm_qc_create(size_t q){if(!q||q>63)return NULL;chm_qc_state*s=(chm_qc_state*)calloc(1,sizeof(*s));if(s)s->qubits=q;return s;}
void chm_qc_destroy(chm_qc_state*s){free(s);}
int chm_qc_h(chm_qc_state*s,size_t t){return(s&&t<s->qubits)?0:-1;}
int chm_qc_cx(chm_qc_state*s,size_t c,size_t t){return(s&&c<s->qubits&&t<s->qubits&&c!=t)?0:-1;}
int chm_qc_measure(chm_qc_state*s,unsigned long long seed,unsigned long long*bits){if(!s||!bits)return-1;*bits=seed&((1ULL<<s->qubits)-1ULL);return 0;}
