#!/usr/bin/env python3

import glob
import shutil
import sys
import os


def trim(directory, patterns_file, verbose=True):
    # Build list of patterns.
    pattern_list = []
    subdir = directory
    with open(patterns_file) as fp:
        for line in fp:
            line = line.strip()
            # Empty line, ignore.
            if not line:
                continue
            # Comment, ignore.
            if line.startswith('#'):
                continue
            # Sub-directory change.
            if line.startswith(':'):
                subdir = os.path.join(directory, line[1:])
                continue
            # Pattern (relative to current sub-directory).
            pattern_list.append(os.path.join(subdir, line))
    # Trim directory tree.
    for pattern in pattern_list:
        for path in reversed(glob.glob(pattern, recursive=True)):
            if verbose:
                print('removing', path)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)


if __name__ == '__main__':
    directory, patterns_file = sys.argv[1:]
    trim(directory, patterns_file)
