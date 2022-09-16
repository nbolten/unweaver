# TODO: actually run the server via the CLI
import pytest

from unweaver.server import setup_app

from .constants import BUILD_PATH, BOOKSTORE_POINT, CAFE_POINT


@pytest.fixture()
def client(built_G_weighted):
    app = setup_app(BUILD_PATH, add_headers=None, debug=False)
    with app.test_client() as client:
        yield client
    # shutdown_func = request.environ.get("werkzeug.server.shutdown")
    # shutdown_func()


class TestServer:
    def test_reachable(self, client):
        resp = client.get(
            "/reachable_tree/distance.json",
            query_string={
                "lon": BOOKSTORE_POINT[0],
                "lat": BOOKSTORE_POINT[1],
                "max_cost": 1,
            },
        )
        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "Ok"

        # Maximum travel is 1 meter, there are two edges that will be
        # reached, and each is much longer than 1 meter each, so total reached
        # distance should be two meters.
        total_distance = sum(
            e["properties"]["length"] for e in data["edges"]["features"]
        )
        # Accounts for errors in distance calculation.
        # FIXME: ensure consistency between distance calculations so that this
        # has a smaller margin of error. 1e-3 is somewhat large since we
        # eventually aggregate tens to hundreds of edges.
        assert total_distance - 2 < 1e-3

        resp = client.get(
            "/reachable_tree/distance.json",
            query_string={
                "lon": BOOKSTORE_POINT[0],
                "lat": BOOKSTORE_POINT[1],
                "max_cost": 30,
            },
        )

        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "Ok"

        total_distance = sum(
            e["properties"]["length"] for e in data["edges"]["features"]
        )

        assert total_distance - 49.62 < 0.1

        # # TODO: check other properties?

    def test_shortest_paths(self, client):
        resp = client.get(
            "/shortest_path_tree/distance.json",
            query_string={
                "lon": BOOKSTORE_POINT[0],
                "lat": BOOKSTORE_POINT[1],
                "max_cost": 100,
            },
        )
        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "Ok"

        total_distance = sum(
            e["properties"]["length"] for e in data["edges"]["features"]
        )
        # Accounts for errors in distance calculation.
        # FIXME: ensure consistency between distance calculations so that this
        # has a smaller margin of error. 1e-3 is somewhat large since we
        # eventually aggregate tens to hundreds of edges.
        assert total_distance == 83.1

        # # TODO: check other properties?

        # TODO: check rounding on geometry outputs

    def test_directions(self, client):
        resp = client.get(
            "/shortest_path/distance.json",
            query_string={
                "lon1": BOOKSTORE_POINT[0],
                "lat1": BOOKSTORE_POINT[1],
                "lon2": CAFE_POINT[0],
                "lat2": CAFE_POINT[1],
            },
        )
        assert resp.status_code == 200
        data = resp.json
        assert data["status"] == "Ok"

        total_distance = sum(e["length"] for e in data["edges"])
        # Accounts for errors in distance calculation.
        # FIXME: ensure consistency between distance calculations so that this
        # has a smaller margin of error. 1e-3 is somewhat large since we
        # eventually aggregate tens to hundreds of edges.
        assert total_distance - 387.62 < 0.1

        # # TODO: check other properties?

        # TODO: check rounding on geometry outputs
