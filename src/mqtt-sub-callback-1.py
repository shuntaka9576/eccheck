import utils.config as Config
import utils.logger as Logger
from awscrt import io, mqtt
from threading import Thread
import json
import time
from concurrent.futures import ThreadPoolExecutor

config = Config.getConfig()
Logger.init()

logger = Logger.getLogger(__name__)

AWS_IOT_ENDPOINT = config.IotEndpoint
# AWS IoTのサポートするkeep-alive 5 - 1200 s
KEEP_ALIVE_SECS = 5
# ms単位なので、KEEP_ALIVE_SECS * 1000 より短い必要がある
PING_TIMEOUT_MS = 1000
THING_NAME = "test-thing"

SUB_TOPIC_A = "sub/a"
SUB_TOPIC_B = "sub/b"


class PublishThread(Thread):
    def __init__(self, mqtt_connection=None, publish_topic_name=None):
        self.connection = mqtt_connection
        self.publish_topic_name = publish_topic_name
        Thread.__init__(self)

    def run(self):

        while True:
            timestamp = int(time.time())
            logger.info(f"publish {self.name} {timestamp}")
            self.connection.publish(
                topic=self.publish_topic_name,
                payload=json.dumps({f"{self.native_id}": timestamp}),
                qos=mqtt.QoS.AT_MOST_ONCE,
            )

            logger.info("publish done")

            time.sleep(1)


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


def sub_heavy_callback(topic, payload, dup, qos, retain):
    logger.info("call heavy func")
    logger.info(f"topic: {topic}, dup: {dup}, qos: {qos}, retain: {retain}")
    logger.info(f"payload: {payload.decode('utf-8')}")
    time.sleep(10)
    logger.info("end heavy func")


def sub_light_callback(topic, payload, dup, qos, retain):
    logger.info("call light func")
    logger.info(f"topic: {topic}, dup: {dup}, qos: {qos}, retain: {retain}")
    logger.info(f"payload: {payload.decode('utf-8')}")
    logger.info("end light func")


def main():
    logger.info("start main thread")
    logger.info("start create mqtt connection")
    connection = createMQTTConnection(
        device_certificate_filepath="./data/device_certificate.pem",
        private_key_filepath="./data/private.key",
        ca_certificate_filepath="./data/ca_certificate.pem",
    )
    logger.info("end create mqtt connection")

    MAX_WORKER = 3
    with ThreadPoolExecutor(
        max_workers=MAX_WORKER, thread_name_prefix="execSubCallbackThread"
    ) as executor:
        subTopic1Publisher = PublishThread(connection, SUB_TOPIC_A)
        subTopic1Publisher.daemon = True
        subTopic1Publisher.name = SUB_TOPIC_A
        subTopic1Publisher.start()

        subTopic2Publisher = PublishThread(connection, SUB_TOPIC_B)
        subTopic2Publisher.daemon = True
        subTopic2Publisher.name = SUB_TOPIC_B
        subTopic2Publisher.start()

        def sub_a_callbcak(topic, payload, dup, qos, retain):
            executor.submit(sub_heavy_callback, topic, payload, dup, qos, retain)

        def sub_b_callbcak(topic, payload, dup, qos, retain):
            executor.submit(sub_light_callback, topic, payload, dup, qos, retain)

        connection.subscribe(
            topic=SUB_TOPIC_A, qos=mqtt.QoS.AT_LEAST_ONCE, callback=sub_a_callbcak
        )
        connection.subscribe(
            topic=SUB_TOPIC_B, qos=mqtt.QoS.AT_LEAST_ONCE, callback=sub_b_callbcak
        )

        while True:
            time.sleep(10)


if __name__ == "__main__":
    main()
