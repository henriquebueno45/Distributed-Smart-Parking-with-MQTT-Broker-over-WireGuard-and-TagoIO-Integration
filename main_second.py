import os
import sys
import time
import json
import random
import string
import signal
import threading
import paho.mqtt.client as mqtt

# ===== CONFIGURATION =====
MQTT_BROKER = os.getenv("MQTT_BROKER", "10.0.0.2")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "estacionamento1/estacionamento")
QOS = int(os.getenv("QOS", "1"))

ID_SENSOR = int(os.getenv("ID_SENSOR", "1"))
NUM_VAGA = int(os.getenv("NUM_VAGA", "1"))

# Time configurations in seconds (min/max wait)
# Default range is 30s (0.5m) to 300s (5m). Easily overridden for faster testing.
MIN_WAIT = float(os.getenv("MIN_WAIT_SECONDS", "30"))
MAX_WAIT = float(os.getenv("MAX_WAIT_SECONDS", "300"))

# Check for minute-based environment variables
min_wait_min = os.getenv("MIN_WAIT_MINUTES")
max_wait_min = os.getenv("MAX_WAIT_MINUTES")
if min_wait_min:
    MIN_WAIT = float(min_wait_min) * 60
if max_wait_min:
    MAX_WAIT = float(max_wait_min) * 60

print("=" * 50)
print(f"Parking Spot Simulator Started")
print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}")
print(f"Topic: {MQTT_TOPIC}")
print(f"Vagas Range: {ID_SENSOR} to {ID_SENSOR + NUM_VAGA - 1} (Total: {NUM_VAGA})")
print(f"Wait Range: {MIN_WAIT}s to {MAX_WAIT}s ({MIN_WAIT/60:.2f}m to {MAX_WAIT/60:.2f}m)")
print("=" * 50)

# ===== HELPERS =====
def generate_plate():
    # Brazilian Mercosul plate format: AAA0A00 (e.g. ABC1D23)
    letters1 = ''.join(random.choices(string.ascii_uppercase, k=3))
    num1 = str(random.randint(0, 9))
    letter2 = random.choice(string.ascii_uppercase)
    num2 = ''.join(random.choices(string.digits, k=2))
    return f"{letters1}{num1}{letter2}{num2}"

# ===== SENSOR SIMULATOR THREAD FUNCTION =====
def sensor_simulator(sensor_id):
    sensor_name = f"sensor_{sensor_id}"
    state = 0  # 0 = Empty, 1 = Occupied
    
    # Slight initial random delay to offset start times of sensors in the container
    time.sleep(random.uniform(0, min(10, MIN_WAIT)))
    
    while True:
        if state == 0:
            print(f"[{sensor_name}] State: 0 (Empty). Waiting next event...")
            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)
            print(f"[{sensor_name}] Sleeping for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            
            # Transition to State 1
            state = 1
            
        elif state == 1:
            print(f"[{sensor_name}] State: 1 (Someone parked). Generating details...")
            plate = generate_plate()
            employee_type = random.choice([1, 2, 3])
            
            payload = {
                "sensor_id": sensor_name,
                "state": state,
                "plate": plate,
                "employee_type": employee_type,
                "timestamp": time.time()
            }
            
            # Publish Occupied state
            try:
                res = client.publish(MQTT_TOPIC, json.dumps(payload), qos=QOS)
                print(f"[{sensor_name}] Sent MQTT payload (OCCUPIED): {json.dumps(payload)}")
            except Exception as e:
                print(f"[{sensor_name}] [ERROR] Failed to send MQTT payload: {e}")
                
            # Wait while occupied
            wait_time = random.uniform(MIN_WAIT, MAX_WAIT)
            print(f"[{sensor_name}] Sleeping for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            
            # Transition to State 0
            state = 0
            
            payload_empty = {
                "sensor_id": sensor_name,
                "state": state,
                "plate": None,
                "employee_type": None,
                "timestamp": int(time.time())
            }
            
            # Publish Empty state
            try:
                res = client.publish(MQTT_TOPIC, json.dumps(payload_empty), qos=QOS)
                print(f"[{sensor_name}] Sent MQTT payload (EMPTY): {json.dumps(payload_empty)}")
            except Exception as e:
                print(f"[{sensor_name}] [ERROR] Failed to send empty state MQTT payload: {e}")

# ===== MQTT CLIENT CALLBACKS =====
def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected to MQTT Broker with result code: {reason_code}")
    if reason_code == 0:
        print(f"Starting {NUM_VAGA} sensor simulation threads...")
        for sensor_id in range(ID_SENSOR, ID_SENSOR + NUM_VAGA):
            t = threading.Thread(target=sensor_simulator, args=(sensor_id,), daemon=True)
            t.start()
    else:
        print("⚠️ Could not connect to broker. Retrying...")

# ===== MQTT CLIENT INITIALIZATION =====
try:
    # Try paho-mqtt v2 API
    from paho.mqtt.enums import CallbackAPIVersion
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
except (ImportError, TypeError):
    # Fallback to paho-mqtt v1 API
    client = mqtt.Client()

client.on_connect = on_connect

# Clean exit handler
def sigterm_handler(signum, frame):
    print("\n[Simulator] Termination signal received. Exiting...")
    client.disconnect()
    sys.exit(0)

signal.signal(signal.SIGINT, sigterm_handler)
signal.signal(signal.SIGTERM, sigterm_handler)

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[Simulator] Simulator stopped by keyboard interrupt.")
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    sys.exit(1)
