"""Constants for the Systemair SAVE Modbus RS485 integration."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "systemair_save_modbus_rs485"

CONF_PORT = "port"
CONF_BAUDRATE = "baudrate"
CONF_SLAVE_ADDRESS = "slave_address"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = "/dev/vsr500"
DEFAULT_BAUDRATE = 19200
DEFAULT_SLAVE_ADDRESS = 1
DEFAULT_SCAN_INTERVAL = 30

# Registers (Official 1-Indexed PDF Register Numbers)
# IR = Input Register (Read Only), HR = Holding Register (Read Write)
# In our hub implementation, we subtract 1 from these addresses for 0-indexed Modbus RTU requests.

# Sensors (Read-Only)
REG_DEMC_RH_HIGHEST = 1001              # IR
REG_DEMC_CO2_HIGHEST = 1002             # IR
REG_USERMODE_REMAINING_TIME_L = 1111    # IR
REG_USERMODE_REMAINING_TIME_H = 1112    # IR
REG_USERMODE_MODE = 1161                # IR
REG_SENSOR_OAT = 12102                  # IR (outside air temp)
REG_SENSOR_SAT = 12103                  # IR (supply air temp)
REG_SENSOR_OHT = 12108                  # IR (overheat temp)
REG_SENSOR_RGS = 12112                  # IR (rotating guard / rotor guard status)
REG_SENSOR_RHS_PDM = 12136              # IR (extract air relative humidity)
REG_SENSOR_RPM_SAF = 12401              # IR (supply air fan rpm)
REG_SENSOR_RPM_EAF = 12402              # IR (extract air fan rpm)
REG_SENSOR_FLOW_PIGGYBACK_SAF = 12403   # IR (piggyback sensor flow saf)
REG_SENSOR_FLOW_PIGGYBACK_EAF = 12404   # IR (piggyback sensor flow eaf)
REG_SENSOR_PDM_EAT_VALUE = 12544        # IR (extract air temp / PDM EAT)
REG_TC_SP_SATC = 2054                   # IR (calculated setpoint supply air)
REG_OUTPUT_Y1_ANALOG = 14101            # IR (heater analog output state)
REG_OUTPUT_Y1_DIGITAL = 14102           # IR (heater digital output state)
REG_TRIAC_CONTROL_SIGNAL = 14381        # IR (TRIAC control signal)
REG_FILTER_REMAINING_TIME_L = 7005      # IR (remaining filter time lower 16 bits)
REG_FILTER_REMAINING_TIME_H = 7006      # IR (remaining filter time upper 16 bits)

# Settings & Commands (Read Write / Holding Registers)
REG_TC_SP = 2001                        # HR (user temperature setpoint)
REG_USERMODE_HOLIDAY_TIME = 1101         # HR (Holiday user mode delay time, days)
REG_USERMODE_AWAY_TIME = 1102           # HR (maps to 1102 0-indexed away time / 1103 fireplace time in config)
REG_USERMODE_FIREPLACE_TIME = 1103      # HR (Fireplace user mode delay time, minutes)
REG_USERMODE_REFRESH_TIME = 1104        # HR (Refresh/Vädring user mode delay time, minutes)
REG_USERMODE_CROWDED_TIME = 1105        # HR (Crowded/Fest user mode delay time, hours)
REG_USERMODE_MANUAL_AIRFLOW_LEVEL_SAF = 1131 # HR (current manual / auto fan speed)
REG_USERMODE_HMI_CHANGE_REQUEST = 1162  # HR (HMI change request, e.g. brasläge / fireplace)
REG_RH_TRANSFER = 2147                  # HR (RH transfer)
REG_EXTRA_CONTROLLER_PREHEATER_SETPOINT_TYPE = 2418 # HR (Preheater setpoint type: 0 - Auto, 1 - Manual)
REG_EXTRA_CONTROLLER_PREHEATER_DEACTIVATE_AT_HIGH_OAT = 2427 # HR (Preheater deactivation status: 0 - Disabled, 1 - Enabled)
REG_EXTRA_CONTROLLER_PREHEATER_ACTIVATION_T = 2428 # HR (Preheater activation temperature)
REG_FILTER_PERIOD = 7001                # HR (filter replacement period in months)
REG_TRIAC_SHALL_BE_USED = 13201         # HR (triac shall be used flag)
