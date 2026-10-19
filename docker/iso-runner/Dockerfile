FROM debian:bookworm-slim
ARG DEBIAN_FRONTEND=noninteractive
ENV DEBIAN_FRONTEND=noninteractive \
    FIRMWARE=bios \
    MEMORY=2048 \
    CPUS=2 \
    QEMU_DISPLAY=vnc=:1

LABEL org.opencontainers.image.title="Chimera II OS ISO Runner Candidate" \
      org.opencontainers.image.description="QEMU wrapper for development ISO; not a production OS release"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates qemu-system-x86 ovmf \
    && rm -rf /var/lib/apt/lists/*

COPY dist/output.iso /opt/chimera-ii-os.iso
COPY docker/iso-runner/entrypoint.sh /usr/local/bin/chimera-iso-runner
RUN chmod 0755 /usr/local/bin/chimera-iso-runner

EXPOSE 5901
ENTRYPOINT ["/usr/local/bin/chimera-iso-runner"]
