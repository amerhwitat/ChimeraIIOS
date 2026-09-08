#include "chimera/isa8192.hpp"
#include <array>
#include <stdexcept>

namespace chimera {
namespace {

constexpr std::array<std::string_view, 0x11D> kNames = [] {
    std::array<std::string_view, 0x11D> a{};
    constexpr std::string_view names =
        "ADD SUB AND OR XOR NOT SHL SHR ROL ROR MUL MULHI MULMOD MODEXP BARRETT DIV REM CMP CMPEQ CMPLT MOV LOAD STORE PREFETCH MEMCPY MEMSET "
        "PIN_PAGES UNPIN_PAGES DMA_MAP DMA_UNMAP DMA_START DMA_WAIT IOMMU_MAP IOMMU_UNMAP GET_FRAME_DESC RELEASE_FRAME XDP_SEND_ZC XDP_RECV_ZC XDP_GET_EVENTFD NETMAP_SEND NETMAP_RECV NIC_REGISTER NIC_UNREGISTER IOCTL IOCTL_RESPOND SYSLOG_WRITE AUDIT_LOG TPM_EXTEND TPM_SEAL TPM_UNSEAL SIGN_VERIFY VERIFY_SIGNATURE LOAD_MODULE UNLOAD_MODULE MODULE_SIGN MODULE_VERIFY KASLR_RESEED RNG_READ RNG_SEED HASH SHA256 SHA512 AESENC AESDEC RSAKEYGEN RSAMOD ECC_POINT_ADD ECC_POINT_MUL RNG_WAIT TRAP SYS_CALL SVC IRQ_ENABLE IRQ_DISABLE CACHE_FLUSH CACHE_INVALIDATE TRACE_START TRACE_STOP DEBUG_BREAK WATCHPOINT_SET WATCHPOINT_CLEAR PERF_EVENT POWER_STATE CLOCK_GET TIMER_SET TIMER_CANCEL CONTEXT_SWITCH TASK_CREATE TASK_EXIT TASK_YIELD TASK_JOIN LOCK_ACQUIRE LOCK_RELEASE RCU_READ_LOCK RCU_READ_UNLOCK RCU_SYNCHRONIZE SLAB_ALLOC SLAB_FREE PAGE_ALLOC PAGE_FREE KMAP KUNMAP USER_COPY_FROM USER_COPY_TO PIN_PAGES_IOCTL MAP_FRAME UNMAP_FRAME RECLAIM_FRAMES GET_EVENTFD NET_POLL NET_CONFIG FS_OPEN FS_READ FS_WRITE FS_CLOSE FS_STAT FS_SYNC VFS_MOUNT VFS_UNMOUNT VFS_LOOKUP VFS_CREATE VFS_REMOVE VFS_RENAME VFS_CHMOD VFS_CHOWN VFS_TRUNCATE VFS_LINK VFS_SYMLINK VFS_READDIR VFS_IOCTL VFS_GETATTR VFS_SETATTR NDB_TABLE_INSERT NDB_TABLE_GET NDB_SNAPSHOT HIVE_SET HIVE_GET HIVE_DELETE HIVE_SNAPSHOT GPU_SUBMIT GPU_WAIT EGL_IMPORT EGL_EXPORT DMABUF_IMPORT DMABUF_EXPORT PIPEWIRE_PUBLISH PIPEWIRE_SUBSCRIBE AUDIO_PLAY AUDIO_STOP VIDEO_ENCODE VIDEO_DECODE GPU_COMPOSITE GPU_BLIT GPU_CLEAR SHADER_COMPILE SHADER_LINK SHADER_BIND SHADER_UNBIND TEXTURE_UPLOAD TEXTURE_DOWNLOAD PBO_MAP PBO_UNMAP PBO_UPLOAD PBO_DOWNLOAD SSAO_PASS TILED_LIGHT_PASS POSTPROCESS_PASS PRESENT_FRAME FRAMEBUFFER_BIND FRAMEBUFFER_UNBIND SWAP_BUFFERS VSYNC_WAIT WP_PRESENT_NOTIFY WP_PRESENT_ACK WP_PRESENT_CANCEL WP_PRESENT_QUERY WP_PRESENT_SET_MODE WP_PRESENT_GET_MODE WP_PRESENT_SET_PRIORITY WP_PRESENT_GET_PRIORITY VIRTIO_INIT VIRTIO_SEND VIRTIO_RECV VIRTIO_SHUTDOWN PCI_PROBE PCI_CONFIG_READ PCI_CONFIG_WRITE PCI_ENABLE_DEVICE PCI_DISABLE_DEVICE PCI_SET_MSI PCI_CLEAR_MSI PCI_MAP_BAR PCI_UNMAP_BAR PCI_DMA_SETUP PCI_DMA_TEARDOWN PMEM_ALLOC PMEM_FREE KERNEL_PANIC REBOOT SHUTDOWN SUSPEND RESUME USER_MODE_ENTER USER_MODE_EXIT PMU_READ PMU_WRITE PERF_SAMPLE TRACE_MARK DEBUG_PRINT USER_YIELD FENCE BARRIER SEV WFE CACHE_LINE_FLUSH CACHE_LINE_INVALIDATE TLB_FLUSH TLB_INVALIDATE PAGE_TABLE_MAP PAGE_TABLE_UNMAP KERNEL_ALLOC KERNEL_FREE USER_ALLOC USER_FREE MAP_IO_REGION UNMAP_IO_REGION IO_PORT_READ IO_PORT_WRITE SMP_SEND_IPI SMP_BROADCAST CPU_FREQ_SET CPU_FREQ_GET THERMAL_QUERY THERMAL_SET_LIMIT LOG_ROTATE CERT_VERIFY KEYSTORE_STORE KEYSTORE_RETRIEVE AUDIT_QUERY LICENSE_CHECK UPDATE_APPLY ROLLBACK HEALTH_CHECK DIAGNOSTIC_RUN METRICS_PUSH ALERT_RAISE ALERT_CLEAR LICENSE_ROTATE SECRETS_ROTATE BACKUP_CREATE BACKUP_RESTORE QUOTA_CHECK QUOTA_ENFORCE SESSION_CREATE SESSION_TERMINATE AUTH_CHALLENGE AUTH_VERIFY POLICY_EVAL POLICY_UPDATE CERT_ROTATE KEY_ROTATE AUDIT_EXPORT CONFIG_GET CONFIG_SET CONFIG_RELOAD LICENSE_QUERY METRICS_QUERY HEARTBEAT CLUSTER_JOIN CLUSTER_LEAVE SERVICE_START SERVICE_STOP SERVICE_RESTART SERVICE_STATUS LOG_LEVEL_SET LOG_LEVEL_GET DIAG_UPLOAD DIAG_DOWNLOAD MAINT_MODE_ENTER MAINT_MODE_EXIT SEC_SCAN_START SEC_SCAN_STOP SEC_SCAN_REPORT POLICY_AUDIT";
    std::size_t index = 1;
    std::size_t start = 0;
    while (start < names.size() && index < a.size()) {
        while (start < names.size() && names[start] == ' ') ++start;
        if (start >= names.size()) break;
        auto end = names.find(' ', start);
        if (end == std::string_view::npos) end = names.size();
        a[index++] = names.substr(start, end - start);
        start = end + 1;
    }
    return a;
}();

bool is_native_alu(std::uint16_t op) noexcept { return op >= OP_ADD && op <= OP_MEMSET; }

Register8192 shift_left(const Register8192& x, unsigned s) noexcept {
    Register8192 y{}; if (s >= 8192) return y;
    const unsigned q=s/64, r=s%64;
    for (unsigned k=q; k<128; ++k) {
        std::uint64_t v=x.lane(k-q)<<r;
        if (r && k>q) v |= x.lane(k-q-1)>>(64-r);
        y.set_u64(k,v);
    }
    return y;
}

Register8192 shift_right(const Register8192& x, unsigned s) noexcept {
    Register8192 y{}; if (s >= 8192) return y;
    const unsigned q=s/64, r=s%64;
    for (unsigned k=0; k<128-q; ++k) {
        std::uint64_t v=x.lane(k+q)>>r;
        if (r && k+q+1<128) v |= x.lane(k+q+1)<<(64-r);
        y.set_u64(k,v);
    }
    return y;
}

Register8192 rotate_left(const Register8192& x, unsigned s) noexcept {
    s%=8192; if (!s) return x;
    return shift_left(x,s) | shift_right(x,8192-s);
}

Register8192 rotate_right(const Register8192& x, unsigned s) noexcept {
    s%=8192; if (!s) return x;
    return shift_right(x,s) | shift_left(x,8192-s);
}

} // namespace

Instr decode(const std::uint8_t* p, std::size_t len) {
    if (!p || len < 8) throw std::invalid_argument("instruction buffer too short");
    Instr i{};
    i.opcode = static_cast<std::uint16_t>(p[0]) | (static_cast<std::uint16_t>(p[1]) << 8);
    i.dst = static_cast<std::uint16_t>(p[2]) | (static_cast<std::uint16_t>(p[3]) << 8);
    i.srcA = static_cast<std::uint16_t>(p[4]) | (static_cast<std::uint16_t>(p[5]) << 8);
    i.srcB = static_cast<std::uint16_t>(p[6]) | (static_cast<std::uint16_t>(p[7]) << 8);
    if (len >= 16) {
        i.imm = static_cast<std::uint64_t>(p[8]) | (static_cast<std::uint64_t>(p[9])<<8) |
                (static_cast<std::uint64_t>(p[10])<<16) | (static_cast<std::uint64_t>(p[11])<<24) |
                (static_cast<std::uint64_t>(p[12])<<32) | (static_cast<std::uint64_t>(p[13])<<40) |
                (static_cast<std::uint64_t>(p[14])<<48) | (static_cast<std::uint64_t>(p[15])<<56);
        i.imm_len=8; i.length=16;
    }
    return i;
}

bool is_defined_opcode(std::uint16_t opcode) noexcept { return opcode >= 0x0001 && opcode <= 0x011C; }

std::string_view opcode_name(std::uint16_t opcode) noexcept {
    return opcode < kNames.size() ? kNames[opcode] : std::string_view{};
}

const OpcodeInfo* opcode_info(std::uint16_t opcode) noexcept {
    if (!is_defined_opcode(opcode)) return nullptr;
    static std::array<OpcodeInfo, 0x11D> table = [] {
        std::array<OpcodeInfo, 0x11D> t{};
        for (std::size_t op=1; op<t.size(); ++op) {
            t[op] = OpcodeInfo{static_cast<std::uint16_t>(op), kNames[op], "R", "rd,rs,rt", false, 1, 1.0, "ALU", "R8192", "Supplied Chimera-II ISA", "internal"};
        }
        // Exact metadata anchors from the supplied specification.
        t[0x003D] = {0x003D,"SHA256","R","rd,rs",false,40,0.05,"CRYPTO","R8192","SHA-256 on wide lanes","internal"};
        t[0x000D] = {0x000D,"MULMOD","R","rd,rs,rt,mod",true,120,0.05,"CRYPTO","R8192","Modular multiply","internal"};
        t[0x000E] = {0x000E,"MODEXP","M","rd,rs,imm",true,200,0.02,"CRYPTO","R8192","Modular exponentiation","internal"};
        t[0x0047] = {0x0047,"SYS_CALL","S","num,args",false,5,1.0,"SYS","HYBRID","System call entry","internal"};
        t[0x00D4] = {0x00D4,"BARRIER","S","scope",true,1,10.0,"SYS","HYBRID","Synchronization barrier","internal"};
        return t;
    }();
    return &table[opcode];
}

ExecuteStatus execute(CPU8192& c, const Instr& i, bool privileged) {
    const auto* info=opcode_info(i.opcode);
    if (!info) return ExecuteStatus::InvalidOpcode;
    if (info->privileged && !privileged) return ExecuteStatus::PrivilegeViolation;
    const auto a=c.gpr[i.srcA], b=c.gpr[i.srcB];
    switch (i.opcode) {
        case OP_ADD: c.gpr[i.dst]=a+b; return ExecuteStatus::Executed;
        case OP_SUB: c.gpr[i.dst]=a-b; return ExecuteStatus::Executed;
        case OP_AND: c.gpr[i.dst]=a&b; return ExecuteStatus::Executed;
        case OP_OR: c.gpr[i.dst]=a|b; return ExecuteStatus::Executed;
        case OP_XOR: c.gpr[i.dst]=a^b; return ExecuteStatus::Executed;
        case OP_NOT: { Register8192 z{}; for (unsigned k=0;k<128;++k) z.set_u64(k,~a.lane(k)); c.gpr[i.dst]=z; return ExecuteStatus::Executed; }
        case OP_SHL: c.gpr[i.dst]=shift_left(a,static_cast<unsigned>(i.imm%8192)); return ExecuteStatus::Executed;
        case OP_SHR: c.gpr[i.dst]=shift_right(a,static_cast<unsigned>(i.imm%8192)); return ExecuteStatus::Executed;
        case OP_ROL: c.gpr[i.dst]=rotate_left(a,static_cast<unsigned>(i.imm%8192)); return ExecuteStatus::Executed;
        case OP_ROR: c.gpr[i.dst]=rotate_right(a,static_cast<unsigned>(i.imm%8192)); return ExecuteStatus::Executed;
        case OP_MOV: c.gpr[i.dst]=a; return ExecuteStatus::Executed;
        case OP_CMP: {
            bool eq=true, lt=false;
            for (int k=127;k>=0;--k) { if (a.lane(k)!=b.lane(k)) { eq=false; lt=a.lane(k)<b.lane(k); break; } }
            c.flags=(eq?1ULL:0ULL)|(lt?2ULL:0ULL); return ExecuteStatus::Executed;
        }
        case OP_CMPEQ: c.flags=(a.words()==b.words())?1ULL:0ULL; return ExecuteStatus::Executed;
        case OP_CMPLT: { bool lt=false; for(int k=127;k>=0;--k){if(a.lane(k)!=b.lane(k)){lt=a.lane(k)<b.lane(k);break;}} c.flags=lt?1ULL:0ULL; return ExecuteStatus::Executed; }
        case OP_MUL: { Register8192 r{}; for(unsigned k=0;k<128;++k) r.set_u64(k,a.lane(k)*b.lane(k)); c.gpr[i.dst]=r; return ExecuteStatus::Executed; }
        default: return is_native_alu(i.opcode) ? ExecuteStatus::UnimplementedService : ExecuteStatus::UnimplementedService;
    }
}

void run(CPU8192& c, const std::uint8_t* code, std::size_t len, bool privileged) {
    while (c.pc < len) {
        const Instr i=decode(code+c.pc,len-c.pc);
        const auto status=execute(c,i,privileged);
        if (status == ExecuteStatus::InvalidOpcode) throw std::runtime_error("invalid Chimera-II opcode");
        if (status == ExecuteStatus::PrivilegeViolation) throw std::runtime_error("privileged Chimera-II opcode in user mode");
        if (status == ExecuteStatus::UnimplementedService) throw std::runtime_error("recognized Chimera-II service is not bound to an OS backend");
        c.pc += i.length;
    }
}

} // namespace chimera
