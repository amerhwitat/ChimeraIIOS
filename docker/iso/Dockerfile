# syntax=docker/dockerfile:1
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG CHIMERA_ARCH=x86_64
ARG CHIMERA_FIRMWARE=uefi
ENV DEBIAN_FRONTEND=noninteractive \
    CHIMERA_ARCH=${CHIMERA_ARCH} \
    CHIMERA_FIRMWARE=${CHIMERA_FIRMWARE}

# The minimal Ubuntu base may not contain a CA bundle. Bootstrap only the
# signed Ubuntu package indexes with TLS peer verification disabled; APT still
# verifies the repository Release signatures. Install the trust store, then
# refresh all indexes again with normal TLS verification before installing the
# build toolchain. Never install packages from the unverified bootstrap pass.
RUN test -f /etc/apt/sources.list.d/ubuntu.sources \
    && sed -i 's|http://archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g; s|http://security.ubuntu.com/ubuntu|https://security.ubuntu.com/ubuntu|g' /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get -o Acquire::Retries=3 -o Acquire::https::Verify-Peer=false -o Acquire::https::Verify-Host=false update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && apt-get -o Acquire::Retries=3 update \
    && apt-get install -y --no-install-recommends \
    bash git gcc g++ gcc-multilib make cmake ninja-build binutils nasm \
    grub-common grub-pc-bin grub-efi-amd64-bin grub-efi-ia32-bin xorriso mtools dosfstools \
    python3 python3-pytest python3-cairosvg qemu-system-x86 ovmf file cpio busybox-static librsvg2-bin rsync xz-utils gzip bzip2 zstd \
    ffmpeg imagemagick unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src
COPY docker/iso/entrypoint.sh /usr/local/bin/chimera-iso-builder
RUN chmod +x /usr/local/bin/chimera-iso-builder tools/build/create-bootable-iso.sh \
    boot/iso/build-iso.sh boot/iso/prepare-layout.sh boot/spitfire/build-spitfire.sh

ENTRYPOINT ["/usr/local/bin/chimera-iso-builder"]
