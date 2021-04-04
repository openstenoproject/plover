# Continuous Integration

The project uses Github Actions (GA), the workflow configuration lives in
`.github/workflows/ci.yml`. Because of the limitation of GA (no YAML
anchors/aliases support, no possibility to re-use actions in composite
actions), in order to reduce duplications, that file is currently generated:

- `.github/workflows/ci/workflow_template.yml` is the
  [Jinja](https://palletsprojects.com/p/jinja/) template.

- `.github/workflows/ci/workflow_context.yml` contains the tests/build jobs
  definitions.

- `.github/workflows/ci/workflow_generate.py` is used to generate the workflow
  configuration: just execute `./.github/workflows/ci/workflow_generate.py` to
  update the workflow configuration after updating one of the files above (the
  script will check whether the output is valid YAML, and that anchors/aliases
  are not used).

- `.github/workflows/ci/helpers.sh` contains the bash functions used by some
  of the steps (e.g. setting up the Python environment, running the tests,
  etc...). Note: this file reuse some of the helpers provided by
  `plover_build_utils/functions.sh`.

The current workflow consists of:

- 3 "platform tests" jobs: Linux, macOS, and Windows
- 3 "platform build" jobs, again: Linux, macOS and Windows, dependent on their
    respective "platform tests" job (so if the `Test (macOS)` job fails, the
    `Build (macOS)` job is skipped).
- 1 "packaging" job that run a number of packaging related checks
- 3 "Python tests" jobs: for checking support for older/newer versions of Python
  (other than the version currently used for the distributions)
- 1 final, optional, "release" job

## Tests / Build jobs

On Linux / Windows, the standard GA action `actions/setup-python` is used
to setup Python: so, for example, configuring a job to use 3.7 will
automatically setup up the most recent 3.7.x version available on the
runner.

On macOS, to support older releases, Python will be setup from an official
installer (see `osx/deps.sh` for the exact version being used). The version
declared in `workflow_context.yml` must match, or an error will be raised
during the job execution (if for example the job is declared to use `3.7`,
but the dependency in `osx/deps.sh` uses `3.6.8`).

Caching is used to speed up the jobs. The cache is keyed with:
- the `epoch` defined `workflow_context`: increasing it can be used to
  force clear all the caches for all the jobs
- the name of the job
- the full Python version setup for the job (so including the patch number)
- a hash of part of the requirements (`reqs/constraints.txt` + the relevant
  `reqs` files for the job in question), and additional files declaring
  extra dependencies for some jobs (e.g. `osx/deps.sh` on macOS)

If the key changes, the cache is cleared/reset, and the Python environment
will be recreated, wheel and extra dependencies re-downloaded, etc...

## Packaging job

This job will run a number of packaging-related checks. See
`packaging_checks` in `functions.sh` for the details.

The resulting source distribution and wheel will also be added
to the artifacts when a release is being created.

## Release job

The final job, it only runs on release (tag), and if all the other jobs
complete successfully.

The job will publish the source distribution and wheel to PyPI. For
this to work, a valid [PyPI token](https://pypi.org/help/#apitoken)
must be configured: the `PYPI_TOKEN` secret of the `release`
[environment](https://docs.github.com/en/actions/reference/environments)
will be used. Additionally, the optional `PYPI_URL` secret can be set to
use another PyPI compatible index (e.g. Test PyPI).

If the previous step was successful, a new release draft will be created
on GitHub. All the artifacts will be included as assets. The release notes
are automatically generated from the last release section in `NEWS.md` and
the template in `.github/RELEASE_DRAFT_TEMPLATE.md`.

## Limitations

- The artifact upload action [always wraps artifacts in a
  zip](https://github.com/actions/upload-artifact/issues/39),
  even if they are a single file such as an exe or a dmg.
