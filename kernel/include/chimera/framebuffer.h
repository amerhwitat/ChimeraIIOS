#ifndef CHIMERA_FRAMEBUFFER_H
#define CHIMERA_FRAMEBUFFER_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define KORONOS_FRAMEBUFFER_ABI 1u
#define KORONOS_FRAMEBUFFER_PHYS_LIMIT 0x100000000ull
typedef struct koronos_framebuffer_info {
 uint64_t address, length;
 uint32_t pitch, width, height;
 uint8_t bits_per_pixel, bytes_per_pixel;
 uint8_t red_position, red_size, green_position, green_size, blue_position, blue_size;
} koronos_framebuffer_info;
int koronos_framebuffer_parse_multiboot2(uint64_t multiboot_info, koronos_framebuffer_info *out);
int koronos_fb_console_init(uint64_t multiboot_info);
void koronos_fb_console_write(const char *text);
int koronos_fb_console_ready(void);
int koronos_fb_console_get_info(koronos_framebuffer_info *out);
#ifdef __cplusplus
}
#endif
#endif
