from typing import Type, Union

from flask import Flask

from unweaver.profile import Profile
from .directions import DirectionsView
from .reachable import ReachableView
from .shortest_paths import ShortestPathsView

View = Union[
    Type[DirectionsView], Type[ReachableView], Type[ShortestPathsView]
]


def add_view(app: Flask, view: View, profile: Profile) -> None:
    # TODO: Could use url_for and a real Flask route template?
    url = f"/{view.view_name}/{profile['name']}.json"

    instantiated_view = view(profile)

    app.add_url_rule(
        url,
        f"{view.view_name}-{profile['name']}",
        instantiated_view.create_view(),
    )


def add_views(app: Flask, profile: Profile) -> None:
    add_view(app, DirectionsView, profile)
    add_view(app, ShortestPathsView, profile)
    add_view(app, ReachableView, profile)
