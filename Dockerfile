# -- Base image --
FROM python:3.8-slim as base

# Upgrade pip to its latest release to speed up dependencies installation
RUN pip install --upgrade pip

# -- Builder --
FROM base as builder

WORKDIR /build

COPY . /build/

RUN python setup.py install


# -- Core --
FROM base as core

COPY --from=builder /usr/local /usr/local

WORKDIR /app


# -- Development --
FROM core as development

# Copy all sources, not only runtime-required files
COPY . /app/

RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

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
