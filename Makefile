# -- Docker
# Get the current user ID to use for docker run and docker exec commands
DOCKER_UID           = $(shell id -u)
DOCKER_GID           = $(shell id -g)
DOCKER_USER          = $(DOCKER_UID):$(DOCKER_GID)
COMPOSE              = DOCKER_USER=$(DOCKER_USER) docker-compose
COMPOSE_RUN          = $(COMPOSE) run --rm
COMPOSE_EXEC         = $(COMPOSE) exec

# ==============================================================================
# RULES

default: help

# -- Docker/compose
build: ## build the app container
	@$(COMPOSE) build ralph
.PHONY: build

logs: ## display app logs (follow mode)
	@$(COMPOSE) logs -f ralph
.PHONY: logs

status: ## an alias for "docker-compose ps"
	@$(COMPOSE) ps
.PHONY: status

# -- Misc
help:
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

