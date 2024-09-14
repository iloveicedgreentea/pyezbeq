"""Constants for ezbeq module."""

COMMAND_TIMEOUT = 3
HEARTBEAT_INTERVAL = 15  # TODO: send heartbeats to see if its available
CONNECT_TIMEOUT = 5
DEFAULT_PORT = 8080
DISCOVERY_ADDRESS = "ezbeq.local"
DEFAULT_SCHEME = "http"
SMALL_DELAY = 2
# save some cpu cycles
TASK_CPU_DELAY = 0.1


# Codecs
ATMOS = "Atmos"
DD_PLUS_ATMOS = "DD+ Atmos"
DD_PLUS_ATMOS_5_1_MAYBE = "DD+Atmos5.1Maybe"
DD_PLUS_ATMOS_7_1_MAYBE = "DD+Atmos7.1Maybe"
ATMOS_MAYBE = "AtmosMaybe"
DTS_X = "DTS-X"
DTS_HD_MA_7_1 = "DTS-HD MA 7.1"
DTS_HD_MA_5_1 = "DTS-HD MA 5.1"
DTS_5_1 = "DTS 5.1"
DTS_HD_HR_7_1 = "DTS-HD HR 7.1"
DTS_HD_HR_5_1 = "DTS-HD HR 5.1"
TRUEHD_5_1 = "TrueHD 5.1"
TRUEHD_6_1 = "TrueHD 6.1"
TRUEHD_7_1 = "TrueHD 7.1"
LPCM_5_1 = "LPCM 5.1"
LPCM_7_1 = "LPCM 7.1"
LPCM_2_0 = "LPCM 2.0"
AAC_2_0 = "AAC 2.0"
AC3_5_1 = "AC3 5.1"
DD_PLUS = "DD+"
EMPTY = "Empty"
