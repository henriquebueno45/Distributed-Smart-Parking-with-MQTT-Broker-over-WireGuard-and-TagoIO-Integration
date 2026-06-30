# 🚗 Distributed Smart Parking IoT
**MQTT Broker over WireGuard and TagoIO Integration**

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-3C5280?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)
![WireGuard](https://img.shields.io/badge/WireGuard-VPN-881798?style=for-the-badge&logo=wireguard&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 📖 About the Project

This project presents a distributed architecture for a **Smart Parking System** tailored for Smart Cities. By leveraging dozens of independent Docker containers, the system simulates the dynamic real-time behavior of parking spots.

The simulated sensor data is transmitted efficiently via the **MQTT protocol**, tunneled securely through a **WireGuard VPN** to a local MQTT Broker hosted on a Raspberry Pi. From there, a data processor validates business rules (e.g., parking time limits) and sends the payloads via HTTPS POST to the **TagoIO** cloud platform for real-time dashboard visualization and automated email alerts.

## 🏗️ Architecture & Network Topology

The ecosystem is divided into three main layers, connected via a secure VPN tunnel to overcome local network routing constraints.

```mermaid
flowchart LR
    subgraph "Application Layer (Cloud)"
        Tago[TagoIO Dashboards & Alerts]
    end

    subgraph "Local Network (192.168.15.0/24)"
        direction TB
        RPi["Raspberry Pi (192.168.15.45)\nMQTT Broker (Port 1883)"]
        Processor["Data Processor\n(HTTPS POST)"]
        RPi --> Processor
    end

    subgraph "Simulation Layer (VirtualBox VM)"
        direction TB
        Ubuntu["Ubuntu 24.04 Server (Host: Windows)"]
        Docker1["Docker: Sensor 1"]
        DockerN["Docker: Sensor N"]
        Ubuntu --- Docker1
        Ubuntu --- DockerN
    end

    %% Connections
    Ubuntu == "WireGuard VPN\n(10.0.0.0/24)" ==> RPi
    Processor == "HTTPS API" ==> Tago
```

## 📂 Repository Structure

* `main.py` / `main_second.py`: The core simulator scripts. They implement the Finite State Machine (FSM) logic for the parking spots, using the `paho-mqtt` library to publish events to the broker.
* `gerar_compose.py`: A Python utility script that dynamically generates the `docker-compose.yml` file. It allows you to effortlessly scale the simulation to dozens of containers/sensors by simply changing a few variables in the code.
* `Dockerfile`: Defines a lightweight image based on `python:3.11-slim` to encapsulate the application and automatically install required dependencies.
* `docker-compose.yml`: The generated manifest configuring environment variables (such as `MQTT_BROKER`, `ID_SENSOR`, `NUM_VAGA`) and setting the network to *host mode* for easier VPN routing.
* `LICENSE`: MIT License terms.

## ⚙️ MQTT Payload Format

Each sensor publishes a JSON message at every state transition. The payload follows this structure:

```json
{
  "sensor_id": "sensor_1",
  "timestamp": 1717084500,
  "plate": "ABC-1234",
  "employee_type": 2,
  "state": 1
}
```
* *`state: 1` = Occupied | `state: 0` = Empty*

> `![State Diagram](docs/Diagram_main.png)` *(Add your state machine image to the docs folder)*

## 🚀 How to Run Locally

### Prerequisites
* **Docker** and **Docker Compose** installed on your machine.
* **Python 3.11+** (to run the setup scripts).
* An active **MQTT Broker** (can be local or accessible via VPN, like the WireGuard setup on IP `10.0.0.2` used in this project).

### Step-by-Step Guide

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/henriquebueno45/Distributed-Smart-Parking-with-MQTT-Broker-over-WireGuard-and-TagoIO-Integration.git](https://github.com/henriquebueno45/Distributed-Smart-Parking-with-MQTT-Broker-over-WireGuard-and-TagoIO-Integration.git)
   cd Distributed-Smart-Parking-with-MQTT-Broker-over-WireGuard-and-TagoIO-Integration
   ```

2. **Configure the Simulation Scale:**
   If you want to change the number of parking spots, edit the `NUM_CONTAINERS` and `SENSORS_PER_CONTAINER` variables inside the `gerar_compose.py` script. Then, generate the new manifest:
   ```bash
   python gerar_compose.py
   ```

3. **Build and Start the Containers:**
   Run the containers in detached mode:
   ```bash
   docker-compose up --build -d
   ```

4. **Monitor the Logs:**
   To watch the state transitions (Empty -> Occupied) and MQTT publications in real-time:
   ```bash
   docker-compose logs -f
   ```

## ⚠️ WireGuard & Virtual Machine Troubleshooting

If you are running the WireGuard server on an **Ubuntu Server 24 VM** using **VirtualBox** on a **Windows** host, you might experience the VPN tunnel dropping when the host computer's screen locks or is idle for a while. To prevent this, ensure the following steps are taken:

1. Add `PersistentKeepalive = 25` to your WireGuard client/server configuration to maintain the handshake.
2. Disable **Hibernation** and **Sleep/Suspension** completely in the Windows host power settings.
3. In the Windows Device Manager, go to the Network Adapters, open properties, and uncheck *"Allow the computer to turn off this device to save power"*.
4. If the connection still drops after a while, verify if there are any remaining energy-saving options active within VirtualBox itself or within the Ubuntu Server 24 VM that might be hibernating network interfaces or freezing processes.

## 📊 Dashboards in TagoIO

The cloud integration allows for real-time visualization of the parking spots and network auditing. 

*(Replace the paths below with your actual image paths once uploaded to the repo's docs folder)*
> `![Parking Dashboard](docs/imagem_vagas_estacionamento.png)`
> `![Network Audit - Latency and Throughput](docs/imagem_latencia_throughput.png)`

## 🎓 Authors & Acknowledgments

Academic project developed by **Dener Kraus**, **Henrique Bueno**, and **Lucas Bueno**.

This work fulfills the final project requirements for the **Wireless Sensor Networks for IoT** course (Postgraduate Program - PPGCC / EEL), taught by Professor Richard Demo Souza at the Federal University of Santa Catarina (UFSC).

## 📄 License

Distributed under the MIT License. See the [LICENSE](LICENSE) file for more information. (Copyright © 2026 **Dener Kraus**, **Henrique Bueno**, and **Lucas Bueno**).
