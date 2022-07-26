"""Reusable exceptions."""


# Graph building / validating exceptions

"""Reusable package-level exceptions."""


class UnrecognizedFileFormat(ValueError):
    pass


class NodeNotFound(ValueError):
    pass


class EdgeNotFound(ValueError):
    pass


class BuildingNotFound(ValueError):
    pass


class UnknownGeometry(ValueError):
    pass


class ImmutableGraphError(Exception):
    pass


class UninitializedEdgeError(Exception):
    pass


class UnderspecifiedGraphError(Exception):
    pass


# Routing exceptions


class InvalidWaypoint(ValueError):
    """When a waypoint input is invalid."""

    pass


class MissingLayersError(Exception):
    """When the build directory has no geospatial input files."""

    pass


class NoPathError(Exception):
    """When no path can be found between two points."""

    pass
