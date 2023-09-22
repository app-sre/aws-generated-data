DIRS := aws_generated_data
POETRY_RUN := poetry run --no-ansi --no-interaction

format:
	$(POETRY_RUN) black $(DIRS)
	$(POETRY_RUN) isort $(DIRS)
.PHONY: format

build-test-image:
	docker build -t agd-test .

pr-check: build-test-image
	docker run --rm agd-test make test
.PHONY: pr-check

test:
	$(POETRY_RUN) pytest -vv
	$(POETRY_RUN) flake8 $(DIRS)
	$(POETRY_RUN) mypy $(DIRS)
	$(POETRY_RUN) black --check $(DIRS)
	$(POETRY_RUN) isort --check-only $(DIRS)
.PHONY: test

ci-run: build-test-image
	# Allow docker to write to output directory
	chmod a+w output/*

	# Run agd rds-eol
	docker run --rm \
		-v '$(PWD)/output':/output \
		-e AGD_RDS_EOL_ENGINES='$(AGD_RDS_EOL_ENGINES)' \
		-e AGD_RDS_EOL_OUTPUT=/output/rds_eol.yaml \
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
run: run-rds-eol

run-rds-eol:
	$(POETRY_RUN) agd rds-eol fetch
