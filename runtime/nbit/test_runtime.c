#include "chimera_nbit_runtime.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 uint64_t a[2]={UINT64_MAX,0},b[2]={1,0},o[2],c=0;
 assert(chimera_nbit_add_u64(o,a,b,2,&c)==0&&o[0]==0&&o[1]==1&&c==0);
 assert(chimera_nbit_sub_u64(o,b,a,2,&c)==0&&o[0]==2&&c==1);
 uint64_t x[2]={3,0},y[2]={7,0},p[2];assert(chimera_nbit_mul_u64(p,2,x,1,y,1)==0&&p[0]==21);
 assert(chimera_nbit_and_u64(o,x,y,2)==0&&o[0]==3);
 assert(chimera_nbit_shl_u64(o,x,2,65)==0&&o[1]==6);
 assert(chimera_nbit_shr_u64(o,o,2,65)==0&&o[0]==3);
 uint64_t q[2],rem[2],num[2]={100,0},den[2]={7,0};assert(chimera_nbit_divmod_u64(q,rem,num,2,den,2)==0&&q[0]==14&&rem[0]==2);
 den[0]=0;assert(chimera_nbit_divmod_u64(q,rem,num,2,den,2)==-2);
 assert(chimera_nbit_cmp_u64(a,b,2)==1);
 puts("nbit runtime: 8 checks passed");return 0;
}
