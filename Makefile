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

create-cert:
	wget https://www.amazontrust.com/repository/AmazonRootCA1.pem
	mv ./AmazonRootCA1.pem ./data/ca_certificate.pem
	aws iot create-keys-and-certificate \
	    --set-as-active \
	    --certificate-pem-outfile ./data/device_certificate.pem \
	    --public-key-outfile ./data/public.key \
	    --private-key-outfile ./data/private.key

create-iot-policy:
	aws iot create-policy \
	create-policy \
	--policy-name test-policy \
	--policy-document <value>
                            