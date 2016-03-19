"""
Knows how to get the commit times for the files under a repository.

Taking into account symlinkd files, includes, excludes and a cache.
"""

from gitmit.cache import get_cached_commit_times, set_cached_commit_times
from gitmit.repo import Repo

from collections import namedtuple
import fnmatch
import logging
import json
import os

log = logging.getLogger("gitmit.mit")

empty = frozenset()

Path = namedtuple("Path", ["path", "relpath"])
SymlinkdPath = namedtuple("Path", ["path", "relpath", "real_relpath"])

class GitTimes(object):
    """
    Responsible for determining what files we want commit times for and then
    finding those commit times.

    The order is something like:

    * Git root under ``root_folder``
    * Files under ``parent_dir`` relative to the git root
    * Only including those files in ``timestamps_for`` relative to parent_dir
    * Exclude files in ``exclude`` relative to parent_dir
    * Re-include any files in ``include`` relative to parent_dir

    Where ``timestamps_for``, ``include`` and ``exclude`` are lists of glob
    patterns.

    ``with_cache`` determines whether to write a cache of the found commit
    times under the .git folder and use them instead of trying to find the
    commit times each time.

    The cache is invalidated when the parent_dir and files to find change.
    """
    def __init__(self, root_folder, parent_dir, timestamps_for=None, include=None, exclude=None, silent=False, with_cache=True, debug=False):
        self.debug = debug
        self.silent = silent
        self.include = include
        self.exclude = exclude
        self.with_cache = with_cache
        self.parent_dir = parent_dir
        self.root_folder = root_folder
        self.timestamps_for = timestamps_for

        self.relpath_cache = {}

    def relpath_for(self, path):
        """Find the relative path from here from the parent_dir"""
        if self.parent_dir in (".", ""):
            return path

        if path == self.parent_dir:
            return ""

        dirname = os.path.dirname(path) or "."
        basename = os.path.basename(path)

        cached = self.relpath_cache.get(dirname, empty)
        if cached is empty:
            cached = self.relpath_cache[dirname] = os.path.relpath(dirname, self.parent_dir)

        return os.path.join(cached, basename)

    def find(self):
        """
        Find all the files we want to find commit times for, and any extra files
        under symlinks.

        Then find the commit times for those files and return a dictionary of
        {relative_path: commit_time_as_epoch}
        """
        mtimes = {}

        git = Repo(self.root_folder)
        all_files = git.all_files()
        use_files = set(self.find_files_for_use(all_files))

        # the git index won't find the files under a symlink :(
        # And we include files under a symlink as seperate copies of the files
        # So we still want to generate modified times for those files
        extras = set(self.extra_symlinked_files(use_files))

        # Combine use_files and extras
        use_files.update(extras)

        # Tell the user something
        if not self.silent:
            log.info("Finding modified times for %s/%s git controlled files in %s", len(use_files), len(all_files), self.root_folder)

        # Finally get the dates from git!
        return self.commit_times_for(git, use_files)

    def commit_times_for(self, git, use_files):
        """
        Return commit times for the use_files specified.

        We will use a cache of commit times if self.with_cache is Truthy.

        Finally, we yield (relpath: epoch) pairs where path is relative
        to self.parent_dir and epoch is the commit time in UTC for that path.
        """
        # Use real_relpath if it exists (SymlinkdPath) and default to just the path
        # This is because we _want_ to compare the commits to the _real paths_
        # As git only cares about the symlink itself, rather than files under it
        # We also want to make sure that the symlink targets are included in use_files
        # If they've been excluded by the filters
        use_files_paths = set([getattr(p, "real_relpath", p.path) for p in use_files if p.relpath])

        # Find us the first commit to consider
        first_commit = str(git.first_commit)

        # Try and get our cached commit times
        # If we get a commit then it means we have a match for this parent/sorted_relpaths
        commit_times = {}
        cached_commit, cached_commit_times = None, {}
        if self.with_cache:
            sorted_relpaths = sorted([p.relpath for p in use_files])
            cached_commit, cached_commit_times = get_cached_commit_times(self.root_folder, self.parent_dir, sorted_relpaths)

            if cached_commit == first_commit:
                commit_times = cached_commit_times

        # If we couldn't find cached commit times, we have to do some work
        if not commit_times:
            for commit_id, commit_time, different_paths in git.file_commit_times(use_files_paths, debug=self.debug):
                for path in different_paths:
                    commit_times[path] = commit_time

            if self.with_cache:
                set_cached_commit_times(self.root_folder, self.parent_dir, first_commit, commit_times, sorted_relpaths)

        # Finally, yield the (relpath, commit_time) for all the files we care about.
        for key in use_files:
            if key.relpath:
                path = getattr(key, "real_relpath", key.path)
                if path in commit_times:
                    yield key.relpath, commit_times[path]
                else:
                    log.warning("Couldn't find commit time for {0}".format(key.real_relpath))

    def extra_symlinked_files(self, potential_symlinks):
        """
        Find any symlinkd folders and yield SymlinkdPath objects for each file
        that is found under the symlink.
        """
        for key in list(potential_symlinks):
            location = os.path.join(self.root_folder, key.path)
            real_location = os.path.realpath(location)

            if os.path.islink(location) and os.path.isdir(real_location):
                for root, dirs, files in os.walk(real_location, followlinks=True):
                    for name in files:
                        # So this is joining the name of the symlink
                        # With the name of the file, relative to the real location of the symlink
                        full_path = os.path.join(root, name)
                        rel_location = os.path.relpath(full_path, real_location)
                        symlinkd_path = os.path.join(key.path, rel_location)

                        # We then get that relative to the parent dir
                        dir_part = os.path.relpath(root, real_location)
                        symlinkd_relpath = os.path.normpath(os.path.join(key.relpath, dir_part, name))

                        # And we need the original file location so we can get a commit time for the symlinkd path
                        real_path = os.path.realpath(full_path)
                        real_root_folder = os.path.realpath(self.root_folder)
                        real_relpath = os.path.relpath(real_path, real_root_folder)

                        # So that's path relative to root_folder, path relative to parent_folder
                        # and path relative to root for the target
                        yield SymlinkdPath(symlinkd_path, symlinkd_relpath, real_relpath)

    def find_files_for_use(self, all_files):
        """
        Given a list of all the files to consider, only yield Path objects
        for those we care about, given our filters
        """
        for path in all_files:
            # Find the path relative to the parent dir
            relpath = self.relpath_for(path)

            # Don't care about the ./
            if relpath.startswith("./"):
                relpath = relpath[2:]

            # Only care about paths that aren't filtered
            if not self.is_filtered(relpath):
                yield Path(path, relpath)

    def is_filtered(self, relpath):
        """Say whether this relpath is filtered out"""
        # Only include files under the parent_dir
        if relpath.startswith("../"):
            return True

        # Ignore files that we don't want timestamps from
        if self.timestamps_for is not None and type(self.timestamps_for) is list:
            match = False
            for line in self.timestamps_for:
                if fnmatch.fnmatch(relpath, line):
                    match = True
                    break
            if not match:
                return True

        # Matched is true by default if
        # * Have exclude
        # * No exclude and no include
        matched = self.exclude or not any([self.exclude, self.include])

        # Anything not matching exclude gets included
        if self.exclude:
            for line in self.exclude:
                if fnmatch.fnmatch(relpath, line):
                    matched = False

        # Anything matching include gets included
        if self.include:
            for line in self.include:
                if fnmatch.fnmatch(relpath, line):
                    matched = True
                    break

        return not matched

