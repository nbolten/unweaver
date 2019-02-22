## Stability

### Allow the use of other servers, e.g. gunicorn

## Speed

### Building the graph should only take a few seconds. Track down the slow part.

## entwiner

### Node attributes

Node attributes are currently ephemeral. These are useful for downstream analyses and
filtering - make them possible.

### Edge attrs with None

Edge attrs are currently fetched using sqlite3.Row, meaning if there is missing data
('none' in SQLite), the key and value exist, but the value is None. This is not
consistent with how one would use networkx - sanitize the dict-like.
