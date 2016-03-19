"""
PrefixTree is used to represent what files we have left to process by creating
a folder like tree of all the remaining files::

    tree = Prefixtree()
    tree.fill(["/path/one", "/path/two", "/second_path/three/four"])

    bool(tree) == True

    tree.remove("/second_path/three/four")

    ("second_path", ) in tree == False
    ("second_path", "three") in tree == False

    tree.remove("/path/one")
    tree.remove("/path/two")

    bool(tree) == False

When a file is removed, all empty folders from that point are also removed. So
if there are no other files or folders in that folder, then it is removed.

If after removal, the parent folder has no files or folders, it is also removed,
and so on and so forth.
"""
from collections import namedtuple

empty = frozenset()

TreeItem = namedtuple("TreeItem", ["name", "folders", "files", "parent"])

class PrefixTree(object):
    """
    Holds a linked list like structure for traversal and a cache of
    ("path", "to", "folder") to the tree representing that folder.

    Each Tree is an instance of TreeItem, as initialised after calling
    PrefixTree#fill.

    The idea is you fill the tree once and then remove files one at a time until
    all the files are gone.
    """
    def __init__(self):
        self.tree = TreeItem(name=(), folders={}, files=set(), parent=None)
        self.cache = {}

    def __bool__(self):
        """Check the cache to see if there are any folders left with contents"""
        return bool(self.cache)
    __nonzero__ = __bool__

    def __contains__(self, prefix):
        """
        Determine if we have this prefix in the tree where prefix is a tuple of
        the parts in the path.
        """
        return prefix in self.cache

    def fill(self, paths):
        """
        Initialise the tree.

        paths is a list of strings where each string is the relative path to some
        file.
        """
        for path in paths:
            tree = self.tree
            parts = tuple(path.split('/'))
            dir_parts = parts[:-1]
            built = ()
            for part in dir_parts:
                self.cache[built] = tree
                built += (part, )
                parent = tree
                tree = parent.folders.get(part, empty)
                if tree is empty:
                    tree = parent.folders[part] = TreeItem(name=built, folders={}, files=set(), parent=parent)

            self.cache[dir_parts] = tree
            tree.files.add(parts[-1])

    def remove(self, prefix, name):
        """
        Remove a path from the tree

        prefix is a tuple of the parts in the dirpath

        name is a string representing the name of the file itself.

        Any empty folders from the point of the file backwards to the root of
        the tree is removed.
        """
        tree = self.cache.get(prefix, empty)
        if tree is empty:
            return False

        if name not in tree.files:
            return False

        tree.files.remove(name)
        self.remove_folder(tree, list(prefix))

        return True

    def remove_folder(self, tree, prefix):
        """
        Used to remove any empty folders

        If this folder is empty then it is removed. If the parent is empty as a
        result, then the parent is also removed, and so on.
        """
        while True:
            child = tree
            tree = tree.parent

            if not child.folders and not child.files:
                del self.cache[tuple(prefix)]
                if tree:
                    del tree.folders[prefix.pop()]

            if not tree or tree.folders or tree.files:
                break
