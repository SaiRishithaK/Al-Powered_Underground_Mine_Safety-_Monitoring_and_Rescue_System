import unittest

from sensor_intelligence import SensorSimulator, evaluate_hazards


class SensorIntelligenceTests(unittest.TestCase):
    def test_normal_simulation_stays_below_demo_thresholds(self):
        simulator = SensorSimulator(seed=7)
        readings = [simulator.sample(index) for index in range(10)]

        self.assertTrue(all(not evaluate_hazards(reading) for reading in readings))

    def test_hazard_demo_emits_warning_records(self):
        simulator = SensorSimulator(seed=7, scenario="hazard-demo")
        simulator.sample(0)
        simulator.sample(1)
        readings = simulator.sample(2)

        hazards = evaluate_hazards(readings)

        self.assertEqual(
            {hazard["sensor"] for hazard in hazards},
            {"methane", "carbon_monoxide", "temperature"},
        )
        self.assertTrue(all(hazard["severity"] == "warning" for hazard in hazards))

    def test_critical_threshold_takes_precedence(self):
        hazards = evaluate_hazards(
            {
                "methane": 1.5,
                "carbon_monoxide": 100,
                "temperature": 40,
            }
        )

        self.assertEqual(len(hazards), 3)
        self.assertTrue(all(hazard["severity"] == "critical" for hazard in hazards))


if __name__ == "__main__":
    unittest.main()
