from typing import Type, Union

from flask import Flask

from unweaver.profile import Profile
from .shortest_path import ShortestPathView
from .reachable_tree import ReachableTreeView
from .shortest_path_tree import ShortestPathTreeView

View = Union[
    Type[ShortestPathView], Type[ReachableTreeView], Type[ShortestPathTreeView]
]


def add_view(app: Flask, view: View, profile: Profile) -> None:
    # TODO: Could use url_for and a real Flask route template?
    url = f"/{view.view_name}/{profile['id']}.json"

    instantiated_view = view(profile)

    app.add_url_rule(
        url,
        f"{view.view_name}-{profile['id']}",
        instantiated_view.create_view(),
    )


def add_views(app: Flask, profile: Profile) -> None:
    add_view(app, ShortestPathView, profile)
    add_view(app, ShortestPathTreeView, profile)
    add_view(app, ReachableTreeView, profile)
