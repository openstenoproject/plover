
from collections import defaultdict
import site

from pkginfo.distribution import Distribution as Metadata
from pkg_resources import DistInfoDistribution, WorkingSet, find_distributions

from plover.plugins_manager.plugin_metadata import PluginMetadata
from plover.plugins_manager.utils import running_under_virtualenv

from plover import log


def list_plugins():
    working_set = WorkingSet()
    # Make sure user site packages are added
    # to the set so user plugins are listed.
    user_site_packages = site.USER_SITE
    if not running_under_virtualenv() and \
       user_site_packages not in working_set.entries:
        working_set.entry_keys.setdefault(user_site_packages, [])
        working_set.entries.append(user_site_packages)
        for dist in find_distributions(user_site_packages, only=True):
            working_set.add(dist, user_site_packages, replace=True)
    plugins = defaultdict(list)
    for dist in working_set.by_key.values():
        if dist.key == 'plover':
            continue
        for entrypoint_type in dist.get_entry_map().keys():
            if entrypoint_type.startswith('plover.'):
                break
        else:
            continue
        if isinstance(dist, DistInfoDistribution):
            metadata_entry = 'METADATA'
        else:
            # Assume it's an egg distribution...
            metadata_entry = 'PKG-INFO'
        if not dist.has_metadata(metadata_entry):
            log.warning('ignoring distribution (missing metadata): %s', dist)
            continue
        metadata = Metadata()
        metadata.parse(dist.get_metadata(metadata_entry))
        plugin_metadata = PluginMetadata.from_dict({
            attr: getattr(metadata, attr)
            for attr in PluginMetadata._fields
        })
        plugins[dist.key].append(plugin_metadata)
    return {
        name: list(sorted(versions))
        for name, versions in plugins.items()
    }
