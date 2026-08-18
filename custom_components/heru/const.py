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

# 1x00010 - 1x00025 are the alarm bits. They are reported as one entity that
# lists whichever are active, rather than thirteen separate binary sensors.
# Names are plain strings because state attributes are not translated.
ALARM_BITS: tuple[tuple[int, str], ...] = (
    (9, "Fire alarm"),
    (10, "Rotor alarm"),
    (12, "Freeze alarm"),
    (13, "Low supply alarm"),
    (14, "Low rotor temperature alarm"),
    (17, "Temperature sensor open circuit alarm"),
    (18, "Temperature sensor short circuit alarm"),
    (19, "Pulser alarm"),
    (20, "Supply fan alarm"),
    (21, "Exhaust fan alarm"),
    (22, "Supply filter alarm"),
    (23, "Exhaust filter alarm"),
    (24, "Filter timer alarm"),
)

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

# Configuration holding registers, fetched as small (address, count) blocks
# rather than one span. A Tasmota Modbus bridge caps a response at
# MBR_MAX_REGISTERS = 64 registers, and reading across registers the unit does
# not implement makes it reject the whole request, so each block stays narrow
# and covers only what is used. Each block is optional and independent.
HOLDING_CONFIG_BLOCKS = ((2, 5), (15, 2), (25, 3), (49, 3), (68, 1))

HOLDING_REGISTER_SUPPLY_FAN_SPEED_EC = 2  # 4x00003, percent
HOLDING_REGISTER_EXHAUST_FAN_SPEED_EC = 3  # 4x00004, percent
# On EC fans the mode coils do not set a speed directly, they select which of
# these per-step registers the unit runs at: away uses min, boost uses mod or
# max depending on 4x00026. If they all hold similar values, switching mode
# produces no visible change.
HOLDING_REGISTER_MIN_EXHAUST_FAN_SPEED_EC = 4  # 4x00005, used by away mode
HOLDING_REGISTER_MOD_EXHAUST_FAN_SPEED_EC = 5  # 4x00006, used by boost
HOLDING_REGISTER_MAX_EXHAUST_FAN_SPEED_EC = 6  # 4x00007, used by boost
HOLDING_REGISTER_BOOST_SPEED = 25  # 4x00026, 3 = Mod, 4 = Max
HOLDING_REGISTER_BOOST_DURATION = 26  # 4x00027, minutes
HOLDING_REGISTER_OVERPRESSURE_DURATION = 27  # 4x00028, minutes
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

# Actual running values, reported alongside the commanded setpoint.
INPUT_REGISTER_SUPPLY_FAN_POWER = 24  # 3x00025, percent
INPUT_REGISTER_EXHAUST_FAN_POWER = 25  # 3x00026, percent
INPUT_REGISTER_SUPPLY_FAN_RPM = 26  # 3x00027
INPUT_REGISTER_EXHAUST_FAN_RPM = 27  # 3x00028

# 3x00001 "Component ID" always reads 10 on a HERU Gen 3, so it doubles as a
# check that the configured unit ID and framer actually reach the unit.
INPUT_REGISTER_COMPONENT_ID = 0
EXPECTED_COMPONENT_ID = 10
