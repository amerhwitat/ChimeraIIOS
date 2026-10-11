#include "chimera/ipc.h"
#include "chimera/nbit.h"

namespace {
struct Message {
    uint32_t sender_pid=0, sender_mode_bits=0, receiver_mode_bits=0;
    uint32_t payload_bits=0, payload_bytes=0;
    uint64_t sequence=0;
    bool occupied=false, in_flight=false;
    uint8_t payload[CHIMERA_IPC_MAX_PAYLOAD]{};
};
struct Endpoint {
    uint32_t id=0, owner_pid=0, head=0, count=0;
    uint64_t capability=0;
    bool used=false;
    Message queue[CHIMERA_IPC_QUEUE_DEPTH]{};
};
Endpoint endpoints[CHIMERA_IPC_MAX_ENDPOINTS];
chimera_ipc_service_ops service_ops{};
uint32_t service_lock=0;
bool initialized=false;
void lock_service(){while(__sync_lock_test_and_set(&service_lock,1u)){}}
void unlock_service(){__sync_lock_release(&service_lock);}
int endpoint_index(uint32_t id) {
    if(!id)return -1;
    for(uint32_t i=0;i<CHIMERA_IPC_MAX_ENDPOINTS;++i)
        if(endpoints[i].used&&endpoints[i].id==id)return (int)i;
    return -1;
}
bool registered(uint32_t pid, chimera_nbit_process_context *ctx) {
    return pid!=0 && chimera_nbit_process_get(pid,ctx)==0;
}
void clear_message(Message &m){m=Message{};}
void clear_endpoint(Endpoint &e){e=Endpoint{};}
}

