#include "chimera/ipc.h"
#include "chimera/nbit.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static int copy_from(void *,uint32_t,void *dst,const void *src,uint32_t n){
    if(!dst||!src)return -1;memcpy(dst,src,n);return 0;
}
static int copy_to(void *,uint32_t,void *dst,const void *src,uint32_t n){
    if(!dst||!src)return -1;memcpy(dst,src,n);return 0;
}
int main(){
    assert(chimera_nbit_init()==0);
    chimera_nbit_process_context sender{},receiver{},other{};
    assert(chimera_nbit_process_init(&sender,101,32,0)==0);
    assert(chimera_nbit_process_init(&receiver,202,128,0)==0);
    assert(chimera_nbit_process_init(&other,303,64,CHIMERA_COMPAT_LINUX)==0);
    chimera_ipc_service_ops ops{};ops.copy_from_user=copy_from;ops.copy_to_user=copy_to;
    assert(chimera_ipc_service_init(&ops)==0);
    const uint64_t cap=0x91a2b3c4d5e6f708ull;
    assert(chimera_ipc_endpoint_bind(202,77,cap)==0);
    assert(chimera_ipc_endpoint_bind(202,77,cap)==-3);
    const uint8_t payload[]={0x43,0x48};
    assert(chimera_ipc_send(101,77,cap^1u,payload,13,1)==-6);
    assert(chimera_ipc_send(101,77,cap,payload,13,1)==2);
    assert(chimera_ipc_queued_messages(77)==1);
    chimera_ipc_message_info unauthorized_info{};
    uint8_t unauthorized_buffer[2]{};
    assert(chimera_ipc_receive(303,77,cap,unauthorized_buffer,sizeof(unauthorized_buffer),&unauthorized_info)==-4);
    assert(chimera_ipc_cancel(101,77,1)==0);
    assert(chimera_ipc_queued_messages(77)==0);
    for(uint64_t seq=10;seq<10+CHIMERA_IPC_QUEUE_DEPTH;++seq)
        assert(chimera_ipc_send(101,77,cap,payload,13,seq)==2);
    assert(chimera_ipc_send(101,77,cap,payload,13,999)==-8);
    uint8_t output[2]={};
    chimera_ipc_message_info info{};
    assert(chimera_ipc_receive(202,77,cap,output,sizeof(output),&info)==2);
    assert(info.sender_pid==101&&info.sender_mode_bits==32&&info.receiver_mode_bits==128);
    assert(info.payload_bits==13&&info.payload_bytes==2&&info.sequence==10);
    assert(output[0]==payload[0]&&output[1]==payload[1]);
    chimera_ipc_process_exit(101);
    assert(chimera_ipc_queued_messages(77)==0);
    assert(chimera_ipc_endpoint_unbind(303,77,cap)==-2);
    assert(chimera_ipc_endpoint_unbind(202,77,cap)==0);
    assert(chimera_nbit_process_unregister(101)==0);
    assert(chimera_nbit_process_unregister(202)==0);
    assert(chimera_nbit_process_unregister(303)==0);
    puts("Capability IPC service, bounded queues, cross-width delivery, cancellation, and cleanup passed.");
    return 0;
}
