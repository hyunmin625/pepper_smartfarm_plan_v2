from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class AdapterTimeoutError(RuntimeError):
    """Raised when a sensor/device adapter exceeds its read budget."""


def default_value_for_field(field_name: str) -> Any:
    if "air_temp" in field_name or "outside_temp" in field_name or "solution_temp" in field_name or "water_temp" in field_name:
        return 24.5
    if "dry_room_temp" in field_name:
        return 31.0
    if "humidity" in field_name or "rh" in field_name:
        return 68.0
    if "co2" in field_name:
        return 820
    if "par" in field_name:
        return 650
    if "solar" in field_name:
        return 540
    if "moisture" in field_name:
        return 44.0
    if "ec" in field_name:
        return 2.3
    if "ph" in field_name:
        return 5.9
    if "volume" in field_name:
        return 3.5
    if "wind" in field_name:
        return 1.8
    if "rain" in field_name:
        return 0.0
    if "rgb_frame" in field_name:
        return f"mock://vision/{field_name}.jpg"
    return 1


@dataclass(frozen=True)
class AdapterContext:
    site_id: str
    measured_at: str
    override: dict[str, Any] | None = None


class BaseSensorAdapter:
    sensor_types: tuple[str, ...] = ()

    def supports(self, sensor_type: str) -> bool:
        return sensor_type in self.sensor_types

    def read(self, sensor: dict[str, Any], context: AdapterContext) -> dict[str, Any]:
        values = {
            field_name: default_value_for_field(field_name)
            for field_name in sensor["measurement_fields"]
        }
        return {
            "record_kind": "sensor",
            "site_id": context.site_id,
            "zone_id": sensor["zone_id"],
            "sensor_id": sensor["sensor_id"],
            "sensor_type": sensor["sensor_type"],
            "measured_at": context.measured_at,
            "protocol": sensor["protocol"],
            "transport_status": "ok",
            "calibration_due": False,
            "values": values,
        }

    def timeout_fallback(self, sensor: dict[str, Any], context: AdapterContext) -> dict[str, Any]:
        values = {field_name: None for field_name in sensor["measurement_fields"]}
        return {
            "record_kind": "sensor",
            "site_id": context.site_id,
            "zone_id": sensor["zone_id"],
            "sensor_id": sensor["sensor_id"],
            "sensor_type": sensor["sensor_type"],
            "measured_at": context.measured_at,
            "protocol": sensor["protocol"],
            "transport_status": "down",
            "calibration_due": False,
            "values": values,
        }


class TemperatureHumiditySensorAdapter(BaseSensorAdapter):
    sensor_types = ("air_temp_rh", "dry_room_temp_rh")


class Co2SensorAdapter(BaseSensorAdapter):
    sensor_types = ("co2",)


class LightSensorAdapter(BaseSensorAdapter):
    sensor_types = ("par",)


class MoistureSensorAdapter(BaseSensorAdapter):
    sensor_types = ("substrate_moisture",)


class EcPhSensorAdapter(BaseSensorAdapter):
    sensor_types = ("drain_ec_ph", "feed_ec_ph")


class TemperatureScalarSensorAdapter(BaseSensorAdapter):
    sensor_types = ("substrate_temp", "nutrient_solution_temp", "source_water_temp")


class OutsideWeatherSensorAdapter(BaseSensorAdapter):
    sensor_types = ("outside_weather",)


class VolumeCounterSensorAdapter(BaseSensorAdapter):
    sensor_types = ("drain_volume",)


class VisionFrameSensorAdapter(BaseSensorAdapter):
    sensor_types = ("crop_image_frame",)


class ProductMoistureSensorAdapter(BaseSensorAdapter):
    sensor_types = ("product_moisture",)


class SensorAdapterRegistry:
    def __init__(self) -> None:
        self._adapters = [
            TemperatureHumiditySensorAdapter(),
            Co2SensorAdapter(),
            LightSensorAdapter(),
            MoistureSensorAdapter(),
            EcPhSensorAdapter(),
            TemperatureScalarSensorAdapter(),
            OutsideWeatherSensorAdapter(),
            VolumeCounterSensorAdapter(),
            VisionFrameSensorAdapter(),
            ProductMoistureSensorAdapter(),
        ]

    def for_sensor(self, sensor: dict[str, Any]) -> BaseSensorAdapter:
        sensor_type = sensor["sensor_type"]
        for adapter in self._adapters:
            if adapter.supports(sensor_type):
                return adapter
        raise KeyError(f"no sensor adapter registered for sensor_type={sensor_type}")
