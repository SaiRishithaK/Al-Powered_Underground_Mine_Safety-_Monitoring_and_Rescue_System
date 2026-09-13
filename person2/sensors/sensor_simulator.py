import random
import time

from ai.hazard_detection import detect_hazard


def read_sensors():
    data = {
        "oxygen": round(random.uniform(18, 21), 2),
        "temperature": round(random.uniform(25, 45), 2),
        "smoke": round(random.uniform(0, 100), 2),
        "methane": round(random.uniform(0, 10), 2),
        "humidity": round(random.uniform(40, 90), 2)
    }

    return data


while True:
    sensor_data = read_sensors()

    risk, hazards = detect_hazard(sensor_data)

    print("\n--- Mine Sensor Data ---")
    print("Oxygen      :", sensor_data["oxygen"], "%")
    print("Temperature :", sensor_data["temperature"], "°C")
    print("Smoke       :", sensor_data["smoke"])
    print("Methane     :", sensor_data["methane"], "%")
    print("Humidity    :", sensor_data["humidity"], "%")

    print("Risk Level  :", risk)
    print("Hazards     :", hazards)

    time.sleep(3)