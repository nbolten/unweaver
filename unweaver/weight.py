import os

import entwiner

from .constants import DB_PATH
from .parsers import parse_profiles


def precalculate_weights(directory):
    profiles = parse_profiles(directory)
    G = entwiner.DiGraphDB(path=os.path.join(directory, DB_PATH))
    for profile in profiles:
        if profile["precalculate"]:
            weight_column = "_weight_{}".format(profile["name"])
            precalculate_weight(G, weight_column, profile["cost_function"])


def precalculate_weight(
    G, weight_column, cost_function_generator, counter=None
):
    cost_function = cost_function_generator()
    # FIXME: __setitem__ silently fails on immutable graph

    batch = []
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
