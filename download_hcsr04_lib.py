"""
Download adafruit_hcsr04 library
Run this script to download the library file
"""
import urllib.request
import os

LIB_URL = "https://raw.githubusercontent.com/adafruit/Adafruit_CircuitPython_HCSR04/main/adafruit_hcsr04.py"
DEST_PATH = "E:/lib/adafruit_hcsr04.py"

print("Downloading adafruit_hcsr04 library...")
try:
    urllib.request.urlretrieve(LIB_URL, DEST_PATH)
    print(f"✓ Downloaded to {DEST_PATH}")
    print("✓ Library ready!")
except Exception as e:
    print(f"✗ Error: {e}")
    print("\nManual download:")
    print("1. Visit: https://circuitpython.org/libraries")
    print("2. Download the bundle")
    print("3. Copy adafruit_hcsr04.mpy to E:\\lib\\")
