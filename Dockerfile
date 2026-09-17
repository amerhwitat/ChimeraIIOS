# syntax=docker/dockerfile:1
FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
ARG CHIMERA_ARCH=x86_64
ARG CHIMERA_FIRMWARE=uefi
ENV CHIMERA_ARCH=${CHIMERA_ARCH} CHIMERA_FIRMWARE=${CHIMERA_FIRMWARE} DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc g++ binutils clang lld nasm cmake ninja-build make pkg-config git ca-certificates python3 python3-pytest python3-pip grub-common grub-pc-bin grub-efi-amd64-bin xorriso mtools dosfstools qemu-system-x86 file cpio rsync xz-utils gzip bzip2 zip unzip openssl && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
RUN git clone --depth 1 https://github.com/amerhwitat/ChimeraIIOS.git /workspace/ChimeraIIOS
WORKDIR /workspace/ChimeraIIOS
RUN set -eux; cmake --version; gcc --version; g++ --version; clang --version; nasm --version; grub-mkrescue --version; xorriso --version; python3 --version; qemu-system-x86_64 --version
ENV BUILD_ROOT=/workspace/ChimeraIIOS/build ISO_ROOT=/workspace/ChimeraIIOS/boot/iso/dist OUTPUT_ROOT=/workspace/ChimeraIIOS/docker-output
RUN set -eux; ./tools/build/build-hosted.sh; ./tools/build/build-baremetal.sh
RUN set -eux; chmod +x boot/iso/*.sh 2>/dev/null || true; ./boot/iso/prepare-layout.sh
RUN set -eux; ./boot/iso/build-iso.sh
RUN set -eux; mkdir -p "$OUTPUT_ROOT"; find boot/iso/dist -maxdepth 3 -type f -print | sort; cp -a boot/iso/dist/. "$OUTPUT_ROOT/"
CMD ["bash", "-lc", "find /workspace/ChimeraIIOS/docker-output -maxdepth 3 -type f -printf '%p\\n' | sort"]
