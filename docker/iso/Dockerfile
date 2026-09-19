# syntax=docker/dockerfile:1
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG CHIMERA_ARCH=x86_64
ARG CHIMERA_FIRMWARE=uefi
ENV DEBIAN_FRONTEND=noninteractive \
    CHIMERA_ARCH=${CHIMERA_ARCH} \
    CHIMERA_FIRMWARE=${CHIMERA_FIRMWARE}

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc g++ gcc-multilib make cmake ninja-build binutils nasm \
    grub-common grub-pc-bin grub-efi-amd64-bin grub-efi-ia32-bin xorriso mtools dosfstools \
    python3 python3-pytest qemu-system-x86 file cpio rsync xz-utils gzip bzip2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src
COPY docker/iso/entrypoint.sh /usr/local/bin/chimera-iso-builder
RUN chmod +x /usr/local/bin/chimera-iso-builder tools/build/create-bootable-iso.sh \
    boot/iso/build-iso.sh boot/iso/prepare-layout.sh boot/spitfire/build-spitfire.sh

ENTRYPOINT ["/usr/local/bin/chimera-iso-builder"]
