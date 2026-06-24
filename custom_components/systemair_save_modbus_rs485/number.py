"""Support for Systemair SAVE Modbus RS485 Numbers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_USERMODE_HOLIDAY_TIME,
    REG_USERMODE_AWAY_TIME,
    REG_USERMODE_FIREPLACE_TIME,
    REG_USERMODE_REFRESH_TIME,
    REG_USERMODE_CROWDED_TIME,
    LOGGER,
)

@dataclass(frozen=True, kw_only=True)
class SystemairNumberEntityDescription(NumberEntityDescription):
    """Class describing Systemair number entities."""

    register: int

NUMBERS: tuple[SystemairNumberEntityDescription, ...] = (
    SystemairNumberEntityDescription(
        key="holiday_time",
        name="Semester varaktighet",
        register=REG_USERMODE_HOLIDAY_TIME,
        native_min_value=1,
        native_max_value=365,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    SystemairNumberEntityDescription(
        key="away_time",
        name="Borta varaktighet",
        register=REG_USERMODE_AWAY_TIME,
        native_min_value=1,
        native_max_value=72,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
    ),
    SystemairNumberEntityDescription(
        key="fireplace_time",
        name="Brasläge varaktighet",
        register=REG_USERMODE_FIREPLACE_TIME,
        native_min_value=1,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SystemairNumberEntityDescription(
        key="refresh_time",
        name="Vädring varaktighet",
        register=REG_USERMODE_REFRESH_TIME,
        native_min_value=1,
        native_max_value=240,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SystemairNumberEntityDescription(
        key="crowded_time",
        name="Fest varaktighet",
        register=REG_USERMODE_CROWDED_TIME,
        native_min_value=1,
        native_max_value=8,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Systemair numbers from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    hub = data["hub"]

    entities = [
        SystemairNumber(coordinator, description, entry, hub)
        for description in NUMBERS
    ]
    async_add_entities(entities, True)

class SystemairNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Systemair Number entity."""

    entity_description: SystemairNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: SystemairNumberEntityDescription,
        entry: ConfigEntry,
        hub: Any,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._hub = hub
        self._entry = entry

        self._attr_unique_id = f"{entry.entry_id}_{description.key}_number"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="VSR500 Ventilation",
            manufacturer="Systemair",
            model="SAVE VSR 500",
        )

    @property
    def native_value(self) -> float | None:
        """Return the value of the number."""
        val = self.coordinator.data.get(self.entity_description.register)
        if val is not None:
            return float(val)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        target_val = int(value)
        LOGGER.debug(
            "Setting number %s to %s (writing %s to register %s)",
            self.entity_description.name,
            value,
            target_val,
            self.entity_description.register,
        )
        await self._hub.write_register(self.entity_description.register, target_val)
        await self.coordinator.async_request_refresh()
