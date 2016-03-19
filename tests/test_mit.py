# coding: spec

from tests.helpers import TestCase

from gitmit.mit import GitTimes, Path, SymlinkdPath
from gitmit import cache

from noseOfYeti.tokeniser.support import noy_sup_setUp
import uuid
import mock
import os

describe TestCase, "GitTimes":
    it "takes in a few arguments":
        debug = str(uuid.uuid1())
        silent = str(uuid.uuid1())
        exclude = str(uuid.uuid1())
        include = str(uuid.uuid1())
        with_cache = str(uuid.uuid1())
        parent_dir = str(uuid.uuid1())
        root_folder = str(uuid.uuid1())
        timestamps_for = str(uuid.uuid1())

        gittimes = GitTimes(root_folder, parent_dir, timestamps_for=timestamps_for, include=include, exclude=exclude, silent=silent, with_cache=with_cache, debug=debug)

        assert gittimes.debug is debug
        assert gittimes.silent is silent
        assert gittimes.exclude is exclude
        assert gittimes.include is include
        assert gittimes.with_cache is with_cache
        assert gittimes.parent_dir is parent_dir
        assert gittimes.root_folder is root_folder
        assert gittimes.timestamps_for is timestamps_for

    describe "relpath_for":
        it "takes in a path and returns that path relative to the parent_dir":
            gittimes = GitTimes("/somewhere/nice", "subtree")

            # Do same folders multiple times to exercise the caching functionality
            self.assertEqual(gittimes.relpath_for("blah/things"), "../blah/things")
            self.assertEqual(gittimes.relpath_for("blah/other"), "../blah/other")
            self.assertEqual(gittimes.relpath_for("subtree/meh/yeap"), "meh/yeap")
            self.assertEqual(gittimes.relpath_for("subtree/stuff/tree"), "stuff/tree")
            self.assertEqual(gittimes.relpath_for("subtree/stuff/tree2"), "stuff/tree2")

        it "returns the path as is if no parent_dir":
            path = mock.NonCallableMock(name="path")

            gittimes = GitTimes("/somewhere/nice", "")
            self.assertEqual(gittimes.relpath_for(path), path)

            gittimes = GitTimes("/somewhere/nice", ".")
            self.assertEqual(gittimes.relpath_for(path), path)

        it "returns the correct thing for a path with no dirname":
            gittimes = GitTimes("/somewhere/nice", "stuff")
            self.assertEqual(gittimes.relpath_for("hello"), "../hello")

        it "returns empty string if the path is the parent_dir":
            gittimes = GitTimes("/somewhere/nice", "stuff")
            self.assertEqual(gittimes.relpath_for("stuff"), "")

    describe "find":
        it "finds use_files, extras and then commit times for those":
            fle1, fle2, fle3, fle4 = mock.Mock(name="fle1"), mock.Mock(name="fle2"), mock.Mock(name="fle3"), mock.Mock(name="fle4")

            repo = mock.Mock(name="repo")
            FakeRepo = mock.Mock(name="Repo", return_value=repo)
            repo.all_files.return_value = [fle1, fle2]

            commit_times = mock.Mock(name="commit_times")
            fake_find_files_for_use = mock.Mock(name="find_files_for_use", return_value=[fle1])
            def fake_extra_symlinked_files(use_files):
                self.assertEqual(use_files, set([fle1]))
                return set([fle3, fle4])
            fake_extra_symlinked_files = mock.Mock(name="fake_extra_symlinked_files", side_effect=fake_extra_symlinked_files)
            fake_commit_times_for = mock.Mock(name="commit_times_for", return_value=commit_times)

            root_folder = mock.Mock(name="root_folder")
            parent_dir = mock.Mock(name="parent_dir")
            gittimes = GitTimes(root_folder, parent_dir)

            with mock.patch.multiple(gittimes, find_files_for_use=fake_find_files_for_use, extra_symlinked_files=fake_extra_symlinked_files, commit_times_for=fake_commit_times_for):
                with mock.patch("gitmit.mit.Repo", FakeRepo):
                    self.assertIs(gittimes.find(), commit_times)

            FakeRepo.assert_called_once_with(root_folder)
            fake_find_files_for_use.assert_called_once_with([fle1, fle2])
            fake_commit_times_for.assert_called_once_with(repo, set([fle1, fle3, fle4]))

    describe "commit_times_for":
        it "uses cached_commit_times if it can find them":
            t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
            parent_dir = "one"
            first_commit = str(uuid.uuid1())

            git = mock.Mock(name="git", spec=["first_commit"], first_commit=first_commit)

            with self.a_temp_dir() as root_folder:
                os.mkdir(os.path.join(root_folder, ".git"))
                cache.set_cached_commit_times(root_folder, parent_dir, first_commit, {"one/two": t1, "one/three": t2}, ["three", "two"])

                gittimes = GitTimes(root_folder, parent_dir)
                use_files = [Path("one/two", "two"), Path("one/three", "three")]
                self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t1, "three": t2})

        it "does not use cached_commit_times if not with_cache":
            t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
            parent_dir = "one"
            first_commit = str(uuid.uuid1())
            second_commit = str(uuid.uuid1())

            git = mock.Mock(name="git", spec=["first_commit", "file_commit_times"], first_commit=first_commit)
            git.file_commit_times.return_value = [(first_commit, t1, ["one/two"]), (second_commit, t2, ["one/three"])]

            with self.a_temp_dir() as root_folder:
                os.mkdir(os.path.join(root_folder, ".git"))
                cache.set_cached_commit_times(root_folder, parent_dir, first_commit, {"one/two": t1, "one/three": t2}, ["three", "two"])

                gittimes = GitTimes(root_folder, parent_dir, with_cache=False)
                use_files = [Path("one/two", "two"), Path("one/three", "three")]
                self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t1, "three": t2})

                # If it calls this, then we didn't use the cache
                git.file_commit_times.assert_called_once_with(set(["one/two", "one/three"]), debug=False)

        it "sets cached_commit_times if with_cache":
            t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
            parent_dir = "one"
            first_commit = str(uuid.uuid1())
            second_commit = str(uuid.uuid1())

            git = mock.Mock(name="git", spec=["first_commit", "file_commit_times"], first_commit=first_commit)
            git.file_commit_times.return_value = [(first_commit, t1, ["one/two"]), (second_commit, t2, ["one/three"])]

            with self.a_temp_dir() as root_folder:
                os.mkdir(os.path.join(root_folder, ".git"))

                gittimes = GitTimes(root_folder, parent_dir)
                use_files = [Path("one/two", "two"), Path("one/three", "three")]
                self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t1, "three": t2})

                self.assertEqual(cache.get_all_cached_commit_times(root_folder)
                    , [ {"parent_dir": parent_dir, "commit": first_commit, "commit_times": {"one/two": t1, "one/three": t2}, "sorted_relpaths": ["three", "two"]}
                      ]
                    )

        it "does not set cached times if not with_cache":
            t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
            parent_dir = "one"
            first_commit = str(uuid.uuid1())
            second_commit = str(uuid.uuid1())

            git = mock.Mock(name="git", spec=["first_commit", "file_commit_times"], first_commit=first_commit)
            git.file_commit_times.return_value = [(first_commit, t1, ["one/two"]), (second_commit, t2, ["one/three"])]

            with self.a_temp_dir() as root_folder:
                os.mkdir(os.path.join(root_folder, ".git"))

                gittimes = GitTimes(root_folder, parent_dir, with_cache=False)
                use_files = [Path("one/two", "two"), Path("one/three", "three")]
                self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t1, "three": t2})

                self.assertEqual(cache.get_all_cached_commit_times(root_folder), [])

        describe "with symlinks":
            it "uses the relpath of the target in use_files to ensure we get a commit times for the target":
                t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
                parent_dir = "one"
                first_commit = str(uuid.uuid1())
                second_commit = str(uuid.uuid1())

                git = mock.Mock(name="git", first_commit=first_commit)
                git.file_commit_times.return_value = [(first_commit, t1, ["three/four", "three/five"]), (second_commit, t2, ["one/three", "one/two"])]

                with self.a_temp_dir() as root_folder:
                    gittimes = GitTimes(root_folder, parent_dir)
                    use_files = [
                          Path("one/two", "two")
                        , Path("one/three", "three")
                        , SymlinkdPath("one/six/four", "six/four", "three/four")
                        , SymlinkdPath("one/six/five", "six/five", "three/five")
                        ]

                    self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t2, "three": t2, "six/four": t1, "six/five": t1})

                    git.file_commit_times.assert_called_once_with(set(["one/two", "one/three", "three/four", "three/five"]), debug=False)

            it "doesn't complain if it can't find the target":
                t1, t2 = str(uuid.uuid1()), str(uuid.uuid1())
                parent_dir = "one"
                first_commit = str(uuid.uuid1())
                second_commit = str(uuid.uuid1())

                git = mock.Mock(name="git", first_commit=first_commit)
                git.file_commit_times.return_value = [(first_commit, t1, ["three/four"]), (second_commit, t2, ["one/three", "one/two"])]

                with self.a_temp_dir() as root_folder:
                    gittimes = GitTimes(root_folder, parent_dir)
                    use_files = [
                          Path("one/two", "two")
                        , Path("one/three", "three")
                        , SymlinkdPath("one/six/four", "six/four", "three/four")
                        , SymlinkdPath("one/six/five", "six/five", "three/five")
                        ]

                    self.assertEqual(dict(gittimes.commit_times_for(git, use_files)), {"two": t2, "three": t2, "six/four": t1})

                    git.file_commit_times.assert_called_once_with(set(["one/two", "one/three", "three/four", "three/five"]), debug=False)

    describe "extra_symlinked_files":
        it "returns us SymlinkdPath objects representing where in the repo, where the symlink is, where the target is":
            with self.a_temp_dir() as dirname:
                os.mkdir(os.path.join(dirname, "one"))
                os.symlink(os.path.join(dirname, "one"), os.path.join(dirname, "two"))
                self.touch_file(dirname, "one/three")

                gittimes = GitTimes(dirname, "two")
                self.assertEqual(list(gittimes.extra_symlinked_files([Path("two", ".")])), [SymlinkdPath("two/three", "three", "one/three")])

        it "works for symlinks in symlinks":
            with self.a_temp_dir() as dirname:
                os.mkdir(os.path.join(dirname, "one"))
                os.symlink(os.path.join(dirname, "one"), os.path.join(dirname, "two"))
                self.touch_file(dirname, "one/three")
                self.touch_file(dirname, "one/four")

                os.symlink(os.path.join(dirname, "one/four"), os.path.join(dirname, "two/seven"))

                gittimes = GitTimes(dirname, "two")
                expected = sorted([SymlinkdPath("two/four", "four", "one/four"), SymlinkdPath("two/three", "three", "one/three"), SymlinkdPath("two/seven", "seven", "one/four")])
                result = sorted(list(gittimes.extra_symlinked_files([Path("two", ".")])))
                self.assertEqual(result, expected)

        it "works with parent_dir same as root_folder":
            with self.a_temp_dir() as dirname:
                os.mkdir(os.path.join(dirname, "one"))
                os.symlink(os.path.join(dirname, "one"), os.path.join(dirname, "two"))
                self.touch_file(dirname, "one/three")
                self.touch_file(dirname, "one/four")

                os.symlink(os.path.join(dirname, "one/four"), os.path.join(dirname, "two/seven"))

                gittimes = GitTimes(dirname, ".")
                expected = sorted([SymlinkdPath("two/four", "two/four", "one/four"), SymlinkdPath("two/three", "two/three", "one/three"), SymlinkdPath("two/seven", "two/seven", "one/four")])
                result = sorted(list(gittimes.extra_symlinked_files([Path("one/three", "one/three"), Path("one/four", "one/four"), Path("two", "two")])))
                self.assertEqual(result, expected)

    describe "find_files_for_use":
        it "finds relpath_for and then yields Path if not is_filtered":
            r1, p1 = "./r1", mock.Mock(name="p1")
            r2, p2 = mock.Mock(name="r2"), mock.Mock(name="p2")
            r2.startswith.return_value = False
            r3, p3 = "./one/two/three", mock.Mock(name="p3")
            all_files = [p1, p2, p3]

            def relpath_for(p):
                return {p1: r1, p2: r2, p3: r3}[p]
            fake_relpath_for = mock.Mock(name="relpath_for", side_effect=relpath_for)

            def is_filtered(p):
                return {"r1": False, r2: True, "one/two/three": False}[p]
            fake_is_filtered = mock.Mock(name="is_filtered", side_effect=is_filtered)

            root_folder = mock.Mock(name="root_folder")
            parent_dir = mock.Mock(name="parent_dir")
            gittimes = GitTimes(root_folder, parent_dir)

            with mock.patch.multiple(gittimes, relpath_for=fake_relpath_for, is_filtered=fake_is_filtered):
                self.assertEqual(list(gittimes.find_files_for_use(all_files)), [Path(p1, "r1"), Path(p3, "one/two/three")])

    describe "is_filtered":
        before_each:
            self.root_folder = mock.Mock(name="root_folder")
            self.parent_dir = mock.Mock(name="parent_dir")
            self.gittimes = GitTimes(self.root_folder, self.parent_dir)

        it "says yes if relpath starts with ../":
            assert self.gittimes.is_filtered("../abc")

        it "says yes if relpath doesn't match anything in timestamps_for":
            self.gittimes.timestamps_for = ["blah/**"]
            assert self.gittimes.is_filtered("meh")
            assert not self.gittimes.is_filtered("blah/one")

        it "says no if no timestamps_for, exclude or include":
            self.assertIs(self.gittimes.timestamps_for, None)
            self.assertIs(self.gittimes.include, None)
            self.assertIs(self.gittimes.exclude, None)
            assert not self.gittimes.is_filtered("somewhere")

        it "says no if matches timestamps_for and no exclude or include":
            self.gittimes.timestmaps_for = ["some*"]
            self.assertIs(self.gittimes.include, None)
            self.assertIs(self.gittimes.exclude, None)
            assert not self.gittimes.is_filtered("somewhere")

        it "says yes if matches anything in exclude":
            self.gittimes.exclude = ["some*"]
            assert self.gittimes.is_filtered("somewhere")
            assert not self.gittimes.is_filtered("other")

        it "says yes if matches anything in exclude and something in include":
            self.gittimes.exclude = ["some*"]
            self.gittimes.include = ["something"]
            assert not self.gittimes.is_filtered("something")
            assert self.gittimes.is_filtered("somewhere")
            assert not self.gittimes.is_filtered("other")

