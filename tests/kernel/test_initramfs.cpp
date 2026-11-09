#include "chimera/initramfs.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace {
static void append_hex(std::vector<uint8_t>& out, uint32_t value) {
    static const char digits[] = "0123456789abcdef";
    for (int shift = 28; shift >= 0; shift -= 4)
        out.push_back(static_cast<uint8_t>(digits[(value >> shift) & 0xFu]));
}
static void pad4(std::vector<uint8_t>& out) {
    while (out.size() & 3u) out.push_back(0);
}
static void append_entry(std::vector<uint8_t>& out, const std::string& name,
                         uint32_t mode, const std::string& payload,
                         bool crc = false, uint32_t checksum_override = 0xFFFFFFFFu) {
    const uint32_t sum = checksum_override == 0xFFFFFFFFu
        ? [&]() { uint32_t v=0; for (unsigned char c : payload) v += c; return v; }()
        : checksum_override;
    const uint32_t fields[13] = {
        1u, mode, 0u, 0u, 1u, 0u, static_cast<uint32_t>(payload.size()),
        0u, 0u, 0u, 0u, static_cast<uint32_t>(name.size() + 1u), crc ? sum : 0u
    };
    const char* magic = crc ? "070702" : "070701";
    for (uint32_t i=0;i<6u;++i) out.push_back(static_cast<uint8_t>(magic[i]));
    for (uint32_t field : fields) append_hex(out,field);
    assert(out.size() % 4u == 2u);
    for (char c : name) out.push_back(static_cast<uint8_t>(c));
    out.push_back(0);
    pad4(out);
    for (unsigned char c : payload) out.push_back(c);
    pad4(out);
}
static std::vector<uint8_t> valid_archive() {
    std::vector<uint8_t> out;
    append_entry(out,".",0040755u,"");
    append_entry(out,"./etc",0040755u,"");
    append_entry(out,"./etc/os-release",0100644u,"NAME=Chimera\nVERSION=1\n");
    append_entry(out,"./tmp",0041777u,"");
    append_entry(out,"./tmp/probe",0100600u,"tmpfs-data");
    append_entry(out,"TRAILER!!!",0u,"");
    return out;
}
struct captured {
    uint32_t count=0;
    std::string os_release;
    std::string tmp_file;
    bool saw_root=false;
};
static int visit(const chimera_initramfs_entry* entry, void* context) {
    auto* out=static_cast<captured*>(context);
    ++out->count;
    if (entry->path_length==0) out->saw_root=true;
    if (std::string(entry->path)=="etc/os-release")
        out->os_release.assign(reinterpret_cast<const char*>(entry->data),entry->size);
    if (std::string(entry->path)=="tmp/probe")
        out->tmp_file.assign(reinterpret_cast<const char*>(entry->data),entry->size);
    return 0;
}
static int count_only(const chimera_initramfs_entry*,void* context) {
    ++*static_cast<uint32_t*>(context); return 0;
}
}

int main() {
    auto archive=valid_archive();
    captured result{};
    chimera_initramfs_report report{};
    assert(chimera_initramfs_scan(archive.data(),archive.size(),visit,&result,&report)==0);
    assert(report.entries==5u);
    assert(report.regular_files==2u);
    assert(report.directories==3u);
    assert(report.symlinks==0u);
    assert(report.payload_bytes==std::string("NAME=Chimera\nVERSION=1\n").size()+std::string("tmpfs-data").size());
    assert(result.count==5u && result.saw_root);
    assert(result.os_release=="NAME=Chimera\nVERSION=1\n");
    assert(result.tmp_file=="tmpfs-data");

    auto traversal=std::vector<uint8_t>{};
    append_entry(traversal,"../escape",0100644u,"x");
    append_entry(traversal,"TRAILER!!!",0u,"");
    uint32_t callbacks=0;
    assert(chimera_initramfs_scan(traversal.data(),traversal.size(),count_only,&callbacks,nullptr)!=0);
    assert(callbacks==0u); // No partial publication on malformed archives.

    auto absolute=std::vector<uint8_t>{};
    append_entry(absolute,"/etc/passwd",0100644u,"x");
    append_entry(absolute,"TRAILER!!!",0u,"");
    assert(chimera_initramfs_scan(absolute.data(),absolute.size(),nullptr,nullptr,nullptr)!=0);

    auto duplicate=std::vector<uint8_t>{};
    append_entry(duplicate,"./etc/os-release",0100644u,"one");
    append_entry(duplicate,"etc/os-release",0100644u,"two");
    append_entry(duplicate,"TRAILER!!!",0u,"");
    assert(chimera_initramfs_scan(duplicate.data(),duplicate.size(),nullptr,nullptr,nullptr)!=0);

    auto truncated=valid_archive();
    truncated.pop_back();
    assert(chimera_initramfs_scan(truncated.data(),truncated.size(),nullptr,nullptr,nullptr)!=0);

    auto missing_trailer=std::vector<uint8_t>{};
    append_entry(missing_trailer,"init",0100755u,"payload");
    assert(chimera_initramfs_scan(missing_trailer.data(),missing_trailer.size(),nullptr,nullptr,nullptr)!=0);

    auto bad_crc=std::vector<uint8_t>{};
    append_entry(bad_crc,"file",0100644u,"payload",true,0u);
    append_entry(bad_crc,"TRAILER!!!",0u,"");
    assert(chimera_initramfs_scan(bad_crc.data(),bad_crc.size(),nullptr,nullptr,nullptr)!=0);

    auto bad_header=valid_archive();
    bad_header[6]='g';
    assert(chimera_initramfs_scan(bad_header.data(),bad_header.size(),nullptr,nullptr,nullptr)!=0);

    std::puts("PASS: bounded CPIO-newc validation, normalized paths, duplicate/traversal rejection, CRC and all-or-nothing callbacks");
    return 0;
}
