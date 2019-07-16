# include some environment variables
include env

# use the name of the current directory as the docker image tag
DOCKERFILE ?= Dockerfile
DOCKER ?= docker
DOCKER_TAG ?= $(shell echo ${PWD} | rev | cut -d/ -f1 | rev)
DOCKER_IMAGE = ${DOCKER_USERNAME}/${DOCKER_REPO}:${DOCKER_TAG}
.DEFAULT_GOAL := help

.PHONY: help
help:  ## Display help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | cut -d: -f2- | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

.PHONY: login
login:  ## Login to Docker
	$(DOCKER) login

.PHONY: build
build:  ## Build the Docker image
	$(DOCKER) build \
		-t ${DOCKER_IMAGE} \
		-f ${DOCKERFILE} \
		.

.PHONY: push
push: login  ## Push the Docker image
	$(DOCKER) push ${DOCKER_IMAGE}:latest

.PHONY: run
run:  ## Run the Docker container
	$(DOCKER) run \
		--mount type=bind,source="$(shell pwd)",target=$(DOCKER_WORKDIR) \
		-e ZILLOW_WSID=${ZILLOW_WSID} \
		-ti \
		--rm \
		${DOCKER_IMAGE} \
		python ${SCRIPT}

.PHONY: atlanta_heatmap
atlanta_heatmap:  ## Generate a heatmap of Atlanta housing prices
	$(MAKE) SCRIPT=atlanta_heatmap.py run

.PHONY: price_by_state
price_by_state:  ## Generate a map of price by state
	$(MAKE) SCRIPT=price_by_state.py run

.PHONY: jup
jup:  ## Run a Jupyter notebook inside the container
	$(DOCKER) run \
		--mount type=bind,source="$(shell pwd)",target=$(DOCKER_WORKDIR) \
		-p ${JUPYTER_PORT}:${JUPYTER_PORT} \
		-e ZILLOW_WSID=${ZILLOW_WSID} \
		-ti \
		--rm \
		${DOCKER_IMAGE} \
		jupyter-lab --allow-root --ip=0.0.0.0 --port=${JUPYTER_PORT} --no-browser 2>&1 | tee jupyter-log.txt
	@rm -f jupyter-log.txt
