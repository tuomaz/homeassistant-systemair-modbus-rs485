"""Support for Systemair SAVE Modbus RS485 Switches."""
from __future__ import annotations

from typing import Any
from homeassistant.components.switch import SwitchEntity
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

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Systemair switches from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    hub = data["hub"]

    async_add_entities([SystemairFireplaceSwitch(coordinator, hub, entry)], True)

class SystemairFireplaceSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to toggle Fireplace Mode (brasläge) on Systemair SAVE."""

    _attr_has_entity_name = True
    _attr_name = "VSR500 brasläge"

    def __init__(self, coordinator, hub, entry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._hub = hub
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_fireplace_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="VSR500 Ventilation",
            manufacturer="Systemair",
            model="SAVE VSR 500",
        )

    @property
    def is_on(self) -> bool:
        """Return True if fireplace mode is active."""
        # Active mode 4 is Fireplace in REG_USERMODE_MODE (0-indexed 1161)
        mode = self.coordinator.data.get(REG_USERMODE_MODE)
        return mode == 4

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn fireplace mode ON."""
        LOGGER.debug("Turning fireplace mode ON (writing 5 to change request)")
        await self._hub.write_register(REG_USERMODE_HMI_CHANGE_REQUEST, 5)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn fireplace mode OFF."""
        LOGGER.debug("Turning fireplace mode OFF (writing 0 to change request)")
        await self._hub.write_register(REG_USERMODE_HMI_CHANGE_REQUEST, 0)
        await self.coordinator.async_request_refresh()
