# -- Base image --
FROM python:3.9-slim as base

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
    apt-get install -y gcc libc6-dev && \
    rm -rf /var/lib/apt/lists/*

RUN python setup.py install


# -- Core --
FROM base as core

RUN apt-get update && \
    apt-get install -y jq && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local /usr/local

WORKDIR /app


# -- Development --
FROM core as development

# Copy all sources, not only runtime-required files
COPY . /app/

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
