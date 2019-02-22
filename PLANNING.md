# API Generation / Cost functions

- Leverage 'Traits' (docs.enthought.com/traits) to help with auto-doc and auto-api?
e.g. a 'Range' trait would be useful for most real-valued data. Also, extensible: a
discretized Range might be handy (just a bunch of stops like an Enum, but without
having to enumerate everything in the docs).

# Directions

- Not all use cases will require directions and directions are defined just as
arbitrarily as cost functions - it depends on the application.

- Need to be able to modularly define directions functions as well. They take in a path
and path data and output a dictionary? Something similar to this.

- An opportunity to allow advanced users manual overrides: the code that finds a route
and generates directions should allow full replacement of how either bit of code works.

- Include some defaults like 'OSM streets', 'OSM pedestrian', etc.
