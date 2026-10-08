#include "chimera_nbit_runtime.h"
#include <string.h>
#include <limits.h>
static uint64_t addc(uint64_t a,uint64_t b,uint64_t c,uint64_t *o){uint64_t x=a+b, c1=x<a, y=x+c, c2=y<x;*o=y;return c1|c2;}
int chimera_nbit_add_u64(uint64_t *o,const uint64_t*a,const uint64_t*b,size_t n,uint64_t*carry){if(!o||!a||!b||!n)return -1;uint64_t c=0;for(size_t i=0;i<n;i++)c=addc(a[i],b[i],c,&o[i]);if(carry)*carry=c;return 0;}
int chimera_nbit_sub_u64(uint64_t *o,const uint64_t*a,const uint64_t*b,size_t n,uint64_t*borrow){if(!o||!a||!b||!n)return -1;uint64_t c=0;for(size_t i=0;i<n;i++){uint64_t x=a[i]-b[i],b1=a[i]<b[i],y=x-c,b2=x<c;o[i]=y;c=b1|b2;}if(borrow)*borrow=c;return 0;}
int chimera_nbit_mul_u64(uint64_t*o,size_t on,const uint64_t*a,size_t an,const uint64_t*b,size_t bn){if(!o||!a||!b||!on||!an||!bn)return -1;memset(o,0,on*sizeof(*o));for(size_t i=0;i<an&&i<on;i++){uint64_t carry=0;for(size_t j=0;j<bn&&i+j<on;j++){size_t k=i+j;
#if defined(__SIZEOF_INT128__)
__uint128_t z=(__uint128_t)a[i]*b[j]+o[k]+carry;o[k]=(uint64_t)z;carry=(uint64_t)(z>>64);
#else
/* Portable 32-bit partial products. */
uint64_t a0=(uint32_t)a[i],a1=a[i]>>32,b0=(uint32_t)b[j],b1=b[j]>>32;
uint64_t p0=a0*b0,p1=a0*b1,p2=a1*b0,p3=a1*b1;
uint64_t lo=p0,hi=p3+(p1>>32)+(p2>>32);uint64_t t=p1<<32,old=lo;lo+=t;hi+=lo<old;t=p2<<32;old=lo;lo+=t;hi+=lo<old;old=lo;lo+=o[k];hi+=lo<old;old=lo;lo+=carry;hi+=lo<old;o[k]=lo;carry=hi;
#endif
}if(i+bn<on)o[i+bn]=carry;}return 0;}
int chimera_nbit_and_u64(uint64_t*o,const uint64_t*a,const uint64_t*b,size_t n){if(!o||!a||!b||!n)return -1;for(size_t i=0;i<n;i++)o[i]=a[i]&b[i];return 0;}
int chimera_nbit_or_u64(uint64_t*o,const uint64_t*a,const uint64_t*b,size_t n){if(!o||!a||!b||!n)return -1;for(size_t i=0;i<n;i++)o[i]=a[i]|b[i];return 0;}
int chimera_nbit_xor_u64(uint64_t*o,const uint64_t*a,const uint64_t*b,size_t n){if(!o||!a||!b||!n)return -1;for(size_t i=0;i<n;i++)o[i]=a[i]^b[i];return 0;}
int chimera_nbit_not_u64(uint64_t*o,const uint64_t*a,size_t n){if(!o||!a||!n)return -1;for(size_t i=0;i<n;i++)o[i]=~a[i];return 0;}
int chimera_nbit_shl_u64(uint64_t*o,const uint64_t*a,size_t n,size_t s){if(!o||!a||!n)return -1;size_t words=s/64,bits=s%64;for(size_t i=n;i-->0;){uint64_t v=0;if(i>=words){v=a[i-words]<<bits;if(bits&&i>words)v|=a[i-words-1]>>(64-bits);}o[i]=v;}return 0;}
int chimera_nbit_shr_u64(uint64_t*o,const uint64_t*a,size_t n,size_t s){if(!o||!a||!n)return -1;size_t words=s/64,bits=s%64;for(size_t i=0;i<n;i++){uint64_t v=0;if(i+words<n){v=a[i+words]>>bits;if(bits&&i+words+1<n)v|=a[i+words+1]<<(64-bits);}o[i]=v;}return 0;}
int chimera_nbit_cmp_u64(const uint64_t*a,const uint64_t*b,size_t n){if(!a||!b||!n)return 0;for(size_t i=n;i-->0;)if(a[i]!=b[i])return a[i]<b[i]?-1:1;return 0;}
static int zero(const uint64_t*a,size_t n){uint64_t v=0;for(size_t i=0;i<n;i++)v|=a[i];return v==0;}
static void shift1(uint64_t*a,size_t n,uint64_t bit){for(size_t i=0;i<n;i++){uint64_t c=a[i]>>63;a[i]=(a[i]<<1)|bit;bit=c;}}
int chimera_nbit_divmod_u64(uint64_t*q,uint64_t*r,const uint64_t*a,size_t n,const uint64_t*b,size_t m){if(!q||!r||!a||!b||!n||!m)return -1;if(zero(b,m))return -2;memset(q,0,n*sizeof(*q));memset(r,0,m*sizeof(*r));for(size_t bit=n*64;bit-->0;){uint64_t in=(a[bit/64]>>(bit%64))&1;shift1(r,m,in);if(chimera_nbit_cmp_u64(r,b,m)>=0){uint64_t borrow=0;chimera_nbit_sub_u64(r,r,b,m,&borrow);q[bit/64]|=UINT64_C(1)<<(bit%64);}}return 0;}
#define FLOAT_OP(NAME,TYPE,UINTTYPE,FROM,TO,OP) UINTTYPE NAME(UINTTYPE aa,UINTTYPE bb){TYPE a,b,c;memcpy(&a,&aa,sizeof a);memcpy(&b,&bb,sizeof b);volatile TYPE x=a,y=b; c=x OP y;UINTTYPE out;memcpy(&out,&c,sizeof out);return out;}
FLOAT_OP(chimera_nbit_f32_add,float,uint32_t,0,0,+)
FLOAT_OP(chimera_nbit_f32_mul,float,uint32_t,0,0,*)
FLOAT_OP(chimera_nbit_f32_div,float,uint32_t,0,0,/)
FLOAT_OP(chimera_nbit_f64_add,double,uint64_t,0,0,+)
FLOAT_OP(chimera_nbit_f64_mul,double,uint64_t,0,0,*)
FLOAT_OP(chimera_nbit_f64_div,double,uint64_t,0,0,/)
