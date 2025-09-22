# Home Assistant Seneye Pi Integration

## Overview
This integration runs a Seneye USB device on a Raspberry Pi and publishes its readings to an MQTT broker for Home Assistant.

## Why MQTT First?
- ✅ Stable: Direct hidraw + pyseneye → MQTT bridge.
- ✅ Works with recent Home Assistant updates.
- ⚠️ USB/IP: No longer reliable after HA core upgrade (breaks hidraw passthrough).

## Features
- Publishes temperature, pH, NH3, lux, and PAR.
- Auto-recovers if the USB feed stalls.
- Installs as a `systemd` service.

## Setup
1. Copy `udev/99-seneye-hidraw.rules` → `/etc/udev/rules.d/`
2. Copy `systemd/seneye-mqtt.service` → `/etc/systemd/system/`
3. Run `scripts/install.sh` to set up Python venv and dependencies.
4. Adjust broker credentials in `seneye_mqtt_daemon.py` (default: `mqtt-user` / `2Kqhd560!`).

## MQTT Topic
```
seneye/state
```

## Example Payload
```json
{
  "ts": "2025-09-19T22:19:38Z",
  "temperature_c": 27.5,
  "ph": 8.17,
  "nh3_mg_l": 0.007,
  "lux": 9,
  "par": 0
}
```
