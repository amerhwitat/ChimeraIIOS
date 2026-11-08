# syntax=docker/dockerfile:1
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG CHIMERA_ARCH=x86_64
ARG CHIMERA_FIRMWARE=uefi
ENV DEBIAN_FRONTEND=noninteractive \
    CHIMERA_ARCH=${CHIMERA_ARCH} \
    CHIMERA_FIRMWARE=${CHIMERA_FIRMWARE}

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then sed -i -E 's/^Components:.*/Components: main universe/' /etc/apt/sources.list.d/ubuntu.sources; fi \
    && apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc g++ gcc-multilib make cmake ninja-build binutils nasm \
    grub-common grub-pc-bin grub-efi-amd64-bin grub-efi-ia32-bin xorriso mtools dosfstools \
    python3 python3-pytest python3-cairosvg qemu-system-x86 qemu-user-static ovmf file cpio busybox-static librsvg2-bin rsync xz-utils gzip bzip2 zstd \
    gcc-i686-linux-gnu gcc-arm-linux-gnueabi gcc-aarch64-linux-gnu gcc-arm-linux-gnueabihf gcc-riscv64-linux-gnu gcc-powerpc64le-linux-gnu gcc-s390x-linux-gnu \
    ffmpeg imagemagick unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src
COPY docker/iso/entrypoint.sh /usr/local/bin/chimera-iso-builder
RUN chmod +x /usr/local/bin/chimera-iso-builder tools/build/create-bootable-iso.sh \
    boot/iso/build-iso.sh boot/iso/prepare-layout.sh boot/spitfire/build-spitfire.sh

ENTRYPOINT ["/usr/local/bin/chimera-iso-builder"]
