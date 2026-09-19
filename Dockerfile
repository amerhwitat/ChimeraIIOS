# syntax=docker/dockerfile:1.7

ARG UBUNTU_VERSION=24.04

FROM ubuntu:${UBUNTU_VERSION} AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc g++ make cmake ninja-build \
    python3 python3-pip python3-venv nodejs npm openjdk-21-jdk-headless \
    rustc cargo perl pciutils usbutils dmidecode iproute2 procps \
    systemd systemd-sysv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . /src

RUN cmake -S /src -B /build -G Ninja \
      -DCHIMERA_ENABLE_EXPERIMENTAL=ON \
      -DCHIMERA_ENABLE_CVEL=ON \
      -DCHIMERA_BUILD_STARTUP_RUNTIME=ON \
      -DCHIMERA_ENABLE_X86_ASM=ON \
    && cmake --build /build --parallel

FROM ubuntu:${UBUNTU_VERSION} AS runtime
ENV DEBIAN_FRONTEND=noninteractive CHIMERA_GUI=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates python3 pciutils usbutils dmidecode iproute2 procps \
    systemd systemd-sysv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /src /app
COPY --from=builder /build/chimera_server /usr/local/bin/chimera_server
COPY --from=builder /build/chimera_kernel /usr/local/bin/chimera_kernel
RUN chmod +x /app/docker/entrypoint.sh /app/hardware/host_scanner.py /app/desktop/aurora/gui_server.py \
    && useradd -m -u 10001 appuser \
    && chown -R appuser:appuser /app \
    && chown root:root /usr/local/bin/chimera_server /usr/local/bin/chimera_kernel \
    && chmod 0755 /usr/local/bin/chimera_server /usr/local/bin/chimera_kernel

EXPOSE 8000 8080
ENTRYPOINT ["/app/docker/entrypoint.sh"]
