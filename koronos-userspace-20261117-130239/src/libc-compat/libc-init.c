/*
 * Koronos libc compatibility layer
 * Minimal libc implementation for Koronos userspace
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/* Standard I/O */
void puts_compat(const char *str) {
    write(STDOUT_FILENO, str, strlen(str));
    write(STDOUT_FILENO, "\n", 1);
}

/* String functions */
char* strcpy_compat(char *dest, const char *src) {
    while ((*dest++ = *src++));
    return dest;
}

int strlen_compat(const char *str) {
    int len = 0;
    while (*str++) len++;
    return len;
}

/* Memory functions */
void* memcpy_compat(void *dest, const void *src, int count) {
    char *d = (char *)dest;
    const char *s = (const char *)src;
    while (count--) *d++ = *s++;
    return dest;
}

void memset_compat(void *ptr, int value, int count) {
    char *p = (char *)ptr;
    while (count--) *p++ = value;
}

/* Init function called by init binary */
int libc_init(int argc, char *argv[], char *envp[]) {
    puts_compat("[KORONOS_LIBC] Koronos libc compatibility layer initialized");
    puts_compat("[KORONOS_LIBC] Standard functions available");
    return 0;
}
