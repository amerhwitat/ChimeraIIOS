#include "chimera_quantum.h"
#include <math.h>
#include <stdlib.h>
int chm_state_init(chm_state_t *s,size_t q){ if(!s||q==0||q>=8*sizeof(size_t)-1)return -1; s->qubits=q;s->count=((size_t)1)<<q;s->amplitudes=calloc(s->count,sizeof(*s->amplitudes));if(!s->amplitudes)return -2;s->amplitudes[0].re=1.0;return 0; }
void chm_state_free(chm_state_t *s){if(s){free(s->amplitudes);s->amplitudes=NULL;s->count=0;s->qubits=0;}}
int chm_hadamard(chm_state_t *s,size_t target){if(!s||!s->amplitudes||target>=s->qubits)return -1;size_t bit=((size_t)1)<<target;double k=1.0/sqrt(2.0);for(size_t i=0;i<s->count;i++)if(!(i&bit)){size_t j=i|bit;chm_complex_t x=s->amplitudes[i],y=s->amplitudes[j];s->amplitudes[i].re=k*(x.re+y.re);s->amplitudes[i].im=k*(x.im+y.im);s->amplitudes[j].re=k*(x.re-y.re);s->amplitudes[j].im=k*(x.im-y.im);}return 0;}
double chm_probability_sum(const chm_state_t *s){if(!s||!s->amplitudes)return 0;double total=0;for(size_t i=0;i<s->count;i++)total+=s->amplitudes[i].re*s->amplitudes[i].re+s->amplitudes[i].im*s->amplitudes[i].im;return total;}
