# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker-compose
COMPOSE_RUN          = $(COMPOSE) run --rm
COMPOSE_TEST_RUN     = $(COMPOSE_RUN)
COMPOSE_TEST_RUN_APP = $(COMPOSE_TEST_RUN) app
MKDOCS               = $(COMPOSE_RUN) --no-deps --publish "8000:8000" app mkdocs

# -- Elasticsearch
ES_PROTOCOL = http
ES_HOST     = localhost
ES_PORT     = 9200
ES_INDEX    = statements
ES_URL      = $(ES_PROTOCOL)://$(ES_HOST):$(ES_PORT)

# ==============================================================================
# RULES

default: help

.env:
	cp .env.dist .env

# -- Docker/compose
bootstrap: ## bootstrap the project for development
bootstrap: \
  .env \
  build \
  dev \
  es-index
.PHONY: bootstrap
build: ## build the app container
	@$(COMPOSE) build app
.PHONY: build

dev: ## perform editable install from mounted project sources
	DOCKER_USER=0 docker-compose run --rm app pip install -e ".[dev]"
.PHONY: dev

docker-hub:  ## Publish locally built image
docker-hub: build
	@$(COMPOSE) push
.PHONY: docker-hub

docs-build: ## build documentation site
	@$(MKDOCS) build
.PHONY: docs-build

docs-deploy: ## deploy documentation site
	@$(MKDOCS) gh-deploy
.PHONY: docs-deploy

docs-serve: ## run mkdocs live server
	@$(MKDOCS) serve --dev-addr 0.0.0.0:8000
.PHONY: docs-serve

down: ## stop and remove backend containers
	@$(COMPOSE) down
.PHONY: down

es-index:  ## create elasticsearch index and sample documents
es-index: run-es
	@echo "Creating $(ES_INDEX) index"
	bin/es index $(ES_INDEX)
.PHONY: es-index

# Nota bene: Black should come after isort just in case they don't agree...
lint: ## lint back-end python sources
lint: \
  lint-isort \
  lint-black \
  lint-flake8 \
  lint-pylint \
  lint-bandit
.PHONY: lint

lint-black: ## lint back-end python sources with black
	@echo 'lint:black started…'
	@$(COMPOSE_TEST_RUN_APP) black src/ralph tests
.PHONY: lint-black

lint-flake8: ## lint back-end python sources with flake8
	@echo 'lint:flake8 started…'
	@$(COMPOSE_TEST_RUN_APP) flake8
.PHONY: lint-flake8

lint-isort: ## automatically re-arrange python imports in back-end code base
	@echo 'lint:isort started…'
	@$(COMPOSE_TEST_RUN_APP) isort --atomic .
.PHONY: lint-isort

lint-pylint: ## lint back-end python sources with pylint
	@echo 'lint:pylint started…'
	@$(COMPOSE_TEST_RUN_APP) pylint src/ralph tests
.PHONY: lint-pylint

lint-bandit: ## lint back-end python sources with bandit
	@echo 'lint:bandit started…'
	@$(COMPOSE_TEST_RUN_APP) bandit -qr src/ralph
.PHONY: lint-bandit

logs: ## display app logs (follow mode)
	@$(COMPOSE) logs -f app
.PHONY: logs

run: ## alias for run-es
run: \
	run-es
.PHONY: run

run-all: ## start all supported local backends
run-all: \
	run-es \
	run-swift
.PHONY: run-all

run-es: ## start elasticsearch backend
	@$(COMPOSE) up -d elasticsearch
	@echo "Waiting for elasticsearch to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://elasticsearch:9200 -timeout 60s
.PHONY: run-es

run-swift: ## start swift backend
	@$(COMPOSE) up -d swift
	@echo "Waiting for swift to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://swift:8080 -wait tcp://swift:35357 -timeout 60s
.PHONY: run-swift

status: ## an alias for "docker-compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stops backend servers
	@$(COMPOSE) stop
.PHONY: stop

test: ## run back-end tests
test: run-es
	bin/pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
