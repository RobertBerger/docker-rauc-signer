FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    git \
    libcurl4-openssl-dev \
    libdbus-1-dev \
    libengine-pkcs11-openssl \
    libglib2.0-dev \
    libjson-glib-dev \
    libnl-genl-3-dev \
    libssl-dev \
    meson \
    ninja-build \
    opensc \
    pcscd \
    pkg-config \
    python3 \
    python3-flask \
    squashfs-tools \
    yubikey-manager \
    && rm -rf /var/lib/apt/lists/*

# Build and install RAUC v1.15.2 to match meta-rauc 1.15.2
RUN git clone --depth 1 --branch v1.15.2 https://github.com/rauc/rauc /tmp/rauc && \
    cd /tmp/rauc && \
    meson setup build -Dservice=false -Dstreaming=false -Dgpt=disabled && \
    ninja -C build && \
    ninja -C build install && \
    ldconfig && \
    rm -rf /tmp/rauc

COPY signer_service.py /app/signer_service.py
WORKDIR /app

EXPOSE 9998
CMD ["sh", "-c", "rm -rf /run/pcscd/* && pcscd --foreground & sleep 1 && python3 /app/signer_service.py"]
