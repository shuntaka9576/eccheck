import threading
import json
import time
from enum import Enum

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
HEALTH_CHECK_TOPIC_NAME = "sub/a"

TIME_OUT_SEC = 3


class HealthCheckStatus(Enum):
    NOT_INIT = "NOT_INIT"
    CONNECTED = "CONNECT"
    DISCONNECT = "DISCONNECT"


class HealthCheckTopic:
    def __init__(self, connection, thing_name: str):
        self.mqtt_connection = connection
        self.thing_name = thing_name

    def publish(self, data):
        future, packet_id = self.mqtt_connection.publish(
            topic=HEALTH_CHECK_TOPIC_NAME,
            payload=json.dumps(data),
            qos=mqtt.QoS.AT_MOST_ONCE,
        )

        return future, packet_id

    def subscribe(self, callback=None):
        self.mqtt_connection.subscribe(
            # publishしたことを確認するために利用、publishとtopicが同じ
            topic=HEALTH_CHECK_TOPIC_NAME,
            qos=mqtt.QoS.AT_MOST_ONCE,
            callback=callback,
        )


class HealthCheckUseCase:
    def __init__(self, mqtt_connection, thing_name) -> None:
        self.subscribe_notify_timestamp = None
        self.__health_check_topic = HealthCheckTopic(mqtt_connection, thing_name)

    def set_timestamp_for_subscriber(self, topic, payload, dup, qos, retain):
        payload_obj = json.loads(payload.decode("utf-8"))
        timestamp = payload_obj.get("timestamp")
        if timestamp is not None:
            self.subscribe_notify_timestamp = timestamp

    def get_status(
        self,
        time_out_sec: int,
    ):
        try:
            self.subscribe_notify_timestamp = None

            timestamp = int(time.time())

            future = self.__health_check_topic.publish(
                {"timestamp": timestamp},
            )

            retry_count = 0


            # time_out_secに指定した秒間ヘルスチェックトピックからメッセージが来ていないかを確認する
            while True:
                # ヘルスチェックトピックへパブリッシュした値とサブスクライブで到着した値が一致すれば接続中と判定
                if timestamp == self.subscribe_notify_timestamp:
                    return HealthCheckStatus.CONNECTED

                retry_count = retry_count + 1
                if retry_count == time_out_sec:
                    logger.info(
                        f"health check timeout: "
                        f"timestamp: {timestamp}, "
                        f"subscribe_notify_timestamp: {self.subscribe_notify_timestamp}"
                    )
                    future.cancel()

                    return HealthCheckStatus.DISCONNECT

                time.sleep(1)

        except Exception as e:
            return HealthCheckStatus.DISCONNECT


class HealthCheckThread(threading.Thread):
    def __init__(
        self,
        mqtt_connection: mqtt.Connection,
        thing_name: str,
    ):
        threading.Thread.__init__(self)

        self.__status = HealthCheckStatus.NOT_INIT
        self.__mqtt_connection = mqtt_connection
        self.__thing_name = thing_name

    def run(self):
        health_check_use_case = HealthCheckUseCase(
            self.__mqtt_connection, self.__thing_name
        )
        health_check_topic = HealthCheckTopic(self.__mqtt_connection, self.__thing_name)
        health_check_topic.subscribe(health_check_use_case.set_timestamp_for_subscriber)

        while True:
            try:
                self.__status = health_check_use_case.get_status(
                    TIME_OUT_SEC,
                )
                logger.info(f"status: {self.__status}")
            except Exception:
                logger.error("Unknown error", exc_info=True)

            # チェック間隔を指定
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


def main():
    logger.info("start main thread")
    logger.info("start create mqtt connection")
    connection = createMQTTConnection(
        device_certificate_filepath="./data/device_certificate.pem",
        private_key_filepath="./data/private.key",
        ca_certificate_filepath="./data/ca_certificate.pem",
    )
    logger.info("end create mqtt connection")

    health_check_thread = HealthCheckThread(mqtt_connection=connection, thing_name=THING_NAME)
    health_check_thread.daemon = True
    health_check_thread.name = "health_check_thread"
    health_check_thread.start()

    while True:
        time.sleep(10)


if __name__ == "__main__":
    main()
