#!/usr/bin/env python3

import os
import subprocess
import sys


# Default directory for caching wheels.
if sys.platform.startswith('darwin'):
    WHEELS_CACHE = os.path.expanduser('~/Library/Caches/wheels')
elif sys.platform.startswith('linux'):
    WHEELS_CACHE = os.path.join(os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')), 'wheels')
elif sys.platform.startswith('win32'):
    WHEELS_CACHE = os.path.expanduser(r'~\AppData\Local\wheels')


def _split_opts(text):
    args = text.split()
    assert (len(args) % 2) == 0
    return dict((name, int(nb_args))
                for name, nb_args
                in zip(*([iter(args)] * 2)))


# Allowed `pip install/wheel` options.
_PIP_OPTS = _split_opts(
    # General.
    '''
    --isolated 0
    -v 0 --verbose 0
    -q 0 --quiet 0
    --log 1
    --proxy 1
    --retries 1
    --timeout 1
    --exists-action 1
    --trusted-host 1
    --cert 1
    --client-cert 1
    --cache-dir 1
    --no-cache-dir 0
    --disable-pip-version-check 0
    '''
    # Install/Wheel.
    '''
    -c 1 --constraint 1
    -r 1 --requirement 1
    '''
    # Package Index.
    '''
    -i 1 --index-url 1
    --extra-index-url 1
    --no-index 0
    -f 1 --find-links 1
    --process-dependency-links 0
    '''
)

# Allowed `pip install` only options.
_PIP_INSTALL_OPTS = _split_opts(
    '''
    -t 1 --target 1
    -U 0 --upgrade 0
    --upgrade-strategy 1
    --force-reinstall 0
    -I 0 --ignore-installed 0
    --no-deps 0
    --user 0
    --root 1
    --prefix 1
    --require-hashes 0
    '''
)

def _pip(args, verbose=True):
    if verbose:
        print('running pip %s' % ' '.join(a for a in args))
    return subprocess.call([sys.executable, '-m', 'pip'] + args)

def install_wheels(args, verbose=True):
    wheels_cache = WHEELS_CACHE
    wheel_args = []
    install_args = []
    constraint_args = []
    while len(args) > 0:
        a = args.pop(0)
        if not a.startswith('-'):
            wheel_args.append(a)
            install_args.append(a)
            continue
        if '=' in a:
            a = a.split('=', 2)
            args.insert(0, a[1])
            a = a[0]
        opt = a
        if opt == '-w':
            wheels_cache = args.pop(0)
            continue
        if opt in _PIP_OPTS:
            nb_args = _PIP_OPTS[opt]
            install_only = False
        elif opt in _PIP_INSTALL_OPTS:
            nb_args = _PIP_INSTALL_OPTS[opt]
            install_only = True
        else:
            raise ValueError('unsupported option: %s' % opt)
        a = [opt] + args[:nb_args]
        del args[:nb_args]
        if opt in ('-c', '--constraint'):
            constraint_args.extend(a)
            continue
        if not install_only:
            wheel_args.extend(a)
        install_args.extend(a)
    wheel_args[0:0] = ['wheel', '-f', wheels_cache, '-w', wheels_cache]
    install_args[0:0] = ['install', '-f', wheels_cache]
    if constraint_args:
        # Since pip will not build and cache wheels for VCS links, we do it ourselves:
        # - first, update the cache (without VCS links), and try to install from it
        code = _pip(wheel_args)
        if code == 0:
            code = _pip(install_args)
    else:
        code = 1
    if code != 0:
      # - if it failed, try to update the cache again, this time with VCS links
      code = _pip(wheel_args + constraint_args)
      if code == 0:
          # - and try again
          code = _pip(install_args)
    if code != 0:
        raise Exception('wheels installation failed: pip execution returned %u' % code)


if __name__ == '__main__':
    install_wheels(sys.argv[1:])
