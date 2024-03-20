DIRS := aws_generated_data
POETRY_RUN := poetry run --no-ansi --no-interaction

format:
	$(POETRY_RUN) ruff check
	$(POETRY_RUN) ruff format
.PHONY: format

build-test-image:
	docker build -t agd-test .

pr-check: build-test-image
	docker run --rm agd-test make test
.PHONY: pr-check

test:
	$(POETRY_RUN) ruff check --no-fix
	$(POETRY_RUN) ruff format --check
	$(POETRY_RUN) pytest -vv
	$(POETRY_RUN) mypy $(DIRS)
.PHONY: test

ci-run: build-test-image
	# Allow docker to write to output directory
	chmod a+w output/*

	# Run agd rds-eol
	docker run --rm \
		-v '$(PWD)/output':/output \
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
.PHONY: ci-run

.PHONY: run
run: run-rds-eol run-msk-eol

run-rds-eol:
	$(POETRY_RUN) agd rds-eol fetch

run-msk-eol:
	$(POETRY_RUN) agd msk-eol fetch
