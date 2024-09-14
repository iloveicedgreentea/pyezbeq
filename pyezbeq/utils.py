from .consts import (
    ATMOS,
    DD_PLUS_ATMOS,
    DD_PLUS_ATMOS_5_1_MAYBE,
    DD_PLUS_ATMOS_7_1_MAYBE,
    ATMOS_MAYBE,
    DTS_X,
    DTS_HD_MA_7_1,
    DTS_HD_MA_5_1,
    DTS_5_1,
    DTS_HD_HR_7_1,
    DTS_HD_HR_5_1,
    TRUEHD_5_1,
    TRUEHD_6_1,
    LPCM_5_1,
    LPCM_7_1,
    LPCM_2_0,
    AAC_2_0,
    AC3_5_1,
    EMPTY,
    DD_PLUS,
    TRUEHD_7_1,
)


def convert_jellyfin_to_plex_format(
    codec: str, display_title: str, profile: str, layout: str
) -> tuple[str, str]:
    """
    Convert Jellyfin codec information to a format compatible with the Plex mapping function.

    :param codec: The codec from Jellyfin
    :param display_title: The display title from Jellyfin
    :param profile: The profile from Jellyfin
    :param layout: The layout from Jellyfin
    :return: A tuple of (short_codec, extended_codec) in a Plex-compatible format
    """
    all_info = f"{codec} {display_title} {profile} {layout}".upper()

    # Extract the main codec type
    if "ATMOS" in all_info:
        short_codec = (
            "DDP 5.1 Atmos"
            if "EAC3" in all_info or "DDP" in all_info
            else "TRUEHD Atmos"
        )
    elif "DTS:X" in all_info or "DTS-X" in all_info:
        short_codec = "DTS-X"
    elif "DTS-HD MA" in all_info:
        short_codec = f"DTS-HD MA {layout}" if layout else "DTS-HD MA"
    elif "TRUEHD" in all_info:
        short_codec = f"TRUEHD {layout}" if layout else "TRUEHD"
    elif "EAC3" in all_info or "DDP" in all_info:
        short_codec = f"EAC3 {layout}" if layout else "EAC3"
    elif "AC3" in all_info:
        short_codec = f"AC3 {layout}" if layout else "AC3"
    elif "DTS" in all_info:
        short_codec = f"DTS {layout}" if layout else "DTS"
    elif "LPCM" in all_info:
        short_codec = f"LPCM {layout}" if layout else "LPCM"
    elif "AAC" in all_info:
        short_codec = (
            "AAC Stereo" if "STEREO" in all_info or "2.0" in all_info else "AAC"
        )
    else:
        short_codec = codec.upper()

    # Construct the extended codec info
    extended_codec = f"{display_title} ({short_codec})"

    return short_codec, extended_codec


def insensitive_contains(s: str, substr: str) -> bool:
    return substr.lower() in s.lower()


def contains_ddp(s: str) -> bool:
    ddp_names = ["ddp", "eac3", "e-ac3", "dd+", "dolby digital+"]
    return any(name in s.lower() for name in ddp_names)


def contains_dtsx(s: str) -> bool:
    return any(x in s.upper() for x in ["DTS:X", "DTS-X", "DTSX"])


def map_audio_codec(short_codec: str, extended_codec: str) -> str:
    print(f"Codecs received: short: {short_codec}, extended: {extended_codec}")

    # Combine all information for easier searching
    all_info = f"{short_codec} {extended_codec}".lower()

    # Atmos logic
    atmos_flag = "atmos" in all_info
    ddp_flag = contains_ddp(all_info)

    print(f"Atmos: {atmos_flag} - DD+: {ddp_flag}")

    if atmos_flag and not ddp_flag:
        return ATMOS
    if atmos_flag and ddp_flag:
        return DD_PLUS_ATMOS
    if not atmos_flag and ddp_flag:
        if "5.1" in all_info:
            return DD_PLUS_ATMOS_5_1_MAYBE
        if "7.1" in all_info:
            return DD_PLUS_ATMOS_7_1_MAYBE
        return DD_PLUS

    # TrueHD logic
    if "truehd" in all_info:
        if "7.1" in all_info:
            return ATMOS_MAYBE
        if "5.1" in all_info:
            return TRUEHD_5_1
        if "6.1" in all_info:
            return TRUEHD_6_1
        if "7.1" in all_info:
            return TRUEHD_7_1

    # DTS logic
    if "dts" in all_info:
        if contains_dtsx(all_info):
            return DTS_X
        if "dts-hd ma 7.1" in all_info:
            return DTS_HD_MA_7_1
        if "dts-hd ma" in all_info and "5.1" in all_info:
            return DTS_HD_MA_5_1
        if "dts-hd hra" in all_info and "7.1" in all_info:
            return DTS_HD_HR_7_1
        if "dts-hd hra" in all_info and "5.1" in all_info:
            return DTS_HD_HR_5_1
        if "5.1" in all_info:
            return DTS_5_1

    # LPCM logic
    if "lpcm" in all_info:
        if "5.1" in all_info:
            return LPCM_5_1
        if "7.1" in all_info:
            return LPCM_7_1
        return LPCM_2_0

    # AAC logic
    if "aac" in all_info and ("stereo" in all_info or "2.0" in all_info):
        return AAC_2_0

    # AC3 logic
    if ("ac3" in all_info or "eac3" in all_info) and "5.1" in all_info:
        return AC3_5_1

    return EMPTY
