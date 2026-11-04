# SPDX-License-Identifier: GPL-3.0
#
# Koronos kernel build -- Linux-style workflow.
#
#   make defconfig          regenerate kernel/.config from kernel/Kconfig
#   make menuconfig         interactive (line-based) configuration
#   make oldconfig          resolve new symbols against an existing .config
#   make -j$(nproc)         build build/koronos/<arch>/koronos.elf + System.map
#   make modules            build loadable modules from kernel/modules/Kbuild
#   make modules_install    install modules under $(DESTDIR)/lib/modules/$(KERNELRELEASE)
#   make install            install the kernel ELF under $(DESTDIR)/boot
#   make legacy             run the historical kernel/build-koronos.sh recipe
#   make clean / mrproper   drop build products / build products + configuration

MAKEFLAGS += --no-print-directory
.DEFAULT_GOAL := all

ROOT := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))/..
ROOT := $(abspath $(ROOT))

ARCH ?= x86_64
BUILD ?= $(ROOT)/build/koronos/$(ARCH)
CONFIG_FILE := $(ROOT)/kernel/.config
OBJ_MK := $(BUILD)/kor-obj.mk

# The configuration and object manifest are regenerated makefiles: `make` treats
# a file created by a recipe with no explicit prerequisites as intermediate and
# deletes it at the end of the run, which restarted defconfig/autoconf forever
# ("Deleting file .../.config"). Keep them, and keep config generation serial so
# a parallel build cannot race two kconfig runs against the same file.
.PRECIOUS: $(CONFIG_FILE) $(OBJ_MK)
.NOTPARALLEL:
KCONFIG := $(ROOT)/kernel/Kconfig
PYTHON ?= python3
CXX ?= g++
NASM ?= nasm
LD ?= ld
NM ?= nm

-include $(CONFIG_FILE)

KERNELRELEASE := 1.0.0$(CONFIG_KORONOS_LOCALVERSION)

KOR_INCLUDE := $(ROOT)/kernel/include
KOR_CXXFLAGS := -ffreestanding -fno-builtin -fno-exceptions -fno-rtti \
	-fno-stack-protector -fno-pic -fno-pie -mcmodel=kernel -mno-red-zone \
	-mno-sse -mno-mmx -nostdinc++ -Wall -Wextra -O2 \
	-I$(KOR_INCLUDE) -I$(BUILD)/include \
	-DKORONOS_KERNEL=1 -DKORONOS_NBIT_WIDTH=$(CONFIG_KORONOS_NBIT_WIDTH) \
	-DKORONOS_LOCALVERSION='"$(CONFIG_KORONOS_LOCALVERSION)"'
KOR_LDFLAGS := -nostdlib -z max-page-size=0x1000 --build-id=none \
	-T $(ROOT)/kernel/arch/x86_64/koronos.ld

ifeq ($(ARCH),x86_64)
else
$(error ARCH=$(ARCH) is not buildable yet; the only accepted target is x86_64)
endif

ifneq ($(CONFIG_ARCH_X86_64),y)
$(warning CONFIG_ARCH_X86_64 is not set in $(CONFIG_FILE); run 'make defconfig')
endif

PHONY := all __build modules modules_install install legacy clean mrproper \
	help defconfig menuconfig oldconfig savedefconfig config autoconf system_map check
.PHONY: $(PHONY)

help:
	@echo "Koronos kernel build ($(KERNELRELEASE), ARCH=$(ARCH))"
	@echo "  make defconfig | menuconfig | oldconfig | savedefconfig"
	@echo "  make [-jN]            build koronos.elf, System.map, vmlinux"
	@echo "  make modules          build obj-m modules"
	@echo "  make modules_install  install modules (DESTDIR=...)"
	@echo "  make install          install kernel ELF (DESTDIR=...)"
	@echo "  make check            verify ELF class, required symbols, boot banners"
	@echo "  make legacy           run kernel/build-koronos.sh"
	@echo "  make clean | mrproper"

config:
	@mkdir -p $(BUILD)

defconfig: config
	@$(PYTHON) $(ROOT)/scripts/kconfig/kconfig.py defconfig $(KCONFIG) $(CONFIG_FILE) --srctree $(ROOT)
	@$(MAKE) -s autoconf

oldconfig: config
	@$(PYTHON) $(ROOT)/scripts/kconfig/kconfig.py oldconfig $(KCONFIG) $(CONFIG_FILE) --srctree $(ROOT)
	@$(MAKE) -s autoconf

menuconfig: config
	@$(PYTHON) $(ROOT)/scripts/kconfig/kconfig.py menuconfig $(KCONFIG) $(CONFIG_FILE) --srctree $(ROOT)
	@$(MAKE) -s autoconf

savedefconfig:
	@$(PYTHON) $(ROOT)/scripts/kconfig/kconfig.py savedefconfig $(KCONFIG) $(ROOT)/kernel/defconfig --srctree $(ROOT)

