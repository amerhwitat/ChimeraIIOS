#include "pe_loader.h"
#include <algorithm>
#include <cstring>
#include <fstream>

namespace chimera::win::pe {
namespace {
#pragma pack(push,1)
struct Dos { std::uint16_t mz; std::uint8_t stub[58]; std::uint32_t peoff; };
struct Coff { std::uint16_t machine, sections; std::uint32_t stamp, symoff, symbols; std::uint16_t opt_size, characteristics; };
struct Sec { char name[8]; std::uint32_t vsize, va, raw_size, raw_ptr, reloc_ptr, line_ptr; std::uint16_t reloc_count, line_count; std::uint32_t characteristics; };
struct Dir { std::uint32_t rva, size; };
struct Exp { std::uint32_t chars, stamp; std::uint16_t major, minor; std::uint32_t name, base, nfunc, nname, funcs, names, ords; };
struct Imp { std::uint32_t lookup, stamp, forwarder, name, thunk; };
#pragma pack(pop)

bool range_ok(std::size_t off,std::size_t len,std::size_t total){ return off<=total && len<=total-off; }
std::uint32_t u32(const std::vector<std::uint8_t>& b,std::size_t p){ std::uint32_t v{}; std::memcpy(&v,b.data()+p,4); return v; }
std::uint64_t u64(const std::vector<std::uint8_t>& b,std::size_t p){ std::uint64_t v{}; std::memcpy(&v,b.data()+p,8); return v; }
std::string cstr(const std::vector<std::uint8_t>& b,std::size_t p){ if(p>=b.size()) return {}; const char* s=reinterpret_cast<const char*>(b.data()+p); std::size_t n=0; while(p+n<b.size()&&s[n]) ++n; return std::string(s,n); }
std::size_t rva_file(const std::vector<Section>& s,std::uint32_t rva){ for(const auto& x:s) if(rva>=x.rva && rva-x.rva<x.raw_size) return static_cast<std::size_t>(x.raw_offset+rva-x.rva); return 0; }
std::vector<std::uint8_t> read_all(const std::string& path){ std::ifstream f(path,std::ios::binary); if(!f) return {}; f.seekg(0,std::ios::end); auto n=f.tellg(); if(n<0) return {}; f.seekg(0); std::vector<std::uint8_t> b(static_cast<std::size_t>(n)); if(!b.empty()) f.read(reinterpret_cast<char*>(b.data()),n); return b; }
}

Status inspect(const std::string& path, Image& out, std::string& error){
    out={}; auto b=read_all(path); if(b.empty()){error="cannot read PE image";return Status::IoError;}
    if(b.size()<64){error="truncated DOS header";return Status::BadDosHeader;}
    const auto* d=reinterpret_cast<const Dos*>(b.data()); if(d->mz!=0x5a4d||d->peoff>=b.size()){error="invalid MZ header";return Status::BadDosHeader;}
    if(!range_ok(d->peoff,24,b.size())||std::memcmp(b.data()+d->peoff,"PE\0\0",4)!=0){error="invalid PE signature";return Status::BadPeHeader;}
    const auto* c=reinterpret_cast<const Coff*>(b.data()+d->peoff+4); out.machine=static_cast<Machine>(c->machine);
    if(out.machine!=Machine::I386&&out.machine!=Machine::AMD64&&out.machine!=Machine::ARM64){error="unsupported PE machine";return Status::UnsupportedMachine;}
    const std::size_t opt=d->peoff+4+sizeof(Coff); if(!range_ok(opt,c->opt_size,b.size())||c->opt_size<2){error="invalid optional header";return Status::UnsupportedOptionalHeader;}
    const auto magic=static_cast<std::uint16_t>(b[opt]|(b[opt+1]<<8)); out.pe32_plus=magic==0x20b; if(magic!=0x10b&&magic!=0x20b){error="unsupported PE optional header";return Status::UnsupportedOptionalHeader;}
    if(out.pe32_plus){ if(c->opt_size<112){error="short PE32+ optional header";return Status::UnsupportedOptionalHeader;} out.preferred_base=u64(b,opt+24); out.entry_rva=u32(b,opt+16); out.section_alignment=u32(b,opt+32); out.image_size=u32(b,opt+56); out.subsystem=static_cast<std::uint32_t>(b[opt+68]|(b[opt+69]<<8)); }
    else { if(c->opt_size<96){error="short PE32 optional header";return Status::UnsupportedOptionalHeader;} out.preferred_base=u32(b,opt+28); out.entry_rva=u32(b,opt+16); out.section_alignment=u32(b,opt+32); out.image_size=u32(b,opt+56); out.subsystem=static_cast<std::uint32_t>(b[opt+68]|(b[opt+69]<<8)); }
    out.kind=(c->characteristics&0x2000)?ImageKind::DLL:ImageKind::EXE; out.relocatable=(c->characteristics&1)==0;
    const std::size_t sec_off=opt+c->opt_size; if(!range_ok(sec_off,static_cast<std::size_t>(c->sections)*sizeof(Sec),b.size())){error="invalid section table";return Status::InvalidSection;}
    for(std::uint16_t i=0;i<c->sections;i++){ const auto* s=reinterpret_cast<const Sec*>(b.data()+sec_off+i*sizeof(Sec)); Section x{}; std::size_t n=0; while(n<8&&s->name[n])++n; x.name.assign(s->name,n); x.rva=s->va; x.virtual_size=s->vsize; x.raw_offset=s->raw_ptr; x.raw_size=s->raw_size; x.characteristics=s->characteristics; if(!range_ok(x.raw_offset,x.raw_size,b.size())){error="section exceeds file";return Status::InvalidSection;} out.sections.push_back(x); }
    const std::size_t dd_off=opt+(out.pe32_plus?112:96); if(!range_ok(dd_off,8*16,b.size())) return Status::Ok;
    auto dir=[&](unsigned n){ return Dir{u32(b,dd_off+n*8),u32(b,dd_off+n*8+4)}; };
    const auto ex=dir(0); if(ex.rva){ auto p=rva_file(out.sections,ex.rva); if(p&&range_ok(p,sizeof(Exp),b.size())){ const auto* e=reinterpret_cast<const Exp*>(b.data()+p); auto np=rva_file(out.sections,e->names),op=rva_file(out.sections,e->ords),fp=rva_file(out.sections,e->funcs); for(std::uint32_t i=0;i<e->nname;i++){ if(!np||!op||!fp) break; auto nr=u32(b,np+i*4); auto ord=static_cast<std::uint16_t>(b[op+i*2]|(b[op+i*2+1]<<8)); if(ord>=e->nfunc) continue; auto fr=u32(b,fp+ord*4); auto namepos=rva_file(out.sections,nr); if(!namepos) continue; out.exports.push_back({cstr(b,namepos),fr,static_cast<std::uint16_t>(e->base+ord)}); } } }
    const auto im=dir(1); if(im.rva){ auto p=rva_file(out.sections,im.rva); while(p&&range_ok(p,sizeof(Imp),b.size())){ const auto* x=reinterpret_cast<const Imp*>(b.data()+p); if(!x->name) break; auto np=rva_file(out.sections,x->name); auto tp=rva_file(out.sections,x->thunk?x->thunk:x->lookup); if(!np||!tp) break; const std::string dll=cstr(b,np); const std::uint64_t ordmask=out.pe32_plus?0x8000000000000000ull:0x80000000ull; for(std::size_t i=0;;i++){ std::uint64_t v=out.pe32_plus?u64(b,tp+i*8):u32(b,tp+i*4); if(!v) break; Import in{}; in.dll=dll; in.by_ordinal=(v&ordmask)!=0; if(in.by_ordinal) in.ordinal=static_cast<std::uint16_t>(v&0xffff); else { auto hp=rva_file(out.sections,static_cast<std::uint32_t>(v&0xffffffffu)); if(!hp) break; in.symbol=cstr(b,hp+2); } out.imports.push_back(std::move(in)); } p+=sizeof(Imp); } }
    const auto rel=dir(5); if(rel.rva){ auto p=rva_file(out.sections,rel.rva); const auto end=p?std::min(b.size(),p+static_cast<std::size_t>(rel.size)):0; while(p&&p+8<=end){ auto page=u32(b,p), sz=u32(b,p+4); if(sz<8||p+sz>end) break; for(std::size_t q=p+8;q+1<p+sz;q+=2){ auto e=static_cast<std::uint16_t>(b[q]|(b[q+1]<<8)); if((e>>12)==10) out.relocation_rvas.push_back(page+(e&0xfff)); } p+=sz; } }
    return Status::Ok;
}

Status map_image(const std::string& path,std::uint64_t load_base,LoadedImage& out,std::string& error){
    Image img; auto st=inspect(path,img,error); if(st!=Status::Ok)return st; if(!img.image_size||img.image_size>1024ull*1024ull*1024ull){error="invalid image size";return Status::InvalidDirectory;}
    auto b=read_all(path); out={}; out.image=std::move(img); out.load_base=load_base?load_base:out.image.preferred_base; out.memory.assign(static_cast<std::size_t>(out.image.image_size),0);
    for(const auto& s:out.image.sections){ if(s.raw_size&&s.rva<out.memory.size()){ auto n=std::min<std::size_t>(s.raw_size,out.memory.size()-s.rva); if(s.raw_offset+n>b.size()){error="section copy exceeds file";return Status::InvalidSection;} std::memcpy(out.memory.data()+s.rva,b.data()+s.raw_offset,n); } }
    out.entrypoint=out.load_base+out.image.entry_rva; return Status::Ok;
}

Status apply_relocations(LoadedImage& image,std::string& error){
    const std::int64_t delta=static_cast<std::int64_t>(image.load_base-image.image.preferred_base); if(delta==0)return Status::Ok;
    if(!image.image.relocatable||image.image.relocation_rvas.empty()){error="image requires relocation but has no usable relocation table";return Status::RelocationsMissing;}
    for(auto r:image.image.relocation_rvas){ if(r+(image.image.pe32_plus?8u:4u)>image.memory.size()){error="relocation outside mapped image";return Status::InvalidDirectory;} if(image.image.pe32_plus){ auto* p=reinterpret_cast<std::uint64_t*>(image.memory.data()+r); *p=static_cast<std::uint64_t>(static_cast<std::int64_t>(*p)+delta); } else { auto* p=reinterpret_cast<std::uint32_t*>(image.memory.data()+r); *p=static_cast<std::uint32_t>(static_cast<std::int64_t>(*p)+delta); } }
    return Status::Ok;
}

Status resolve_imports(LoadedImage&,std::string& error){ error="imports require the Chimera Win32 API-set/module resolver"; return Status::ImportUnresolved; }
const Export* find_export(const Image& image,const std::string& name){ for(const auto& e:image.exports) if(e.name==name)return &e; return nullptr; }
Status validate_for_process(const Image& image,Machine process_machine,std::string& error){ if(image.machine!=process_machine){error="PE image architecture does not match process architecture; use WOW64/ARM64 translation boundary";return Status::ArchitectureMismatch;} return Status::Ok; }
}
