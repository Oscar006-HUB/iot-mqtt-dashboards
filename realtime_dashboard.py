from collections import deque
import json
import threading
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import paho.mqtt.client as mqtt
import plotly.graph_objs as go

# ------------------------------------------------------------------------------
# Data Storage & Thread Lock Setup
# ------------------------------------------------------------------------------
MAX_LEN = 20
data_lock = threading.Lock()

sensor_buffers = {
    "temperature": deque(maxlen=MAX_LEN),
    "humidity": deque(maxlen=MAX_LEN),
    "light": deque(maxlen=MAX_LEN),
    "distance": deque(maxlen=MAX_LEN),
    "time": deque(maxlen=MAX_LEN),
}

# ------------------------------------------------------------------------------
# MQTT Callbacks & Client Configuration
# ------------------------------------------------------------------------------
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/RUNECRAFT/data"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))

        with data_lock:
            sensor_buffers["temperature"].append(payload.get("temperature", 0))
            sensor_buffers["humidity"].append(payload.get("humidity", 0))
            sensor_buffers["light"].append(payload.get("light", 0))
            sensor_buffers["distance"].append(payload.get("distance", 0))

            next_step = (
                (sensor_buffers["time"][-1] + 1)
                if sensor_buffers["time"]
                else 1
            )
            sensor_buffers["time"].append(next_step)
    except (json.JSONDecodeError, KeyError):
        pass


mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

# ------------------------------------------------------------------------------
# Dash Layout Setup
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)
app.title = "ESP32 Sensor Monitor"

METRICS = [
    ("temp-graph", "Temperature", "°C", "#FF5722"),
    ("humidity-graph", "Humidity", "%", "#2196F3"),
    ("light-graph", "Light Intensity", "Analog Value", "#FFEB3B"),
    ("distance-graph", "Distance", "cm", "#4CAF50"),
]

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "padding": "20px",
        "backgroundColor": "#f4f6f8",
    },
    children=[
        html.H2(
            "ESP32 Real-Time Sensor Dashboard",
            style={"textAlign": "center", "color": "#333"},
        ),
        dcc.Interval(id="interval-component", interval=3000, n_intervals=0),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "20px",
            },
            children=[
                dcc.Graph(id=graph_id) for graph_id, _, _, _ in METRICS
            ],
        ),
    ],
)

# ------------------------------------------------------------------------------
# Helper Function & Callbacks
# ------------------------------------------------------------------------------
def create_sensor_figure(x, y, title, unit, color):
    fig = go.Figure(
        data=[
            go.Scatter(
                x=x,
                y=y,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=6),
            )
        ]
    )
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.05),
        xaxis_title="Reading Sample",
        yaxis_title=unit,
        margin=dict(l=40, r=20, t=40, b=40),
        template="plotly_white",
    )
    return fig


@app.callback(
    [Output(graph_id, "figure") for graph_id, _, _, _ in METRICS],
    [Input("interval-component", "n_intervals")],
)
def update_graphs(n):
    # Lock data during read to avoid length mismatch with background MQTT thread
    with data_lock:
        time_list = list(sensor_buffers["time"])
        data_snapshots = {
            key: list(sensor_buffers[key])
            for key in ["temperature", "humidity", "light", "distance"]
        }

    figures = [
        create_sensor_figure(
            time_list,
            data_snapshots[key],
            title,
            unit,
            color,
        )
        for key, (graph_id, title, unit, color) in zip(
            ["temperature", "humidity", "light", "distance"], METRICS
        )
    ]
    return figures


if __name__ == "__main__":
    app.run(debug=True)