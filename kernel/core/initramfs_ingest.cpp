#include "chimera/initramfs_ingest.h"
#include "chimera/gzip.h"
#include <stdint.h>
namespace {
static bool gzip_magic(const uint8_t *p,uint64_t n){return n>=2u&&p[0]==0x1fu&&p[1]==0x8bu;}
}
extern "C" int chimera_initramfs_prepare_newc(const void *input,uint64_t input_size,
                                                void *workspace,uint64_t workspace_capacity,
                                                uint64_t *archive_size,chimera_cpio_summary *summary) {
    if(archive_size)*archive_size=0;
    if(summary)*summary=chimera_cpio_summary{};
    if(!input||!workspace||!archive_size||!summary)return CHIMERA_CPIO_E_ARGUMENT;
    if(input_size==0u||input_size>CHIMERA_INITRAMFS_MAX_INPUT_BYTES||
       workspace_capacity>CHIMERA_CPIO_MAX_ARCHIVE_BYTES||workspace_capacity<110u)
        return CHIMERA_CPIO_E_LIMIT;
    const uintptr_t in_addr=reinterpret_cast<uintptr_t>(input);
    const uintptr_t out_addr=reinterpret_cast<uintptr_t>(workspace);
    if(input_size>UINTPTR_MAX-in_addr||workspace_capacity>UINTPTR_MAX-out_addr)
        return CHIMERA_CPIO_E_ARGUMENT;
    /* Do not permit in-place or partial-overlap decompression: writes must not
       overwrite bytes the inflater has yet to consume. */
    if(in_addr<out_addr+workspace_capacity&&out_addr<in_addr+input_size)
        return CHIMERA_CPIO_E_ARGUMENT;
    const auto *src=static_cast<const uint8_t*>(input);
    auto *dst=static_cast<uint8_t*>(workspace);
    uint64_t produced=0;
    if(gzip_magic(src,input_size)) {
        const int rc=chimera_gzip_decompress_bounded(input,input_size,workspace,workspace_capacity,&produced);
        if(rc!=0)return CHIMERA_CPIO_E_COMPRESSION;
    } else {
        if(input_size>workspace_capacity||input_size>CHIMERA_CPIO_MAX_ARCHIVE_BYTES)
            return CHIMERA_CPIO_E_LIMIT;
        if(input!=workspace)for(uint64_t i=0;i<input_size;++i)dst[i]=src[i];
        produced=input_size;
    }
    chimera_cpio_summary checked{};
    const int rc=chimera_cpio_validate_newc(workspace,produced,&checked);
    if(rc!=CHIMERA_CPIO_OK)return rc;
    *archive_size=produced;*summary=checked;return CHIMERA_CPIO_OK;
}
