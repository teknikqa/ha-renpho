"""Sensors for the latest Renpho measurement."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .api import timestamp
from .const import DOMAIN
from .coordinator import RenphoConfigEntry, RenphoCoordinator

PARALLEL_UPDATES = 0

MEASURED_AT = "measured_at"


def _mass(key: str, translation_key: str | None = None) -> SensorEntityDescription:
    # Renpho stores kilograms; the weight device class lets each user pick lb or st.
    return SensorEntityDescription(
        key=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    )


def _metric(
    key: str, translation_key: str, unit: str | None = None, *, enabled: bool = True
) -> SensorEntityDescription:
    return SensorEntityDescription(
        key=key,
        translation_key=translation_key,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=enabled,
    )


# key is the field name in the API record.
SENSORS = (
    _mass("weight"),
    _metric("bmi", "bmi"),
    _metric("bodyfat", "body_fat", PERCENTAGE),
    _metric("water", "body_water", PERCENTAGE),
    _metric("muscle", "skeletal_muscle", PERCENTAGE),
    _metric("protein", "protein", PERCENTAGE),
    _metric("subfat", "subcutaneous_fat", PERCENTAGE),
    _metric("visfat", "visceral_fat"),
    _metric("bmr", "bmr", "kcal/d"),
    _metric("bodyage", "body_age", UnitOfTime.YEARS),
    # Confirmed on a live record: fatFreeWeight = sinew + bone, all in kg.
    _mass("sinew", "muscle_mass"),
    _mass("bone", "bone_mass"),
    _mass("fatFreeWeight", "fat_free_weight"),
    # Only some scales measure these.
    _metric("heartRate", "heart_rate", "bpm", enabled=False),
    _metric("cardiacIndex", "cardiac_index", enabled=False),
    SensorEntityDescription(
        key=MEASURED_AT,
        translation_key="last_measurement",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RenphoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the sensors for one Renpho account."""
    async_add_entities(RenphoSensor(entry.runtime_data, desc) for desc in SENSORS)


class RenphoSensor(CoordinatorEntity[RenphoCoordinator], SensorEntity):
    """One field of the newest measurement."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: RenphoCoordinator, description: SensorEntityDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(entry.unique_id))},
            name=entry.title,
            manufacturer="Renpho",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | datetime | None:
        record = self.coordinator.data
        if not record:
            return None
        if self.entity_description.key == MEASURED_AT:
            ts = timestamp(record)
            return dt_util.utc_from_timestamp(ts) if ts else None
        try:
            # Renpho reports 0 for anything the scale did not measure.
            return float(record.get(self.entity_description.key)) or None
        except (TypeError, ValueError):
            return None
