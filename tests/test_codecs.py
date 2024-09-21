# type: ignore

import pytest
from pyezbeq.consts import (
    ATMOS,
    DD_PLUS_ATMOS,
    DD_PLUS_ATMOS_5_1_MAYBE,
    ATMOS_MAYBE,
    DTS_X,
    DTS_HD_MA_5_1,
    TRUEHD_5_1,
    LPCM_5_1,
    LPCM_7_1,
    LPCM_2_0,
    AAC_2_0,
    AC3_5_1,
    EMPTY,
    DD_PLUS,
)
from pyezbeq.utils import map_audio_codec, convert_jellyfin_to_plex_format


@pytest.mark.parametrize(
    "short_codec,extended_codec,expected",
    [
        ("EAC3", "EAC3", DD_PLUS),
        ("EAC3 5.1", "German (German EAC3 5.1)", DD_PLUS_ATMOS_5_1_MAYBE),
        ("DDP 5.1 Atmos", "DDP 5.1 Atmos (Engelsk EAC3)", DD_PLUS_ATMOS),
        ("TRUEHD 7.1", "Surround 7.1 (English TRUEHD)", ATMOS_MAYBE),
        (
            "TRUEHD 5.1",
            "Dolby TrueHD Audio / 5.1 / 48 kHz / 1541 kbps / 16-bit (English)",
            TRUEHD_5_1,
        ),
        (
            "DTS-HD MA 5.1",
            "DTS-HD Master Audio / 5.1 / 48 kHz / 3887 kbps / 24-bit (English)",
            DTS_HD_MA_5_1,
        ),
        ("TRUEHD Atmos", "TrueHD Atmos 7.1 (English)", ATMOS),
        (
            "DTS-X",
            "DTS:X / 7.1 / 48 kHz / 4213 kbps / 24-bit (English DTS-HD MA)",
            DTS_X,
        ),
    ],
)
def test_map_audio_codec_plex(short_codec, extended_codec, expected):
    assert map_audio_codec(short_codec, extended_codec) == expected


@pytest.mark.parametrize(
    "codec,display_title,profile,layout,expected_short,expected_extended",
    [
        (
            "EAC3",
            "English - Dolby Digital+ - Stereo - Default",
            "",
            "",
            "EAC3",
            "English - Dolby Digital+ - Stereo - Default (EAC3)",
        ),
        (
            "AC3",
            "English - Dolby Digital - 5.1 - Default",
            "",
            "5.1",
            "AC3 5.1",
            "English - Dolby Digital - 5.1 - Default (AC3 5.1)",
        ),
        (
            "eac3",
            "English - Dolby Digital+ - 5.1 - Default",
            "",
            "5.1",
            "EAC3 5.1",
            "English - Dolby Digital+ - 5.1 - Default (EAC3 5.1)",
        ),
        (
            "dts",
            "DTS-HD MA 5.1 - English - Default",
            "DTS-HD MA",
            "",
            "DTS-HD MA",
            "DTS-HD MA 5.1 - English - Default (DTS-HD MA)",
        ),
        (
            "DTS",
            "Surround 5.1 - English - DTS-HD MA - Default",
            "",
            "5.1",
            "DTS-HD MA 5.1",
            "Surround 5.1 - English - DTS-HD MA - Default (DTS-HD MA 5.1)",
        ),
        (
            "truehd",
            "Dolby TrueHD Audio / 7.1 / 48 kHz / 16-bit (AC3 Embedded: 5.1 / 48 kHz / 640 kbps) - English - Default",
            "",
            "7.1",
            "TRUEHD 7.1",
            "Dolby TrueHD Audio / 7.1 / 48 kHz / 16-bit (AC3 Embedded: 5.1 / 48 kHz / 640 kbps) - English - Default (TRUEHD 7.1)",
        ),
        (
            "TRUEHD",
            "TrueHD Atmos 7.1 - English - Default",
            "",
            "",
            "TRUEHD Atmos",
            "TrueHD Atmos 7.1 - English - Default (TRUEHD Atmos)",
        ),
    ],
)
def test_convert_jellyfin_to_plex_format(
    codec, display_title, profile, layout, expected_short, expected_extended
):
    short, extended = convert_jellyfin_to_plex_format(
        codec, display_title, profile, layout
    )
    assert short == expected_short
    assert extended == expected_extended


def test_jellyfin_to_plex_to_map():
    jellyfin_cases = [
        ("EAC3", "English - Dolby Digital+ - Stereo - Default", "", "", DD_PLUS),
        ("AC3", "English - Dolby Digital - 5.1 - Default", "", "5.1", AC3_5_1),
        (
            "eac3",
            "English - Dolby Digital+ - 5.1 - Default",
            "",
            "5.1",
            DD_PLUS_ATMOS_5_1_MAYBE,
        ),
        ("dts", "DTS-HD MA 5.1 - English - Default", "DTS-HD MA", "", DTS_HD_MA_5_1),
        (
            "DTS",
            "Surround 5.1 - English - DTS-HD MA - Default",
            "",
            "5.1",
            DTS_HD_MA_5_1,
        ),
        (
            "truehd",
            "Dolby TrueHD Audio / 7.1 / 48 kHz / 16-bit (AC3 Embedded: 5.1 / 48 kHz / 640 kbps) - English - Default",
            "",
            "7.1",
            ATMOS_MAYBE,
        ),
        ("TRUEHD", "TrueHD Atmos 7.1 - English - Default", "", "", ATMOS),
    ]

    for codec, display_title, profile, layout, expected in jellyfin_cases:
        short, extended = convert_jellyfin_to_plex_format(
            codec, display_title, profile, layout
        )
        result = map_audio_codec(short, extended)
        assert (
            result == expected
        ), f"Failed for {codec}, {display_title}, {profile}, {layout}. Got {result}, expected {expected}"


# Additional edge cases
def test_map_audio_codec_edge_cases():
    assert map_audio_codec("LPCM", "LPCM 5.1") == LPCM_5_1
    assert map_audio_codec("LPCM", "LPCM 7.1") == LPCM_7_1
    assert map_audio_codec("LPCM", "LPCM 2.0") == LPCM_2_0
    assert map_audio_codec("AAC", "AAC Stereo") == AAC_2_0
    assert map_audio_codec("Unknown", "Unknown Codec") == EMPTY
