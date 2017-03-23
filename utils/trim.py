#!/usr/bin/env python3

import glob
import shutil
import sys
import os


def trim(directory, patterns_file, verbose=True):
    with open(patterns_file) as fp:
        for pattern in fp:
            pattern = os.path.join(directory, pattern.strip())
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
