"""Constants for use in submodules."""

# Expected database location
DB_PATH = "graph.gpkg"

# The rectangular distance (r-tree distance in meters) within to search for
# nearby edges.
DWITHIN = 30

# Default database insert/update batch size
BATCH_SIZE = 1000
