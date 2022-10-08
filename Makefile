POLICY_NAME := "test-policy"

lint:
	poetry run black ./src
	poetry run isort ./src
	poetry run flake8 --config=.config/flake8 ./src

install:
	export CRYPTOAUTHLIB_NOUSB=True; \
	poetry install

clean:
	-aws iot detach-policy --policy-name $(POLICY_NAME) --target $(shell cat ./data/cert.json | jq -r ".certificateArn")
	-aws iot update-certificate --new-status INACTIVE --certificate-id $(shell cat ./data/cert.json | jq -r ".certificateId")
	-aws iot delete-certificate --certificate-id $(shell cat ./data/cert.json | jq -r ".certificateId")

create-cert: clean
	# IoT Coreとの接続に必要な証明書を作成
	wget https://www.amazontrust.com/repository/AmazonRootCA1.pem
	mv ./AmazonRootCA1.pem ./data/ca_certificate.pem
	aws iot create-keys-and-certificate \
	    --set-as-active \
	    --certificate-pem-outfile ./data/device_certificate.pem \
	    --public-key-outfile ./data/public.key \
	    --private-key-outfile ./data/private.key >./data/cert.json

# 証明書にポリシーをアタッチ
create-policy:
	aws iot create-policy \
	--policy-name test-policy \
	--policy-document file://iot-policy.json

attach-policy:
	aws iot attach-policy \
	--policy-name $(POLICY_NAME) \
	--target "$(shell cat ./data/cert.json | jq -r ".certificateArn")"
                            