#!/bin/bash
set -e

echo "[+] Creating venv..."
python3 -m venv ~/seneye-venv

echo "[+] Installing requirements..."
~/seneye-venv/bin/pip install -U pip
~/seneye-venv/bin/pip install -r requirements.txt

echo "[+] Copying udev rule..."
sudo cp udev/99-seneye-hidraw.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger

echo "[+] Installing systemd service..."
sudo cp systemd/seneye-mqtt.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now seneye-mqtt.service

echo "[✓] Done. Seneye MQTT service installed and started."
