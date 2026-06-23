# Home Assistant Systemair SAVE Modbus RS485 Integration

A custom Home Assistant integration to control and monitor Systemair SAVE (e.g. VSR-500) ventilation units over Modbus RTU serial (RS-485).

This integration is completely asynchronous, UI-configurable, and exposes the ventilation unit as a unified Climate entity, along with diagnostic sensors and manual mode switches. It runs under the custom domain `systemair_save_modbus_rs485` to avoid conflicts with other TCP-based Systemair Modbus integrations.

## Features

- **Climate Entity (`climate.systemair_save_modbus_rs485`)**:
  - Exposes `fan_only` and `off` modes.
  - Temperature setpoint control (maps to user temperature setpoint `REG_TC_SP`).
  - Fan speed control (`low`, `medium`, `high`) corresponding to manual airflow speed settings.
  - Real-time supply air temperature (`REG_SENSOR_SAT`).
- **Diagnostic Sensors (`sensor.vsr500_*`)**:
  - Outdoor Air Temperature (`REG_SENSOR_OAT`)
  - Supply Air Temperature (`REG_SENSOR_SAT`)
  - Overheat Temperature (`REG_SENSOR_OHT`)
  - Extract Air Temperature / PDM EAT (`REG_SENSOR_PDM_EAT_VALUE`)
  - Setpoint Supply Air / Calculated Setpoint (`REG_TC_SP_SATC`)
  - Fan Speed RPMs (Supply fan RPM and Extract fan RPM)
  - Relative Humidity and CO2 values (extract humidity, highest relative humidity, highest CO2)
  - Filter replacement periods and remaining filter duration (in seconds and months)
  - Heat exchanger rotating guard status
  - TRIAC control signals and heater analog/digital output states
- **Manual Mode Toggle (`switch.vsr500_braslage`)**:
  - A switch to toggle **Fireplace Mode** (brasläge). Turns on by writing `5` to the HMI change request register and checks the active user mode register to report state.

## Installation

1. Copy the `custom_components/systemair_save_modbus_rs485` directory into your Home Assistant `config/custom_components/` folder.
2. Restart Home Assistant.
3. Go to **Settings -> Devices & Services -> Add Integration** and search for `Systemair SAVE Modbus RS485`.
4. Enter your connection settings:
   - **Serial Port:** (e.g., `/dev/vsr500`)
   - **Baud Rate:** 19200 (default)
   - **Modbus Slave Address (Unit ID):** 1 (default)
   - **Polling Interval (seconds):** 30 (default)

## License
MIT License.
