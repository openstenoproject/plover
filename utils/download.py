#!/usr/bin/env python3

import contextlib
import hashlib
import os
import sys

import requests


def download(url, checksum, dst):
    import requests
    retries = 0
    while retries < 2:
        if not os.path.exists(dst):
            retries += 1
            try:
                with contextlib.closing(requests.get(url, stream=True)) as r:
                    with open(dst, 'wb') as fp:
                        for chunk in iter(lambda: r.raw.read(4 * 1024), b''):
                            fp.write(chunk)
            except Exception as e:
                print('error', e)
                continue
        h = hashlib.sha1()
        with open(dst, 'rb') as fp:
            while True:
                d = fp.read(4 * 1024 * 1024)
                if not d:
                    break
                h.update(d)
        if h.hexdigest() == checksum:
            break
        print('sha1 does not match: %s instead of %s' % (h.hexdigest(), checksum))
        os.unlink(dst)
    assert os.path.exists(dst), 'could not successfully retrieve %s' % url


if __name__ == '__main__':
    url, sha1, dst = sys.argv[1:]
    download(url, sha1, dst)
