# Publishing Plugins

Once you've finished testing your plugin works as expected, you're ready to
publish it to be installed by other users that are not developers. This is done
by uploading your package to [Python Package Index](https://pypi.org/) (PyPI) with some
guidelines around it.

Those guidelines up front:

- Your plugin's name as defined in your setup files should start with
  `plover-` to avoid clashing with general Python package namespaces
- Your plugin's setup files must define one of its keywords to be
  `plover_plugin` as this is how the plugin manager finds it on PyPI
- Your plugin's setup files must define a `long_description`. The plugin
  manager can display plain text, `.rst`, or `.md` files specified here.
- Your plugin should only use features that the distributed version of Plover
  supports in order to prevent errors for end users; that version can be
  verified by looking at Plover's setup files.

The first thing you need to do to actually publish is make an account on PyPI
which should be relatively straightforward.

There are a myriad of ways to actually build and publish a package but the
easiest and most recommended way to publish to PyPI is by running `twine` in
your plugin directory like so:

    python setup.py sdist bdist_wheel
    twine upload dist/*

See its documentation for more information on how to install it and set it up.
You don't need to publish to Test PyPI as it suggests unless you want to as
part of your workflow. One thing to note about `twine` is it will
automatically convert your `plover_x_name` snake case name for your plugin
into a `plover-x-name` hyphenated name for the package it uploads.

## Plugins Registry

Once it's shown up on PyPI, you will also need to add it to the Plover
[Plugins Registry](https://github.com/openstenoproject/plover_plugins_registry), so that it can be installed through Plover's Plugins Manager.

To do this, just send a pull request to that repository, adding a line in
`registry.json` with the name of the plugin you want to add to the registry.
Once approved and merged, your plugin will appear in the Plugins Manager
anywhere from right away to a few hours later depending on end user caching.
