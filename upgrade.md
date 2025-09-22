# Upgrade / Migration Notes

## September 2025 Update

Recent changes in Home Assistant OS broke some previously working Seneye connection methods.  
Here’s the current status and how to migrate to the stable setup.

---

### ❌ USB/IP Bridge (Raspberry Pi → HA)
- **Status:** Broken after recent HA OS updates (kernel + USB/IP module changes).  
- **Impact:** Devices attached via USB/IP no longer appear as `/dev/hidraw*` inside HA.  
- **Recommendation:** Do not rely on this method going forward. Left in documentation for reference only.

---

### ⚠️ Direct USB (HID backend)
- **Status:** Flaky on some HA OS builds, depending on container permissions and udev rules.  
- **Recommendation:** Prefer MQTT instead. Only use HID if your HA host is bare-metal Linux and can see `/dev/hidraw*`.

---

### ✅ MQTT Publisher (Stable & Recommended)
- **Status:** Confirmed working and now the recommended backend.  
- **How it works:** A Raspberry Pi (or any Linux host) runs a lightweight Python daemon (`seneye_mqtt_daemon.py`) that:
  - Talks to the Seneye probe locally via `/dev/hidraw*`
  - Publishes JSON readings to MQTT (`seneye/state`, `seneye/status`)
- **Setup:** See [`mqtt_publisher/`](./mqtt_publisher/) for requirements, systemd unit, and udev rules.
- **In HA:** Configure the integration backend as `MQTT` with prefix `seneye`.

---

## Migration Steps (USB/IP → MQTT)

1. **On your Pi with the Seneye attached:**
   - Install the publisher daemon (see [`scripts/install.sh`](./scripts/install.sh))
   - Enable the `systemd` unit
   - Confirm you see MQTT topics:
     - `seneye/status` → `online`
     - `seneye/state` → JSON payload with `temperature_c`, `ph`, `nh3_mg_l`, etc.

2. **In Home Assistant:**
   - Open Seneye integration options → set backend to `MQTT`
   - Keep prefix as `seneye` (or adjust to match your publisher config)
   - Test with `seneye.connection_test` service call.

3. **Optional (Monitoring):**
   - Import the prebuilt automation that detects stale MQTT values (>1h) and triggers auto-recovery.

---

### Quick Topic Reference

- `seneye/status` → `"online"` (retained)
- `seneye/state` → JSON like:
  ```json
  {
    "temperature_c": 27.5,
    "ph": 8.17,
    "nh3_mg_l": 0.007,
    "lux": 12,
    "par": 0
  }

TL;DR
	•	USB/IP bridge = dead.
	•	Direct USB = unreliable.
	•	MQTT publisher = stable, recommended, future-proof.
