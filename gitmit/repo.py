"""
The core of the entire module! This is where we traverse the commits under our
git repository to find the commit times of our files.

The idea is that this is as close to the speed of git log as we can get.
Unfortunately git log is faster than libgit by quite a bit, but for most
repositories, the difference isn't noticeable.

For example, compare the speed of::

    $ time git whatchanged --pretty=%at > /dev/null

and::

    $ time gitmit --no-cache > /dev/null
"""
from gitmit.prefix_tree import PrefixTree

from collections import defaultdict
from pygit2 import Repository
import logging
import fnmatch
import time
import os

empty = frozenset()

log = logging.getLogger("gitmit.repo")

class Repo(object):
    """
    Wrapper around a libgit Repository that knows:

    * How to get all the files in the repository
    * How to get the oid of HEAD
    * How to get the commit times of the files we want commit times for

    It's written with speed in mind, given the constraints of making
    performant code in python!
    """
    def __init__(self, root_folder):
        self.git = Repository(root_folder)

    def all_files(self):
        """Return a set of all the files under git control"""
        return set([entry.path for entry in self.git.index])

    @property
    def first_commit(self):
        """Return the oid of HEAD"""
        return self.git.head.target

    def file_commit_times(self, use_files_paths, debug=False):
        """
        Traverse the commits in the repository, starting from HEAD until we have
        found the commit times for all the files we care about.

        Yield each file once, only when it is found to be changed in some commit.

        If self.debug is true, also output log.debug for the speed we are going
        through commits (output commits/second every 1000 commits and every
        100000 commits)
        """
        prefixes = PrefixTree()
        prefixes.fill(use_files_paths)

        beginning = start = time.time()
        commit_count = 0
        cumalative_commit_count = 0

        for commit in self.git.walk(self.first_commit):
            if debug:
                commit_count += 1

            # Commit time taking into account the offset
            commit_time = commit.commit_time - (commit.commit_time_offset * 60)

            # Get us the two different tree structures between parents and current
            cf_and_pf, changes = self.tree_structures_for((), commit.tree.oid, [p.tree.oid for p in commit.parents], prefixes)

            # Deep dive into any differences
            difference = []
            if changes:
                cfs_and_pfs = [(cf_and_pf, changes)]
                while cfs_and_pfs:
                    nxt, changes = cfs_and_pfs.pop(0)
                    for thing, changes, is_path in self.differences_between(nxt[0], nxt[1], changes, prefixes):
                        if is_path:
                            found = prefixes.remove(thing[:-1], thing[-1])
                            if found:
                                difference.append('/'.join(thing))
                        else:
                            cfs_and_pfs.append((thing, changes))

            # Only yield if there was a difference
            if difference:
                yield commit.oid, commit_time, difference

            if debug and commit_count == 1000:
                cumalative_commit_count += commit_count
                log.debug("{0} commits ({1:.2f} per second)".format(cumalative_commit_count, commit_count / float(time.time() - start)))
                if cumalative_commit_count % 100000 == 0:
                    log.debug("{0:.2f} commits per second".format(cumalative_commit_count / float(time.time() - beginning)))
                start = time.time()
                commit_count = 0

            # If nothing remains, then break!
            if not prefixes:
                break

    def entries_in_tree_oid(self, prefix, tree_oid):
        """Find the tree at this oid and return entries prefixed with ``prefix``"""
        tree = self.git.get(tree_oid, empty)
        if tree is empty:
            log.warning("Couldn't find object {0}".format(tree_oid))
            return empty
        else:
            return frozenset(self.entries_in_tree(prefix, tree))

    def entries_in_tree(self, prefix, tree):
        """
        Traverse the entries in this tree and yield (prefix, is_tree, oid)

        Where prefix is a tuple of the given prefix and the name of the entry.
        """
        for entry in tree:
            if prefix:
                new_prefix = prefix + (entry.name, )
            else:
                new_prefix = (entry.name, )

            yield (new_prefix, entry.type == "tree", entry.oid)

    def tree_structures_for(self, prefix, current_oid, parent_oids, prefixes):
        """
        Return the entries for this commit, the entries of the parent commits,
        and the difference between the two (current_files - parent_files)
        """
        if prefix and prefixes and prefix not in prefixes:
            return empty, empty

        parent_files = set()
        for oid in parent_oids:
            parent_files.update(self.entries_in_tree_oid(prefix, oid))

        current_files = self.entries_in_tree_oid(prefix, current_oid)
        return (current_files, parent_files), (current_files - parent_files)

    def differences_between(self, current_files, parent_files, changes, prefixes):
        """
        yield (thing, changes, is_path)

        If is_path is true, changes is None and thing is the path as a tuple.

        If is_path is false, thing is the current_files and parent_files for
        that changed treeentry and changes is the difference between current_files
        and parent_files.

        The code here is written to squeeze as much performance as possible out
        of this operation.
        """
        parent_oid = None

        if any(is_tree for _, is_tree, _ in changes):
            if len(changes) == 1:
                wanted_path = list(changes)[0][0]
                parent_oid = frozenset([oid for path, is_tree, oid in parent_files if path == wanted_path and is_tree])
            else:
                parent_values = defaultdict(set)
                parent_changes = parent_files - current_files
                for path, is_tree, oid in parent_changes:
                    if is_tree:
                        parent_values[path].add(oid)

        for path, is_tree, oid in changes:
            if is_tree and path not in prefixes:
                continue

            if not is_tree:
                yield path, None, True
            else:
                parent_oids = parent_oid if parent_oid is not None else parent_values.get(path, empty)
                cf_and_pf, changes = self.tree_structures_for(path, oid, parent_oids, prefixes)
                if changes:
                    yield cf_and_pf, changes, False

