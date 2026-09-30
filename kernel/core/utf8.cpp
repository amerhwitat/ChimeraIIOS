#include <chimera/utf8.h>
static int scalar(uint32_t cp) { return cp <= 0x10FFFFu && !(cp >= 0xD800u && cp <= 0xDFFFu); }
void chimera_utf8_decoder_init(chimera_utf8_decoder* d) {
    if (!d) return;
    d->codepoint=0; d->minimum=0; d->expected=0; d->seen=0;
}
int chimera_unicode_scalar(uint32_t cp) { return scalar(cp); }
int chimera_utf8_decode(chimera_utf8_decoder* d,uint8_t byte,uint32_t* cp) {
    if (!d || !cp) return CHIMERA_UTF8_INVALID;
    if (d->expected==0) {
        if (byte<=0x7Fu) { *cp=byte; return CHIMERA_UTF8_OK; }
        if (byte>=0xC2u && byte<=0xDFu) { d->codepoint=byte&0x1Fu; d->minimum=0x80u; d->expected=1; d->seen=0; return CHIMERA_UTF8_NEED_MORE; }
        if (byte>=0xE0u && byte<=0xEFu) { d->codepoint=byte&0x0Fu; d->minimum=0x800u; d->expected=2; d->seen=0; return CHIMERA_UTF8_NEED_MORE; }
        if (byte>=0xF0u && byte<=0xF4u) { d->codepoint=byte&0x07u; d->minimum=0x10000u; d->expected=3; d->seen=0; return CHIMERA_UTF8_NEED_MORE; }
        return CHIMERA_UTF8_INVALID;
    }
    if ((byte&0xC0u)!=0x80u) { chimera_utf8_decoder_init(d); return CHIMERA_UTF8_INVALID; }
    d->codepoint=(d->codepoint<<6)|(byte&0x3Fu); d->seen++;
    if (d->seen<d->expected) return CHIMERA_UTF8_NEED_MORE;
    uint32_t value=d->codepoint, minimum=d->minimum; chimera_utf8_decoder_init(d);
    if (value<minimum) return CHIMERA_UTF8_OVERLONG;
    if (value>=0xD800u && value<=0xDFFFu) return CHIMERA_UTF8_SURROGATE;
    if (value>0x10FFFFu) return CHIMERA_UTF8_OUT_OF_RANGE;
    *cp=value; return CHIMERA_UTF8_OK;
}
int chimera_utf8_validate(const uint8_t* data,size_t length) {
    if (!data) return length==0?CHIMERA_UTF8_OK:CHIMERA_UTF8_INVALID;
    chimera_utf8_decoder d; chimera_utf8_decoder_init(&d); uint32_t cp=0;
    for (size_t i=0;i<length;++i) { int rc=chimera_utf8_decode(&d,data[i],&cp); if (rc<0) return rc; }
    return d.expected==0?CHIMERA_UTF8_OK:CHIMERA_UTF8_NEED_MORE;
}
size_t chimera_utf8_encode(uint32_t cp,uint8_t out[4]) {
    if (!out || !scalar(cp)) return 0;
    if (cp<=0x7Fu) { out[0]=(uint8_t)cp; return 1; }
    if (cp<=0x7FFu) { out[0]=(uint8_t)(0xC0u|(cp>>6)); out[1]=(uint8_t)(0x80u|(cp&0x3Fu)); return 2; }
    if (cp<=0xFFFFu) { out[0]=(uint8_t)(0xE0u|(cp>>12)); out[1]=(uint8_t)(0x80u|((cp>>6)&0x3Fu)); out[2]=(uint8_t)(0x80u|(cp&0x3Fu)); return 3; }
    out[0]=(uint8_t)(0xF0u|(cp>>18)); out[1]=(uint8_t)(0x80u|((cp>>12)&0x3Fu)); out[2]=(uint8_t)(0x80u|((cp>>6)&0x3Fu)); out[3]=(uint8_t)(0x80u|(cp&0x3Fu)); return 4;
}
uint32_t chimera_utf8_version(void) { return 1; }
