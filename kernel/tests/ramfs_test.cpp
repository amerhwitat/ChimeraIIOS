#include "chimera/ramfs.h"
#include "chimera/initramfs_cpio.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
struct alloc_state { int fail_at; int calls; int outstanding; };
static void* alloc_cb(uint64_t n,void*ctx) {
    auto*s=static_cast<alloc_state*>(ctx);const int call=s->calls++;
    if(s->fail_at>=0&&call==s->fail_at)return nullptr;
    void*p=malloc((size_t)n);if(p)++s->outstanding;return p;
}
static void free_cb(void*p,void*ctx) {
    if(!p)return;
    auto*s=static_cast<alloc_state*>(ctx);
    assert(s->outstanding>0);
    --s->outstanding;
    free(p);
}
static size_t entry(uint8_t*b,size_t o,const char*name,uint32_t mode,const char*data) {
    size_t nl=strlen(name)+1,sz=data?strlen(data):0;
    memset(b+o,'0',110);memcpy(b+o,"070701",6);
    uint32_t v[13]={1,mode,0,0,1,0,(uint32_t)sz,0,0,0,0,(uint32_t)nl,0};
    for(int k=0;k<13;k++){char x[9];snprintf(x,sizeof(x),"%08x",v[k]);memcpy(b+o+6+k*8,x,8);}
    o+=110;memcpy(b+o,name,nl);o=(o+nl+3)&~(size_t)3;
    if(sz)memcpy(b+o,data,sz);
    o=(o+sz+3)&~(size_t)3;
    return o;
}
static size_t make_archive(uint8_t*b,int duplicate) {
    size_t n=0;n=entry(b,n,".",0040000,nullptr);n=entry(b,n,"./bin",0040000,nullptr);
    n=entry(b,n,"./bin/init",0100755,"hello");
    n=entry(b,n,"./bin/busybox",0100000,"applet");
    n=entry(b,n,"./bin/sh",0120000,"busybox");
    if(duplicate)n=entry(b,n,"bin/init",0100000,"again");
    return entry(b,n,"TRAILER!!!",0,nullptr);
}
int main() {
    /* Output pointers are cleared even when argument validation fails. */
    chimera_ramfs_node *invalid_out=reinterpret_cast<chimera_ramfs_node*>(uintptr_t(1));
    assert(chimera_ramfs_extract_newc(nullptr,0,nullptr,nullptr,&invalid_out)==CHIMERA_RAMFS_E_ARGUMENT);
    assert(invalid_out==nullptr);

    alloc_state state{-1,0,0};chimera_ramfs_allocator a{alloc_cb,free_cb,&state};
    chimera_ramfs_limits l{128,255,1048576,4194304};uint8_t b[4096]{};
    size_t n=make_archive(b,0);
    chimera_cpio_summary summary{};
    assert(chimera_cpio_validate_newc(b,n,&summary)==CHIMERA_CPIO_OK);
    chimera_cpio_entry entry_view{};
    assert(chimera_cpio_lookup_executable_newc(b,n,"/bin/init",&entry_view)==CHIMERA_CPIO_OK);
    assert(entry_view.size==5u && entry_view.data && !memcmp(entry_view.data,"hello",5));
    assert(chimera_cpio_lookup_newc(b,n,"bin/missing",&entry_view)==CHIMERA_CPIO_E_NOT_FOUND);
    assert(entry_view.data==nullptr && entry_view.size==0u);
    assert(chimera_cpio_lookup_executable_newc(b,n,"/bin/sh",&entry_view)==CHIMERA_CPIO_E_TYPE);
    assert(chimera_cpio_lookup_newc(b,n,"/bin/../init",&entry_view)==CHIMERA_CPIO_E_PATH);
    char oversized_path[CHIMERA_CPIO_MAX_PATH + 2];
    memset(oversized_path,'a',sizeof(oversized_path));
    oversized_path[sizeof(oversized_path)-1]=0;
    assert(chimera_cpio_lookup_newc(b,n,oversized_path,&entry_view)==CHIMERA_CPIO_E_PATH);
    assert(entry_view.data==nullptr && entry_view.size==0u);
    chimera_ramfs_node*r=nullptr;
    assert(chimera_ramfs_extract_newc(b,n,&a,&l,&r)==CHIMERA_RAMFS_OK);
    auto*f=chimera_ramfs_lookup(r,"/bin/init");assert(f&&chimera_ramfs_file_size(f)==5);
    char out[8]{};uint64_t got=0;
    assert(chimera_ramfs_read(f,0,out,sizeof(out),&got)==0&&got==5&&!memcmp(out,"hello",5));
    auto*link=chimera_ramfs_lookup(r,"/bin/sh");
    assert(link&&chimera_ramfs_file_size(link)==6);
    memset(out,0,sizeof(out));got=0;
    assert(chimera_ramfs_read(link,0,out,sizeof(out),&got)==0&&got==6&&!memcmp(out,"applet",6));
    assert(!chimera_ramfs_lookup(r,"/bin/../init"));
    chimera_ramfs_destroy(r,&a);assert(state.outstanding==0);
    memset(b,0,sizeof(b));n=make_archive(b,1);r=nullptr;
    assert(chimera_ramfs_extract_newc(b,n,&a,&l,&r)!=CHIMERA_RAMFS_OK&&!r);
    assert(state.outstanding==0);
    memset(b,0,sizeof(b));n=0;n=entry(b,n,".",0040000,nullptr);
    n=entry(b,n,"bin",0040000,"not-a-directory");n=entry(b,n,"TRAILER!!!",0,nullptr);
    r=nullptr;assert(chimera_ramfs_extract_newc(b,n,&a,&l,&r)==CHIMERA_RAMFS_E_TYPE&&!r);
    assert(state.outstanding==0);
    memset(b,0,sizeof(b));n=make_archive(b,0);
    for(int fail_at=0;fail_at<32;++fail_at) {
        state.fail_at=fail_at;state.calls=0;state.outstanding=0;r=nullptr;
        const int rc=chimera_ramfs_extract_newc(b,n,&a,&l,&r);
        if(rc==CHIMERA_RAMFS_OK){assert(r);chimera_ramfs_destroy(r,&a);r=nullptr;}
        else assert(!r);
        assert(state.outstanding==0);
    }
    state.fail_at=-1;state.calls=0;
    puts("RAMFS transactional extraction and allocation-failure rollback tests passed");
}
