# coding: spec

from tests.helpers import TestCase

from gitmit.executor import main

from noseOfYeti.tokeniser.support import noy_sup_setUp
from contextlib import contextmanager
import mock

describe TestCase, "mainline":
    before_each:
        self.fake_setup_logging = mock.Mock(name="setup_logging")
        self.gittimes = mock.Mock(name="gittimes")
        self.gittimes.find.return_value = {}
        self.fakeGitTimes = mock.Mock(name="GitTimes", return_value=self.gittimes)

    @contextmanager
    def patched_things(self):
        with mock.patch("gitmit.executor.setup_logging", self.fake_setup_logging):
            with mock.patch("gitmit.executor.GitTimes", self.fakeGitTimes):
                yield

    it "sets up the argparse and runs GitTimes with the correct arguments":
        with self.patched_things():
            main([])

        self.fake_setup_logging.assert_called_once_with(debug=False)
        self.fakeGitTimes.assert_called_once_with(".", ".", True, None, None, debug=False, with_cache=True)
        self.gittimes.find.assert_called_once_with()

    it "multiple include, exclude and timestamps_for produces list of those itmes":
        with self.patched_things():
            main(["--include", "one", "--exclude", "two", "--include", "three", "--timestamps-for", "four", "--exclude", "five", "--timestamps-for", "six"])

        self.fake_setup_logging.assert_called_once_with(debug=False)
        self.fakeGitTimes.assert_called_once_with(".", ".", ["four", "six"], ["one", "three"], ["two", "five"], debug=False, with_cache=True)
        self.gittimes.find.assert_called_once_with()

    it "--no-cache makes with_cache equal to false":
        with self.patched_things():
            main(["--no-cache"])

        self.fake_setup_logging.assert_called_once_with(debug=False)
        self.fakeGitTimes.assert_called_once_with(".", ".", True, None, None, debug=False, with_cache=False)
        self.gittimes.find.assert_called_once_with()

    it "--debug makes debug equal to true":
        with self.patched_things():
            main(["--debug"])

        self.fake_setup_logging.assert_called_once_with(debug=True)
        self.fakeGitTimes.assert_called_once_with(".", ".", True, None, None, debug=True, with_cache=True)
        self.gittimes.find.assert_called_once_with()

    it "--consider makes the parent_dir change":
        with self.patched_things():
            main(["--consider", "place"])

        self.fake_setup_logging.assert_called_once_with(debug=False)
        self.fakeGitTimes.assert_called_once_with(".", "place", True, None, None, debug=False, with_cache=True)
        self.gittimes.find.assert_called_once_with()

    it "--root-folder makes the root_dir and parent_dir change":
        with self.patched_things():
            main(["--root-folder", "/somewhere/nice", "--consider", "place"])

        self.fake_setup_logging.assert_called_once_with(debug=False)
        self.fakeGitTimes.assert_called_once_with("/somewhere/nice", "place", True, None, None, debug=False, with_cache=True)
        self.gittimes.find.assert_called_once_with()

