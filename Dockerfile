# -- Base image --
FROM python:3.12.0-slim AS base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base AS builder

WORKDIR /build

COPY . /build/

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libc6-dev \
        libffi-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install .[full]


# -- Core --
FROM base AS core

RUN apt-get update && \
    apt-get install -y \
        curl \
        jq \
        wget && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

WORKDIR /app


# -- Development --
FROM core AS development

# Copy all sources, not only runtime-required files
COPY . /app/

# Only the M1 Mac images need these packages installed
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; \
    then apt-get update && \
        apt-get install -y \
            build-essential \
            gcc && \
        rm -rf /var/lib/apt/lists/*; \
    fi;

# Install git for documentation deployment
RUN apt-get update && \
    apt-get install -y \
        git && \
    rm -rf /var/lib/apt/lists/*;

# Uninstall ralph and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y ralph-malph
RUN pip install -e .[dev]

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}


# -- Production --
FROM core AS production

# Un-privileged user running the application
ARG DOCKER_USER=1000
USER ${DOCKER_USER}

CMD ["ralph"]
