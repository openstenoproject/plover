# `plover.resource` -- Resources

This module contains utility functions for accessing resources. All of these
functions involve the use of asset paths; see {ref}`asset-paths` below for more
information.

```{py:module} plover.resource
```

```{function} resource_exists(resource_name)
Return `True` if the resource with the given file name or asset path
exists, `False` otherwise.
```

```{function} resource_filename(resource_name)
If `resource_name` is an asset path, return the file name of the resource
it refers to; return the file name as is otherwise.
```

```{function} resource_timestamp(resource_name)
Return the last modified time of the resource with the given file name or
asset path.
```

````{function} resource_update(resource_name)
A context manager to update the contents of the resource with the given
file name or asset path. The context manager provides as a value the name of
a temporary file that the caller may write to. When the context manager
exits, the file is written to the original resource file.

This allows you to update the resource without destroying the existing
contents if it fails.

```
with resource_update(foo) as temp_filename:
  with open(temp_filename, mode="w") as temp_file:
    # Do things with `temp_file`
    pass
```
````

(asset-paths)=

## Asset Paths

Plover uses asset paths to find resources within both the base Plover
distribution as well as plugins. Asset paths have the format:

    asset:<plugin>:<relative_path>

For example, the default word list, called `main.json` in the `plover`
package, uses this asset path:

    asset:plover:assets/main.json
