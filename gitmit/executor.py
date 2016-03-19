"""
Creation of a cli tool! Once gitmit is installed, you will have the ``gitmit``
command::

    $ cd /some/repository
    $ gitmit
    <timestamp> <file>
    <timestamp> <file>
    ...

Run gitmit --help to see the options available.
"""

from gitmit.mit import GitTimes

import argparse
import logging
import sys
import os

def setup_logging(debug=False):
    log = logging.getLogger()
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("\033[1;37m%(asctime)s %(levelname)-7s %(name)-15s %(message)s\033[0m"))
    log.addHandler(handler)
    log.setLevel([logging.INFO, logging.DEBUG][debug])

def main(argv=None):
    parser = argparse.ArgumentParser(description="Tool for finding the commit times of all files under a git repository")

    parser.add_argument("--debug"
        , help = "Show debug output"
        , action = "store_true"
        )

    parser.add_argument("--root-folder"
        , help = "The root of the git repository"
        , default = "."
        )

    parser.add_argument("--consider"
        , help = "The part of the repository relative to the root_folder that we want to get commit times for"
        , default = "."
        )

    parser.add_argument("--timestamps-for"
        , help = "Glob to say which paths relative to the consider that we should actually get commit times for (can be specified multiple times)"
        , action = "append"
        )

    parser.add_argument("--include"
        , help = "A list of globs of what should be included in the results after excluded is taken into account (can be specified multiple times)"
        , action = "append"
        )

    parser.add_argument("--exclude"
        , help = "A list of globs of what should be excluded from the results (can be specified multiple times)"
        , action = "append"
        )

    parser.add_argument("--no-cache"
        , help = "Whether to create a cache of the commit times"
        , action = "store_true"
        )

    args = parser.parse_args(argv)
    setup_logging(debug=args.debug)

    timestamps_for = args.timestamps_for
    if not timestamps_for:
        timestamps_for = True

    commit_times = GitTimes(args.root_folder, args.consider, timestamps_for, args.include, args.exclude, with_cache=not args.no_cache, debug=args.debug)
    results = commit_times.find()
    for key, epoch in results:
        print("{0} {1}".format(epoch, key))

if __name__ == "__main__":
    main()

