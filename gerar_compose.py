NUM_CONTAINERS = 4
SENSORS_PER_CONTAINER = 1

RASPBERRY_IP = "10.0.0.2"

QOS = 1

EXPERIMENT = "mqtt_baseline_4sensors"

MIN_WAIT_SECONDS = 30
MAX_WAIT_SECONDS = 300

with open("docker-compose.yml", "w") as f:

    f.write("services:\n")

    for i in range(NUM_CONTAINERS):

        service_name = f"sensor_group_{i+1}"

        start_sensor_id = (
            i * SENSORS_PER_CONTAINER
        ) + 1

        f.write(f"  {service_name}:\n")

        f.write("    build: .\n")

        f.write(
            f"    container_name: {service_name}\n"
        )

        f.write("    environment:\n")

        f.write(
            f"      - ID_SENSOR={start_sensor_id}\n"
        )

        f.write(
            f"      - NUM_VAGA={SENSORS_PER_CONTAINER+i}\n"
        )

        f.write(
            f"      - MQTT_BROKER={RASPBERRY_IP}\n"
        )

        f.write(
            "      - MQTT_PORT=1883\n"
        )

        f.write(
            "      - MQTT_TOPIC_PREFIX=estacionamento1\n"
        )

        f.write(
            f"      - QOS={QOS}\n"
        )

        f.write(
            f"      - EXPERIMENT={EXPERIMENT}\n"
        )

        f.write(
            f"      - MIN_WAIT_SECONDS={MIN_WAIT_SECONDS}\n"
        )

        f.write(
            f"      - MAX_WAIT_SECONDS={MAX_WAIT_SECONDS}\n"
        )

        f.write(
            "    network_mode: host\n"
        )

print(
    f"Generated docker-compose.yml with "
    f"{NUM_CONTAINERS} containers and "
    f"{NUM_CONTAINERS * SENSORS_PER_CONTAINER} sensors."
)

