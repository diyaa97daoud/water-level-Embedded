# Water Level Monitoring - Embedded System (NRF52840)

CircuitPython-based embedded system for water level monitoring using Adafruit Feather nRF52840 with BLE connectivity.

## 🔧 Hardware

- **Adafruit Feather nRF52840 Express** - Main microcontroller with BLE
- **HC-SR04 Ultrasonic Sensor** - Water level distance measurement
- **SSD1306 OLED Display** - Local status display
- **Relay Module** - Water pump control

## 📋 Prerequisites

- Python 3.7+ (for gateway script)
- CircuitPython installed on nRF52840
- Backend server running
- Required Python libraries (see `REQUIRED_LIBRARIES.md`)

## 🚀 Quick Start Guide

### 1. Prepare the Device

Connect the nRF52840 to your PC via USB. The device should appear as a mounted drive (e.g., `CIRCUITPY`).

### 2. Start Backend Server

Ensure the backend server is running:

```bash
cd "WaterLevel Backend"
./gradlew bootRun
```

The server should be accessible at `http://localhost:8080`

### 3. Register Device in Dashboard

1. Open the web dashboard at `http://localhost:5173`
2. Login with admin credentials
3. Navigate to **Device Management**
4. Click **Register New Device**
5. Fill in device details
6. **Copy the generated `device_key`** - you'll need this for provisioning

### 4. Provision Device via BLE

1. Click the `A` button on the OLED screen to enter BLE provisioning mode.
2. Open `ble_provisioning.html` in a web browser (Chrome/Edge recommended for Web Bluetooth API)
3. Click **Connect to Device**
4. Select `WaterLevel-Device` from the Bluetooth pairing dialog, then `pair`.
5. Enter credentials:
   - **device_id**: identifier, we can keep the default
   - **device_kry**: The key copied from dashboard registration
6. Click **Save Configuration**
7. Wait for confirmation that credentials are saved, the nrf will reset after saving the configuration.
8. **Close the provisioning tab**

### 5. Start MQTT Gateway

Run the gateway script to bridge BLE and MQTT:

```bash
python ble_mqtt_gateway.py
```

The gateway will:

- Scan and connect to the nRF52840 via BLE
- Establish MQTT connection with the backend
- Forward sensor data from device to backend
- Relay pump commands from backend to device

You should see output like:

```
🔍 Scanning for 'WaterLevel-Device'...
✅ Found device: WaterLevel-Device
📡 Connected to BLE device
🔗 Connected to MQTT broker
📊 Sensor data: {...}
```

## 📁 Key Files

- **`code.py`** - Main CircuitPython firmware running on nRF52840
- **`ble_mqtt_gateway.py`** - Python script bridging BLE to MQTT
- **`ble_provisioning.html`** - Web-based BLE provisioning interface
- **`config.json`** - Device configuration (WiFi, backend URL, device key)
- **`lib/`** - CircuitPython libraries for sensors and display

## 🔄 System Operation

Once configured and running:

1. **nRF52840** reads water level via HC-SR04 sensor every 5 seconds
2. Data is sent via **BLE** to the gateway script
3. **Gateway** forwards data to backend via **MQTT**
4. Backend processes data and can send pump control commands
5. Commands flow back: Backend → MQTT → Gateway → BLE → nRF52840
6. Device controls relay to start/stop water pump

## 🛠️ Troubleshooting

**BLE Connection Fails**

- Ensure Bluetooth is enabled on your PC
- Device must be in range (~10m)
- Try restarting the nRF52840 (press reset button)

**Gateway Cannot Connect**

- Check that `device_key` matches in config.json and backend
- Verify backend server is running and accessible
- Check MQTT broker is running (usually bundled with backend)

**Sensor Readings Not Updating**

- Check HC-SR04 wiring connections
- Verify sensor power supply (5V depending on sensor)
- Check serial output from nRF52840 for error messages

**Provisioning Doesn't Work**

- Use Chrome or Edge browser (Firefox has limited Web Bluetooth support)
- Enable Bluetooth permissions in browser
- Check browser console for error messages

## 📦 Dependencies

Install Python dependencies:

```bash
pip install bleak paho-mqtt
```

CircuitPython libraries are included in `lib/` folder.

## 📞 Related Projects

- [Backend Server](https://github.com/aliyehiawi/water-level-monitoring-backend) - Java Spring Boot API with MQTT
- [Web Dashboard](https://github.com/aliyehiawi/smart-garden-frontend) - Vue.js monitoring interface
- [Android App](https://github.com/diyaa97daoud/water-level-Android) - Mobile monitoring app
