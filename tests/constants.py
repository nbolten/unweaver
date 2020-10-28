# Path for unweaver building
BUILD_PATH = "./tests/data/build"

# Near UW Bookstore
BOOKSTORE_POINT = (-122.313108, 47.661011)
# Near Cafe Solstice
CAFE_POINT = (-122.313170, 47.657524)

EXAMPLE_NODE = "-122.3154903, 47.6562992"


def cost_fun(u, v, d):
    return d.get("length", None)
