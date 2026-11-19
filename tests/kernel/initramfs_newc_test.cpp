#include "chimera/initramfs_newc.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <vector>
#include <string>

static void hexfield(std::vector<uint8_t>& out, uint32_t value) {
    static const char digits[]="0123456789abcdef";
    for(int i=7;i>=0;--i) out.push_back((uint8_t)digits[(value>>(i*4))&15u]);
}
static void pad4(std::vector<uint8_t>& out) { while(out.size()&3u) out.push_back(0); }
static void append(std::vector<uint8_t>& out,const char* name,const char* data,uint32_t mode,bool crc=false) {
    const uint32_t n=(uint32_t)strlen(name)+1u, z=data?(uint32_t)strlen(data):0u;
    uint32_t sum=0; for(uint32_t i=0;i<z;i++) sum+=(uint8_t)data[i];
    const char* magic=crc?"070702":"070701"; out.insert(out.end(),magic,magic+6);
    hexfield(out,1);hexfield(out,mode);hexfield(out,0);hexfield(out,0);hexfield(out,1);
    hexfield(out,0);hexfield(out,z);hexfield(out,0);hexfield(out,0);hexfield(out,0);
    hexfield(out,0);hexfield(out,n);hexfield(out,crc?sum:0);
    out.insert(out.end(),name,name+n);pad4(out);
    if(z) out.insert(out.end(),data,data+z);pad4(out);
}
static int visit(void* p,const koronos_newc_entry* e) {
    uint32_t* count=(uint32_t*)p; ++*count;
    assert(e->name_size>0); assert(e->name[e->name_size]==0);
    return 0;
}
int main() {
    std::vector<uint8_t> archive;
    append(archive,"./etc","",KORONOS_NEWC_DIR);
    append(archive,"./init","hello",KORONOS_NEWC_REG,true);
    append(archive,"TRAILER!!!",nullptr,KORONOS_NEWC_REG);
    koronos_newc_result result{}; uint32_t visited=0;
    assert(koronos_newc_walk(archive.data(),archive.size(),visit,&visited,&result)==0);
    assert(visited==2 && result.entries==2 && result.directories==1);
    assert(result.regular_files==1 && result.payload_bytes==5);

    std::vector<uint8_t> traversal;
    append(traversal,"../escape","x",KORONOS_NEWC_REG);
    append(traversal,"TRAILER!!!",nullptr,KORONOS_NEWC_REG);
    assert(koronos_newc_walk(traversal.data(),traversal.size(),nullptr,nullptr,&result)==-1);
    assert(koronos_newc_walk(traversal.data(),traversal.size(),nullptr,nullptr,&result)==-1);

    std::vector<uint8_t> badpath;
    append(badpath,"../escape","x",KORONOS_NEWC_REG);
    append(badpath,"TRAILER!!!",nullptr,KORONOS_NEWC_REG);
    assert(koronos_newc_walk(badpath.data(),badpath.size(),nullptr,(void*)1,&result)==-6);

    archive.pop_back();
    assert(koronos_newc_walk(archive.data(),archive.size(),nullptr,nullptr,&result)!=0);
    puts("Koronos newc initramfs parser tests: OK");
    return 0;
}
