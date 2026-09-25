"""Router factory."""

from evcycle.routers.base import BaseRouter
from evcycle.routers.mock import MockRouter
from evcycle.routers.online import OpenRouteServiceRouter, OSRMRouter


def get_router(name: str) -> BaseRouter:
    normalized = name.lower().replace("-", "").replace("_", "")
    if normalized == "mock":
        return MockRouter()
    if normalized in {"osrm"}:
        return OSRMRouter()
    if normalized in {"ors", "openrouteservice"}:
        return OpenRouteServiceRouter()
    raise ValueError(f"unknown router: {name}")


__all__ = [
    "BaseRouter",
    "MockRouter",
    "OpenRouteServiceRouter",
    "OSRMRouter",
    "get_router",
]
