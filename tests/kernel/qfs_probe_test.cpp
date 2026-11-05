#include "chimera/qfs_probe.h"
#include <assert.h>
#include <stdint.h>
#include <string.h>

namespace {
uint8_t media[512u * 512u]{};
void put32(uint8_t *p, uint32_t v) {
    p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); p[2]=(uint8_t)(v>>16); p[3]=(uint8_t)(v>>24);
}
void put64(uint8_t *p, uint64_t v) {
    put32(p,(uint32_t)v); put32(p+4,(uint32_t)(v>>32));
}
int read_media(void *, uint64_t lba, uint32_t count, void *buffer) {
    memcpy(buffer,media+lba*512u,(size_t)count*512u); return 0;
}
int write_media(void *, uint64_t lba, uint32_t count, const void *buffer) {
    memcpy(media+lba*512u,buffer,(size_t)count*512u); return 0;
}
void make_header() {
    memset(media,0,sizeof(media));
    put32(media,CHIMERA_QFS_MAGIC); put32(media+4,CHIMERA_QFS_VERSION);
    put32(media+8,4096); put32(media+12,512);
    put64(media+16,64); put64(media+24,1); put64(media+32,8); put64(media+40,1);
    for(unsigned i=0;i<16;i++) media[48+i]=(uint8_t)(i+1);
}
}
int main() {
    const chimera_block_ops ops{read_media,write_media,nullptr};
    uint32_t handle=0;
    assert(chimera_block_register("qfs-test",512,512,0,&ops,nullptr,&handle)==0);
    make_header();
    chimera_qfs_probe_info info{};
    assert(chimera_qfs_probe(handle,&info)==0);
    assert(info.abi==CHIMERA_QFS_PROBE_ABI && info.block_size==4096);
    assert(info.total_blocks==64 && info.data_start==8 && info.root_inode==1);
    put32(media+8,2048);
    assert(chimera_qfs_probe(handle,&info)==CHM_BLOCK_EINVAL);
    make_header(); put64(media+16,UINT64_MAX);
    assert(chimera_qfs_probe(handle,&info)==CHM_BLOCK_EINVAL);
    make_header(); put32(media,0);
    assert(chimera_qfs_probe(handle,&info)==CHM_BLOCK_ENOTSUP);
    assert(chimera_block_unregister(handle)==0);
    return 0;
}
