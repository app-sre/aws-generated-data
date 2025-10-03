CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: format
format:
	uv run ruff check
	uv run ruff format

.PHONY: test
test:
	uv run ruff check --no-fix
	uv run ruff format --check
	uv run pytest -vv
	uv run mypy

.PHONY: build-image
build-image:
	$(CONTAINER_ENGINE) build -t agd-test --target prod .

.PHONY: ci-run
ci-run: build-image
	# Allow docker to write to output directory
	chmod a+w output/*

	# Run agd rds-eol
	$(CONTAINER_ENGINE) run --rm \
		-v '$(PWD)/output':/output:z \
		-e AGD_RDS_EOL_ENGINES='$(AGD_RDS_EOL_ENGINES)' \
		-e AGD_RDS_EOL_OUTPUT='/output/$(AGD_RDS_EOL_OUTPUT)' \
		-e AGD_MSK_RELEASE_CALENDAR_URL='$(AGD_MSK_RELEASE_CALENDAR_URL)' \
		-e AGD_MSK_EOL_OUTPUT='/output/$(AGD_MSK_EOL_OUTPUT)' \
		agd-test make run

	# Commit changes if any
	@status=$$(git status --porcelain --untracked-files=no); \
	if [ ! -z "$${status}" ]; \
	then \
		git add output/*; \
		git commit -m "Update data"; \
	fi

.PHONY: run
run: run-rds-eol run-msk-eol

run-rds-eol:
	uv run agd rds-eol fetch

run-msk-eol:
	uv run agd msk-eol fetch
