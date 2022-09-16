# Path for unweaver building
BUILD_PATH = "./example"

# Near UW Bookstore
BOOKSTORE_POINT = (-122.313108, 47.661011)
# Near Cafe Solstice
CAFE_POINT = (-122.313170, 47.657524)

EXAMPLE_NODE = "-122.3154903, 47.6562992"
EXAMPLE_POLYGON = {  # TODO: test this out
    "type": "Feature",
    "properties": {},
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [-122.33113288879395, 47.60124394587685],
                [-122.33139038085936, 47.600694135598154],
                [-122.33091831207275, 47.6001877262822],
                [-122.32855796813965, 47.600303477415146],
                [-122.32933044433592, 47.601489911762435],
                [-122.33113288879395, 47.60124394587685],
            ]
        ],
    },
}


def cost_fun(u, v, d):
    return d.get("length", None)
