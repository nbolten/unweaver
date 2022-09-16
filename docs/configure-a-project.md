# Create a project

An unweaver project is a directory that contains all of the configuration files
and data needed to run or deploy unweaver.

An unweaver project must contain a `layers` directory with at least one
GDAL-readable LineString dataset and a `profile.json` with an `id` attribute.

## Project directory layout

    layers/
        ...:  # One or more GDAL-readable file (GeoJSON) of LineString data.
    cost-*.py # (optional) A Python module that defines a cost function generator.
    shortest-path-*.py # (optional) A Python module that defines a shortest path result function.
    profile-*.json # A JSON configuration file that defines combinations of other user-defined elements.

### The `layers` directory

Unweaver builds a routable network that's stored as a GeoPackage based on
geospatial input data that's placed into a the `layers` directory of a project.

The geospatial data files must contain LineString geometries and readable by
GDAL, which includes GeoJSON and shapefiles. In order to be built into a
network, these geometries will be connected end-to-end based on spatial
proximity (the proximity tolerance is configurable during the build process and
defaults to ~10 centimeters).

### Profiles

Any file that follows the pattern `profile-*.json` will be assumed to be a
JSON configuration file defining an Unweaver profile. An Unweaver profile JSON
ties together a set of user-definable prefences that are intended to be used
together; since Unweaver allows a user to define multiple cost functions,
shortest path result functions, shortest path tree functions, and runtime
parameters for their cost functions, there is a need to declare which exact set
should be used for a given purpose, such as running the Unweaver web server and
providing shortest path routes.

An Unweaver profile also provides a flexible way in which to alternatively
hard-code some of the arguments to a user-defined cost function and to
declare that a given profile should be used to precalculate static edge
traversal weights using a cost function and hard-coded cost function arguments.

An Unweaver profile has the following layout:

    {
      "id": string,    # A unique identifier (and name) for this profile.
      "args": [        # A list of runtime arguments for parameterizing the cost function.
        {
            "name": string,  # The name of this runtime argument
            "type": Marshmallow field string  # A string containing a Marshmallow field.
        },
        ...,
      ],
      "precalculate": boolean  # Whether to precalculate static weights for this profile.
      "static": {
        str: value  # Hard-coded arguments for the cost function (useful if precalculate is true).
      },
      "cost_function": string  # The Python module filename for a cost function.
      "shortest_path": string  # The Python module filename for a shortest path result function.
      "shortest_path_tree": string  # The Python module filename for a shortest path tree result function.
      "reachable_tree": string  # The Python module filename for a reachable paths result function.
    }

For example:

    {
        "id": "example",
        "args": [
            {
                "name": "pedestrianMode",
                "type": "fields.Boolean()"
            }
        ],
        "cost_function": "cost-flexible.py",
        "shortest_path": "shortest-path-best.py"
    }

Or for the same profile, but with precalculated weights:

    {
        "id": "example-pedestrian",
        "static": {
          "pedestrianMode": true
        },
        "cost_function": "cost-flexible.py",
        "shortest_path": "shortest-path-best.py"
    }

Nearly all of the top-level fields that can be set in an Unweaver profile have
default fallback settings, so the only part of an Unweaver profile that must
be set is the `id` field. Therefore, this is a valid profile:

    {
      "id": "test"
    }

It will use the cost function, directions function, shortest paths function,
and reachable function defines in the `unweaver/default_profile_functions.py`
module.

The meaning and use of the various user-defined function modules that may be
referenced by an Unweaver profile will be covered in the next sections.

### Cost functions

Any file that follows the pattern `cost-*.py` will be assumed to be a Python
module that defines a "cost function generator", a function with the following
signature:

    def cost_function_generator(**kwargs: Any) -> Callable[[str, str, dict], Optional[float]]:

Where `kwargs` are named parameters are any user-defined inputs needed at
runtime by the Unweaver web server (you can also define no arguments for this
function) and `Callable[[str, str, dict], Optional[float]]` is a
`networkx` shortest-path algorithm-compatible cost function. Specifically,
`networkx` shortest-path algorithms expect a cost function to accept the
start node (`u`, in this case a string), the end node (`v`, also a string), and
an edge data dictionary (`d`, a dictionary of your geospatial data's
per-LineString feature properties).

### Shortest path

Any file that follows the pattern `shortest-path-*.py` will be assumed to be a
Python module that defines a directions result function, which is a function
with the following signature:

	def shortest_path(
	    status: str,
	    G: DiGraphGPKG,
	    origin: Feature[Point],
	    destination: Feature[Point],
	    cost: Optional[float],
	    nodes: ReachedNodes,
	    edges: List[EdgeData],
	) -> dict:

This function allows you to completely customize the directions JSON response
returned by the Unweaver web API for a given profile. It is sent a given a
large amount of context that it can use to query for information about a
shortest path result, including the entire graph (a `DiGraphGPKG`), and returns
a dictionary that will be converted into JSON.

### Shortest path trees

Any file that follows the pattern `shortest-path-tree-*.py` will be assumed to be a
Python module that defines a shortest paths tree result function, which is a
function with the following signature:

	def shortest_path_tree(
	    status: str,
	    G: DiGraphGPKGView,
	    origin: Feature[Point],
	    nodes: ReachedNodes,
	    paths: Paths,
	    edges: List[EdgeData],
	) -> dict:

This function allows you to completely customize the shortest path tree JSON
response returned by the Unweaver web API for a given profile. Like the
directions function, it is provided with a large amount of context in addition
to the result.

### Reachable tree

Any file that follows the pattern `reachable-tree-*.py` will be assumed to be a
Python module that defines a reachable paths tree result function, which is a
function with the following signature:

	def reachable_tree(
	    status: str,
	    G: DiGraphGPKGView,
	    origin: Feature[Point],
	    nodes: ReachedNodes,
	    edges: List[EdgeData],
	) -> dict:

This function allows you to completely customize the reachable paths tree JSON
response returned by the Unweaver web API for a given profile. Like the
directions function, it is provided with a large amount of context in addition
to the result.
