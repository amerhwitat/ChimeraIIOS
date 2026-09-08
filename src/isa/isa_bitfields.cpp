#include "chimera/isa_bitfields.hpp"
#include <cctype>
#include <fstream>
#include <limits>
#include <map>
#include <sstream>
#include <variant>

namespace chimera::isa {
namespace {
struct J {
    using object = std::map<std::string, J>;
    using array = std::vector<J>;
    using value = std::variant<std::nullptr_t, bool, double, std::string, object, array>;
    value v;
    const J* get(std::string_view k) const {
        if (auto p = std::get_if<object>(&v)) { auto it = p->find(std::string(k)); return it == p->end() ? nullptr : &it->second; }
        return nullptr;
    }
    std::string str() const { return std::get<std::string>(v); }
    std::uint64_t u64() const { return static_cast<std::uint64_t>(std::get<double>(v)); }
};
class P {
public:
    explicit P(std::string_view s): s_(s) {}
    J parse() { ws(); J x = value(); ws(); if (i_ != s_.size()) throw std::runtime_error("trailing JSON"); return x; }
private:
    std::string_view s_; std::size_t i_=0;
    void ws(){while(i_<s_.size() && std::isspace(static_cast<unsigned char>(s_[i_]))) ++i_;}
    char take(){if(i_>=s_.size()) throw std::runtime_error("unexpected end"); return s_[i_++];}
    void expect(char c){if(take()!=c) throw std::runtime_error("unexpected JSON token");}
    J value(){ws(); if(i_>=s_.size()) throw std::runtime_error("missing value"); char c=s_[i_]; if(c=='{') return object(); if(c=='[') return array(); if(c=='\"') return J{string()}; if(c=='t'){lit("true"); return J{true};} if(c=='f'){lit("false"); return J{false};} if(c=='n'){lit("null"); return J{nullptr};} return J{number()};}
    void lit(std::string_view x){if(s_.substr(i_,x.size())!=x) throw std::runtime_error("invalid literal"); i_+=x.size();}
    std::string string(){expect('\"'); std::string out; while(i_<s_.size()){char c=take(); if(c=='\"') return out; if(c=='\\'){char e=take(); switch(e){case 'n':out+='\n';break;case 'r':out+='\r';break;case 't':out+='\t';break;case 'b':out+='\b';break;case 'f':out+='\f';break;case '\\':out+='\\';break;case '\"':out+='\"';break; default: throw std::runtime_error("unsupported JSON escape");}} else out+=c;} throw std::runtime_error("unterminated string");}
    double number(){std::size_t b=i_; if(s_[i_]=='-') ++i_; while(i_<s_.size() && std::isdigit(static_cast<unsigned char>(s_[i_]))) ++i_; if(i_<s_.size() && s_[i_]=='.'){++i_; while(i_<s_.size() && std::isdigit(static_cast<unsigned char>(s_[i_]))) ++i_;} if(i_<s_.size() && (s_[i_]=='e'||s_[i_]=='E')){++i_;if(i_<s_.size()&&(s_[i_]=='+'||s_[i_]=='-'))++i_;while(i_<s_.size()&&std::isdigit(static_cast<unsigned char>(s_[i_])))++i_;} return std::stod(std::string(s_.substr(b,i_-b)));}
    J object(){expect('{'); J::object o; ws(); if(i_<s_.size()&&s_[i_]=='}'){++i_;return J{o};} for(;;){ws(); std::string k=string(); ws(); expect(':'); o.emplace(std::move(k),value()); ws(); char c=take(); if(c=='}')break; if(c!=',')throw std::runtime_error("expected comma");} return J{o};}
    J array(){expect('['); J::array a; ws(); if(i_<s_.size()&&s_[i_]==']'){++i_;return J{a};} for(;;){a.push_back(value());ws();char c=take();if(c==']')break;if(c!=',')throw std::runtime_error("expected comma");} return J{a};}
};
std::uint64_t hex(std::string s){return std::stoull(s, nullptr, 16);}
}

bool BitfieldRegistry::load_file(const std::string& path, std::string* error) {
    std::ifstream f(path); if(!f){if(error)*error="cannot open "+path;return false;}
    std::ostringstream ss; ss<<f.rdbuf(); return load_json(ss.str(), error);
}

bool BitfieldRegistry::load_json(std::string_view json, std::string* error) {
    try {
        J root=P(json).parse();
        const J* abi=root.get("canonical_abi"); const J* count=root.get("instruction_count"); const J* list=root.get("instructions");
        if(!abi||!count||!list) throw std::runtime_error("missing ISA schema members");
        abi_bytes_=static_cast<std::uint32_t>(abi->get("bytes")->u64()); abi_layout_=abi->get("layout")->str();
        instructions_.clear();
        for(const J& item: std::get<J::array>(list->v)){
            BitfieldInstruction ins; ins.mnemonic=item.get("mnemonic")->str(); ins.opcode=static_cast<std::uint16_t>(hex(item.get("opcode")->str())); ins.encoding_template=item.get("encoding_template")->str(); ins.encoding_status=item.get("encoding_status")->str();
            const J* fs=item.get("bitfields"); if(fs){for(const J& jf:std::get<J::array>(fs->v)){BitField b; b.name=jf.get("name")->str(); b.start=static_cast<std::uint16_t>(jf.get("start")->u64()); b.end=static_cast<std::uint16_t>(jf.get("end")->u64()); b.width=static_cast<std::uint16_t>(jf.get("width")->u64()); b.mask_hex=jf.get("mask")->str(); b.shift=static_cast<std::uint16_t>(jf.get("shift")->u64()); ins.bitfields.push_back(std::move(b));}}
            instructions_.push_back(std::move(ins));
        }
        if(static_cast<std::uint64_t>(count->u64())!=instructions_.size()) throw std::runtime_error("instruction_count mismatch");
        return true;
    } catch(const std::exception& e){if(error)*error=e.what();return false;}
}

const BitfieldInstruction* BitfieldRegistry::by_opcode(std::uint16_t opcode) const noexcept { for(const auto& x:instructions_)if(x.opcode==opcode)return &x; return nullptr; }
const BitfieldInstruction* BitfieldRegistry::by_mnemonic(std::string_view mnemonic) const noexcept { for(const auto& x:instructions_)if(x.mnemonic==mnemonic)return &x; return nullptr; }

std::uint64_t extract_bits(std::uint64_t word, std::uint16_t shift, std::uint16_t width) noexcept {
    if(width==0)return 0; if(width>=64)return word>>shift; return (word>>shift)&((std::uint64_t{1}<<width)-1);
}
std::uint64_t insert_bits(std::uint64_t word, std::uint64_t value, std::uint16_t shift, std::uint16_t width) noexcept {
    if(width==0)return word; if(width>=64)return value; const auto mask=((std::uint64_t{1}<<width)-1)<<shift; return (word&~mask)|((value<<shift)&mask);
}
} // namespace chimera::isa
