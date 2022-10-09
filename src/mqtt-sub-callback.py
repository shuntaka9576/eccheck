import utils.config as Config
import utils.logger as Logger
from awscrt import io, mqtt
from threading import Thread
import json
import time

config = Config.getConfig()
Logger.init()

logger = Logger.getLogger(__name__)

AWS_IOT_ENDPOINT = config.IotEndpoint
MQTT_KEEP_ALIVE_TIME_MILLS = 200
PUBLISH_TOPIC_NAME = "sample/test"
THING_NAME = "test-thing"


def createMQTTConnection(
    device_certificate_filepath: str,
    private_key_filepath: str,
    ca_certificate_filepath: str,
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


class PublishThread(Thread):
    def __init__(self, mqtt_connection=None):
        self.connection = mqtt_connection

        Thread.__init__(self)
        self.setDaemon(True)
        self.start()

    def run(self):

        while True:
            self.connection.publish(
                topic=PUBLISH_TOPIC_NAME,
                payload=json.dumps({"Aスレッド": "dayo"}),
                qos=mqtt.QoS.AT_LEAST_ONCE,
            )

            time.sleep(5)


def main():
    logger.info("start")
    con = createMQTTConnection(
        device_certificate_filepath="./data/device_certificate.pem",
        private_key_filepath="./data/private.key",
        ca_certificate_filepath="./data/ca_certificate.pem",
    )

    # PublishThread(con)

    # con.subscribe(
    #     topic="callback1",
    #     qos=mqtt.QoS.AT_LEAST_ONCE,
    #     callback=callback,
    # )


if __name__ == "__main__":
    main()
