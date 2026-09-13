import random

from ai.hazard_detection import detect_hazard

def drone_response(risk_level):

    if risk_level == "NORMAL":
        action = "Continue routine patrol"

    elif risk_level == "WARNING":
        action = "Investigate hazardous area"

    elif risk_level == "CRITICAL":
        action = "Start emergency inspection and alert rescue team"

    else:
        action = "Unknown risk level"

    return action


if __name__ == "__main__":

    sensor_data = {
        "oxygen": round(random.uniform(18, 21), 2),
        "temperature": round(random.uniform(25, 45), 2),
        "smoke": round(random.uniform(0, 100), 2),
        "methane": round(random.uniform(0, 10), 2),
        "humidity": round(random.uniform(40, 90), 2)
    }

    risk, hazards = detect_hazard(sensor_data)

    action = drone_response(risk)

    print("\n===== UNDERGROUND MINE MONITORING =====")

    print("\nSensor Data:")
    for sensor, value in sensor_data.items():
        print(f"{sensor.capitalize():12}: {value}")

    print("\nDetected Hazards:", hazards)
    print("Risk Level      :", risk)
    print("Drone Action    :", action)