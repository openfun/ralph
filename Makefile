# -- General
SHELL := /bin/bash

# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker compose
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

# -- Arnold
ARNOLD              = ARNOLD_IMAGE_TAG=master bin/arnold
ARNOLD_APP          = ralph
ARNOLD_APP_VARS     = group_vars/customer/$(ARNOLD_CUSTOMER)/$(ARNOLD_ENVIRONMENT)/main.yml
ARNOLD_CUSTOMER    ?= ralph
ARNOLD_ENVIRONMENT ?= development

# -- RALPH
RALPH_IMAGE_NAME         ?= ralph
RALPH_IMAGE_TAG          ?= development
RALPH_IMAGE_BUILD_TARGET ?= development
RALPH_LRS_AUTH_USER_NAME  = ralph
RALPH_LRS_AUTH_USER_PWD   = secret
RALPH_LRS_AUTH_USER_SCOPE = ralph_scope
RALPH_LRS_AUTH_USER_AGENT_MBOX = mailto:ralph@example.com

# -- K3D
K3D_CLUSTER_NAME              ?= ralph
K3D_REGISTRY_HOST             ?= registry.127.0.0.1.nip.io
K3D_REGISTRY_NAME             ?= k3d-registry.127.0.0.1.nip.io
K3D_REGISTRY_PORT             ?= 5000
K3D_REGISTRY_RALPH_IMAGE_NAME  = $(K3D_REGISTRY_NAME):$(K3D_REGISTRY_PORT)/$(ARNOLD_ENVIRONMENT)-$(ARNOLD_APP)/$(RALPH_IMAGE_NAME)
K8S_NAMESPACE                  = $(ARNOLD_ENVIRONMENT)-$(ARNOLD_CUSTOMER)


# ==============================================================================
# RULES

default: help

bin/arnold:
	curl -Lo "bin/arnold" "https://raw.githubusercontent.com/openfun/arnold/master/bin/arnold"
	chmod +x bin/arnold

bin/init-cluster:
	curl -Lo "bin/init-cluster" "https://raw.githubusercontent.com/openfun/arnold/master/bin/init-cluster"
	chmod +x bin/init-cluster

.env:
	cp .env.dist .env

.ralph/auth.json:
	@$(COMPOSE_RUN) app ralph \
		auth \
		-u $(RALPH_LRS_AUTH_USER_NAME) \
		-p $(RALPH_LRS_AUTH_USER_PWD) \
		-s $(RALPH_LRS_AUTH_USER_SCOPE) \
		-M $(RALPH_LRS_AUTH_USER_AGENT_MBOX)
		-w


