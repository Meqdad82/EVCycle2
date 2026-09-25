"""Minimal online router adapters.

Online responses are not used by the fixed manuscript benchmark.
"""

from __future__ import annotations

import os

import numpy as np
import requests

from evcycle.models import RouteData, RouteInput
from evcycle.routers.base import BaseRouter


def _flat_elevation(distance_m: float) -> tuple[np.ndarray, np.ndarray]:
    distance = np.linspace(0.0, distance_m, 101)
    return distance, np.zeros_like(distance)


class OSRMRouter(BaseRouter):
    endpoint = "https://router.project-osrm.org/route/v1/driving"

    def route(self, request: RouteInput) -> RouteData:
        lat1, lon1 = request.origin
        lat2, lon2 = request.destination
        url = f"{self.endpoint}/{lon1},{lat1};{lon2},{lat2}"
        response = requests.get(
            url,
            params={"overview": "false", "steps": "false"},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        item = payload["routes"][0]
        distance_m = float(item["distance"])
        duration_s = float(item["duration"])
        distance, elevation = _flat_elevation(distance_m)
        nominal = distance_m / duration_s
        return RouteData(
            distance_m=distance_m,
            duration_s=duration_s,
            nominal_speed_ms=nominal,
            speed_limit_ms=max(nominal * 1.35, 16.67),
            road_class="online",
            distance_samples_m=distance,
            elevation_samples_m=elevation,
            provider="OSRM",
        )


class OpenRouteServiceRouter(BaseRouter):
    endpoint = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ORS_API_KEY")
        if not self.api_key:
            raise ValueError("ORS_API_KEY is required for OpenRouteService")

    def route(self, request: RouteInput) -> RouteData:
        lat1, lon1 = request.origin
        lat2, lon2 = request.destination
        response = requests.post(
            self.endpoint,
            headers={"Authorization": self.api_key, "Content-Type": "application/json"},
            json={"coordinates": [[lon1, lat1], [lon2, lat2]], "elevation": True},
            timeout=45,
        )
        response.raise_for_status()
        feature = response.json()["features"][0]
        summary = feature["properties"]["summary"]
        distance_m = float(summary["distance"])
        duration_s = float(summary["duration"])
        coords = feature["geometry"]["coordinates"]
        if coords and len(coords[0]) >= 3:
            raw_elevation = np.asarray([c[2] for c in coords], dtype=float)
            distance = np.linspace(0.0, distance_m, len(raw_elevation))
        else:
            distance, raw_elevation = _flat_elevation(distance_m)
        nominal = distance_m / duration_s
        return RouteData(
            distance_m=distance_m,
            duration_s=duration_s,
            nominal_speed_ms=nominal,
            speed_limit_ms=max(nominal * 1.35, 16.67),
            road_class="online",
            distance_samples_m=distance,
            elevation_samples_m=raw_elevation,
            provider="OpenRouteService",
        )
