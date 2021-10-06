## Bugs

### Create a read-only mode for 'serve'

### Rework --changes-sign into config-based option like everything else. layers.json?

### Handle waypoints-on-same-edge case

## Formats

Add support for more formats, at least GPKG and Shapefiles. Ideally, use fiona and
attempt to read all files in the `layers` directory.

## Stability

### Allow the use of other servers, e.g. gunicorn

## Routing Speed

### networkx's dijkstra uses G[key].items(), which means multiple round trips to the
db. Need to either replace nx's Atlas upstream in `graphs.digraphgpkg` or
reimplement dijkstra.
