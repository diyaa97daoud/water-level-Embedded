## 🚀 System Description: Smart Water Level Management (MQTT-Centric)

This system is an event-driven solution for monitoring and controlling a water level device (Hardware) through a web-based **Frontend**. Communication is managed asynchronously via an **MQTT Broker**, which handles messaging between the **Hardware** and the **Backend** server.

---

## 💻 Architecture and Communication Flow

### 1. Core Components

The system relies on three main components:

- **Hardware (MQTT Client/Publisher):** The physical device (Adafruit Feather nrf528) that measures the water level and controls the pump.
- **MQTT Broker:** The central communication hub that manages message topics, subscriptions, and publications.
- **Backend (MQTT Client/Subscriber):** The server handling data persistence, business logic, user authentication, and command publishing.
- **Frontend:** The user interface for display and administration.

### 2. Device Provisioning and Security

1.  **Admin Registration:** An **Admin** registers a new device via the **Frontend**, sending the name to the **Backend**.
2.  **Key Exchange:** The **Backend** generates a unique **Device ID** and a secure **Device Key**, returning them to the Frontend.
3.  **Hardware Configuration:** The **Frontend** uses **Bluetooth** to communicate with the physical device, storing the **Device Key** in its memory. This key is used by the **Hardware** to authenticate and connect securely to the **MQTT Broker** for all subsequent communications.

### 3. Data and Command Flow (MQTT Topics)

Communication between the Hardware and Backend is instant and bidirectional using specific **MQTT Topics**:

| Flow Type          | Publisher | Subscriber | Topic Example                    | Purpose                                           |
| :----------------- | :-------- | :--------- | :------------------------------- | :------------------------------------------------ |
| **Data**           | Hardware  | Backend    | `devices/DEVICE_ID/data`         | Real-time sensor readings (water level).          |
| **Thresholds**     | Backend   | Hardware   | `devices/DEVICE_ID/thresholds`   | Sending updated MIN/MAX values.                   |
| **Manual Control** | Backend   | Hardware   | `devices/DEVICE_ID/pump/control` | Sending immediate pump START command.             |
| **Status Update**  | Hardware  | Backend    | `devices/DEVICE_ID/status`       | Hardware confirming actions (e.g., pump started). |

---

## 👤 User Roles and Capabilities

The system supports two access roles authenticated via **Login** and **Register** pages on the Frontend.

| Role               | Capabilities                                                                                                                                                                                                                                                                                            | Interaction                                                                                         |
| :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :-------------------------------------------------------------------------------------------------- |
| **Read-Only User** | **Data Viewing:** Can view the **Dashboard** and the **Water Level Table**. The table shows the current water level and a history of all previous data points and threshold settings.                                                                                                                   | Accesses the **Frontend**.                                                                          |
| **Admin**          | **All Read-Only Capabilities** plus: **Threshold Adjustment:** Set and submit new **MIN/MAX** thresholds. **Manual Pump Control:** Initiate a manual pump start command. **User Management:** Create new Admin users and delete existing users. **Device Registration:** Register new hardware devices. | Interacts with the **Frontend**, which triggers **Backend** actions (API calls and MQTT publishes). |

---

## ⚙️ Hardware and System Interaction

### 1. Real-Time Data Monitoring

- The **Hardware** periodically publishes its **Water Level** sensor data to the MQTT Broker.
- The **Backend** is continuously **listening** (subscribed) to this topic, instantly storing the data and making it available for the **Frontend** dashboard.

### 2. Autonomous and Threshold Management

- **Admin Action:** An Admin submits new MIN/MAX thresholds via the UI.
- **Backend Action:** The Backend saves the new thresholds and immediately **publishes** them to the Hardware's threshold topic.
- **Hardware Reaction:** The **Hardware** is **listening** to the threshold topic and updates its internal memory instantly. It then manages the **auto starting and stopping of the pump** autonomously based on the current water level and the most recent thresholds it received.

### 3. Manual Pump Start Override

Manual pump control is handled via an immediate command:

1.  **Frontend Action:** Admin clicks the **Start Pump** button.
2.  **Backend Action:** The Backend updates a database flag (tracking the manual request) and instantly **publishes** a START command to the Hardware's control topic.
3.  **Hardware Reaction:** The **Hardware** immediately receives the command, starts the pump, and **publishes** a status update (e.g., "Pump Started") back to the Broker.
4.  **Backend Confirmation:** The Backend receives the status update and uses it to reset the manual pump flag in the database, confirming the command execution.
