import json
import os

from unweaver.profile import ProfileSchema


def parse_profiles(directory):
    """Parse all profiles in a directory - all files matching profle-*.json

    :param directory: Directory (path) from which to parse profiles.
    :type directory: str

    """
    # TODO: add something to catch "no profiles found", possibly help users with
    # extensions (e.g. naming .py instead of .json)
    profiles = []
    for p in os.listdir(directory):
        if p.startswith("profile-") and p.endswith(".json"):
            profiles.append(parse_profile(os.path.join(directory, p)))

    return profiles


def parse_profile(path):
    """Parse a single profile.

    :param path: File path from which to parse profiles.
    :type path: str

    """
    working_path = os.path.dirname(path)

    # TODO: add directions
    with open(path) as f:
        profile_json = json.load(f)

    context = {"working_path": working_path}

    schema = ProfileSchema(strict=True, context=context)
    # TODO: add error handling
    profile = schema.load(profile_json).data

    # TODO: create + return a Profile class?
    return profile
