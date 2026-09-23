#include "aurora_utf.hpp"
#include "aurora_emoji.hpp"
#include <cassert>
#include <iostream>
int main(){assert(aurora::utf8::valid("Hello العربية עברית 😀"));assert(aurora::utf8::codepoint_count("A😀")==2);assert(aurora::utf8::is_emoji(0x1F680));assert(aurora::utf8::is_combining(0x0301));assert(aurora::emoji::contains_emoji("Chimera 🧬"));assert(aurora::emoji::replace_aliases(":rocket:")=="🚀");std::cout<<"aurora-utf-selftest: PASS\n";}