import json
import time
from threading import Thread
from concurrent import futures

from awscrt import io, mqtt

import utils.config as Config
import utils.logger as Logger

config = Config.getConfig()
Logger.init()

logger = Logger.getLogger(__name__)

AWS_IOT_ENDPOINT = config.IotEndpoint
KEEP_ALIVE_SECS = 5
PING_TIMEOUT_MS = 1000
THING_NAME = "test-thing"

SUB_TOPIC_A = "sub/a"


class PublishThread(Thread):
    def __init__(self, mqtt_connection=None, publish_topic_name=None):
        self.connection = mqtt_connection
        self.publish_topic_name = publish_topic_name
        Thread.__init__(self)

    def run(self):
        while True:
            try:
                timestamp = int(time.time())
                logger.info(f"publish {self.name} {timestamp}")
                publish_future, _ = self.connection.publish(
                    topic=self.publish_topic_name,
                    payload=json.dumps({f"{self.native_id}": timestamp}),
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                )

                # publish_future.result(timeout=10)

                logger.info("publish done")

                time.sleep(1)
            except futures._base.TimeoutError as e:
                logger.info(f"futures timeout error: {e}", exc_info=True)
                # publish_future.cancel()
            except Exception as e:
                logger.info(f"publish error: {e}", exc_info=True)


def sub_callback(topic, payload, dup, qos, retain):
    logger.info("call sub_callback")
    logger.info(f"topic: {topic}, dup: {dup}, qos: {qos}, retain: {retain}")
    logger.info(f"payload: {payload.decode('utf-8')}")
    logger.info("end sub_callback")


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
        keep_alive_secs=KEEP_ALIVE_SECS,
        ping_timeout_ms=PING_TIMEOUT_MS,
    )

    connect_future = mqtt_connection.connect()
    connect_future.result()

    return mqtt_connection


def main():
    logger.info("start main thread")
    logger.info("start create mqtt connection")
    connection = createMQTTConnection(
        device_certificate_filepath="./data/device_certificate.pem",
        private_key_filepath="./data/private.key",
        ca_certificate_filepath="./data/ca_certificate.pem",
    )
    logger.info("end create mqtt connection")

    subTopic1Publisher = PublishThread(connection, SUB_TOPIC_A)
    subTopic1Publisher.daemon = True
    subTopic1Publisher.name = SUB_TOPIC_A
    subTopic1Publisher.start()

    connection.subscribe(
        topic=SUB_TOPIC_A, qos=mqtt.QoS.AT_LEAST_ONCE, callback=sub_callback
    )

    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
