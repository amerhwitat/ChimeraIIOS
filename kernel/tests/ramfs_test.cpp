#include "chimera/ramfs.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
static void*alloc_cb(uint64_t n,void*){return malloc((size_t)n);}static void free_cb(void*p,void*){free(p);}
static size_t entry(uint8_t*b,size_t o,const char*name,uint32_t mode,const char*data){size_t nl=strlen(name)+1,sz=data?strlen(data):0;memset(b+o,'0',110);memcpy(b+o,"070701",6);uint32_t v[13]={1,mode,0,0,1,0,(uint32_t)sz,0,0,0,0,(uint32_t)nl,0};for(int k=0;k<13;k++){char x[9];snprintf(x,sizeof(x),"%08x",v[k]);memcpy(b+o+6+k*8,x,8);}o+=110;memcpy(b+o,name,nl);o=(o+nl+3)&~(size_t)3;if(sz)memcpy(b+o,data,sz);o=(o+sz+3)&~(size_t)3;return o;}
static size_t make_archive(uint8_t*b,int duplicate){size_t n=0;n=entry(b,n,".",0040000,nullptr);n=entry(b,n,"bin",0040000,nullptr);n=entry(b,n,"bin/init",0100000,"hello");if(duplicate)n=entry(b,n,"bin/init",0100000,"again");return entry(b,n,"TRAILER!!!",0,nullptr);}
int main(){chimera_ramfs_allocator a{alloc_cb,free_cb,nullptr};chimera_ramfs_limits l{128,255,1048576,4194304};uint8_t b[4096]{};size_t n=make_archive(b,0);chimera_ramfs_node*r=nullptr;assert(chimera_ramfs_extract_newc(b,n,&a,&l,&r)==CHIMERA_RAMFS_OK);auto*f=chimera_ramfs_lookup(r,"/bin/init");assert(f&&chimera_ramfs_file_size(f)==5);char out[8]{};uint64_t got=0;assert(chimera_ramfs_read(f,0,out,sizeof(out),&got)==0&&got==5&&!memcmp(out,"hello",5));assert(!chimera_ramfs_lookup(r,"/bin/../init"));chimera_ramfs_destroy(r,&a);memset(b,0,sizeof(b));n=make_archive(b,1);r=nullptr;assert(chimera_ramfs_extract_newc(b,n,&a,&l,&r)==CHIMERA_RAMFS_E_DUPLICATE&&!r);puts("RAMFS transactional extraction tests passed");}
