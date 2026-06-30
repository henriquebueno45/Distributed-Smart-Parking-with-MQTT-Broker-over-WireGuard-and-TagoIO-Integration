import os
import sys
import time
import json
import random
import string
import signal
import socket
import threading
import paho.mqtt.client as mqtt


MQTT_BROKER = os.getenv("MQTT_BROKER", "10.0.0.2")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "estacionamento1/estacionamento")
QOS = int(os.getenv("QOS", "1"))

ID_SENSOR = int(os.getenv("ID_SENSOR", "1"))
NUM_VAGA = int(os.getenv("NUM_VAGA", "1"))

MIN_WAIT = float(os.getenv("MIN_WAIT_SECONDS", "30"))
MAX_WAIT = float(os.getenv("MAX_WAIT_SECONDS", "300"))

min_wait_min = os.getenv("MIN_WAIT_MINUTES")
max_wait_min = os.getenv("MAX_WAIT_MINUTES")

if min_wait_min:
    MIN_WAIT = float(min_wait_min) * 60

if max_wait_min:
    MAX_WAIT = float(max_wait_min) * 60

HOSTNAME = socket.gethostname()

print("=" * 50)
print("Parking Spot Simulator Started")
print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"Topic: {MQTT_TOPIC}")
print(f"Hostname: {HOSTNAME}")
print(f"Vagas Range: {ID_SENSOR} to {ID_SENSOR + NUM_VAGA - 1} (Total: {NUM_VAGA})")
print(f"Wait Range: {MIN_WAIT}s to {MAX_WAIT}s ({MIN_WAIT/60:.2f}m to {MAX_WAIT/60:.2f}m)")
print("=" * 50)

def generate_plate():
    letters1 = ''.join(random.choices(string.ascii_uppercase, k=3))
    num1 = str(random.randint(0, 9))
    letter2 = random.choice(string.ascii_uppercase)
    num2 = ''.join(random.choices(string.digits, k=2))
    return f"{letters1}{num1}{letter2}{num2}"

def sensor_simulator(sensor_id):

    sensor_name = f"sensor_{sensor_id}"

    state = 0
    seq = 0

    time.sleep(random.uniform(0, min(10, MIN_WAIT)))

    while True:

        if state == 0:

            print(f"[{sensor_name}] State: EMPTY")
            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)

            print(f"[{sensor_name}] Sleeping {wait_time:.2f}s...")
            time.sleep(wait_time)

            state = 1

        elif state == 1:

            print(f"[{sensor_name}] State: OCCUPIED")

            plate = generate_plate()
            employee_type = random.choice([1, 2, 3])

            payload = {
                "sensor_id": sensor_name,
                "state": state,
                "plate": plate,
                "employee_type": employee_type,

                "timestamp": time.time(),

                # Per-sensor sequence number
                "seq": seq,

                # Host running this simulator
                "hostname": HOSTNAME
            }

            try:
                client.publish(
                    MQTT_TOPIC,
                    json.dumps(payload),
                    qos=QOS
                )

                print(f"[{sensor_name}] OCCUPIED -> seq={seq}")

            except Exception as e:
                print(f"[{sensor_name}] Publish ERROR: {e}")

            seq += 1

            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)

            print(f"[{sensor_name}] Sleeping {wait_time:.2f}s...")
            time.sleep(wait_time)

            state = 0

            payload_empty = {
                "sensor_id": sensor_name,
                "state": state,
                "plate": None,
                "employee_type": None,

                "timestamp": time.time(),

                "seq": seq,

                "hostname": HOSTNAME
            }

            try:
                client.publish(
                    MQTT_TOPIC,
                    json.dumps(payload_empty),
                    qos=QOS
                )

                print(f"[{sensor_name}] EMPTY -> seq={seq}")

            except Exception as e:
                print(f"[{sensor_name}] Publish ERROR: {e}")

            seq += 1


# MQTT CALLBACKS
def on_connect(client, userdata, flags, reason_code, properties=None):

    print(f"Connected to MQTT Broker with result code: {reason_code}")

    if reason_code == 0:

        print(f"Starting {NUM_VAGA} sensor threads...")

        for sensor_id in range(ID_SENSOR, ID_SENSOR + NUM_VAGA):

            t = threading.Thread(
                target=sensor_simulator,
                args=(sensor_id,),
                daemon=True
            )

            t.start()

    else:
        print("Connection failed. Retrying...")

try:
    from paho.mqtt.enums import CallbackAPIVersion
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
except (ImportError, TypeError):
    client = mqtt.Client()

client.on_connect = on_connect

def sigterm_handler(signum, frame):

    print("\nTermination signal received.")

    client.disconnect()

    sys.exit(0)


signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

except KeyboardInterrupt:
    print("\nSimulator stopped.")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)
