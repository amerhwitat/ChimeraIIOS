CC ?= gcc
LD ?= ld
ASFLAGS := -m32
CFLAGS := -m32 -std=c11 -O2 -Wall -Wextra -Werror -ffreestanding -fno-pie -fno-stack-protector -fno-asynchronous-unwind-tables -fno-unwind-tables
LDFLAGS := -m elf_i386 -T linker.ld -nostdlib
BUILD ?= build

.PHONY: all clean check
all: $(BUILD)/koronos32-probe.elf

$(BUILD):
	mkdir -p "$@"

$(BUILD)/boot.o: boot.S | $(BUILD)
	$(CC) $(ASFLAGS) -c "$<" -o "$@"

$(BUILD)/kernel.o: kernel.c | $(BUILD)
	$(CC) $(CFLAGS) -c "$<" -o "$@"

$(BUILD)/koronos32-probe.elf: $(BUILD)/boot.o $(BUILD)/kernel.o linker.ld
	$(LD) $(LDFLAGS) -o "$@" $(BUILD)/boot.o $(BUILD)/kernel.o

check: $(BUILD)/koronos32-probe.elf
	readelf -h "$<" | grep -Eq 'Class:[[:space:]]+ELF32'
	readelf -h "$<" | grep -Eq 'Machine:[[:space:]]+Intel 80386'

clean:
	rm -rf "$(BUILD)"
