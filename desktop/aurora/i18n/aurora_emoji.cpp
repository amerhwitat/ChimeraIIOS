#include "aurora_emoji.hpp"
#include "aurora_utf.hpp"
namespace aurora::emoji{
static const std::vector<Entry> k={{"grinning","😀","faces"},{"joy","😂","faces"},{"heart","❤️","symbols"},{"thumbs_up","👍","people"},{"fire","🔥","symbols"},{"rocket","🚀","travel"},{"check","✅","symbols"},{"warning","⚠️","symbols"},{"gear","⚙️","objects"},{"globe","🌐","travel"},{"lock","🔒","objects"},{"terminal","🖥️","objects"},{"folder","📁","objects"},{"file","📄","objects"},{"camera","📷","objects"},{"microphone","🎙️","objects"},{"keyboard","⌨️","objects"},{"mouse","🖱️","objects"},{"accessibility","♿","symbols"},{"rtl","↔️","symbols"},{"language","🗣️","people"},{"chimera","🧬","symbols"},{"aurora","🌌","nature"}};
const std::vector<Entry>& catalog(){return k;}
const Entry* find(std::string_view n){for(auto&x:k)if(n==x.name)return &x;return nullptr;}
bool contains_emoji(std::string_view s){for(auto c:aurora::utf8::decode(s))if(aurora::utf8::is_emoji(c.value))return true;return false;}
std::string replace_aliases(std::string_view s){std::string o(s);for(auto&x:k){std::string a=":"+std::string(x.name)+":";std::size_t p=0;while((p=o.find(a,p))!=std::string::npos){o.replace(p,a.size(),x.glyph);p+=std::string(x.glyph).size();}}return o;}
}