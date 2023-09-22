DIRS := aws_generated_data

format:
	poetry run black $(DIRS)
	poetry run isort $(DIRS)
.PHONY: format

build-test-image:
	docker build -t agd-test .

pr-check: build-test-image
	docker run --rm agd-test make test
.PHONY: pr-check

test:
	poetry run pytest -vv
	poetry run flake8 $(DIRS)
	poetry run mypy $(DIRS)
	poetry run black --check $(DIRS)
	poetry run isort --check-only $(DIRS)
.PHONY: test

ci-run: build-test-image
	docker run --rm \
		-v $(PWD)/output:/output \
		-e AGD_RDS_EOL_ENGINES='$(AGD_RDS_EOL_ENGINES)' \
		-e AGD_RDS_EOL_OUTPUT=/output/rds_eol.yaml \
		agd-test make run

	# Commit changes if any
	@status=$$(git status --porcelain --untracked-files=no); \
	if [ ! -z "$${status}" ]; \
	then \
		echo git add output/*; \
		echo git commit -m "Update data"; \
	fi
.PHONY: ci-run

.PHONY: run
run: run-rds-eol

run-rds-eol:
	poetry run agd rds-eol fetch
