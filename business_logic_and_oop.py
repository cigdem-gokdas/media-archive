"""
This module contains the business logic and Object-Oriented Programming (OOP)
structures for the Media Archive project. It defines the protocols,
abstract base classes, and concrete media types (Movie, Series).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, Any, ClassVar, Set


class MediaItem(ABC):
    """
    Abstract Base Class that enforces implementation of info
    and dictionary conversion methods.
    """
    # pylint: disable=too-few-public-methods
    @abstractmethod
    def get_info(self) -> str:
        """Return a formatted information string."""

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary."""


@dataclass
class BaseMedia:
    """
    Base Data Class representing shared attributes for all media types.
    """
    title: str
    year: str
    rating: str
    poster_url: str
    page_url: str
    status: str
    media_type: str


class Movie(BaseMedia, MediaItem):
    """
    Concrete class representing a Movie, inheriting from BaseMedia and MediaItem.
    """
    VALID_STATUSES: ClassVar[Set[str]] = {"watched", "not watched"}

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        title: str,
        year: str,
        rating: str,
        poster_url: str,
        page_url: str,
        status: str = "not watched"
    ):
        """Initialize a Movie object."""
        clean_status = status.lower()
        if clean_status not in self.VALID_STATUSES:
            clean_status = "not watched"

        super().__init__(title, year, rating, poster_url, page_url, clean_status, "movie")

    def get_info(self) -> str:
        icon = "✅" if self.status == "watched" else "📅"
        return f"🎬 MOVIE: {self.title} ({self.year}) | {icon} {self.status.upper()}"

    def to_dict(self) -> dict:
        return asdict(self)


class Series(BaseMedia, MediaItem):
    """
    Concrete class representing a Series, inheriting from BaseMedia and MediaItem.
    """
    VALID_STATUSES: ClassVar[Set[str]] = {"watched", "not watched", "watching"}

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        title: str,
        year: str,
        rating: str,
        poster_url: str,
        page_url: str,
        status: str = "not watched"
    ):
        clean_status = status.lower()
        if clean_status not in self.VALID_STATUSES:
            clean_status = "not watched"

        super().__init__(title, year, rating, poster_url, page_url, clean_status, "series")

    def get_info(self) -> str:
        if self.status == "watching":
            icon = "▶"
        elif self.status == "watched":
            icon = "✅"
        else:
            icon = "📅"

        return f"📺 SERIES: {self.title} ({self.year}) | {icon} {self.status.upper()}"

    def to_dict(self) -> dict:
        return asdict(self)
