"""Support for the Systemair SAVE Modbus RS485 Climate platform."""
from __future__ import annotations

from typing import Any
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_TC_SP,
    REG_SENSOR_SAT,
    REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF,
    REG_USERMODE_MODE,
    REG_USERMODE_HMI_CHANGE_REQUEST,
    LOGGER,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Systemair Modbus RS485 Climate platform."""
    data = hass.data[DOMAIN][entry.entry_id]
    hub = data["hub"]
    coordinator = data["coordinator"]

    async_add_entities([SystemairClimate(coordinator, hub, entry)], True)

class SystemairClimate(CoordinatorEntity, ClimateEntity):
    """Climate entity for Systemair SAVE VSR-500."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_min_temp = 12.0
    _attr_max_temp = 30.0

    _attr_fan_modes = ["low", "medium", "high"]
    _attr_hvac_modes = [HVACMode.FAN_ONLY, HVACMode.OFF]
    _attr_preset_modes = [
        "auto",
        "manual",
        "crowded",
        "refresh",
        "fireplace",
        "away",
        "holiday",
    ]

    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.PRESET_MODE
    )

    _preset_map_mode = {
        0: "auto",
        1: "manual",
        2: "crowded",
        3: "refresh",
        4: "fireplace",
        5: "away",
        6: "holiday",
        7: "cooker_hood",
        8: "vacuum_cleaner",
        12: "pressure_guard",
    }

    _preset_map_hmi = {
        "auto": 1,
        "manual": 2,
        "crowded": 3,
        "refresh": 4,
        "fireplace": 5,
        "away": 6,
        "holiday": 7,
    }

    def __init__(self, coordinator, hub, entry) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._hub = hub
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="VSR500 Ventilation",
            manufacturer="Systemair",
            model="SAVE VSR 500",
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature (supply air temperature)."""
        temp = self.coordinator.data.get(REG_SENSOR_SAT)
        if temp is not None:
            if temp > 32767:
                temp -= 65536
            return temp / 10.0
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the target user temperature setpoint."""
        temp = self.coordinator.data.get(REG_TC_SP)
        if temp is not None:
            if temp > 32767:
                temp -= 65536
            return temp / 10.0
        return None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current HVAC mode."""
        fan_speed = self.coordinator.data.get(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF)
        if fan_speed == 0:
            return HVACMode.OFF
        return HVACMode.FAN_ONLY

    @property
    def fan_mode(self) -> str:
        """Return the current fan mode."""
        val = self.coordinator.data.get(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF)
        if val == 2:
            return "low"
        if val == 3:
            return "medium"
        if val == 4:
            return "high"
        return "low"

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target HVAC mode."""
        LOGGER.debug("Setting HVAC mode to: %s", hvac_mode)
        if hvac_mode == HVACMode.OFF:
            # Turn OFF (write 0 to fan speed register)
            await self._hub.write_register(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF, 0)
        else:
            # Turn ON to normal / medium speed (write 3)
            await self._hub.write_register(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF, 3)
        await self.coordinator.async_request_refresh()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new target fan mode."""
        LOGGER.debug("Setting fan mode to: %s", fan_mode)
        if fan_mode == "low":
            await self._hub.write_register(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF, 2)
        elif fan_mode == "medium":
            await self._hub.write_register(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF, 3)
        elif fan_mode == "high":
            await self._hub.write_register(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF, 4)
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target setpoint temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        target_val = int(round(temperature * 10))
        LOGGER.debug("Setting User setpoint to %s (°C * 10: %s)", temperature, target_val)
        await self._hub.write_register(REG_TC_SP, target_val)
        await self.coordinator.async_request_refresh()

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        mode = self.coordinator.data.get(REG_USERMODE_MODE)
        return self._preset_map_mode.get(mode)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode not in self._preset_map_hmi:
            LOGGER.warning("Preset mode %s is read-only or unsupported", preset_mode)
            return
        val = self._preset_map_hmi[preset_mode]
        LOGGER.debug("Setting User Mode request to preset %s (writing %s)", preset_mode, val)
        await self._hub.write_register(REG_USERMODE_HMI_CHANGE_REQUEST, val)
        await self.coordinator.async_request_refresh()
