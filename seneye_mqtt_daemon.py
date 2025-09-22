#!/usr/bin/env python3
import time, json, logging, socket
import paho.mqtt.client as mqtt
from pyseneye.sud import SUDevice, Action

BROKER_HOST = "192.168.7.253"
BROKER_PORT = 1883
BROKER_USER = "mqtt-user"
BROKER_PASS = "2Kqhd560!"
MQTT_TOPIC = "seneye/state"
CLIENT_ID = f"seneye-pi-{socket.gethostname()}"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def main():
    client = mqtt.Client(client_id=CLIENT_ID)
    client.username_pw_set(BROKER_USER, BROKER_PASS)
    client.connect(BROKER_HOST, BROKER_PORT, 60)
    client.loop_start()

    dev = SUDevice()
    while True:
        try:
            dev.action(Action.ENTER_INTERACTIVE_MODE)
            resp = dev.action(Action.SENSOR_READING)
            data = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "temperature_c": getattr(resp, "temperature", None),
                "ph": getattr(resp, "ph", None),
                "nh3_mg_l": getattr(resp, "nh3", None),
                "lux": getattr(resp, "lux", None),
                "par": getattr(resp, "par", None),
            }
            logging.info("Published: %s", data)
            client.publish(MQTT_TOPIC, json.dumps(data), qos=1, retain=False)
        except Exception as e:
            logging.warning("Read/publish failed: %s", e)
        time.sleep(10)

if __name__ == "__main__":
    main()
