# IoT MQTT Dashboards

Python scripts that subscribe to ESP32 sensor telemetry over MQTT and display it on real-time Plotly Dash dashboards.

## Contents

| File | Description |
|------|-------------|
| `mqtt_server.py` | Flask + Dash dashboard for temperature, humidity, light and distance, with CSV export |
| `realtime_dashboard.py` | Thread-safe real-time Dash dashboard fed by a Paho MQTT subscriber |
| `lab.py` | Python list practice |
| `work.cpp` | C++ class practice (employee) |

## Running

```bash
pip install dash plotly flask paho-mqtt
python mqtt_server.py
```

Set `MQTT_BROKER` at the top of the script to your broker's IP address. The topic is `esp32/RUNECRAFT/data`.

---

Author: **Prince Oscar Mwinnuo** ([@Oscar006-HUB](https://github.com/Oscar006-HUB))
