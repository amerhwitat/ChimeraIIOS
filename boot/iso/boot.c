#include <stdint.h>
static volatile uint16_t *const vga=(uint16_t*)0xB8000;
static inline void outb(uint16_t port,uint8_t value){__asm__ volatile("outb %0,%1"::"a"(value),"Nd"(port));}
static inline uint8_t inb(uint16_t port){uint8_t v;__asm__ volatile("inb %1,%0":"=a"(v):"Nd"(port));return v;}
static void serial_init(void){outb(0x3F9,0);outb(0x3FB,0x80);outb(0x3F8,3);outb(0x3F9,0);outb(0x3FB,3);outb(0x3FA,0xC7);outb(0x3FC,3);}
static void serial_puts(const char *s){for(uint32_t i=0;s[i];++i){while(!(inb(0x3FD)&0x20)){}outb(0x3F8,(uint8_t)s[i]);}}
void chimera_boot_main(uint32_t magic,uint32_t multiboot_info){
    (void)multiboot_info; serial_init();
    const char *msg=(magic==0x36d76289u)?"Chimera II OS bootstrap: Multiboot2 OK\r\n":"Chimera II OS bootstrap: invalid Multiboot2 magic\r\n";
    serial_puts(msg);
    for(uint32_t i=0;msg[i] && msg[i]!='\r';++i)vga[i]=(uint16_t)msg[i]|0x0700u;
}
