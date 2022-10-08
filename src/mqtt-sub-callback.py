import utils.config as Config
from awscrt import io, mqtt

config = Config.getConfig()

AWS_IOT_ENDPOINT = config.IotEndpoint
THING_NAME = "db2bca16-2f32-47d7-8804-57686a0cd6aa"
MQTT_KEEP_ALIVE_TIME_MILLS = 200


def createMQTTConnection(
    device_certificate_filepath: str,
    private_key_filepath: str,
    ca_certificate_filepath: str,
    client_id: str,
):
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    tls_ctx_options = io.TlsContextOptions.create_client_with_mtls_from_path(
        device_certificate_filepath, private_key_filepath
    )
    tls_ctx_options.override_default_trust_store_from_path(
        None, ca_certificate_filepath
    )
    tls_ctx = io.ClientTlsContext(tls_ctx_options)

    mqtt_client = mqtt.Client(client_bootstrap, tls_ctx)
    mqtt_connection = mqtt.Connection(
        client=mqtt_client,
        client_id=THING_NAME,
        host_name=AWS_IOT_ENDPOINT,
        port=8883,
        clean_session=False,
        keep_alive_secs=MQTT_KEEP_ALIVE_TIME_MILLS,
    )

    connect_future = mqtt_connection.connect()
    connect_future.result()

    return mqtt_connection


def main():
    createMQTTConnection(
        device_certificate_filepath="./data/device_certificate.pem",
        private_key_filepath="./data/private.key",
        ca_certificate_filepath="./data/ca_certificate.pem",
        client_id="",
    )


if __name__ == "__main__":
    # print(config.IotEndpoint)
    print(config.IotEndpoint)

    main()
