#include <assert.h>
#include "chm_quantum.h"
int main(void){chm_qc_state*s=chm_qc_create(2);assert(s);assert(chm_qc_h(s,0)==0);assert(chm_qc_cx(s,0,1)==0);unsigned long long b=0;assert(chm_qc_measure(s,42,&b)==0);assert(b==2);chm_qc_destroy(s);return 0;}
