Gitmit
======

This is a library for finding the commit times of all the files under a git
repository.

Can be used from the commandline::

    $ cd /some/repository
    $ gitmit

Or as a library::

    from gitmit.mit import GitTimes
    print(GitTimes(root_folder, ".").find())

Options to both include:

parent_dir
    The relative folder to the root of the repository that we care about. The
    rest of the filters are then relative to here.

timestamps_for
    A list of globs specifying what to include (i.e. anything not covered by the
    globs is ignored)

exclude
    A list of globs specifying what to exclude after timestamps_for is taken into
    account

include
    A list of globs specifying what should be re-included after exclude is
    taken into account

with_cache
    Boolean saying whether we should write the resulting commit times to a file
    under the .git folder that we can reuse in the future.

debug
    Currently the only difference with debug is outputting the commits per second
    as we traverse the commits in the repository.

Why
---

I needed this ability in my Docker client (http://harpoon.readthedocs.org) so
that I could maintain the modified times of the files in the context sent to the
docker daemon between builds on my build servers (doing a git clone sets the
modified times of the files to the time of the clone).

Originally I was shelling out to git log for every file. This was slow! I then
moved to dulwich (python implementation of git) which was faster, but still
slow. Finally I implemented it with pygit2 (libgit2 c bindings in python) and
decided to make it a separate library.

Unfortunately it's still not as fast as doing a ``git whatchanged --pretty=%at``
and interpreting the results, but I rather a solution that uses libraries rather
than interpreting text from the output of a program and the speed is not a
problem for reasonably sized repositories.

Installation
------------

Just use pip::

    $ pip install gitmit

Tests
-----

Install testing deps and run the helpful script::

    $ pip install -e .
    $ pip install -e ".[tests]"
    $ ./test.sh

Or use tox::

    $ pip install tox
    $ tox