extern "C" int chimera_ipc_service_init(const chimera_ipc_service_ops *ops) {
    if(!ops||!ops->copy_from_user||!ops->copy_to_user)return -1;
    lock_service();
    for(uint32_t i=0;i<CHIMERA_IPC_MAX_ENDPOINTS;++i)clear_endpoint(endpoints[i]);
    service_ops=*ops; initialized=true;
    unlock_service();
    return 0;
}
extern "C" int chimera_ipc_endpoint_bind(uint32_t owner_pid,uint32_t id,uint64_t capability) {
    chimera_nbit_process_context owner{};
    if(!id||!capability||!registered(owner_pid,&owner))return -1;
    lock_service();
    if(!initialized){unlock_service();return -2;}
    if(endpoint_index(id)>=0){unlock_service();return -3;}
    for(uint32_t i=0;i<CHIMERA_IPC_MAX_ENDPOINTS;++i)if(!endpoints[i].used){
        endpoints[i].id=id;endpoints[i].owner_pid=owner_pid;
        endpoints[i].capability=capability;endpoints[i].used=true;
        unlock_service();return 0;
    }
    unlock_service();return -4;
}
extern "C" int chimera_ipc_endpoint_unbind(uint32_t owner_pid,uint32_t id,uint64_t capability) {
    lock_service();int i=endpoint_index(id);
    if(i<0){unlock_service();return -1;}
    Endpoint &e=endpoints[(uint32_t)i];
    if(e.owner_pid!=owner_pid||e.capability!=capability){unlock_service();return -2;}
    for(uint32_t q=0;q<e.count;++q)
        if(e.queue[(e.head+q)%CHIMERA_IPC_QUEUE_DEPTH].in_flight){unlock_service();return -3;}
    clear_endpoint(e);unlock_service();return 0;
}
extern "C" int chimera_ipc_send(uint32_t sender_pid,uint32_t id,uint64_t capability,
                                  const void *user_payload,uint32_t payload_bits,uint64_t sequence) {
    chimera_nbit_process_context sender{};
    if(!user_payload||!payload_bits||!registered(sender_pid,&sender))return -1;
    const uint64_t bytes64=((uint64_t)payload_bits+7u)/8u;
    if(bytes64>CHIMERA_IPC_MAX_PAYLOAD)return -2;
    chimera_ipc_service_ops ops{};
    lock_service();
    if(!initialized){unlock_service();return -3;}
    ops=service_ops;unlock_service();
    uint8_t staged[CHIMERA_IPC_MAX_PAYLOAD]{};
    if(ops.copy_from_user(ops.context,sender_pid,staged,user_payload,(uint32_t)bytes64)!=0)return -4;
    lock_service();int i=endpoint_index(id);
    if(i<0){unlock_service();return -5;}
    Endpoint &e=endpoints[(uint32_t)i];
    if(e.capability!=capability){unlock_service();return -6;}
    chimera_nbit_process_context receiver{};
    if(!registered(e.owner_pid,&receiver)){unlock_service();return -7;}
    if(e.count>=CHIMERA_IPC_QUEUE_DEPTH){unlock_service();return -8;}
    const uint32_t slot=(e.head+e.count)%CHIMERA_IPC_QUEUE_DEPTH;
    Message &m=e.queue[slot];
    if(m.occupied){unlock_service();return -9;}
    m.sender_pid=sender_pid;m.sender_mode_bits=sender.mode_bits;
    m.receiver_mode_bits=receiver.mode_bits;m.payload_bits=payload_bits;
    m.payload_bytes=(uint32_t)bytes64;m.sequence=sequence;m.occupied=true;m.in_flight=false;
    for(uint32_t b=0;b<m.payload_bytes;++b)m.payload[b]=staged[b];
    ++e.count;unlock_service();return (int)bytes64;
}
extern "C" int chimera_ipc_receive(uint32_t receiver_pid,uint32_t id,uint64_t capability,
                                     void *user_buffer,uint32_t capacity,chimera_ipc_message_info *out) {
    if(!user_buffer||!out)return -1;
    chimera_nbit_process_context receiver{};
    if(!registered(receiver_pid,&receiver))return -2;
    uint8_t staged[CHIMERA_IPC_MAX_PAYLOAD]{};
    chimera_ipc_message_info info{};
    uint64_t sequence=0;
    chimera_ipc_service_ops ops{};
    lock_service();int i=endpoint_index(id);
    if(i<0){unlock_service();return -3;}
    Endpoint &e=endpoints[(uint32_t)i];
    if(e.owner_pid!=receiver_pid||e.capability!=capability){unlock_service();return -4;}
    if(!e.count){unlock_service();return 0;}
    Message &m=e.queue[e.head];
    if(!m.occupied||m.in_flight){unlock_service();return -5;}
    if(capacity<m.payload_bytes){unlock_service();return -6;}
    m.in_flight=true;sequence=m.sequence;ops=service_ops;
    info.sender_pid=m.sender_pid;info.sender_mode_bits=m.sender_mode_bits;
    info.receiver_mode_bits=m.receiver_mode_bits;info.payload_bits=m.payload_bits;
    info.payload_bytes=m.payload_bytes;info.sequence=m.sequence;
    for(uint32_t b=0;b<m.payload_bytes;++b)staged[b]=m.payload[b];
    unlock_service();
    if(ops.copy_to_user(ops.context,receiver_pid,user_buffer,staged,info.payload_bytes)!=0){
        lock_service();i=endpoint_index(id);
        if(i>=0){Endpoint &again=endpoints[(uint32_t)i];if(again.count){
            Message &head=again.queue[again.head];
            if(head.occupied&&head.sequence==sequence)head.in_flight=false;
        }}unlock_service();return -7;
    }
    lock_service();i=endpoint_index(id);
    if(i<0){unlock_service();return -8;}
    Endpoint &again=endpoints[(uint32_t)i];
    if(again.owner_pid!=receiver_pid||!again.count){unlock_service();return -8;}
    Message &head=again.queue[again.head];
    if(!head.occupied||!head.in_flight||head.sequence!=sequence){unlock_service();return -8;}
    clear_message(head);again.head=(again.head+1u)%CHIMERA_IPC_QUEUE_DEPTH;--again.count;
    unlock_service();*out=info;return (int)info.payload_bytes;
}
extern "C" int chimera_ipc_cancel(uint32_t sender_pid,uint32_t id,uint64_t sequence) {
    lock_service();int i=endpoint_index(id);
    if(i<0){unlock_service();return -1;}
    Endpoint &e=endpoints[(uint32_t)i];
    for(uint32_t q=0;q<e.count;++q){
        uint32_t slot=(e.head+q)%CHIMERA_IPC_QUEUE_DEPTH;Message &m=e.queue[slot];
        if(m.occupied&&m.sender_pid==sender_pid&&m.sequence==sequence){
            if(m.in_flight){unlock_service();return -2;}
            /* Keep FIFO order: cancellation marks a tombstone, drained by receive. */
            m.sender_pid=0;m.payload_bytes=0;m.payload_bits=0;
            unlock_service();return 0;
        }
    }
    unlock_service();return -3;
}
extern "C" void chimera_ipc_process_exit(uint32_t pid) {
    if(!pid)return;
    lock_service();
    for(uint32_t i=0;i<CHIMERA_IPC_MAX_ENDPOINTS;++i){
        Endpoint &e=endpoints[i];if(!e.used)continue;
        if(e.owner_pid==pid){
            bool busy=false;for(uint32_t q=0;q<e.count;++q)
                if(e.queue[(e.head+q)%CHIMERA_IPC_QUEUE_DEPTH].in_flight)busy=true;
            if(!busy)clear_endpoint(e);
            continue;
        }
        uint32_t kept=0;Message temp[CHIMERA_IPC_QUEUE_DEPTH]{};
        for(uint32_t q=0;q<e.count;++q){
            Message &m=e.queue[(e.head+q)%CHIMERA_IPC_QUEUE_DEPTH];
            if(m.occupied&&m.sender_pid!=pid){temp[kept++]=m;}
        }
        for(uint32_t q=0;q<CHIMERA_IPC_QUEUE_DEPTH;++q)clear_message(e.queue[q]);
        for(uint32_t q=0;q<kept;++q)e.queue[q]=temp[q];
        e.head=0;e.count=kept;
    }
    unlock_service();
}
extern "C" uint32_t chimera_ipc_queued_messages(uint32_t id) {
    lock_service();int i=endpoint_index(id);
    uint32_t n=i<0?0:endpoints[(uint32_t)i].count;
    unlock_service();return n;
}
