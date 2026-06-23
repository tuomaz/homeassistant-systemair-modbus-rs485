"""Support for Systemair SAVE Modbus RS485 Sensors."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime, PERCENTAGE, CONCENTRATION_PARTS_PER_MILLION
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_DEMC_RH_HIGHEST,
    REG_DEMC_CO2_HIGHEST,
    REG_USERMODE_REMAINING_TIME_L,
    REG_USERMODE_REMAINING_TIME_H,
    REG_USERMODE_MODE,
    REG_SENSOR_OAT,
    REG_SENSOR_SAT,
    REG_SENSOR_OHT,
    REG_SENSOR_RGS,
    REG_SENSOR_RHS_PDM,
    REG_SENSOR_RPM_SAF,
    REG_SENSOR_RPM_EAF,
    REG_SENSOR_FLOW_PIGGYBACK_SAF,
    REG_SENSOR_FLOW_PIGGYBACK_EAF,
    REG_SENSOR_PDM_EAT_VALUE,
    REG_TC_SP_SATC,
    REG_OUTPUT_Y1_ANALOG,
    REG_OUTPUT_Y1_DIGITAL,
    REG_TRIAC_CONTROL_SIGNAL,
    REG_FILTER_REMAINING_TIME_L,
    REG_FILTER_REMAINING_TIME_H,
    REG_USERMODE_AWAY_TIME,
    REG_USERMODE_FIREPLACE_TIME,
    REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF,
    REG_RH_TRANSFER,
    REG_FILTER_PERIOD,
    REG_TRIAC_SHALL_BE_USED,
)

@dataclass(frozen=True, kw_only=True)
class SystemairSensorEntityDescription(SensorEntityDescription):
    """Class describing Systemair sensor entities."""

    value_fn: Callable[[dict, Any], float | int | str | None]

def get_temp_value(data: dict, register: int) -> float | None:
    """Helper to convert registered Celsius * 10 to float."""
    val = data.get(register)
    if val is None:
        return None
    if val > 32767:
        val -= 65536
    return val / 10.0

SENSORS: tuple[SystemairSensorEntityDescription, ...] = (
    # Temperature Sensors
    SystemairSensorEntityDescription(
        key="outdoor_air_temperature",
        name="VSR500 outdoor air temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: get_temp_value(data, REG_SENSOR_OAT),
    ),
    SystemairSensorEntityDescription(
        key="supply_air_temperature",
        name="VSR500 supply air temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: get_temp_value(data, REG_SENSOR_SAT),
    ),
    SystemairSensorEntityDescription(
        key="overheat_temperature",
        name="VSR500 overheat temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: get_temp_value(data, REG_SENSOR_OHT),
    ),
    SystemairSensorEntityDescription(
        key="pdm_eat",
        name="VSR500 PDM EAT",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: get_temp_value(data, REG_SENSOR_PDM_EAT_VALUE),
    ),
    SystemairSensorEntityDescription(
        key="set_point_supply_air",
        name="VSR500 set point supply air",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: get_temp_value(data, REG_TC_SP_SATC),
    ),

    # Fan & RPM Sensors
    SystemairSensorEntityDescription(
        key="supply_air_fan_rpm",
        name="VSR500 supply air fan rpm",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: data.get(REG_SENSOR_RPM_SAF),
    ),
    SystemairSensorEntityDescription(
        key="extract_air_fan",
        name="VSR500 extract air fan",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: data.get(REG_SENSOR_RPM_EAF),
    ),

    # Humidity & CO2
    SystemairSensorEntityDescription(
        key="pdm_rhs",
        name="VSR500 PDM RHS",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: data.get(REG_SENSOR_RHS_PDM),
    ),
    SystemairSensorEntityDescription(
        key="max_rhs",
        name="VSR500 max RHS",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: data.get(REG_DEMC_RH_HIGHEST),
    ),
    SystemairSensorEntityDescription(
        key="max_co2",
        name="VSR500 max CO2",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: data.get(REG_DEMC_CO2_HIGHEST),
    ),

    # Durations & Runtimes (32-bit registers)
    SystemairSensorEntityDescription(
        key="remaining_filter_time",
        name="VSR500 remaning filter time",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: (data.get(REG_FILTER_REMAINING_TIME_H, 0) * 65536) + data.get(REG_FILTER_REMAINING_TIME_L, 0),
    ),
    SystemairSensorEntityDescription(
        key="time_remaining_user_mode",
        name="VSR500 time remaining user mode",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, hub: (data.get(REG_USERMODE_REMAINING_TIME_H, 0) * 65536) + data.get(REG_USERMODE_REMAINING_TIME_L, 0),
    ),

    # Delay settings & configurations
    SystemairSensorEntityDescription(
        key="time_delay_fireplace",
        name="VSR500 time delay setting for user mode fire place",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=lambda data, hub: data.get(REG_USERMODE_AWAY_TIME),
    ),
    SystemairSensorEntityDescription(
        key="current_user_mode",
        name="VSR500 current user mode",
        value_fn=lambda data, hub: data.get(REG_USERMODE_MODE),
    ),
    SystemairSensorEntityDescription(
        key="current_auto_fan_speed",
        name="VSR500 current auto fan speed",
        value_fn=lambda data, hub: data.get(REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF),
    ),
    SystemairSensorEntityDescription(
        key="filter_replacement_period",
        name="VSR500 filter replacement time in months",
        native_unit_of_measurement="months",
        value_fn=lambda data, hub: data.get(REG_FILTER_PERIOD),
    ),

    # Flow & Analog Output Sensors
    SystemairSensorEntityDescription(
        key="rotating_guard",
        name="VSR500 rotating guard",
        value_fn=lambda data, hub: data.get(REG_SENSOR_RGS),
    ),
    SystemairSensorEntityDescription(
        key="flow_piggyback_saf",
        name="VSR500 flow value piggy back sensor saf",
        value_fn=lambda data, hub: data.get(REG_SENSOR_FLOW_PIGGYBACK_SAF),
    ),
    SystemairSensorEntityDescription(
        key="flow_piggyback_eaf",
        name="VSR500 flow value piggy back sensor eaf",
        value_fn=lambda data, hub: data.get(REG_SENSOR_FLOW_PIGGYBACK_EAF),
    ),
    SystemairSensorEntityDescription(
        key="triac_control_signal",
        name="VSR500 TRIAC control signal",
        value_fn=lambda data, hub: data.get(REG_TRIAC_CONTROL_SIGNAL),
    ),
    SystemairSensorEntityDescription(
        key="heater_ao_state",
        name="VSR500 heater AO state",
        value_fn=lambda data, hub: data.get(REG_OUTPUT_Y1_ANALOG),
    ),
    SystemairSensorEntityDescription(
        key="heater_do_state",
        name="VSR500 heater DO state",
        value_fn=lambda data, hub: data.get(REG_OUTPUT_Y1_DIGITAL),
    ),
    SystemairSensorEntityDescription(
        key="rh_transfer",
        name="VSR500 RH transfer",
        value_fn=lambda data, hub: data.get(REG_RH_TRANSFER),
    ),
    SystemairSensorEntityDescription(
        key="triac_shall_be_used",
        name="Triac shall be used",
        value_fn=lambda data, hub: data.get(REG_TRIAC_SHALL_BE_USED),
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Systemair sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    hub = data["hub"]

    entities = [
        SystemairSensor(coordinator, description, entry, hub)
        for description in SENSORS
    ]
    async_add_entities(entities, True)

class SystemairSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Systemair Sensor."""

    entity_description: SystemairSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: SystemairSensorEntityDescription,
        entry: ConfigEntry,
        hub: Any,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._hub = hub
        
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="VSR500 Ventilation",
            manufacturer="Systemair",
            model="SAVE VSR 500",
        )

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data, self._hub)
