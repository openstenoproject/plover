#!/usr/bin/env python3

import contextlib
import hashlib
import os
import sys

import requests


DOWNLOADS_DIR = os.path.join('.cache', 'downloads')


def download(url, sha1=None, filename=None, downloads_dir=DOWNLOADS_DIR):
    session = requests.Session()
    req = requests.Request('GET', url)
    prepped = session.prepare_request(req)
    if filename is None:
        filename = os.path.basename(prepped.path_url)
    dst = os.path.join(downloads_dir, filename)
    dst_dir = os.path.dirname(dst)
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    retries = 0
    while retries < 2:
        if sha1 is None or not os.path.exists(dst):
            retries += 1
            try:
                with contextlib.closing(session.send(prepped, stream=True)) as resp:
                    with open(dst, 'wb') as fp:
                        for chunk in resp.iter_content(chunk_size=4 * 1024):
                            fp.write(chunk)
            except Exception as e:
                print('error', e)
                continue
        if sha1 is None:
            break
        h = hashlib.sha1()
        with open(dst, 'rb') as fp:
            while True:
                d = fp.read(4 * 1024 * 1024)
                if not d:
                    break
                h.update(d)
        if h.hexdigest() == sha1:
            break
        print('sha1 does not match: %s instead of %s' % (h.hexdigest(), sha1))
        os.unlink(dst)
    assert os.path.exists(dst), 'could not successfully retrieve %s' % url
    return dst


if __name__ == '__main__':
    args = sys.argv[1:]
    url = args.pop(0)
    sha1 = None
    filename = None
    if args:
        sha1 = args.pop(0) or None
    if args:
        filename = args.pop(0)
    print(download(url, sha1, filename))
