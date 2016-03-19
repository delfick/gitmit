"""
This holds the functionality to write and read a cache of the modified times
for a repository.
"""

import logging
import json
import os

log = logging.getLogger("gitmit.cache")

def cache_location(root_folder):
    """
    Return us the location to the commit times cache

    This is <root_folder>/.git/gitmit_cached_commit_times.json
    """
    return os.path.join(root_folder, ".git", "gitmit_cached_commit_times.json")

def get_all_cached_commit_times(root_folder):
    """
    Find the gitmit cached commit_times and return them if they are the right shape.

    This means the file is a list of dictionaries.

    If they aren't, issue a warning and return an empty list, it is just a cache
    after all!
    """
    result = []
    location = cache_location(root_folder)

    if os.path.exists(location):
        try:
            result = json.load(open(location))
        except (TypeError, ValueError) as error:
            log.warning("Failed to open gitmit cached commit_times\tlocation=%s\terror=%s", location, error)
        else:
            if type(result) is not list or not all(type(item) is dict for item in result):
                log.warning("Gitmit cached commit_times needs to be a list of dictionaries\tlocation=%s\tgot=%s", location, type(result))
                result = []

    return result

def get_cached_commit_times(root_folder, parent_dir, sorted_relpaths):
    """
    Get the cached commit times for the combination of this parent_dir and relpaths

    Return the commit assigned to this combination and the actual times!
    """
    result = get_all_cached_commit_times(root_folder)

    for item in result:
        if sorted(item.get("sorted_relpaths", [])) == sorted_relpaths and item.get("parent_dir") == parent_dir:
            return item.get("commit"), item.get("commit_times")

    return None, {}

def set_cached_commit_times(root_folder, parent_dir, first_commit, commit_times, sorted_relpaths):
    """
    Set the cached commit times in a json file at cache_location(root_folder)

    We first get what is currently in the cache and either modify the existing
    entry for this combo of parent_dir and sorted_relpaths.

    Or add to the entries.

    We then ensure there's less than 5 entries to keep the cache from growing
    too large (arbitrary number is arbitrary).

    Finally, we write the cache or issue a warning if we can't.
    """
    current = get_all_cached_commit_times(root_folder)
    location = cache_location(root_folder)

    found = False
    for item in current:
        if sorted(item.get("sorted_relpaths", [])) == sorted_relpaths and item.get("parent_dir") == parent_dir:
            item["commit_times"] = commit_times
            item["commit"] = str(first_commit)
            found = True
            break

    if not found:
        current.append({"commit": str(first_commit), "parent_dir": parent_dir, "commit_times": commit_times, "sorted_relpaths": sorted_relpaths})

    # Make sure it doesn't grow too big....
    # Arbitrary number is arbitrary
    while len(current) > 5:
        current.pop(0)

    try:
        log.info("Writing gitmit cached commit_times\tlocation=%s", location)
        with open(location, "w") as fle:
            json.dump(current, fle)
    except (TypeError, ValueError, IOError) as error:
        log.warning("Failed to dump gitmit mtime cache\tlocation=%s\terror=%s", location, error)

