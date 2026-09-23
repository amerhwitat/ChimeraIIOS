#include "aurora_utf.hpp"
namespace aurora::utf8 {
static bool cont(unsigned char c){return (c&0xC0)==0x80;}
static bool scalar(char32_t c){return c<=0x10FFFF && !(c>=0xD800&&c<=0xDFFF);}
bool valid(std::string_view s){for(std::size_t i=0;i<s.size();){unsigned char c=s[i];char32_t v=0;std::size_t n=1;
if(c<0x80)v=c;else if((c&0xE0)==0xC0){n=2;if(i+1>=s.size()||!cont(s[i+1]))return false;v=c&31;v=(v<<6)|(s[i+1]&63);if(v<0x80)return false;}
else if((c&0xF0)==0xE0){n=3;for(int j=1;j<3;j++)if(i+j>=s.size()||!cont(s[i+j]))return false;v=c&15;for(int j=1;j<3;j++)v=(v<<6)|(s[i+j]&63);if(v<0x800)return false;}
else if((c&0xF8)==0xF0){n=4;for(int j=1;j<4;j++)if(i+j>=s.size()||!cont(s[i+j]))return false;v=c&7;for(int j=1;j<4;j++)v=(v<<6)|(s[i+j]&63);if(v<0x10000)return false;}
else return false;if(!scalar(v))return false;i+=n;}return true;}
std::vector<CodePoint> decode(std::string_view s){std::vector<CodePoint> r;for(std::size_t i=0;i<s.size();){auto off=i;unsigned char c=s[i];char32_t v=0;std::size_t n=1;
if(c<0x80)v=c;else if((c&0xE0)==0xC0&&i+1<s.size()&&cont(s[i+1])){n=2;v=c&31;v=(v<<6)|(s[i+1]&63);}
else if((c&0xF0)==0xE0&&i+2<s.size()&&cont(s[i+1])&&cont(s[i+2])){n=3;v=c&15;v=(v<<6)|(s[i+1]&63);v=(v<<6)|(s[i+2]&63);}
else if((c&0xF8)==0xF0&&i+3<s.size()&&cont(s[i+1])&&cont(s[i+2])&&cont(s[i+3])){n=4;v=c&7;for(int j=1;j<4;j++)v=(v<<6)|(s[i+j]&63);}
else{v=0xFFFD;n=1;}if(!scalar(v))v=0xFFFD;r.push_back({v,off,n});i+=n;}return r;}
std::string encode(char32_t c){if(!scalar(c))c=0xFFFD;std::string s;if(c<0x80)s.push_back(char(c));else if(c<0x800){s.push_back(char(0xC0|(c>>6)));s.push_back(char(0x80|(c&63)));}else if(c<0x10000){s.push_back(char(0xE0|(c>>12)));s.push_back(char(0x80|((c>>6)&63)));s.push_back(char(0x80|(c&63)));}else{s.push_back(char(0xF0|(c>>18)));s.push_back(char(0x80|((c>>12)&63)));s.push_back(char(0x80|((c>>6)&63)));s.push_back(char(0x80|(c&63)));}return s;}
std::size_t codepoint_count(std::string_view s){return decode(s).size();}
std::string sanitize(std::string_view s,char32_t repl){std::string o;for(auto c:decode(s))o+=encode(c.value);return o;}
bool is_combining(char32_t c){return(c>=0x300&&c<=0x36F)||(c>=0x1AB0&&c<=0x1AFF)||(c>=0x1DC0&&c<=0x1DFF)||(c>=0x20D0&&c<=0x20FF)||(c>=0xFE20&&c<=0xFE2F);}
bool is_variation_selector(char32_t c){return(c>=0xFE00&&c<=0xFE0F)||(c>=0xE0100&&c<=0xE01EF);}
bool is_emoji(char32_t c){return(c>=0x1F000&&c<=0x1FAFF)||(c>=0x2600&&c<=0x27BF)||(c>=0x2300&&c<=0x23FF)||(c>=0x2B00&&c<=0x2BFF);}
bool is_rtl_codepoint(char32_t c){return(c>=0x0590&&c<=0x08FF)||(c>=0xFB1D&&c<=0xFDFF)||(c>=0xFE70&&c<=0xFEFF);}
bool is_whitespace(char32_t c){return c==0x20||c==0x09||c==0x0A||c==0x0D||c==0xA0||(c>=0x2000&&c<=0x200A)||c==0x2028||c==0x2029||c==0x202F||c==0x205F||c==0x3000;}
int display_width(char32_t c){if(c==0||is_combining(c)||is_variation_selector(c))return 0;if(is_emoji(c))return 2;if(is_whitespace(c))return 1;if(c<0x20||c==0x7F)return 0;return 1;}
}