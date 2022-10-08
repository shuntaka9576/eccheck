import utils.config as Config

config = Config.getConfig()


def createMQTTConnection(
    device_certificate_filepath: str,
    private_key_filepath: str,
    ca_certificate_filepath: str,
    client_id: str,
):
    print("create")


def main():
    createMQTTConnection("", "", "", "")
    print("start")


if __name__ == "__main__":
    # print(config.IotEndpoint)
    print(config.IotEndpoint)

    main()
