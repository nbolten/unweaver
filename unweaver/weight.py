import os

import entwiner

from .parsers import parse_profiles


def precalculate_weights(directory):
    profiles = parse_profiles(directory)
    G = entwiner.DiGraphDB(path=os.path.join(directory, "graph.db"), immutable=False)
    for profile in profiles:
        if profile["precalculate"]:
            weight_column = "_weight_{}".format(profile["name"])
            precalculate_weight(G, weight_column, profile["cost_function"])


def precalculate_weight(G, weight_column, cost_function_generator):
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

    # Update any remaining edges in batch
    if batch:
        G.update_edges(batch)
