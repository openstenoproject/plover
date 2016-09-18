#!/usr/bin/env python2

# Python 2/3 compatibility.
from __future__ import print_function

import os
import pkg_resources
import sys
import shutil


def collect_requirements(distribution, requirements=None):
    if requirements is None:
        requirements = set()
    for dependency in distribution.requires():
        dependency = pkg_resources.get_distribution(dependency)
        if dependency in requirements:
            continue
        requirements.add(dependency)
        collect_requirements(dependency, requirements)
    return requirements

def get_metadata(distribution):
    egg_info = '%s.egg-info' % distribution.egg_name()
    metadata = distribution.egg_info
    if metadata is None:
        metadata = '%s/%s' % (distribution.location, egg_info)
        if not os.path.exists(metadata):
            metadata = '%s/%s-%s.egg-info' % (
                distribution.location,
                pkg_resources.to_filename(distribution.project_name),
                pkg_resources.to_filename(distribution.version),
            )
            if not os.path.exists(metadata):
                return None
    return (metadata, egg_info)

def collect_metadata(distribution):
    metadata_list = [ get_metadata(distribution) ]
    requirements = collect_requirements(distribution)
    requirements = sorted(requirements, key=lambda d: d.key)
    for dependency in requirements:
        metadata = get_metadata(dependency)
        if metadata is None:
            print('no metadata for: %s' % dependency.project_name)
            continue
        metadata_list.append(metadata)
    return metadata_list

def pack(root_dir, path, archive_name):
    if os.path.isfile(path):
        dest = '%s/%s' % (root_dir, archive_name)
        dest_dir = os.path.dirname(dest)
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)
        shutil.copy(path, dest)
        return
    for entry in os.listdir(path):
        pack(root_dir,
             '%s/%s' % (path, entry),
             '%s/%s' % (archive_name, entry))

def copy_metadata(source, destination):
    distribution = list(pkg_resources.find_distributions(source, only=True))[0]
    print('adding metadata from %s (%s) to %s' % (
        source,
        distribution.project_name,
        destination,
    ))
    for metadata in collect_metadata(distribution):
        print('adding metadata: %s' % metadata[1])
        pack(destination, metadata[0], metadata[1])

if __name__ == '__main__':
    source = sys.argv[1]
    destination = sys.argv[2]
    copy_metadata(source, destination)

