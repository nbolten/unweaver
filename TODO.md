## Bugs

### Rework --changes-sign into config-based option like everything else. layers.json?

### Handle waypoints-on-same-edge case

## Stability

### Allow the use of other servers, e.g. gunicorn

## Routing Speed

### networkx's dijkstra uses G[key].items(), which means multiple round trips to the
db. Need to either replace nx's Atlas upstream in `entwiner` or reimplement dijkstra.

## entwiner

## Scaling

### Write Go version

Go is going (ha) to be much faster at most operations, particularly if the graph can
fit in memory. Users can easily supply new functions via a go plugin - though they
will need to use the go dev tools (or docker).

### Storage projections / geographic CRS

Lon-lat seems fine as a universal storage base, but some disance calculations would be
faster in a cartesian reference system. At least add hacks so that distances are
accurate.
