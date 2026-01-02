import paho.mqtt.client as mqtt
import json
import sys

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
CONFIG_FILE = "e:\\config.json"

# Read device_key from config.json
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        DEVICE_KEY = config.get("device_key")
        if not DEVICE_KEY:
            print("Error: device_key not found in config.json")
            sys.exit(1)
except FileNotFoundError:
    print(f"Error: {CONFIG_FILE} not found")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Invalid JSON in {CONFIG_FILE}")
    sys.exit(1)

action = sys.argv[1] if len(sys.argv) > 1 else "START_PUMP"
topic = f"devices/{DEVICE_KEY}/pump/start"  # Backend uses /start not /command
message = json.dumps({"action": action})

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.publish(topic, message)
client.disconnect()

print(f"Sent to {topic}: {message}")