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

# Un-privileged user running the application
USER ${DOCKER_USER:-1000}

WORKDIR /app

CMD python -m ralph

# -- Development --
FROM core as development

# Switch back to the root user to install development dependencies
USER root:root

# Copy all sources, not only runtime-required files
COPY . /app/

RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

# Uninstall ralph and re-install it in editable mode along with development
# dependencies
RUN pip uninstall -y ralph-malph
RUN pip install -e .[dev]

# Restore the un-privileged user running the application
USER ${DOCKER_USER:-1000}


# -- Production --
FROM core as production
