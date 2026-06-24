"""Support for Systemair SAVE Modbus RS485 Switches."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_USERMODE_HMI_CHANGE_REQUEST,
    REG_USERMODE_MODE,
    LOGGER,
)

@dataclass(frozen=True, kw_only=True)
class SystemairSwitchEntityDescription(SwitchEntityDescription):
    """Class describing Systemair switch entities."""

    hmi_val: int
    active_val: int

SWITCHES: tuple[SystemairSwitchEntityDescription, ...] = (
    SystemairSwitchEntityDescription(
        key="fireplace",
        name="Brasläge",
        hmi_val=5,
        active_val=4,
    ),
    SystemairSwitchEntityDescription(
        key="away",
        name="Borta",
        hmi_val=6,
        active_val=5,
    ),
    SystemairSwitchEntityDescription(
        key="holiday",
        name="Semester",
        hmi_val=7,
        active_val=6,
    ),
    SystemairSwitchEntityDescription(
        key="crowded",
        name="Fest",
        hmi_val=3,
        active_val=2,
    ),
    SystemairSwitchEntityDescription(
        key="refresh",
        name="Vädring",
        hmi_val=4,
        active_val=3,
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Systemair switches from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    hub = data["hub"]

    entities = [
        SystemairSwitch(coordinator, description, entry, hub)
        for description in SWITCHES
    ]
    async_add_entities(entities, True)

class SystemairSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Systemair Switch to toggle a user mode."""

    entity_description: SystemairSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: SystemairSwitchEntityDescription,
        entry: ConfigEntry,
        hub: Any,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._hub = hub
        self._entry = entry
        
        self._attr_unique_id = f"{entry.entry_id}_{description.key}_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="VSR500 Ventilation",
            manufacturer="Systemair",
            model="SAVE VSR 500",
        )

    @property
    def is_on(self) -> bool:
        """Return True if this specific user mode is active."""
        mode = self.coordinator.data.get(REG_USERMODE_MODE)
        return mode == self.entity_description.active_val

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn this user mode ON."""
        hmi_val = self.entity_description.hmi_val
        LOGGER.debug("Setting user mode to %s (writing %s to HMI change request)", self.entity_description.name, hmi_val)
        await self._hub.write_register(REG_USERMODE_HMI_CHANGE_REQUEST, hmi_val)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn this user mode OFF (reverts to Auto/Manual / writes 0)."""
        LOGGER.debug("Deactivating user mode %s (writing 0 to HMI change request)", self.entity_description.name)
        await self._hub.write_register(REG_USERMODE_HMI_CHANGE_REQUEST, 0)
        await self.coordinator.async_request_refresh()