autoconf: $(CONFIG_FILE)
	@$(PYTHON) $(ROOT)/scripts/kconfig/kconfig.py autoconf $(KCONFIG) $(CONFIG_FILE) \
		$(BUILD)/include/config/auto.conf $(BUILD)/include/generated/autoconf.h --srctree $(ROOT)

$(CONFIG_FILE):
	@$(MAKE) -s defconfig

all:
	@$(MAKE) -s $(OBJ_MK)
	@$(MAKE) -s autoconf
	@$(MAKE) -s __build

$(OBJ_MK): $(CONFIG_FILE)
	@$(PYTHON) $(ROOT)/scripts/kbuild/obj2mk.py --root $(ROOT) --build $(BUILD) \
		--config $(CONFIG_FILE) --out $(OBJ_MK) --json $(BUILD)/kor-obj.json

-include $(OBJ_MK)

__build: $(BUILD)/koronos.elf

$(BUILD)/%.o: $(ROOT)/kernel/%.cpp | $(BUILD)
	@echo "  CXX  $(<:$(ROOT)/kernel/%=%)"
	@mkdir -p $(dir $@)
	@$(CXX) $(KOR_CXXFLAGS) $(KO_CFLAGS) -c $< -o $@

$(BUILD)/%.o: $(ROOT)/kernel/%.asm | $(BUILD)
	@echo "  ASM  $(<:$(ROOT)/kernel/%=%)"
	@mkdir -p $(dir $@)
	@$(NASM) -f elf64 $< -o $@

$(BUILD):
	@mkdir -p $(BUILD)

$(BUILD)/koronos.elf: $(KO_OBJS) $(ROOT)/kernel/arch/x86_64/koronos.ld
	@echo "  LD   koronos.elf"
	@$(LD) $(KOR_LDFLAGS) $(KO_OBJS) -o $@
	@ln -sfn koronos.elf $(BUILD)/vmlinux
	@cp -f $@ $(BUILD)/koronos.elf64
	@$(MAKE) -s system_map
	@echo "  OK   $@"

system_map: $(BUILD)/koronos.elf
	@$(NM) -n $(BUILD)/koronos.elf > $(BUILD)/System.map 2>/dev/null || true

modules:
	@$(MAKE) -s $(OBJ_MK)
	@$(MAKE) -s autoconf
	@mkdir -p $(BUILD)/modules
	@for m in $(KO_MODULES); do \
		name=$$(basename $$m .ko); \
		echo "  MOD  $$name.ko"; \
		$(NASM) -f elf64 -D KORONOS_MODULE_NAME='"'"'$$name'"'"' \
			-o $(BUILD)/modules/$$name.obj $(ROOT)/kernel/modules/$$name.asm || exit 1; \
		$(LD) -r -o $(BUILD)/modules/$$name.ko $(BUILD)/modules/$$name.obj || exit 1; \
		printf 'name: %s\nversion: %s\nlicense: GPL-3.0\n' $$name $(KERNELRELEASE) \
			> $(BUILD)/modules/$$name.modinfo; \
	done
	@echo "  OK   modules in $(BUILD)/modules"

modules_install: modules
	@install_dir=$(DESTDIR)/lib/modules/$(KERNELRELEASE); \
	mkdir -p $$install_dir/kernel/modules; \
	cp -f $(BUILD)/modules/*.ko $(BUILD)/modules/*.modinfo $$install_dir/kernel/modules/; \
	: > $$install_dir/modules.dep; \
	for m in $(BUILD)/modules/*.ko; do \
		printf '%s:\n' "$$(basename $$m)" >> $$install_dir/modules.dep; done; \
	echo "  INSTALL modules -> $$install_dir"

install: $(BUILD)/koronos.elf
	@install -d $(DESTDIR)/boot
	@install -m 0644 $(BUILD)/koronos.elf $(DESTDIR)/boot/koronos-$(KERNELRELEASE).elf
	@install -m 0644 $(BUILD)/System.map $(DESTDIR)/boot/System.map-$(KERNELRELEASE) 2>/dev/null || true
	@echo "  INSTALL $(DESTDIR)/boot/koronos-$(KERNELRELEASE).elf"

check: $(BUILD)/koronos.elf
	@$(PYTHON) $(ROOT)/scripts/kbuild/verify.py --elf $(BUILD)/koronos.elf

legacy:
	@bash $(ROOT)/kernel/build-koronos.sh

clean:
	@rm -rf $(BUILD)
	@echo "  CLEAN $(BUILD)"

mrproper: clean
	@rm -f $(CONFIG_FILE) $(CONFIG_FILE).json
	@rm -rf $(ROOT)/build/koronos
	@echo "  MRPROPER removed $(CONFIG_FILE) and build/koronos"
