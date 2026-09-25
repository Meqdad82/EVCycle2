"""Router interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from evcycle.models import RouteData, RouteInput


class BaseRouter(ABC):
    """Return route metadata in the common EVCycle representation."""

    @abstractmethod
    def route(self, request: RouteInput) -> RouteData:
        raise NotImplementedError
