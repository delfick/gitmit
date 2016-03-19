#coding: spec

from tests.helpers import TestCase

from gitmit import cache

from noseOfYeti.tokeniser.support import noy_sup_setUp
import json
import uuid
import os

describe TestCase, "cache_location":
    it "joins the .git folder with gitmit_cached_commit_times.json":
        with self.a_temp_dir() as dirname:
            self.assertEqual(cache.cache_location(dirname), "{0}/.git/gitmit_cached_commit_times.json".format(dirname))

describe TestCase, "get_all_cached_commit_times":
    it "returns an empty array if the cache doesn't exist":
        with self.a_temp_dir() as dirname:
            self.assertEqual(cache.get_all_cached_commit_times(dirname), [])

    it "returns an empty array if the cache isn't valid json":
        with self.a_temp_dir() as dirname:
            git_folder = os.path.join(dirname, ".git")
            os.mkdir(git_folder)

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write("[")

            self.assertEqual(cache.get_all_cached_commit_times(dirname), [])

    it "returns an empty array if the cache isn't a list of dictionaries":
        with self.a_temp_dir() as dirname:
            git_folder = os.path.join(dirname, ".git")
            os.mkdir(git_folder)

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write("[1, 2]")

            self.assertEqual(cache.get_all_cached_commit_times(dirname), [])

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write('{"1":2}')

            self.assertEqual(cache.get_all_cached_commit_times(dirname), [])

    it "returns the result if it's a list of dictionaries":
        with self.a_temp_dir() as dirname:
            git_folder = os.path.join(dirname, ".git")
            os.mkdir(git_folder)

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write('[{"1":2}, {"3":4}]')

            self.assertEqual(cache.get_all_cached_commit_times(dirname), [{"1":2}, {"3":4}])

describe TestCase, "get_cached_commit_times":
    before_each:
        self.commit = str(uuid.uuid1())
        self.commit_times = str(uuid.uuid1())
        self.parent_dir = str(uuid.uuid1())
        self.relpath1 = str(uuid.uuid1())
        self.relpath2 = str(uuid.uuid1())
        self.sorted_relpaths = sorted([self.relpath1, self.relpath2])

    it "returns None, {} if it can't match to parent_dir and sorted_relpaths":
        with self.a_temp_dir() as dirname:
            git_folder = os.path.join(dirname, ".git")
            os.mkdir(git_folder)

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write('[{"1":2}, {"3":4}]')

            self.assertEqual(cache.get_cached_commit_times(dirname, self.parent_dir, self.sorted_relpaths), (None, {}))

    it "returns the commit id and the commit_times if parent_dir, sorted_relpaths combination can be found":
        with self.a_temp_dir() as dirname:
            git_folder = os.path.join(dirname, ".git")
            os.mkdir(git_folder)

            with open(cache.cache_location(dirname), "w") as fle:
                fle.write(json.dumps(
                    [{"parent_dir": self.parent_dir, "sorted_relpaths": self.sorted_relpaths, "commit": self.commit, "commit_times": self.commit_times}]
                ))
            self.assertEqual(cache.get_cached_commit_times(dirname, self.parent_dir, self.sorted_relpaths), (self.commit, self.commit_times))

describe TestCase, "set_cached_commit_times":
    before_each:
        self.first_commit = str(uuid.uuid1())
        self.commit_times = str(uuid.uuid1())
        self.parent_dir = str(uuid.uuid1())
        self.relpath1 = str(uuid.uuid1())
        self.relpath2 = str(uuid.uuid1())
        self.sorted_relpaths = sorted([self.relpath1, self.relpath2])

    it "doesn't complain if it can't write to the cache location":
        with self.a_temp_dir() as dirname:
            assert not os.path.exists(os.path.join(dirname, ".git"))
            cache.set_cached_commit_times(dirname, self.parent_dir, self.first_commit, self.commit_times, self.sorted_relpaths)
            assert not os.path.exists(cache.cache_location(dirname))

    it "adds to the current cache":
        with self.a_temp_dir() as dirname:
            os.mkdir(os.path.join(dirname, ".git"))
            cache.set_cached_commit_times(dirname, self.parent_dir, self.first_commit, self.commit_times, self.sorted_relpaths)

            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [{"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}]
                )

            parent_dir2 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir2, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

    it "removes the oldest item if there is already 5 in the list":
        with self.a_temp_dir() as dirname:
            os.mkdir(os.path.join(dirname, ".git"))
            cache.set_cached_commit_times(dirname, self.parent_dir, self.first_commit, self.commit_times, self.sorted_relpaths)

            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [{"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}]
                )

            parent_dir2 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir2, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

            parent_dir3 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir3, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir3, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

            parent_dir4 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir4, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir3, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir4, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

            parent_dir5 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir5, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir3, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir4, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir5, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

            parent_dir6 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, parent_dir6, self.first_commit, self.commit_times, self.sorted_relpaths)
            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [ {"parent_dir": parent_dir2, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir3, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir4, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir5, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  , {"parent_dir": parent_dir6, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}
                  ]
                )

    it "alters the entry if it has the same parent_dir and sorted_relpaths":
        with self.a_temp_dir() as dirname:
            os.mkdir(os.path.join(dirname, ".git"))
            cache.set_cached_commit_times(dirname, self.parent_dir, self.first_commit, self.commit_times, self.sorted_relpaths)

            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [{"parent_dir": self.parent_dir, "commit": self.first_commit, "commit_times": self.commit_times, "sorted_relpaths": self.sorted_relpaths}]
                )

            commit_times2 = str(uuid.uuid1())
            commit2 = str(uuid.uuid1())
            cache.set_cached_commit_times(dirname, self.parent_dir, commit2, commit_times2, self.sorted_relpaths)

            self.assertEqual(cache.get_all_cached_commit_times(dirname)
                , [{"parent_dir": self.parent_dir, "commit": commit2, "commit_times": commit_times2, "sorted_relpaths": self.sorted_relpaths}]
                )

