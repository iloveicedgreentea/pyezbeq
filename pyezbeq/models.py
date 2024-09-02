from dataclasses import dataclass, field
from typing import List


@dataclass
class SearchRequest:
    tmdb: str
    year: int
    codec: str
    preferred_author: str
    edition: str
    skip_search: bool = False
    entry_id: str = ""
    mv_adjust: float = 0.0
    dry_run_mode: bool = False
    media_type: str = ""
    devices: List[str] = field(default_factory=list)
    slots: List[int] = field(default_factory=list)
    title: str = ""


@dataclass
class BeqCatalog:
    id: str
    title: str
    sort_title: str
    year: int
    audio_types: List[str]
    digest: str
    mv_adjust: float
    edition: str
    movie_db_id: str
    author: str


@dataclass
class BeqSlot:
    id: str
    last: str
    active: bool
    gain1: float
    gain2: float
    mute1: bool
    mute2: bool


@dataclass
class BeqDevice:
    name: str
    master_volume: float
    mute: bool
    slots: List[BeqSlot] = field(default_factory=list)


@dataclass
class BeqPatchV2:
    mute: bool
    master_volume: float
    slots: List["SlotsV2"] = field(default_factory=list)


@dataclass
class SlotsV2:
    id: str
    active: bool
    entry: str
    gains: List[float] = field(default_factory=list)
    mutes: List[bool] = field(default_factory=list)


@dataclass
class BeqPatchV1:
    mute: bool
    master_volume: float
    slots: List["SlotsV1"] = field(default_factory=list)


@dataclass
class SlotsV1:
    id: str
    active: bool
    entry: str
    gains: List[float] = field(default_factory=list)
    mutes: List[bool] = field(default_factory=list)
