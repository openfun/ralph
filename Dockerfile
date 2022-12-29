# -- Base image --
FROM python:3.11-slim as base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# Upgrade system packages to install security updates
RUN apt-get update && \
    apt-get -y upgrade && \
    rm -rf /var/lib/apt/lists/*


# -- Builder --
FROM base as builder

WORKDIR /build

COPY . /build/

RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libc6-dev \
        libffi-dev \
        python-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install .[backend-clickhouse,backend-es,backend-ldp,backend-mongo,backend-swift,backend-ws,cli,lrs]


# -- Core --
FROM base as core

RUN apt-get update && \
    apt-get install -y \
        curl \
        jq \
        wget && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

WORKDIR /app


# -- Development --
FROM core as development

# Copy all sources, not only runtime-required files
COPY . /app/

# Only the M1 Mac images need these packages installed
ARG TARGETPLATFORM
RUN if [ "$TARGETPLATFORM" = "linux/arm64" ]; \
    then apt-get update && \
        apt-get install -y \
            build-essential \
            gcc \
            python-dev && \
        rm -rf /var/lib/apt/lists/*; \
    fi;

# Uninstall ralph and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y ralph-malph
RUN pip install -e .[dev]

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}


# -- Production --
FROM core as production

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

CMD ["ralph"]
