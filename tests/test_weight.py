TEST_EDGES = [
    ("-122.3166084, 47.6569613", "-122.3156396, 47.6569496"),
    ("-122.3156015, 47.6583997", "-122.3165426, 47.6584109"),
    ("-122.3156396, 47.6569496", "-122.3154731, 47.6569503"),
]

DISTANCE_WEIGHTS = [72.8, 70.7, 12.5]


def test_precalculate_weights(built_G_weighted):
    for (u, v), weight in zip(TEST_EDGES, DISTANCE_WEIGHTS):
        d = built_G_weighted[u][v]
        assert d["_weight_distance"] == weight
