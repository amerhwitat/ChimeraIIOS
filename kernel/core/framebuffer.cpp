#include "chimera/framebuffer.h"
namespace {
constexpr uint32_t TAG_END=0, TAG_FRAMEBUFFER=8, MAX_INFO=16u*1024u*1024u;
constexpr uint32_t CELL_W=8, CELL_H=16, WHITE=0xFFFFFFu, BLACK=0;
static koronos_framebuffer_info fb{};
static uint32_t col=0,row=0,ready=0;
static uint32_t r32(const uint8_t*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static uint64_t r64(const uint8_t*p){return (uint64_t)r32(p)|((uint64_t)r32(p+4)<<32);}
static uint32_t mask(uint8_t p,uint8_t n){return ((1u<<n)-1u)<<p;}
static bool field_ok(uint8_t p,uint8_t n,uint8_t b){return n&&n<=8&&p<b&&(uint32_t)p+n<=b;}
static void put_pixel(uint32_t x,uint32_t y,uint32_t c){
 if(x>=fb.width||y>=fb.height)return;
 volatile uint8_t*p=(volatile uint8_t*)(uintptr_t)fb.address+(uint64_t)y*fb.pitch+(uint64_t)x*fb.bytes_per_pixel;
 for(uint32_t i=0;i<fb.bytes_per_pixel;++i)p[i]=(uint8_t)(c>>(i*8u));
}
static void fill(uint32_t x,uint32_t y,uint32_t w,uint32_t h,uint32_t c){
 uint32_t xe=x+w<fb.width?x+w:fb.width, ye=y+h<fb.height?y+h:fb.height;
 for(uint32_t py=y;py<ye;++py)for(uint32_t px=x;px<xe;++px)put_pixel(px,py,c);
}
static const uint8_t font[36][7]={
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},
 {30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
 {14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{14,4,4,4,4,4,14},
 {7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
 {17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},
 {30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
 {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},
 {17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},
 {17,17,10,4,4,4,4},{31,1,2,4,8,16,31},
 {14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},
 {30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},
 {14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},{14,17,17,15,1,1,14}
};
static void glyph(char c,uint8_t out[7]){
 if(c>='a'&&c<='z')c=(char)(c-'a'+'A');
 if(c>='A'&&c<='Z'){for(uint32_t i=0;i<7;++i)out[i]=font[(uint32_t)(c-'A')][i];return;}
 if(c>='0'&&c<='9'){for(uint32_t i=0;i<7;++i)out[i]=font[26u+(uint32_t)(c-'0')][i];return;}
 uint8_t p[7]={0,0,0,0,0,0,0};
 switch(c){
 case ' ':break; case '.':p[6]=4;break; case ',':p[5]=4;p[6]=8;break;
 case ':':p[2]=4;p[5]=4;break;case ';':p[2]=4;p[5]=4;p[6]=8;break;
 case '-':p[3]=14;break;case '_':p[6]=31;break;case '+':p[2]=4;p[3]=14;p[4]=4;break;
 case '=':p[2]=14;p[4]=14;break;case '/':p[0]=1;p[1]=2;p[2]=2;p[3]=4;p[4]=8;p[5]=8;p[6]=16;break;
 case '[':p[0]=14;p[1]=8;p[2]=8;p[3]=8;p[4]=8;p[5]=8;p[6]=14;break;
 case ']':p[0]=14;p[1]=2;p[2]=2;p[3]=2;p[4]=2;p[5]=2;p[6]=14;break;
 case '(':p[0]=2;p[1]=4;p[2]=8;p[3]=8;p[4]=8;p[5]=4;p[6]=2;break;
 case ')':p[0]=8;p[1]=4;p[2]=2;p[3]=2;p[4]=2;p[5]=4;p[6]=8;break;
 case '%':p[0]=17;p[1]=2;p[2]=4;p[3]=8;p[4]=17;break;
 case '!':p[0]=4;p[1]=4;p[2]=4;p[3]=4;p[5]=4;break;
 case '?':p[0]=14;p[1]=17;p[2]=1;p[3]=2;p[4]=4;p[6]=4;break;
 case '#':p[0]=10;p[1]=31;p[2]=10;p[3]=10;p[4]=31;p[5]=10;break;
 case '*':p[1]=21;p[2]=14;p[3]=31;p[4]=14;p[5]=21;break;
 case '<':p[1]=2;p[2]=4;p[3]=8;p[4]=4;p[5]=2;break;
 case '>':p[1]=8;p[2]=4;p[3]=2;p[4]=4;p[5]=8;break;
 case '\\':p[0]=16;p[1]=8;p[2]=8;p[3]=4;p[4]=2;p[5]=2;p[6]=1;break;
 case '\'':p[0]=4;p[1]=4;break;case '"':p[0]=10;p[1]=10;break;
 default:p[0]=14;p[1]=17;p[2]=1;p[3]=2;p[4]=4;p[6]=4;break;
 }
 for(uint32_t i=0;i<7;++i)out[i]=p[i];
}
static void draw(uint32_t x,uint32_t y,char c){
 uint8_t rows[7];glyph(c,rows);
 for(uint32_t gy=0;gy<7;++gy)for(uint32_t gx=0;gx<5;++gx)
  if(rows[gy]&(1u<<(4u-gx))){put_pixel(x*CELL_W+1u+gx,y*CELL_H+1u+gy*2u,WHITE);put_pixel(x*CELL_W+1u+gx,y*CELL_H+2u+gy*2u,WHITE);}
}
static void scroll(){
 volatile uint8_t*p=(volatile uint8_t*)(uintptr_t)fb.address;
 uint64_t n=(uint64_t)(fb.height-CELL_H)*fb.pitch, shift=(uint64_t)CELL_H*fb.pitch;
 for(uint64_t i=0;i<n;++i)p[i]=p[i+shift];
 fill(0,fb.height-CELL_H,fb.width,CELL_H,BLACK);
 uint32_t rows=fb.height/CELL_H;row=rows?rows-1u:0u;
}
static void nl(){col=0;++row;if(row>=fb.height/CELL_H)scroll();}
}
extern "C" int koronos_framebuffer_parse_multiboot2(uint64_t address,koronos_framebuffer_info*out){
 if(!address||!out)return -1;
 const uint8_t*b=(const uint8_t*)(uintptr_t)address;uint32_t total=r32(b);
 if(total<16u||total>MAX_INFO)return -2;
 for(uint32_t off=8u;off<=total-8u;){
  uint32_t type=r32(b+off),size=r32(b+off+4u);
  if(size<8u||size>total-off)return -3;
  if(type==TAG_END)break;
  if(type==TAG_FRAMEBUFFER){
   if(size<38u)return -4;
   koronos_framebuffer_info v{};
   v.address=r64(b+off+8u);v.pitch=r32(b+off+16u);v.width=r32(b+off+20u);v.height=r32(b+off+24u);
   v.bits_per_pixel=b[off+28u];if(b[off+29u]!=1u)return -5;
   v.red_position=b[off+32u];v.red_size=b[off+33u];v.green_position=b[off+34u];v.green_size=b[off+35u];v.blue_position=b[off+36u];v.blue_size=b[off+37u];
   if(v.bits_per_pixel!=24u&&v.bits_per_pixel!=32u)return -6;
   v.bytes_per_pixel=(uint8_t)(v.bits_per_pixel/8u);
   if(v.width<CELL_W||v.height<CELL_H||v.width>8192u||v.height>8192u)return -7;
   if(v.pitch<(uint64_t)v.width*v.bytes_per_pixel)return -8;
   if(!field_ok(v.red_position,v.red_size,v.bits_per_pixel)||!field_ok(v.green_position,v.green_size,v.bits_per_pixel)||!field_ok(v.blue_position,v.blue_size,v.bits_per_pixel))return -9;
   uint32_t rm=mask(v.red_position,v.red_size),gm=mask(v.green_position,v.green_size),bm=mask(v.blue_position,v.blue_size);
   if((rm&gm)||(rm&bm)||(gm&bm))return -10;
   v.length=(uint64_t)v.pitch*v.height;
   if(!v.address||!v.length||v.address>=KORONOS_FRAMEBUFFER_PHYS_LIMIT||v.length>KORONOS_FRAMEBUFFER_PHYS_LIMIT-v.address)return -11;
   *out=v;return 0;
  }
  uint32_t aligned=(size+7u)&~7u;if(aligned<size||aligned>total-off)return -12;off+=aligned;
 }
 return -13;
}
extern "C" int koronos_fb_console_init(uint64_t info){
 koronos_framebuffer_info parsed{};int rc=koronos_framebuffer_parse_multiboot2(info,&parsed);if(rc)return rc;
 fb=parsed;col=0;row=0;ready=1;fill(0,0,fb.width,fb.height,BLACK);return 0;
}
extern "C" void koronos_fb_console_write(const char*text){
 if(!ready||!text)return;
 while(*text){char c=*text++;if(c=='\r')col=0;else if(c=='\n')nl();else if(c=='\t'){for(uint32_t i=0;i<4;++i){draw(col,row,' ');if(++col>=fb.width/CELL_W)nl();}}else{draw(col,row,c);if(++col>=fb.width/CELL_W)nl();}}
}
extern "C" int koronos_fb_console_ready(void){return ready?1:0;}
extern "C" int koronos_fb_console_get_info(koronos_framebuffer_info*out){if(!ready||!out)return -1;*out=fb;return 0;}
