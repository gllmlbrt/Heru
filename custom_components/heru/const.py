"""Constants for the Heru integration."""

DOMAIN = "heru"
DEFAULT_NAME = "Heru"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
UPDATE_INTERVAL_SECONDS = 15

CONF_DEVICE_ID = "device_id"
CONF_FRAMER = "framer"

FRAMER_SOCKET = "socket"
FRAMER_RTU = "rtu"
DEFAULT_FRAMER = FRAMER_SOCKET
FRAMER_OPTIONS = [FRAMER_SOCKET, FRAMER_RTU]

# 1x00005 - 1x00009 are not implemented on the HERU Gen 3. Reading straight
# across that gap makes the unit reject the whole request with "illegal data
# address", so the discrete inputs are fetched as two contiguous blocks of
# (address, count) and reassembled into one 34-entry list.
DISCRETE_INPUT_COUNT = 34
DISCRETE_INPUT_BLOCKS = ((0, 4), (9, 25))

# Coils 0x00001 - 0x00006 are contiguous and read/write. The last two are
# momentary: they act on write and always read back 0.
COIL_COUNT = 6
COIL_UNIT_ON = 0
COIL_OVERPRESSURE_MODE = 1
COIL_BOOST_MODE = 2
COIL_AWAY_MODE = 3
COIL_CLEAR_ALARMS = 4
COIL_RESET_FILTER_TIMER = 5

# Temperatures are reported in tenths of a degree as signed 16-bit values.
TEMPERATURE_SCALE = 0.1

# Heating, cooling and recovery power are reported over a 0-255 range.
POWER_255_TO_PERCENT = 100 / 255

# 4x00001 takes 0 = Off and steps 1-4. The manual names them Min/Std/Mod/Max;
# the step numbers are used here so they line up with the unit's own display.
FAN_STEP_OPTIONS = ["off", "1", "2", "3", "4"]

# Configuration holding registers 4x00003 - 4x00069, read as one optional
# block. The "connected" flags describe which hardware is fitted: the unit
# marks a temperature sensor as required based on them and raises an
# open-circuit alarm when a flag is set but no sensor is present.
HOLDING_CONFIG_START = 2
HOLDING_CONFIG_COUNT = 67

HOLDING_REGISTER_SUPPLY_FAN_SPEED_EC = 2  # 4x00003, percent
HOLDING_REGISTER_EXHAUST_FAN_SPEED_EC = 3  # 4x00004, percent
HOLDING_REGISTER_WEEKTIMER_ENABLE = 68  # 4x00069
HOLDING_REGISTER_SNC_ENABLE = 15  # 4x00016, summer night cooling
HOLDING_REGISTER_FREEZE_PROTECTION_LIMIT = 16  # 4x00017
HOLDING_REGISTER_WATER_HEATER_CONNECTED = 49  # 4x00050, requires sensor T5
HOLDING_REGISTER_ELECTRIC_HEATER_CONNECTED = 50  # 4x00051
HOLDING_REGISTER_COOLER_CONNECTED = 51  # 4x00052

FREEZE_PROTECTION_LIMIT_MIN = 5
FREEZE_PROTECTION_LIMIT_MAX = 10

HOLDING_REGISTER_USER_FAN_SPEED = 0
HOLDING_REGISTER_TEMPERATURE_SETPOINT = 1
INPUT_REGISTER_ROOM_TEMPERATURE = 7
# Air drawn out of the house, before the heat exchanger. This is the unit's
# measure of indoor temperature - waste air is the same air after heat
# recovery, so it tracks the outdoor side instead.
INPUT_REGISTER_EXHAUST_AIR_TEMPERATURE = 3

# 3x00001 "Component ID" always reads 10 on a HERU Gen 3, so it doubles as a
# check that the configured unit ID and framer actually reach the unit.
INPUT_REGISTER_COMPONENT_ID = 0
EXPECTED_COMPONENT_ID = 10
