# Quickstart

## With pip-installed Unweaver

### Clone the git repo to get an example project directory

    git clone https://github.com/nbolten/unweaver
    cd unweaver

### Build a routable geopackage

    unweaver build ./example

### Start the Unweaver web server

    unweaver serve ./example

### Get shortest-path routes!

    curl "http://localhost:8000/shortest_path/distance.json?lon1=-122.313108&lat1=47.661011&lon2=-122.313170&lat2=47.65724"

## With Docker

### Clone the git repo to get an example project directory

    git clone https://github.com/nbolten/unweaver
    cd unweaver

### Build a routable geopackage

    docker run --rm -v $(pwd)/example:/project unweaver build /project

### Start the Unweaver web server

    docker run --rm -v $(pwd)/example:/project:ro -p 8000:8000 unweaver serve -h 0.0.0.0 /project

### Get shortest-path routes!

    curl "http://localhost:8000/shortest_path/distance.json?lon1=-122.313108&lat1=47.661011&lon2=-122.313170&lat2=47.65724"

