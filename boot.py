# SPDX-FileCopyrightText: 2025
# SPDX-License-Identifier: MIT
"""
Boot configuration for Water Level Management Device
This file runs before code.py and configures the filesystem
"""

import storage
import board
import digitalio
import time

# Check if Button B is pressed during boot
# If pressed, keep filesystem writable for development
button_b = digitalio.DigitalInOut(board.D6)
button_b.direction = digitalio.Direction.INPUT
button_b.pull = digitalio.Pull.UP

# Small delay to ensure button state is stable
time.sleep(0.1)

# If Button B is NOT pressed, make filesystem writable for BLE provisioning
if button_b.value:  # Button not pressed (pull-up = True when not pressed)
    # Make filesystem writable so BLE provisioning can save config
    storage.remount("/", False)
    print("Filesystem: WRITABLE (for BLE provisioning)")
else:
    # Button B pressed - keep filesystem read-only for USB access
    print("Filesystem: READ-ONLY (Button B pressed - USB mode)")
