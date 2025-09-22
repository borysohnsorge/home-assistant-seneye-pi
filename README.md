# Home Assistant – Seneye (HID / USB-IP / MQTT)

Universal Seneye integration for Home Assistant. Works with direct USB, a Raspberry Pi MQTT publisher, or (historically) a Raspberry Pi USB/IP bridge. Shipped with dashboards, blueprints, and automations for an instant, useful setup.

Honesty check:  
- **Confirmed working:** Direct USB (HID backend) and Raspberry Pi MQTT publisher (stable, recommended).  
- **Broken after recent HA OS updates:** Raspberry Pi USB/IP bridge. Left in docs for reference, but no longer reliable.  
- **Expected to work:** AquaPi MQTT bridge. PRs welcome!

---

## Contents
- Features
- Architecture
- Which setup should I choose?
- Install the integration (HACS or manual)
- Setup A – Direct USB (HID backend)
- Setup B – Raspberry Pi as USB/IP bridge (**broken after HA updates**)
- Setup C – MQTT publisher (Pi / AquaPi / Linux / Windows)
- Setup D – Windows USB/IP server (untested, expected to work)
- Setup E – Network USB hubs (guidance)
- Options & Services
- Dashboards, Blueprints & Automations
- Troubleshooting
- Tested & Untested Setups
- Contributing
- License

---

## Features
- **Multiple Backends:** Connect via the method that best suits your setup.
- **HID (Default):** For devices directly connected via USB.
- **MQTT (Recommended):** For devices connected to a remote computer (like a Raspberry Pi or AquaPi), which then publishes sensor data over the network.
- **Standalone MQTT Publisher:** A lightweight Python script with a systemd service to run on any Linux-based machine (e.g., Raspberry Pi) that has the Seneye device attached.
- **Pre-made Dashboards:** Three ready-to-use Lovelace dashboards (Standard, ApexCharts, and Mushroom).
- **Automation Blueprints:** Easy-to-configure blueprints for critical alerts, including high NH3, pH out of range, and stale data warnings.
- **Installer Scripts:** Helper scripts for Linux and Windows to automate the installation of the dashboard files.

---

## Architecture
This diagram illustrates the different ways you can connect your Seneye device to Home Assistant using this integration:
Seneye USB Probe
|
|–> [Option 1: Direct Connection]
|      |
|      +–> Home Assistant Host (using HID Backend)
|
|–> [Option 2: USB over Network]
|      |
|      +–> Raspberry Pi / PC (running USB/IP Server)
|           |
|           +– (USB over IP) –> Home Assistant (using USB/IP Client & HID Backend)
|
+–> [Option 3: MQTT over Network]
|
+–> Any PC / Pi (running MQTT Publisher Script)
|
+– (MQTT) –> MQTT Broker
|
+– (MQTT) –> Home Assistant (using MQTT Backend)
- HID (default) reads `/dev/hidraw*`.  
- MQTT backend subscribes to `<prefix>/state` with parsed readings (publisher included here).

---

## Recommended Hardware for Raspberry Pi Setups
If you are connecting your Seneye to a Raspberry Pi (for MQTT), **power stability is critical**.  

- **High-Quality Power Supply:** Use an official or high-quality supply (e.g., 5V 3A for Pi 4/Zero 2 W).  
- **Powered USB Hub:** Ensures stable power to the Seneye probe.  
- **Correct Connection:** Raspberry Pi → Powered USB Hub → Seneye Probe.  

---

## Which setup should I choose?

| Scenario                            | Recommended path              | Notes                              |
|-------------------------------------|--------------------------------|------------------------------------|
| Seneye plugged into HA box          | Setup A: Direct USB (HID)      | Easiest                            |
| Seneye in another room; Pi nearby   | Setup C: Pi MQTT publisher     | Stable, confirmed                  |
| Want to decouple transport / AquaPi | Setup C: MQTT publisher        | Publisher included                 |
| Windows machine shares Seneye       | Setup D: USB/IP (usbipd-win)   | Expected to work                   |
| Network USB hub                     | Setup E guidance               | Depends on hub                     |
| (Legacy) Pi USB/IP bridge           | Setup B                        | **Broken after HA updates**        |

