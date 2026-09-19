FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive CHIMERA_GUI=1
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates git gcc g++ make cmake ninja-build python3 python3-pip python3-venv nodejs npm openjdk-21-jdk-headless rustc cargo perl pciutils usbutils dmidecode iproute2 procps systemd systemd-sysv && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app
RUN chmod +x /app/docker/entrypoint.sh /app/hardware/host_scanner.py /app/desktop/aurora/gui_server.py && useradd -m -u 10001 appuser && chown -R appuser:appuser /app
EXPOSE 8000 8080
ENTRYPOINT ["/app/docker/entrypoint.sh"]
