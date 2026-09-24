#include "chimera/nbit_isa.hpp"

#include <cctype>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace chimera::isa {
namespace {
struct J {
    enum class Kind { Object, Array, String, Number, Bool, Null };
    Kind kind{Kind::Null};
    std::string s;
    double n{0};
    bool b{false};
    std::vector<J> a;
    std::vector<std::pair<std::string,J>> o;
    const J* get(std::string_view key) const noexcept {
        for (const auto& [k,v] : o) if (k == key) return &v;
        return nullptr;
    }
    std::string string() const { return s; }
    std::size_t number() const { return static_cast<std::size_t>(n); }
};
class Parser {
public:
    explicit Parser(std::string_view s): s_(s) {}
    J parse(){ ws(); auto v=value(); ws(); if(i_!=s_.size()) throw std::runtime_error("trailing JSON"); return v; }
private:
    std::string_view s_; std::size_t i_{0};
    void ws(){ while(i_<s_.size() && std::isspace(static_cast<unsigned char>(s_[i_]))) ++i_; }
    char take(){ if(i_>=s_.size()) throw std::runtime_error("unexpected end"); return s_[i_++]; }
    void expect(char c){ if(take()!=c) throw std::runtime_error("unexpected JSON token"); }
    J value(){
        ws(); if(i_>=s_.size()) throw std::runtime_error("missing JSON value");
        if(s_[i_]=='{') return object(); if(s_[i_]=='[') return array(); if(s_[i_]=='"'){J x;x.kind=J::Kind::String;x.s=string();return x;}
        if(s_.substr(i_,4)=="true"){i_+=4;J x;x.kind=J::Kind::Bool;x.b=true;return x;}
        if(s_.substr(i_,5)=="false"){i_+=5;J x;x.kind=J::Kind::Bool;return x;}
        if(s_[i_]=='n'){i_+=4;J x;return x;}
        J x;x.kind=J::Kind::Number;x.n=number();return x;
    }
    std::string string(){
        expect('"'); std::string out;
        while(i_<s_.size()){char c=take(); if(c=='"') return out; if(c!='\\'){out+=c;continue;} char e=take(); switch(e){case '"':out+='"';break;case '\\\\':out+='\\';break;case 'n':out+='\n';break;case 'r':out+='\r';break;case 't':out+='\t';break;default:throw std::runtime_error("unsupported JSON escape");}}
        throw std::runtime_error("unterminated JSON string");
    }
    double number(){std::size_t b=i_; while(i_<s_.size() && (std::isdigit(static_cast<unsigned char>(s_[i_]))||s_[i_]=='-'||s_[i_]=='+'||s_[i_]=='.'||s_[i_]=='e'||s_[i_]=='E'))++i_; return std::stod(std::string(s_.substr(b,i_-b))); }
    J object(){J x;x.kind=J::Kind::Object;expect('{');ws();if(i_<s_.size()&&s_[i_]=='}'){++i_;return x;}for(;;){ws();auto k=string();ws();expect(':');x.o.push_back({std::move(k),value()});ws();char c=take();if(c=='}')return x;if(c!=',')throw std::runtime_error("expected comma");}}
    J array(){J x;x.kind=J::Kind::Array;expect('[');ws();if(i_<s_.size()&&s_[i_]==']'){++i_;return x;}for(;;){x.a.push_back(value());ws();char c=take();if(c==']')return x;if(c!=',')throw std::runtime_error("expected comma");}}
};
ISAStyle style(std::string_view s){return s=="RISC"?ISAStyle::RISC:s=="CISC"?ISAStyle::CISC:ISAStyle::Hybrid;}
bool boolean(const J* x){return x&&x->kind==J::Kind::Bool&&x->b;}
std::size_t num(const J* x,std::size_t d){return x&&x->kind==J::Kind::Number?x->number():d;}
std::string str(const J* x,std::string d={}){return x&&x->kind==J::Kind::String?x->string():std::move(d);}
}
bool NBitISACatalog::load_file(const std::string& path,std::string* error){
    std::ifstream f(path); if(!f){if(error)*error="cannot open "+path;return false;}
    std::ostringstream s;s<<f.rdbuf();return load_json(s.str(),error);
}
bool NBitISACatalog::load_json(std::string_view json,std::string* error){
    try{
        auto root=Parser(json).parse(); const auto* profiles=root.get("profiles");
        if(!profiles||profiles->kind!=J::Kind::Array) throw std::runtime_error("missing profiles");
        profiles_.clear();
        for(const auto& p:profiles->a){
            NBitProfile x;
            x.name=str(p.get("name")); x.source=str(p.get("source")); x.style=style(str(p.get("style"),"Hybrid"));
            x.register_bits=num(p.get("register_bits"),64); x.min_register_bits=num(p.get("min_register_bits"),8); x.max_register_bits=num(p.get("max_register_bits"),64);
            x.hardware_native=boolean(p.get("hardware_native"));
            if(const auto* f=p.get("format")){x.format.opcode_bits=static_cast<std::uint16_t>(num(f->get("opcode_bits"),16));x.format.register_index_bits=static_cast<std::uint16_t>(num(f->get("register_index_bits"),16));x.format.immediate_bits=static_cast<std::uint16_t>(num(f->get("immediate_bits"),64));x.format.min_instruction_bytes=static_cast<std::uint16_t>(num(f->get("min_instruction_bytes"),16));x.format.max_instruction_bytes=static_cast<std::uint16_t>(num(f->get("max_instruction_bytes"),16));x.format.variable_length=boolean(f->get("variable_length"));}
            if(x.name.empty()||!valid_nbit_width(x.register_bits)) throw std::runtime_error("invalid N-bit profile");
            profiles_.push_back(std::move(x));
        }
        return true;
    }catch(const std::exception& e){if(error)*error=e.what();return false;}
}
const NBitProfile* NBitISACatalog::find(std::string_view name) const noexcept{for(const auto& p:profiles_)if(p.name==name)return &p;return nullptr;}
const NBitProfile* NBitISACatalog::find_width(std::size_t bits) const noexcept{for(const auto& p:profiles_)if(p.register_bits==bits)return &p;return nullptr;}
bool is_generated_width(const NBitISACatalog& catalog,std::size_t bits) noexcept{return catalog.find_width(bits)!=nullptr;}
} // namespace chimera::isa
