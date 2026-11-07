# syntax=docker/dockerfile:1
FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG CHIMERA_ARCH=x86_64
ARG CHIMERA_FIRMWARE=uefi
ENV DEBIAN_FRONTEND=noninteractive \
    CHIMERA_ARCH=${CHIMERA_ARCH} \
    CHIMERA_FIRMWARE=${CHIMERA_FIRMWARE}

RUN if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then sed -i -E '/^Components:/ { /(^|[[:space:]])universe([[:space:]]|$)/! s/$/ universe/; }' /etc/apt/sources.list.d/ubuntu.sources; fi \
    && apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc g++ make cmake ninja-build binutils nasm \
    grub-common grub-pc-bin grub-efi-amd64-bin grub-efi-ia32-bin xorriso mtools dosfstools \
    python3 python3-pytest python3-cairosvg qemu-system-x86 qemu-user-static ovmf file cpio busybox-static librsvg2-bin rsync xz-utils gzip bzip2 zstd \
    gcc-13-i686-linux-gnu gcc-13-arm-linux-gnueabi gcc-13-aarch64-linux-gnu gcc-13-arm-linux-gnueabihf gcc-13-riscv64-linux-gnu gcc-13-powerpc64le-linux-gnu gcc-13-s390x-linux-gnu \
    libc6-dev-i386-cross libc6-dev-armel-cross libc6-dev-arm64-cross libc6-dev-armhf-cross libc6-dev-riscv64-cross libc6-dev-ppc64el-cross libc6-dev-s390x-cross \
    linux-libc-dev-i386-cross linux-libc-dev-armel-cross linux-libc-dev-arm64-cross linux-libc-dev-armhf-cross linux-libc-dev-riscv64-cross linux-libc-dev-ppc64el-cross linux-libc-dev-s390x-cross \
    ffmpeg imagemagick unzip \
    && for target in i686-linux-gnu arm-linux-gnueabi aarch64-linux-gnu arm-linux-gnueabihf riscv64-linux-gnu powerpc64le-linux-gnu s390x-linux-gnu; do \
         test -x "/usr/bin/${target}-gcc-13" || { echo "Missing versioned cross compiler: ${target}" >&2; exit 2; }; \
         ln -sf "/usr/bin/${target}-gcc-13" "/usr/local/bin/${target}-gcc"; \
       done \
    && for qemu in qemu-i386-static qemu-arm-static qemu-aarch64-static qemu-riscv64-static qemu-ppc64le-static qemu-s390x-static; do command -v "$qemu" >/dev/null || { echo "Missing QEMU user emulator: $qemu" >&2; exit 2; }; done \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src
COPY docker/iso/entrypoint.sh /usr/local/bin/chimera-iso-builder
RUN chmod +x /usr/local/bin/chimera-iso-builder tools/build/create-bootable-iso.sh \
    boot/iso/build-iso.sh boot/iso/prepare-layout.sh boot/spitfire/build-spitfire.sh

ENTRYPOINT ["/usr/local/bin/chimera-iso-builder"]
