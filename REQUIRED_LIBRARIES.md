# Required CircuitPython Libraries

To use BLE provisioning, you need to install these libraries to your `lib/` folder:

## Required for BLE:

1. **adafruit_ble** (folder)
   - Download from: https://github.com/adafruit/Adafruit_CircuitPython_BLE/releases
   - Or use circup: `circup install adafruit_ble`

## How to Install:

### Option 1: Using circup (Recommended)

```bash
pip install circup
circup install adafruit_ble
```

### Option 2: Manual Download

1. Go to https://circuitpython.org/libraries
2. Download the library bundle matching your CircuitPython version (10.0.3)
3. Extract and copy the `adafruit_ble` folder to your `E:\lib\` directory

## Alternative: Simplified Version

If you want to test without BLE first, I can create a simplified version that skips BLE provisioning and uses hardcoded credentials for testing.
