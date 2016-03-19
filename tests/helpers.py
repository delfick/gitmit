from contextlib import contextmanager
from unittest import TestCase
import subprocess
import tempfile
import shutil
import sys
import os

if sys.version_info[0] == 3:
    long = int

here = os.path.dirname(__file__)

class TestCase(TestCase):
    @contextmanager
    def a_temp_file(self, body=None):
        fle = None
        try:
            fle = tempfile.NamedTemporaryFile(delete=False).name
            if body:
                with open(fle, "w") as f:
                    f.write(body)
            yield fle
        finally:
            if fle and os.path.exists(fle):
                os.remove(fle)

    @contextmanager
    def a_temp_dir(self):
        dirname = None
        try:
            dirname = tempfile.mkdtemp()
            yield dirname
        finally:
            if dirname and os.path.isdir(dirname):
                shutil.rmtree(dirname)

    def touch_file(self, dirname, relpath):
        with open(os.path.join(dirname, relpath), "w") as fle:
            fle.write("")

    @contextmanager
    def cloned_repo(self, name):
        with self.a_temp_dir() as root_folder:
            bundle = os.path.join(here, "bundles", name, "repo.bundle")
            commit_times = os.path.join(os.path.dirname(bundle), "repo.commit_times")

            if not os.path.exists(bundle):
                raise Exception("No bundle named {0}".format(bundle))

            if not os.path.exists(commit_times):
                raise Exception("No commit times for the bundle! {0}".format(commit_Times))

            commit_times = dict(line.strip().rsplit(" ", 1) for line in open(commit_times).readlines())
            commit_times = dict((key, long(epoch)) for key, epoch in commit_times.items())

            shutil.rmtree(root_folder)
            p = subprocess.Popen(['git', 'clone', bundle, root_folder], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            p.wait()
            if p.poll() != 0:
                raise Exception("Failed to git clone! {0}", p.stdout.read())
            yield root_folder, commit_times

    def do_git_cmd(self, root_folder, *args):
        p = subprocess.Popen(("git", ) + args, cwd=root_folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        if p.poll() != 0:
            raise Exception("Failed to git clone! {0}", p.stdout.read())
        return p.stdout.read()
