from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SearchRequest:
    """Search request for BEQ profiles."""
    tmdb: str
    year: int
    codec: str
    preferred_author: str
    edition: str
    skip_search: bool = False
    entry_id: str = ""
    mvAdjust: float = 0.0
    dry_run_mode: bool = False
    media_type: str = ""
    slots: List[int] = field(default_factory=list)
    title: str = ""


@dataclass
class BeqCatalog:
    """BEQ profile catalog entry."""
    id: str
    title: str
    sortTitle: str
    year: int
    audioTypes: List[str]
    digest: str
    mvAdjust: float
    edition: str
    theMovieDB: str
    author: str
    content_type: str
    catalogue_url: str
    extra_fields: Dict[str, Any] = field(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        # Set the known fields
        for f in self.__annotations__:
            if f != "extra_fields":
                setattr(self, f, kwargs.pop(f, None))

        # Set any remaining fields as extra fields
        self.extra_fields = kwargs

    def __setattr__(self, name: Any, value: Any) -> None:
        if name in self.__annotations__:
            super().__setattr__(name, value)
        else:
            self.extra_fields[name] = value

    def __getattr__(self, name: Any) -> Any:
        if name in self.extra_fields:
            return self.extra_fields[name]
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )


@dataclass
class BeqSlot:
    """Device slot info"""
    id: str
    last: str
    active: bool
    gain1: float
    gain2: float
    mute1: bool
    mute2: bool


@dataclass
class BeqDevice:
    """Device info"""
    name: str
    mute: bool
    type: str
    masterVolume: float = 0.0
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
