start:
	if [ -n "${ENV}" ]; then \
		.venv/bin/dotenv --file ${ENV} run -- .venv/bin/python src/main.py; \
	else \
		.venv/bin/dotenv --file .env.dev run -- .venv/bin/python src/main.py; \
	fi

lint:
	poetry run black ./src
	poetry run isort ./src
	poetry run flake8 --config=.config/flake8 ./src

lint-fix:
	poetry run pysen run format && \
	poetry run pysen run lint

test-unit:
	poetry run pytest

install:
	export CRYPTOAUTHLIB_NOUSB=True; \
	poetry install