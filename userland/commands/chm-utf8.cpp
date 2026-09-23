#include "../../desktop/aurora/i18n/aurora_utf.hpp"
#include "../../desktop/aurora/i18n/aurora_emoji.hpp"
#include <iostream>
#include <string>
int main(int argc,char**argv){if(argc<2){std::cout<<"usage: chm-utf8 check|count|sanitize|emoji|aliases TEXT\n";return 2;}std::string s=argc>2?argv[2]:"";std::string op=argv[1];if(op=="check"){bool ok=aurora::utf8::valid(s);std::cout<<(ok?"valid UTF-8":"invalid UTF-8")<<"\n";return ok?0:1;}if(op=="count"){std::cout<<aurora::utf8::codepoint_count(s)<<" code points\n";return 0;}if(op=="sanitize"){std::cout<<aurora::utf8::sanitize(s)<<"\n";return 0;}if(op=="emoji"){std::cout<<(aurora::emoji::contains_emoji(s)?"emoji-present":"no-emoji")<<"\n";return 0;}if(op=="aliases"){std::cout<<aurora::emoji::replace_aliases(s)<<"\n";return 0;}return 2;}