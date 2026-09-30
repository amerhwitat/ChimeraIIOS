#pragma once
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
typedef enum chimera_utf8_status {
    CHIMERA_UTF8_OK = 0,
    CHIMERA_UTF8_NEED_MORE = 1,
    CHIMERA_UTF8_INVALID = -1,
    CHIMERA_UTF8_OVERLONG = -2,
    CHIMERA_UTF8_SURROGATE = -3,
    CHIMERA_UTF8_OUT_OF_RANGE = -4
} chimera_utf8_status;
typedef struct chimera_utf8_decoder {
    uint32_t codepoint;
    uint32_t minimum;
    uint8_t expected;
    uint8_t seen;
} chimera_utf8_decoder;
void chimera_utf8_decoder_init(chimera_utf8_decoder* d);
int chimera_utf8_decode(chimera_utf8_decoder* d, uint8_t byte, uint32_t* codepoint);
int chimera_utf8_validate(const uint8_t* data, size_t length);
size_t chimera_utf8_encode(uint32_t codepoint, uint8_t out[4]);
int chimera_unicode_scalar(uint32_t codepoint);
uint32_t chimera_utf8_version(void);
#ifdef __cplusplus
}
#endif
