def detect_hazard(sensor_data):

    oxygen = sensor_data["oxygen"]
    temperature = sensor_data["temperature"]
    smoke = sensor_data["smoke"]
    methane = sensor_data["methane"]

    hazards = []

    if oxygen < 19.5:
        hazards.append("Low Oxygen")

    if temperature > 40:
        hazards.append("High Temperature")

    if smoke > 70:
        hazards.append("High Smoke")

    if methane > 5:
        hazards.append("High Methane")

    if len(hazards) == 0:
        risk = "NORMAL"
    elif len(hazards) <= 2:
        risk = "WARNING"
    else:
        risk = "CRITICAL"

    return risk, hazards


if __name__ == "__main__":

    sample_data = {
        "oxygen": 18.43,
        "temperature": 44.32,
        "smoke": 50.86,
        "methane": 3.87,
        "humidity": 70.01
    }

    risk, hazards = detect_hazard(sample_data)

    print("Risk Level:", risk)
    print("Detected Hazards:", hazards)