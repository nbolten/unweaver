"""Reusable exceptions."""


class InvalidWaypoint(ValueError):
    """When a waypoint input is invalid."""

    pass


class MissingLayersError(Exception):
    """When the build directory has no geospatial input files."""

    pass


class NoPathError(Exception):
    """When no path can be found between two points."""

    pass
