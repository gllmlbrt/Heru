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

HOLDING_REGISTER_USER_FAN_SPEED = 0
HOLDING_REGISTER_TEMPERATURE_SETPOINT = 1
INPUT_REGISTER_ROOM_TEMPERATURE = 7

# 3x00001 "Component ID" always reads 10 on a HERU Gen 3, so it doubles as a
# check that the configured unit ID and framer actually reach the unit.
INPUT_REGISTER_COMPONENT_ID = 0
EXPECTED_COMPONENT_ID = 10
