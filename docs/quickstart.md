# Quickstart

## Create a minimal project directory

    mkdir -p my-project/layers
    echo '{ "id": "my-profile" }' > my-project/profile-my.json

## Put data in the project directory

    cp /path/to/a/linestring.geojson my-project/layers/

## Build a routable geopackage

    unweaver build ./my-project

## Start the Unweaver web server

    unweaver serve ./my-project

## Get shortest-path routes!

    curl localhost:8000/shortest_path/my-project.json?lon1={lon1}&lat1={lat1}&lon2={lon2}&lat2={lat2}