# -- Docker/compose
arnold-bootstrap: ## bootstrap arnold's project
arnold-bootstrap: \
	bin/arnold
	source .k3d-cluster.env.sh && \
	  $(ARNOLD) -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) setup && \
	  $(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a $(ARNOLD_APP) create_app_vaults && \
	  $(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a elasticsearch create_app_vaults && \
	  $(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -- vault -a $(ARNOLD_APP) decrypt
	sed -i 's/^# RALPH_BACKENDS__DATA__ES/RALPH_BACKENDS__DATA__ES/g' group_vars/customer/$(ARNOLD_CUSTOMER)/$(ARNOLD_ENVIRONMENT)/secrets/$(ARNOLD_APP).vault.yml
	source .k3d-cluster.env.sh && \
	  $(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -- vault -a $(ARNOLD_APP) encrypt
	echo "skip_verification: True" > $(ARNOLD_APP_VARS)
	echo "apps:" >> $(ARNOLD_APP_VARS)
	echo "  - name: elasticsearch" >> $(ARNOLD_APP_VARS)
	echo "  - name: $(ARNOLD_APP)" >> $(ARNOLD_APP_VARS)
	echo "ralph_image_name: $(K3D_REGISTRY_RALPH_IMAGE_NAME)" >> $(ARNOLD_APP_VARS)
	echo "ralph_image_tag: $(RALPH_IMAGE_TAG)" >> $(ARNOLD_APP_VARS)
	echo "ralph_app_replicas: 1" >> $(ARNOLD_APP_VARS)
	echo "ralph_cronjobs:" >> $(ARNOLD_APP_VARS)
	echo "  - name: $(ARNOLD_ENVIRONMENT)-test" >> $(ARNOLD_APP_VARS)
	echo "    schedule: '* * * * *'" >> $(ARNOLD_APP_VARS)
	echo "    command: ['date']" >> $(ARNOLD_APP_VARS)
.PHONY: arnold-bootstrap

arnold-deploy: ## deploy Ralph to k3d using Arnold
	source .k3d-cluster.env.sh && \
		$(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a $(ARNOLD_APP) deploy && \
		$(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a $(ARNOLD_APP) switch
.PHONY: arnold-deploy

arnold-init: ## initialize Ralph k3d project using Arnold
	source .k3d-cluster.env.sh && \
		$(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a elasticsearch,ralph init && \
  	$(ARNOLD) -d -c $(ARNOLD_CUSTOMER) -e $(ARNOLD_ENVIRONMENT) -a elasticsearch deploy && \
		kubectl -n $(K8S_NAMESPACE) wait --for=condition=ready pod --selector=type=es-node --timeout=120s && \
		kubectl -n $(K8S_NAMESPACE) exec svc/elasticsearch -- curl -s -X PUT "localhost:9200/statements?pretty"
.PHONY: arnold-init

bootstrap: ## bootstrap the project for development
bootstrap: \
  .env \
  build \
  dev \
  .ralph/auth.json \
  es-index
.PHONY: bootstrap

build: ## build the app container
build: .env
	RALPH_IMAGE_BUILD_TARGET=$(RALPH_IMAGE_BUILD_TARGET) \
	RALPH_IMAGE_NAME=$(RALPH_IMAGE_NAME) \
	RALPH_IMAGE_TAG=$(RALPH_IMAGE_TAG) \
	  $(COMPOSE) build app
.PHONY: build

dev: ## perform editable install from mounted project sources
	DOCKER_USER=0 docker compose run --rm app pip install -e ".[dev]"
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

es-index: ## create elasticsearch index
es-index: run-es
	@echo "Creating $(ES_INDEX) index..."
	curl -X PUT $(ES_URL)/$(ES_INDEX)
	@echo -e "\nConfiguring $(ES_INDEX) index..."
	curl -X PUT $(ES_URL)/$(ES_INDEX)/_settings -H 'Content-Type: application/json' -d '{"index": {"number_of_replicas": 0}}'
.PHONY: es-index

k3d-cluster: ## boot a k3d cluster for k8s-related development
k3d-cluster: \
	bin/init-cluster
	source .k3d-cluster.env.sh && \
		bin/init-cluster "$(K3D_CLUSTER_NAME)"
.PHONY: k3d-cluster

k3d-push: ## push build image to local k3d docker registry
k3d-push: build
	source .k3d-cluster.env.sh && \
		docker tag \
			$(RALPH_IMAGE_NAME):$(RALPH_IMAGE_TAG) \
			"$(K3D_REGISTRY_RALPH_IMAGE_NAME):$(RALPH_IMAGE_TAG)" && \
		docker push \
			"$(K3D_REGISTRY_RALPH_IMAGE_NAME):$(RALPH_IMAGE_TAG)"
.PHONY: k3d-push

k3d-stop: ## stop local k8s cluster
	source .k3d-cluster.env.sh && \
		k3d cluster stop "$(K3D_CLUSTER_NAME)"
.PHONY: k3d-stop

# Nota bene: Black should come after isort just in case they don't agree...
lint: ## lint back-end python sources
lint: \
  lint-isort \
  lint-black \
  lint-flake8 \
  lint-pylint \
  lint-bandit \
  lint-pydocstyle
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

lint-pydocstyle: ## lint Python docstrings with pydocstyle
	@echo 'lint:pydocstyle started…'
	@$(COMPOSE_TEST_RUN_APP) pydocstyle
.PHONY: lint-pydocstyle

lint-mypy: ## lint back-end python sources with mypy
	@echo 'lint:mypy started…'
	@$(COMPOSE_TEST_RUN_APP) mypy
.PHONY: lint-mypy

logs: ## display app logs (follow mode)
	@$(COMPOSE) logs -f app
.PHONY: logs

run: ## run LRS server with the runserver backends (development mode)
run: \
	run-databases
	@$(COMPOSE) up -d app
.PHONY: run

run-all: ## start all supported local backends
run-all: \
	run-databases \
	run-swift
.PHONY: run-all

run-clickhouse: ## start clickhouse backend
	@$(COMPOSE) up -d clickhouse
	@echo "Waiting for clickhouse to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://clickhouse:9000 -timeout 60s
.PHONY: run-clickhouse

run-databases: ## alias for running database services
run-databases: \
	run-es \
	run-mongo \
	run-clickhouse
.PHONY: run-databases

run-es: ## start elasticsearch backend
	@$(COMPOSE) up -d elasticsearch
	@echo "Waiting for elasticsearch to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://elasticsearch:9200 -timeout 60s
.PHONY: run-es

run-mongo: ## start mongodb backend
	@$(COMPOSE) up -d mongo
	@echo "Waiting for mongo to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://mongo:27017 -timeout 60s
.PHONY: run-mongo

run-swift: ## start swift backend
	@$(COMPOSE) up -d swift
	@echo "Waiting for swift to be up and running..."
	@$(COMPOSE_RUN) dockerize -wait tcp://swift:8080 -wait tcp://swift:35357 -timeout 60s
.PHONY: run-swift

status: ## an alias for "docker compose ps"
	@$(COMPOSE) ps
.PHONY: status

stop: ## stops backend servers
	@$(COMPOSE) stop
.PHONY: stop

test: ## run back-end tests
test: run
	bin/pytest
.PHONY: test

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help
