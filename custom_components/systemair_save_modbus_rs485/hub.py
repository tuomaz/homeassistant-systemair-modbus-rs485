"""Modbus Hub for Systemair SAVE Modbus RS485 integration."""
import asyncio
import inspect
from pymodbus.client import ModbusSerialClient
from .const import (
    LOGGER,
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
    REG_USERMODE_HOLIDAY_TIME,
    REG_USERMODE_AWAY_TIME,
    REG_USERMODE_FIREPLACE_TIME,
    REG_USERMODE_REFRESH_TIME,
    REG_USERMODE_CROWDED_TIME,
    REG_TC_SP,
    REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF,
    REG_USERMODE_HMI_CHANGE_REQUEST,
    REG_RH_TRANSFER,
    REG_EXTRA_CONTROLLER_PREHEATER_SETPOINT_TYPE,
    REG_EXTRA_CONTROLLER_PREHEATER_DEACTIVATE_AT_HIGH_OAT,
    REG_EXTRA_CONTROLLER_PREHEATER_ACTIVATION_T,
    REG_FILTER_PERIOD,
    REG_TRIAC_SHALL_BE_USED,
)

def _detect_slave_keyword(client: ModbusSerialClient) -> str:
    """Detect the correct keyword argument for the slave/unit address.

    pymodbus changed the parameter name across versions:
      - 2.x: 'unit'
      - 3.0-3.10: 'slave'
      - 3.11+: 'device_id'
    """
    sig = inspect.signature(client.read_holding_registers)
    params = sig.parameters
    for candidate in ("device_id", "slave", "unit"):
        if candidate in params:
            LOGGER.debug("Detected pymodbus slave keyword: %s", candidate)
            return candidate
    LOGGER.warning("Could not detect pymodbus slave keyword, defaulting to 'slave'")
    return "slave"

