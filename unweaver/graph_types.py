from typing import Any, Callable, Dict, Optional, Tuple

# TODO: add derived properties to EdgeData? e.g. _length
NodeData = dict
NodeTuple = Tuple[str, NodeData]
EdgeData = Dict[str, Any]
EdgeTuple = Tuple[str, str, EdgeData]
CostFunction = Callable[[str, str, EdgeData], Optional[float]]
BuildingData = Dict[str, Any]
BuildingTuple = Tuple[str, BuildingData]