---

## Install the integration (HACS or manual)

### Option 1 – HACS (recommended)
1. Install HACS in HA.  
2. HACS → Integrations → Custom repositories → add this repo URL under Integration.  
3. Search **Seneye** → Install.  
4. Restart HA → Settings → Devices & Services → Add Integration → Seneye.  

### Option 2 – Manual copy
Copy `custom_components/seneye/` into `/config/custom_components/`.  
Restart HA → Add Integration → Seneye.  

---

## Setup A – Direct USB (HID backend)
- Plug Seneye into the HA host (or VM with USB passthrough).  
- Add Seneye integration.  
- Backend = HID.  
- Call `seneye.connection_test` to confirm.  

---

## Setup B – Raspberry Pi as USB/IP bridge (**Broken after HA OS updates**)
This setup previously worked but is **no longer stable after recent Home Assistant OS kernel changes**.  
Docs are left here for reference only. If you need a network transport, **use MQTT (Setup C)** instead.

---

## Setup C – MQTT publisher (Recommended)
This is the **most stable method today**.  

Publisher script runs on the Pi (or any Linux/Windows machine with Seneye plugged in) → sends JSON to MQTT → HA subscribes.  

### On the machine with Seneye attached
```bash
sudo apt update && sudo apt install -y python3-venv git
sudo mkdir -p /opt/seneye-mqtt && sudo chown $USER:$USER /opt/seneye-mqtt
cd /opt/seneye-mqtt
git clone https://github.com/tamengual/home-assistant-seneye-pi.git .
cd mqtt_publisher

python3 -m venv venv
. venv/bin/activate
pip install -U pip
pip install -r requirements.txt

## Configure /etc/default/seneye-mqtt:
MQTT_HOST=192.168.1.10
MQTT_PORT=1883
MQTT_USERNAME=mqtt-user
MQTT_PASSWORD=yourpassword
MQTT_PREFIX=seneye
INTERVAL=300
HIDRAW_PATH=/dev/hidraw0

## Enable service:
sudo cp systemd/seneye-mqtt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now seneye-mqtt

## You should see in MQTT:
seneye/status → online (retained)
seneye/state  → {"temperature_c":25.1,"ph":8.15,"nh3_mg_l":0.01,...}

	•	Integration Options → Backend = MQTT.
	•	Run seneye.connection_test.

⸻

Setup D – Windows USB/IP server (untested)

Using usbipd-win to share Seneye from Windows. Expected to work similarly to Pi USB/IP.

⸻

Setup E – Network USB hubs

If the hub exposes /dev/hidraw*, use HID backend.
If not, run the MQTT publisher on a companion PC.

⸻

Options & Services

Options (integration card):
	•	Backend (hid/mqtt)
	•	Update interval (min)
	•	Offsets (Temp/pH)
	•	PAR scale
	•	MQTT prefix

Services:
	•	seneye.force_update
	•	seneye.connection_test

⸻

Dashboards, Blueprints & Automations
	•	Dashboards: Standard, ApexCharts, Mushroom
	•	Blueprints: NH3 alert, pH alert, Data stale
	•	Install via scripts/install_dashboards.sh

⸻

Troubleshooting
	•	No entities: check backend setting, logs.
	•	HID not found: confirm /dev/hidraw* exists.
	•	MQTT no state: check broker creds, retained state at <prefix>/state.

⸻

Tested & Untested

✅ Direct USB (HID)
✅ Raspberry Pi MQTT publisher
❌ Raspberry Pi USB/IP (broken after HA OS updates)
⚠️ AquaPi MQTT publisher (expected)
⚠️ Windows USB/IP (expected)
⚠️ Network USB hubs

⸻

Contributing

PRs welcome! Bugfixes, docs, dashboards, new backends.

⸻

License

MIT