class SystemairSaveHub:
    """Wrapper class for pymodbus client interfacing with Systemair SAVE ventilation unit."""

    def __init__(self, port: str, baudrate: int, slave_address: int) -> None:
        """Initialize the Modbus hub."""
        self._port = port
        self._baudrate = baudrate
        self._slave = slave_address

        self._client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity="N",
            stopbits=1,
            bytesize=8,
            timeout=1,
        )
        self._lock = asyncio.Lock()
        self._slave_kw = _detect_slave_keyword(self._client)

    async def connect(self) -> bool:
        """Connect to the Modbus device."""
        async with self._lock:
            return await asyncio.to_thread(self._client.connect)

    async def close(self) -> None:
        """Close the Modbus connection."""
        async with self._lock:
            await asyncio.to_thread(self._client.close)

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read holding registers thread-safely. Subtracts 1 from 1-indexed address for 0-indexed modbus request."""
        zero_indexed_address = address - 1
        kwargs = {"address": zero_indexed_address, "count": count, self._slave_kw: self._slave}
        async with self._lock:
            result = await asyncio.to_thread(
                lambda: self._client.read_holding_registers(**kwargs)
            )
            if result.isError():
                LOGGER.error("Error reading registers at address %s: %s", address, result)
                raise Exception(f"Modbus error reading registers at address {address}: {result}")
            return result.registers

    async def write_register(self, address: int, value: int) -> None:
        """Write holding register thread-safely. Subtracts 1 from 1-indexed address for 0-indexed modbus request."""
        zero_indexed_address = address - 1
        kwargs = {"address": zero_indexed_address, "value": value, self._slave_kw: self._slave}
        async with self._lock:
            result = await asyncio.to_thread(
                lambda: self._client.write_register(**kwargs)
            )
            if result.isError():
                LOGGER.error("Error writing register %s value %s: %s", address, value, result)
                raise Exception(f"Modbus error writing register at {address}: {result}")

    async def async_update_data(self) -> dict:
        """Retrieve all register data in bulk blocks."""
        # Registers are queried using the contiguous blocks to minimize requests:
        
        # Block 1: 1001-1002 (RH highest, CO2 highest)
        block1 = await self.read_holding_registers(REG_DEMC_RH_HIGHEST, 2)
        
        # Block 2: 1101-1162 (Holiday, Away, Fireplace, Refresh, Crowded times, remaining user mode time, user manual fan speed, HMI mode change)
        # Note: 1162 - 1101 + 1 = 62 registers
        block2 = await self.read_holding_registers(REG_USERMODE_HOLIDAY_TIME, 62)
        
        # Block 3: 2054-2147 (Setpoint supply air, RH transfer)
        # Note: 2147 - 2054 + 1 = 94 registers
        block3 = await self.read_holding_registers(REG_TC_SP_SATC, 94)
        
        # Block 4: 7001-7006 (Filter replacement months, remaining filter time L/H)
        block4 = await self.read_holding_registers(REG_FILTER_PERIOD, 6)
        
        # Block 5: 12102-12136 (OAT, SAT, OHT, rotating guard RGS, relative humidity RHS)
        # Note: 12136 - 12102 + 1 = 35 registers
        block5 = await self.read_holding_registers(REG_SENSOR_OAT, 35)
        
        # Block 6: 12401-12404 (Fan RPMs, piggyback flow sensors)
        block6 = await self.read_holding_registers(REG_SENSOR_RPM_SAF, 4)
        
        # Block 7: 12544 (Extract air temperature PDM EAT)
        block7 = await self.read_holding_registers(REG_SENSOR_PDM_EAT_VALUE, 1)
        
        # Block 8: 13201 (Triac shall be used flag)
        block8 = await self.read_holding_registers(REG_TRIAC_SHALL_BE_USED, 1)
        
        # Block 9: 14101-14102 (Heater AO/DO states)
        block9 = await self.read_holding_registers(REG_OUTPUT_Y1_ANALOG, 2)
        
        # Block 10: 14381 (TRIAC control signal)
        block10 = await self.read_holding_registers(REG_TRIAC_CONTROL_SIGNAL, 1)
        
        # Block 11: 2001 (User temperature setpoint)
        block11 = await self.read_holding_registers(REG_TC_SP, 1)

        # Block 12: 2418-2428 (Preheater settings)
        # Note: 2428 - 2418 + 1 = 11 registers
        block12 = await self.read_holding_registers(REG_EXTRA_CONTROLLER_PREHEATER_SETPOINT_TYPE, 11)

        data = {
            # Block 1
            REG_DEMC_RH_HIGHEST: block1[0],
            REG_DEMC_CO2_HIGHEST: block1[1],
            
            # Block 2
            REG_USERMODE_HOLIDAY_TIME: block2[0], # 1101
            REG_USERMODE_AWAY_TIME: block2[1], # 1102
            REG_USERMODE_FIREPLACE_TIME: block2[2], # 1103
            REG_USERMODE_REFRESH_TIME: block2[3], # 1104
            REG_USERMODE_CROWDED_TIME: block2[4], # 1105
            REG_USERMODE_REMAINING_TIME_L: block2[10], # 1111
            REG_USERMODE_REMAINING_TIME_H: block2[11], # 1112
            REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF: block2[30], # 1131
            REG_USERMODE_MODE: block2[60], # 1161
            REG_USERMODE_HMI_CHANGE_REQUEST: block2[61], # 1162
            
            # Block 3
            REG_TC_SP_SATC: block3[0], # 2054
            REG_RH_TRANSFER: block3[93], # 2147
            
            # Block 4
            REG_FILTER_PERIOD: block4[0], # 7001
            REG_FILTER_REMAINING_TIME_L: block4[4], # 7005
            REG_FILTER_REMAINING_TIME_H: block4[5], # 7006
            
            # Block 5
            REG_SENSOR_OAT: block5[0], # 12102
            REG_SENSOR_SAT: block5[1], # 12103
            REG_SENSOR_OHT: block5[6], # 12108
            REG_SENSOR_RGS: block5[10], # 12112
            REG_SENSOR_RHS_PDM: block5[34], # 12136
            
            # Block 6
            REG_SENSOR_RPM_SAF: block6[0], # 12401
            REG_SENSOR_RPM_EAF: block6[1], # 12402
            REG_SENSOR_FLOW_PIGGYBACK_SAF: block6[2], # 12403
            REG_SENSOR_FLOW_PIGGYBACK_EAF: block6[3], # 12404
            
            # Block 7
            REG_SENSOR_PDM_EAT_VALUE: block7[0], # 12544
            
            # Block 8
            REG_TRIAC_SHALL_BE_USED: block8[0], # 13201
            
            # Block 9
            REG_OUTPUT_Y1_ANALOG: block9[0], # 14101
            REG_OUTPUT_Y1_DIGITAL: block9[1], # 14102
            
            # Block 10
            REG_TRIAC_CONTROL_SIGNAL: block10[0], # 14381

            # Block 11
            REG_TC_SP: block11[0], # 2001

            # Block 12
            REG_EXTRA_CONTROLLER_PREHEATER_SETPOINT_TYPE: block12[0], # 2418
            REG_EXTRA_CONTROLLER_PREHEATER_DEACTIVATE_AT_HIGH_OAT: block12[9], # 2427
            REG_EXTRA_CONTROLLER_PREHEATER_ACTIVATION_T: block12[10], # 2428
        }
        
        return data
