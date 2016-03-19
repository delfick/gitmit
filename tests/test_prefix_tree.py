# coding: spec

from tests.helpers import TestCase

from gitmit.prefix_tree import PrefixTree

describe TestCase, "PrefixTree":
    it "instantiates a tree and cache":
        prefix_tree = PrefixTree()

        self.assertEqual(prefix_tree.cache, {})
        self.assertEqual(prefix_tree.tree.name, ())
        self.assertEqual(prefix_tree.tree.folders, {})
        self.assertEqual(prefix_tree.tree.files, set())
        self.assertEqual(prefix_tree.tree.parent, None)

    it "says the tree is nonzero if anything is in the cache":
        prefix_tree = PrefixTree()
        self.assertEqual(prefix_tree.cache, {})
        self.assertEqual(bool(prefix_tree), False)

        prefix_tree.cache[1] = 2
        self.assertEqual(bool(prefix_tree), True)

        del prefix_tree.cache[1]
        self.assertEqual(bool(prefix_tree), False)

    it "says something is in the tree if it can be found in the cache":
        prefix_tree = PrefixTree()
        prefix = ("one", "two")

        assert prefix not in prefix_tree

        prefix_tree.cache[prefix] = True
        assert prefix in prefix_tree

    describe "fill":
        it "creates a linked list like structure using parent, folders and files":
            paths = ["one/two/three", "one/two/four", "one/five", "six"]

            prefix_tree = PrefixTree()
            prefix_tree.fill(paths)

            self.assertEqual(prefix_tree.tree.files, set(["six"]))
            self.assertEqual(list(prefix_tree.tree.folders.keys()), ["one"])
            self.assertIs(prefix_tree.tree.folders["one"].parent, prefix_tree.tree)
            self.assertEqual(list(prefix_tree.tree.folders["one"].folders.keys()), ["two"])
            self.assertEqual(prefix_tree.tree.folders["one"].folders["two"].files, set(["three", "four"]))
            self.assertEqual(prefix_tree.tree.folders["one"].folders["two"].folders, {})
            self.assertEqual(prefix_tree.tree.folders["one"].folders["two"].parent, prefix_tree.tree.folders["one"])

        it "creates a cache of dirparts to treeitems":
            paths = ["one/two/three", "one/two/four", "one/five", "six"]

            prefix_tree = PrefixTree()
            prefix_tree.fill(paths)

            self.assertEqual(prefix_tree.cache[()].files, set(["six"]))
            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three", "four"]))

    describe "remove":
        it "returns False if the prefix is not in the cache":
            prefix_tree = PrefixTree()
            self.assertEqual(prefix_tree.cache, {})
            assert not prefix_tree.remove(("one", ), "thing")

        it "returns False if the file isn't present":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three", "one/two/four"])

            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three", "four"]))

            assert not prefix_tree.remove(("one", "two"), "five")

        it "returns True if the file is present":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three", "one/two/four"])

            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three", "four"]))

            assert prefix_tree.remove(("one", "two"), "four")

        it "attempts to remove the folder if it finds the file":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three", "one/two/four"])
            assert ("one", "two") in prefix_tree

            assert prefix_tree.remove(("one", "two"), "three")
            assert ("one", "two") in prefix_tree

            assert prefix_tree.remove(("one", "two"), "four")
            assert ("one", "two") not in prefix_tree

    describe "remove_folder":
        it "does nothing if the folder has files or folders":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three", "one/two/four"])
            assert ("one", "two") in prefix_tree
            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three", "four"]))

            prefix_tree.remove_folder(prefix_tree.cache[("one", "two")], ["one", "two"])

            assert ("one", "two") in prefix_tree
            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three", "four"]))

            prefix_tree.remove_folder(prefix_tree.cache[("one", )], ["one"])
            assert ("one", ) in prefix_tree
            self.assertEqual(list(prefix_tree.cache[("one", )].folders.keys()), ["two"])

        it "removes just that folder if it's parent isn't empty after removal":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three", "one/four"])
            assert ("one", "two") in prefix_tree
            self.assertEqual(prefix_tree.cache[("one", "two")].files, set(["three"]))

            prefix_tree.cache[("one", "two")].files.pop()
            prefix_tree.remove_folder(prefix_tree.cache[("one", "two")], ["one", "two"])

            assert ("one", "two") not in prefix_tree
            assert ("one", ) in prefix_tree
            self.assertEqual(list(prefix_tree.cache[("one", )].folders.keys()), [])
            self.assertEqual(prefix_tree.cache[("one", )].files, set(["four"]))

        it "removes parent folders until it finds a parent that isn't empty":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three/four", "one/five"])
            assert ("one", "two", "three") in prefix_tree
            self.assertEqual(prefix_tree.cache[("one", "two", "three")].files, set(["four"]))

            prefix_tree.cache[("one", "two", "three")].files.pop()
            prefix_tree.remove_folder(prefix_tree.cache[("one", "two", "three")], ["one", "two", "three"])

            assert ("one", "two", "three") not in prefix_tree
            assert ("one", "two") not in prefix_tree
            assert ("one", ) in prefix_tree
            self.assertEqual(list(prefix_tree.cache[("one", )].folders.keys()), [])
            self.assertEqual(prefix_tree.cache[("one", )].files, set(["five"]))

        it "removes the whole cache if it can":
            prefix_tree = PrefixTree()
            prefix_tree.fill(["one/two/three/four"])
            assert ("one", "two", "three") in prefix_tree
            self.assertEqual(prefix_tree.cache[("one", "two", "three")].files, set(["four"]))

            prefix_tree.cache[("one", "two", "three")].files.pop()
            prefix_tree.remove_folder(prefix_tree.cache[("one", "two", "three")], ["one", "two", "three"])

            assert ("one", "two", "three") not in prefix_tree
            assert ("one", "two") not in prefix_tree
            assert ("one", ) not in prefix_tree
            self.assertEqual(prefix_tree.cache, {})
