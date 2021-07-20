import os
from typing import Callable, List, Optional

from click._termui_impl import ProgressBar

from unweaver.constants import DB_PATH
from unweaver.graph_types import EdgeTuple, CostFunction
from unweaver.graphs import DiGraphGPKG
from unweaver.parsers import parse_profiles


def precalculate_weights(directory: str) -> None:
    profiles = parse_profiles(directory)
    G = DiGraphGPKG(path=os.path.join(directory, DB_PATH))
    for profile in profiles:
        if profile["precalculate"]:
            weight_column = f"_weight_{profile['name']}"
            precalculate_weight(G, weight_column, profile["cost_function"])


def precalculate_weight(
    G: DiGraphGPKG,
    weight_column: str,
    cost_function_generator: Callable[..., CostFunction],
    counter: Optional[ProgressBar] = None,
) -> None:
    cost_function = cost_function_generator()
    # FIXME: __setitem__ silently fails on immutable graph

    batch: List[EdgeTuple] = []
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
