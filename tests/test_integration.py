# coding: spec

from tests.helpers import TestCase

from gitmit.mit import GitTimes

describe TestCase, "Integration":
    def assertCorrectFor(self, name, make_commit_times=lambda ct: ct):
        with self.cloned_repo(name) as (root_folder, commit_times):
            result = dict(GitTimes(root_folder, '.').find())
            self.assertEqual(result, make_commit_times(commit_times))

            # And test again with the cache
            result = dict(GitTimes(root_folder, '.').find())
            self.assertEqual(result, make_commit_times(commit_times))

    it "works with symlinks and paths and such":
        def maker(commit_times):
            # Need to include the symlink!
            commit_times = dict(commit_times)
            commit_times["five/four"] = commit_times["three/four"]
            return commit_times
        self.assertCorrectFor("paths", maker)

    it "works with merge commits that don't introduce any changes":
        self.assertCorrectFor("merge_with_no_changes")

    it "works with merge commits that do introduce changes":
        self.assertCorrectFor("merge_with_changes")

    it "works when a folder replaces a file":
        self.assertCorrectFor("tree_that_was_a_blob")

    it "works when a file replaces a folder":
        self.assertCorrectFor("blob_that_was_a_tree")

describe TestCase, "filters":
    it "works with symlinks when the target is excluded":
        def maker(commit_times):
            commit_times = dict(commit_times)

            # Need to include the symlink!
            commit_times["five/four"] = commit_times["three/four"]

            # Need to exclude the three folder
            commit_times = dict((key, epoch) for key, epoch in commit_times.items() if not key.startswith("three"))

            return commit_times

        with self.cloned_repo("paths") as (root_folder, commit_times):
            result = dict(GitTimes(root_folder, '.', exclude=["three/**"]).find())
            self.assertEqual(result, maker(commit_times))

            # And test with the cache
            result = dict(GitTimes(root_folder, '.', exclude=["three/**"]).find())
            self.assertEqual(result, maker(commit_times))

    it "works with symlinks when the parent_dir is above the target of the symlink":
        with self.cloned_repo("paths") as (root_folder, commit_times):
            result = dict(GitTimes(root_folder, 'five').find())
            self.assertEqual(result, {"four": commit_times["three/four"]})

            # And test with the cache
            result = dict(GitTimes(root_folder, 'five').find())
            self.assertEqual(result, {"four": commit_times["three/four"]})

