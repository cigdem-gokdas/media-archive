"""
This module contains the business logic and Object-Oriented Programming (OOP)
structures for the Media Archive project. It defines the protocols,
abstract base classes, and concrete media types (Movie, Series).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Protocol, Optional, Dict, Any

class InfoProtocol(Protocol):
    """Protocol defining objects that can provide information string."""
    # pylint: disable=too-few-public-methods
    def get_info(self) -> str:
        """Return a formatted information string."""

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
    status: str
    media_type: str


class Movie(BaseMedia, MediaItem):
    """
    Concrete class representing a Movie, inheriting from BaseMedia and MediaItem.
    """
    def __init__(
        self,
        title: str,
        year: str,
        rating: str,
        poster_url: str,
        status: str = "not watched"
    ):
        """Initialize a Movie object."""
        # Pylint complains about too many arguments (limit is 5), but we need them here.
        # pylint: disable=too-many-arguments, too-many-positional-arguments
        super().__init__(title, year, rating, poster_url, status, "movie")

    def get_info(self) -> str:
        return f"[MOVIE] {self.title} - {self.year} ({self.status})"

    def to_dict(self) -> dict:
        return asdict(self)


class Series(BaseMedia, MediaItem):
    """
    Concrete class representing a Series, inheriting from BaseMedia and MediaItem.
    """
    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        title: str,
        year: str,
        rating: str,
        poster_url: str,
        status: str = "not watched"
    ):
        super().__init__(title, year, rating, poster_url, status, "series")

    def get_info(self) -> str:
        return f"[SERIES] {self.title} - {self.year} ({self.status})"

    def to_dict(self) -> dict:
        return asdict(self)

class SimpleORM:
    """
    A simple Object-Relational Mapping (ORM) class to handle
    in-memory storage of media items.
    """
    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}

    def save(self, item: MediaItem):
        """Save a media item to the internal storage."""
        data = item.to_dict()
        key = data["title"]
        self.storage[key] = data

    def find(self, title: str) -> Optional[Dict[str, Any]]:
        """Find and return a media item by title."""
        return self.storage.get(title, None)
