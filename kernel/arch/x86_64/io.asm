BITS 64
section .text
global koronos_inb
global koronos_inw
global koronos_inl
global koronos_outb
global koronos_outw
global koronos_outl
koronos_inb: mov dx,di; in al,dx; movzx eax,al; ret
koronos_inw: mov dx,di; in ax,dx; movzx eax,ax; ret
koronos_inl: mov dx,di; in eax,dx; ret
koronos_outb: mov dx,di; mov al,sil; out dx,al; ret
koronos_outw: mov dx,di; mov ax,si; out dx,ax; ret
koronos_outl: mov dx,di; mov eax,esi; out dx,eax; ret
