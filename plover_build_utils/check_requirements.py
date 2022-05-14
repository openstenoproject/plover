#!/usr/bin/env python3

from collections import OrderedDict

import pkg_resources

from plover.registry import Registry


def sorted_requirements(requirements):
    return sorted(requirements, key=lambda r: str(r).lower())


# Find all available distributions.
all_requirements = [
    dist.as_requirement()
    for dist in pkg_resources.working_set
]

# Find Plover requirements.
plover_deps = set()
for dist in pkg_resources.require('plover'):
    plover_deps.add(dist.as_requirement())

# Load plugins.
registry = Registry(suppress_errors=False)
registry.update()

# Find plugins requirements.
plugins = OrderedDict()
plugins_deps = set()
for plugin_dist in registry.list_distributions():
    if plugin_dist.dist.project_name != 'plover':
        plugins[plugin_dist.dist.as_requirement()] = set()
for requirement, deps in plugins.items():
    for dist in pkg_resources.require(str(requirement)):
        if dist.as_requirement() not in plover_deps:
            deps.add(dist.as_requirement())
    plugins_deps.update(deps)

# List requirements.
print('# plover')
for requirement in sorted_requirements(plover_deps):
    print(requirement)
for requirement, deps in plugins.items():
    print('#', requirement.project_name)
    for requirement in sorted_requirements(deps):
        print(requirement)
print('# other')
for requirement in sorted_requirements(all_requirements):
    if requirement not in plover_deps and \
       requirement not in plugins_deps:
        print(requirement)
print('# ''vim: ft=cfg commentstring=#\\ %s list')
