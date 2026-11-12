"""Simulated mine-environment readings and configurable hazard thresholds."""
from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class Threshold:
    warning: float
    critical: float
    unit: str

    def __post_init__(self) -> None:
        if self.warning < 0 or self.critical <= self.warning:
            raise ValueError("Thresholds must be non-negative and critical > warning.")


DEFAULT_THRESHOLDS = {
    "methane": Threshold(warning=1.0, critical=1.5, unit="% vol (demo)"),
    "carbon_monoxide": Threshold(warning=50.0, critical=100.0, unit="ppm"),
    "temperature": Threshold(warning=35.0, critical=40.0, unit="°C"),
}


class SensorSimulator:
    """Generate repeatable, synthetic readings for pipeline demonstrations."""

    def __init__(self, seed: int = 42, scenario: str = "normal") -> None:
        if scenario not in {"normal", "hazard-demo"}:
            raise ValueError("scenario must be 'normal' or 'hazard-demo'.")
        self._random = random.Random(seed)
        self._scenario = scenario
        self._sample_index = 0
        self._methane = self._random.uniform(0.1, 0.4)
        self._carbon_monoxide = self._random.uniform(3.0, 15.0)
        self._temperature = self._random.uniform(23.0, 29.0)

    def sample(self, timestamp_seconds: float) -> dict[str, float]:
        """Return one synthetic reading set at the given video-relative time."""
        self._methane = min(0.8, max(0.05, self._methane + self._random.uniform(-0.08, 0.08)))
        self._carbon_monoxide = min(
            35.0, max(0.0, self._carbon_monoxide + self._random.uniform(-3.0, 3.0))
        )
        self._temperature = min(
            33.0, max(18.0, self._temperature + self._random.uniform(-0.5, 0.5))
        )

        values = {
            "timestamp_seconds": round(timestamp_seconds, 3),
            "methane": round(self._methane, 3),
            "carbon_monoxide": round(self._carbon_monoxide, 2),
            "temperature": round(self._temperature, 2),
        }
        if self._scenario == "hazard-demo" and self._sample_index == 2:
            values.update(methane=1.2, carbon_monoxide=60.0, temperature=36.0)

        self._sample_index += 1
        return values


def evaluate_hazards(
    readings: dict[str, float],
    thresholds: dict[str, Threshold] | None = None,
) -> list[dict[str, str | float]]:
    """Return one hazard record per sensor reading that crosses a threshold."""
    active_thresholds = DEFAULT_THRESHOLDS if thresholds is None else thresholds
    hazards: list[dict[str, str | float]] = []
    for sensor_name, threshold in active_thresholds.items():
        value = readings[sensor_name]
        if value >= threshold.critical:
            level, crossed_threshold = "critical", threshold.critical
        elif value >= threshold.warning:
            level, crossed_threshold = "warning", threshold.warning
        else:
            continue
        hazards.append(
            {
                "sensor": sensor_name,
                "value": value,
                "unit": threshold.unit,
                "severity": level,
                "threshold": crossed_threshold,
            }
        )
    return hazards
