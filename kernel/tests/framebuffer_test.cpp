#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "chimera/framebuffer.h"
static void w32(uint8_t*p,uint32_t v){p[0]=(uint8_t)v;p[1]=(uint8_t)(v>>8);p[2]=(uint8_t)(v>>16);p[3]=(uint8_t)(v>>24);}
static void w64(uint8_t*p,uint64_t v){w32(p,(uint32_t)v);w32(p+4,(uint32_t)(v>>32));}
static void valid(uint8_t*b){memset(b,0,64);w32(b,64);w32(b+8,8);w32(b+12,38);w64(b+16,0xE0000000ull);w32(b+24,3200);w32(b+28,800);w32(b+32,600);b[36]=32;b[37]=1;b[40]=16;b[41]=8;b[42]=8;b[43]=8;b[44]=0;b[45]=8;w32(b+48,0);w32(b+52,8);}
int main(){uint8_t b[64];koronos_framebuffer_info i{};valid(b);
 if(koronos_framebuffer_parse_multiboot2((uint64_t)(uintptr_t)b,&i))return 1;
 if(i.width!=800||i.height!=600||i.pitch!=3200||i.length!=1920000ull||i.bytes_per_pixel!=4)return 2;
 valid(b);w32(b+24,100);if(!koronos_framebuffer_parse_multiboot2((uint64_t)(uintptr_t)b,&i))return 3;
 valid(b);w64(b+16,0xFFFFFFFFull);if(!koronos_framebuffer_parse_multiboot2((uint64_t)(uintptr_t)b,&i))return 4;
 valid(b);b[37]=0;if(!koronos_framebuffer_parse_multiboot2((uint64_t)(uintptr_t)b,&i))return 5;
 valid(b);w32(b,0xFFFFFFFFu);if(!koronos_framebuffer_parse_multiboot2((uint64_t)(uintptr_t)b,&i))return 6;
 puts("Koronos Multiboot2 framebuffer parser tests passed");return 0;}
