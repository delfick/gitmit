# coding: spec

from tests.helpers import TestCase

from gitmit.repo import Repo, empty

from collections import namedtuple
import uuid
import mock
import os

Entry = namedtuple("Entry", ["name", "type", "oid"])

describe TestCase, "Repo":
    it "takes in the root_folder and creates a libgit Repository from it":
        git = mock.Mock(name="git")
        root_folder = mock.Mock(name="root_folder")
        FakeRepository = mock.Mock(name="FakeRepository", return_value=git)

        with mock.patch("gitmit.repo.Repository", FakeRepository):
            repo = Repo(root_folder)

        self.assertIs(repo.git, git)
        FakeRepository.assert_called_once_with(root_folder)

    describe "all_files":
        it "returns a list of all the paths under git control":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                self.assertEqual(Repo(root_folder).all_files(), set(commit_times.keys()))

        it "includes files that are currently deleted in the working dir":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                os.remove(os.path.join(root_folder, "one"))
                self.assertEqual(Repo(root_folder).all_files(), set(commit_times.keys()))

        it "does not include files that are currently deleted in the index":
            # It would be nice if this wasn't the case to be honest, but oh well.....
            # Leaving test here to know if this behaviour ever changes
            with self.cloned_repo("paths") as (root_folder, commit_times):
                os.remove(os.path.join(root_folder, "one"))
                self.do_git_cmd(root_folder, "add", "one")
                self.assertEqual(Repo(root_folder).all_files(), set(p for p in commit_times.keys() if p != "one"))

    describe "first_commit":
        it "totes returns the oid of the HEAD":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                os.remove(os.path.join(root_folder, "one"))
                head = self.do_git_cmd(root_folder, "rev-parse", "HEAD").strip().decode('utf-8')
                self.assertEqual(str(Repo(root_folder).first_commit), head)

    describe "file_commit_times":
        it "yields the commit oid, commit time and files changed in that commit":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                repo = Repo(root_folder)
                paths = set(["five", "three/four", "one", "two", "seven", "six"])

                expected = [
                    ('6c463ce367c5d7b26da45be6a67456536d944211', 1459036362, sorted(['seven', 'six']))
                  , ('9265c0337a90334d989e758942d86dc60b267a71', 1459034839, ['five'])
                  , ('64c9970cc3cfa981882825d16830e23fec9951b3', 1459034833, ['three/four'])
                  , ('278d6da34464e7a0a430fdce5aedc659e9ae99e0', 1459034798, ['one'])
                  , ('fd76f9c5367989f4a8aea127c4c5a39474c879de', 1459034782, ['two'])
                  ]

                actual = []
                times = {}
                for coid, ctime, differences in repo.file_commit_times(paths):
                    actual.append((str(coid), ctime, sorted(differences)))
                    for name in differences:
                        times[name] = int(ctime)

                self.assertEqual(actual, expected)
                self.assertEqual(times, commit_times)

        it "stops when it's found all the paths it cares about":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                repo = Repo(root_folder)
                paths = set(["three/four"])

                expected = [
                    ('64c9970cc3cfa981882825d16830e23fec9951b3', 1459034833, ['three/four'])
                  ]

                actual = []
                for coid, ctime, differences in repo.file_commit_times(paths):
                    actual.append((str(coid), ctime, differences))

                self.assertEqual(actual, expected)

        it "only yields files it cares about":
            with self.cloned_repo("paths") as (root_folder, commit_times):
                repo = Repo(root_folder)
                paths = set(["three/four", "six", "two"])

                expected = [
                    ('6c463ce367c5d7b26da45be6a67456536d944211', 1459036362, ['six'])
                  , ('64c9970cc3cfa981882825d16830e23fec9951b3', 1459034833, ['three/four'])
                  , ('fd76f9c5367989f4a8aea127c4c5a39474c879de', 1459034782, ['two'])
                  ]

                actual = []
                for coid, ctime, differences in repo.file_commit_times(paths):
                    actual.append((str(coid), ctime, differences))

                self.assertEqual(actual, expected)

    describe "entries_in_tree_oid":
        it "returns empty if tree_oid not in git":
            tree_oid = str(uuid.uuid1())
            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo(str(uuid.uuid1()))
            repo.git = {}
            self.assertIs(repo.entries_in_tree_oid(str(uuid.uuid1()), tree_oid), empty)

        it "gets entries_in_tree as a set if can find a tree":
            tree = mock.Mock(name="tree")
            prefix = mock.Mock(name="prefix")
            tree_oid = mock.Mock(name="tree_oid")

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo(str(uuid.uuid1()))

            repo.git = {tree_oid: tree}
            e1, e2 = mock.Mock(name="e1"), mock.Mock(name="e2")
            fake_entries_in_tree = mock.Mock(name="entries_in_tree", return_value=[e1, e2])

            with mock.patch.multiple(repo, entries_in_tree=fake_entries_in_tree):
                self.assertEqual(repo.entries_in_tree_oid(prefix, tree_oid), set([e1, e2]))

            fake_entries_in_tree.assert_called_once_with(prefix, tree)

    describe "entries_in_tree":
        it "yields new_prefix as just the name if no prefix":
            oid = str(uuid.uuid1())
            name = str(uuid.uuid1())
            tree = [Entry(name, "blob", oid)]

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            self.assertEqual(list(repo.entries_in_tree((), tree)), [((name, ), False, oid)])

        it "yields new_prefix as combination of prefix and name if there is a prefix":
            oid = str(uuid.uuid1())
            name = str(uuid.uuid1())
            tree = [Entry(name, "blob", oid)]
            prefix_part = str(uuid.uuid1())

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            self.assertEqual(list(repo.entries_in_tree((prefix_part, ), tree)), [((prefix_part, name, ), False, oid)])

        it "yields is_tree as True if type is tree":
            oid = str(uuid.uuid1())
            name = str(uuid.uuid1())
            tree = [Entry(name, "tree", oid)]
            prefix_part = str(uuid.uuid1())

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            self.assertEqual(list(repo.entries_in_tree((prefix_part, ), tree)), [((prefix_part, name, ), True, oid)])

    describe "tree_structures_for":
        it "returns empty and empty if prefix not in prefixes":
            prefixes = {1:2}
            prefix = 3

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            self.assertEqual(repo.tree_structures_for(prefix, str(uuid.uuid1()), [str(uuid.uuid1())], prefixes), (empty, empty))

        it "returns entries_for_tree_oid for current files and parent files":
            prefix = str(uuid.uuid1())
            prefixes = {prefix: set(["one"])}
            current_oid = mock.Mock(name="current_oid")
            parent_oid_1 = mock.Mock(name="parent_oid_1")
            parent_oids = [parent_oid_1]

            current_files = set(["one", "two"])
            parent_files = set(["one"])
            changes = set(["two"])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            def entries_in_tree_oid(prefix, oid):
                return {current_oid: current_files, parent_oid_1: parent_files}[oid]
            fake_entries_in_tree_oid = mock.Mock(name="entries_in_tree_oid", side_effect=entries_in_tree_oid)

            with mock.patch.multiple(repo, entries_in_tree_oid=fake_entries_in_tree_oid):
                self.assertEqual(repo.tree_structures_for(prefix, current_oid, parent_oids, prefixes), ((current_files, parent_files), changes))

            self.assertEqual(fake_entries_in_tree_oid.mock_calls, [mock.call(prefix, parent_oid_1), mock.call(prefix, current_oid)])

        it "joins multiple parent_files together":
            prefix = str(uuid.uuid1())
            prefixes = {prefix: set(["one"])}
            current_oid = mock.Mock(name="current_oid")
            parent_oid_1 = mock.Mock(name="parent_oid_1")
            parent_oid_2 = mock.Mock(name="parent_oid_2")
            parent_oids = [parent_oid_1, parent_oid_2]

            current_files = set(["one", "two", "three", "four"])
            parent_files = set(["one", "three", "four"])
            changes = set(["two"])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            def entries_in_tree_oid(prefix, oid):
                return {current_oid: current_files, parent_oid_1: set(["one"]), parent_oid_2: set(["three", "four"])}[oid]
            fake_entries_in_tree_oid = mock.Mock(name="entries_in_tree_oid", side_effect=entries_in_tree_oid)

            with mock.patch.multiple(repo, entries_in_tree_oid=fake_entries_in_tree_oid):
                self.assertEqual(repo.tree_structures_for(prefix, current_oid, parent_oids, prefixes), ((current_files, parent_files), changes))

            self.assertEqual(fake_entries_in_tree_oid.mock_calls, [mock.call(prefix, parent_oid_1), mock.call(prefix, parent_oid_2), mock.call(prefix, current_oid)])

    describe "differences_between":
        it "yields paths if all that has changed is blobs":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, False, oid1), (path2, False, oid2)])
            parent_files = set([(path1, False, oid1)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {}))

            self.assertEqual(result, [(path2, None, True)])

        it "yields nothing if the path is for a tree and not in prefixes":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, True, oid1), (path2, True, oid2)])
            parent_files = set([(path1, True, oid1)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            fake_tree_structures_for = mock.NonCallableMock(name="tree_structures_for")

            with mock.patch.multiple(repo, tree_structures_for=fake_tree_structures_for):
                result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {}))

            self.assertEqual(result, [])

        it "yields next layer if path is indeed in prefixes and it's a tree":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, True, oid1), (path2, True, oid2)])
            parent_files = set([(path1, True, oid1)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            cf_and_pf = mock.Mock(name="cf_and_pf")
            changes = mock.Mock(name="changes")
            fake_tree_structures_for = mock.Mock(name="tree_structures_for", return_value=(cf_and_pf, changes))

            with mock.patch.multiple(repo, tree_structures_for=fake_tree_structures_for):
                result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {path2: True}))

            self.assertEqual(result, [(cf_and_pf, changes, False)])

            fake_tree_structures_for.assert_called_once_with(path2, oid2, frozenset([]), {path2: True})

        it "works when the tree has one parent":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            oid3 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, True, oid1), (path2, True, oid2)])
            parent_files = set([(path1, True, oid1), (path2, True, oid3)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            cf_and_pf = mock.Mock(name="cf_and_pf")
            changes = mock.Mock(name="changes")
            fake_tree_structures_for = mock.Mock(name="tree_structures_for", return_value=(cf_and_pf, changes))

            with mock.patch.multiple(repo, tree_structures_for=fake_tree_structures_for):
                result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {path2: True}))

            self.assertEqual(result, [(cf_and_pf, changes, False)])

            fake_tree_structures_for.assert_called_once_with(path2, oid2, frozenset([oid3]), {path2: True})

        it "works when the tree has more than one parent":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            oid3 = str(uuid.uuid1())
            oid4 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, True, oid1), (path2, True, oid2)])
            parent_files = set([(path1, True, oid1), (path2, True, oid3), (path2, True, oid4)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            cf_and_pf = mock.Mock(name="cf_and_pf")
            changes = mock.Mock(name="changes")
            fake_tree_structures_for = mock.Mock(name="tree_structures_for", return_value=(cf_and_pf, changes))

            with mock.patch.multiple(repo, tree_structures_for=fake_tree_structures_for):
                result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {path2: True}))

            self.assertEqual(result, [(cf_and_pf, changes, False)])

            fake_tree_structures_for.assert_called_once_with(path2, oid2, frozenset([oid3, oid4]), {path2: True})

        it "ignores parents that aren't trees":
            oid1 = str(uuid.uuid1())
            oid2 = str(uuid.uuid1())
            oid3 = str(uuid.uuid1())
            oid4 = str(uuid.uuid1())
            path1 = str(uuid.uuid1())
            path2 = str(uuid.uuid1())
            current_files = set([(path1, True, oid1), (path2, True, oid2)])
            parent_files = set([(path1, True, oid1), (path2, True, oid3), (path2, False, oid4)])

            with mock.patch("gitmit.repo.Repository", mock.Mock(name="Repository")):
                repo = Repo("root_folder")

            cf_and_pf = mock.Mock(name="cf_and_pf")
            changes = mock.Mock(name="changes")
            fake_tree_structures_for = mock.Mock(name="tree_structures_for", return_value=(cf_and_pf, changes))

            with mock.patch.multiple(repo, tree_structures_for=fake_tree_structures_for):
                result = list(repo.differences_between(current_files, parent_files, current_files-parent_files, {path2: True}))

            self.assertEqual(result, [(cf_and_pf, changes, False)])

            fake_tree_structures_for.assert_called_once_with(path2, oid2, frozenset([oid3]), {path2: True})
