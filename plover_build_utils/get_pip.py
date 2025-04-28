#!/usr/bin/env python3

import os
import sys
import subprocess

def get_pip(args=None):
    os.makedirs("build", exist_ok=True)

    cmd = ["curl", "https://bootstrap.pypa.io/get-pip.py", "-o", "build/get-pip.py"]
    subprocess.call(cmd)
    cmd = [sys.executable,"build/get-pip.py","pip==25.1"]
    subprocess.call(cmd)
    if args:
        cmd = [sys.executable, "-m", "pip", "install"] + args
        print('running', ' '.join(cmd), flush=True)
        subprocess.check_call(cmd)



if __name__ == '__main__':
    get_pip(sys.argv[1:])
