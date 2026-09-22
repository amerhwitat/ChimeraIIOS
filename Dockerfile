# syntax=docker/dockerfile:1.7

ARG UBUNTU_VERSION=24.04

FROM ubuntu:${UBUNTU_VERSION} AS builder
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates git gcc g++ make cmake ninja-build \
    python3 python3-pip python3-venv nodejs npm openjdk-21-jdk-headless \
    rustc cargo perl pciutils usbutils dmidecode iproute2 procps \
    systemd systemd-sysv dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu 24.04 uses PEP 668. Keep Python application dependencies in an
# isolated virtual environment and prefer prebuilt wheels for architecture safety.
ENV VIRTUAL_ENV=/opt/chimera-venv
RUN python3 -m venv "$VIRTUAL_ENV" && \
    "$VIRTUAL_ENV/bin/python" -m pip install --upgrade --no-cache-dir \
      --retries 5 --timeout 120 pip setuptools wheel
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN set -eux; \
    pip_install() { \
      echo "[Chimera] Installing Python group: $*"; \
      "$VIRTUAL_ENV/bin/python" -m pip install --no-cache-dir \
        --retries 5 --timeout 120 --prefer-binary "$@"; \
    }; \
    pip_install requests beautifulsoup4 lxml; \
    pip_install web3 eth-keys eth-typing cryptography pycryptodome; \
    pip_install flask fastapi uvicorn sqlalchemy alembic; \
    pip_install psycopg2-binary mysql-connector-python redis celery; \
    pip_install pytest pytest-cov sphinx pylint black flake8 mypy; \
    pip_install jupyter ipython notebook; \
    pip_install numpy scipy pandas matplotlib seaborn scikit-learn; \
    pip_install nltk spacy gensim pillow opencv-python selenium; \
    if ! "$VIRTUAL_ENV/bin/python" -m pip install --no-cache-dir --retries 5 --timeout 120 --prefer-binary xgboost; then \
      echo "[Chimera][WARN] xgboost wheel unavailable; continuing"; \
    fi; \
    if ! "$VIRTUAL_ENV/bin/python" -m pip install --no-cache-dir --retries 5 --timeout 120 --prefer-binary lightgbm; then \
      echo "[Chimera][WARN] lightgbm wheel unavailable; continuing"; \
    fi; \
    "$VIRTUAL_ENV/bin/python" -m pip check; \
    "$VIRTUAL_ENV/bin/python" -m pip cache purge || true

WORKDIR /src
COPY . /src

# Normalize shell scripts with a POSIX-safe CR detector. Do not use Bash-only
# ANSI-C quoting ($'\\r') here because Docker RUN defaults to /bin/sh.
RUN set -eux; \
    find /src -type f \\( \
      -name '*.sh' -o -name '*.bash' -o -name '*.command' -o \
      -name '*.ps1' -o -name 'Dockerfile*' -o \
      -name '*.yml' -o -name '*.yaml' \
    \\) -print0 | xargs -0 -r dos2unix; \
    grep -RIlZ --exclude-dir=.git '^#!' /src | xargs -0 -r dos2unix; \
    # Explicitly strip any remaining CR at end-of-line from shell scripts. \
    find /src -type f \\( -name '*.sh' -o -name '*.bash' -o -name '*.command' \\) -print0 | \
      xargs -0 -r sed -i 's/\\r$//'; \
    # POSIX-safe verification: grep for a literal carriage-return byte. \
    CR=$(printf '\\r'); \
    if find /src -type f \\( -name '*.sh' -o -name '*.bash' -o -name '*.command' \\) -print0 | \
         xargs -0 -r grep -Il "$CR" | grep -q .; then \
      echo 'CRLF remains in a shell script after normalization' >&2; \
      find /src -type f \\( -name '*.sh' -o -name '*.bash' -o -name '*.command' \\) -print0 | \
        xargs -0 -r grep -Il "$CR" || true; \
      exit 1; \
    fi

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

# Final runtime safety pass for scripts copied from the source tree.
RUN set -eux; \
    find /app -type f \( -name '*.sh' -o -name '*.bash' -o -name '*.command' \) -print0 | \
      xargs -0 -r sed -i 's/\r$//'; \
    sed -i '1s/\r$//' /app/docker/entrypoint.sh; \
    chmod +x /app/docker/entrypoint.sh /app/hardware/host_scanner.py /app/desktop/aurora/gui_server.py; \
    useradd -m -u 10001 appuser; \
    chown -R appuser:appuser /app; \
    chown root:root /usr/local/bin/chimera_server /usr/local/bin/chimera_kernel; \
    chmod 0755 /usr/local/bin/chimera_server /usr/local/bin/chimera_kernel; \
    /bin/bash -n /app/docker/entrypoint.sh

EXPOSE 8000 8080
ENTRYPOINT ["/app/docker/entrypoint.sh"]
