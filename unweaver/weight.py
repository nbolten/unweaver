import os
from typing import Callable, List, Optional

from click._termui_impl import ProgressBar
import entwiner

from unweaver.constants import DB_PATH
from unweaver.graph import Edge, CostFunction
from unweaver.parsers import parse_profiles


def precalculate_weights(directory: str) -> None:
    profiles = parse_profiles(directory)
    G = entwiner.DiGraphDB(path=os.path.join(directory, DB_PATH))
    for profile in profiles:
        if profile["precalculate"]:
            weight_column = f"_weight_{profile['name']}"
            precalculate_weight(G, weight_column, profile["cost_function"])


def precalculate_weight(
    G: entwiner.DiGraphDB,
    weight_column: str,
    cost_function_generator: Callable[..., CostFunction],
    counter: Optional[ProgressBar] = None,
) -> None:
    cost_function = cost_function_generator()
    # FIXME: __setitem__ silently fails on immutable graph

    batch: List[Edge] = []
    for i, (u, v, d) in enumerate(G.iter_edges()):
        # Update 100 at a time
        weight = cost_function(u, v, d)
        if len(batch) == 1000:
            G.update_edges(batch)
            batch = []
        batch.append((u, v, {weight_column: weight}))
        if counter is not None:
            counter.update(1)

    # Update any remaining edges in batch
    if batch:
        G.update_edges(batch)
