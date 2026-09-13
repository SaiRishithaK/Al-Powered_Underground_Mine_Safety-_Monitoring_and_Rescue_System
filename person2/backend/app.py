from flask import Flask, jsonify
import random

from ai.hazard_detection import detect_hazard
from drone.drone_controller import drone_response


app = Flask(__name__)


def generate_sensor_data():
    return {
        "oxygen": round(random.uniform(18, 21), 2),
        "temperature": round(random.uniform(25, 45), 2),
        "smoke": round(random.uniform(0, 100), 2),
        "methane": round(random.uniform(0, 10), 2),
        "humidity": round(random.uniform(40, 90), 2)
    }


@app.route("/")
def home():
    return "Underground Mine Safety Monitoring API is running"


@app.route("/monitor")
def monitor():

    sensor_data = generate_sensor_data()

    risk, hazards = detect_hazard(sensor_data)

    action = drone_response(risk)

    response = {
        "sensor_data": sensor_data,
        "detected_hazards": hazards,
        "risk_level": risk,
        "drone_action": action
    }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)