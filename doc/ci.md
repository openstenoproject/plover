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

- 1 pre-processing job: "Analyze", all other jobs depend on it
- 3 "platform tests" jobs: Linux, macOS, and Windows
- 3 "platform build" jobs, again: Linux, macOS and Windows, dependent on their
    respective "platform tests" job (so if the `Test (macOS)` job fails, the
    `Build (macOS)` job is skipped).
- 1 "packaging" job that run a number of packaging related checks
- 3 "Python tests" jobs: for checking support for older/newer versions of Python
  (other than the version currently used for the distributions)
- 1 final, optional, "release" job


## Analyze job

This job has 2 roles:
- determine if a release will be made (will the final "Release" job be skipped?)
- analyze the source tree to determine if some of the jobs can be skipped

## Release conditions

Two (exclusive) conditions can result in a release:
- a tag build, and the tag name is not `continuous`
- a branch build on `secrets.CONTINUOUS_RELEASE_BRANCH`


## Skipping Test/Build jobs

First, jobs are never skipped when a release is done.

Otherwise, a special job specific cache is used to determine if a job can be
skipped.

Each job will update that cache as part of their run.

The cache is keyed with:
- the `epoch` defined in `workflow_context`
- the name of the job
- a hash of the relevant part of the source tree

On cache hit, the job is skipped.

### Creating the tree hash

Let's take the example of the "Linux Build" job, the steps used for creating
the skip cache key are:
- a list of exclusion patterns is built, in this case from `skiplist_default.txt`,
  `skiplist_job_build.txt`, and `skiplist_os_linux.txt`
- that list of exclusion patterns is used to create the list of files
   used by the job: `git ls-files [...] ':!:doc/*' [...] ':!:reqs/test.txt' [...]`
- part of the `HEAD` tree object listing is hashed:
  `git ls-tree @ [...] linux/appimage/deps.sh [...] | sha1sum`

Note: the extra `git ls-files` step is needed because exclusion patterns are
not supported by `git ls-tree`.


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

The final job, only run on release (*tagged* or *continuous*), and if
all the other jobs completed successfully.


### PyPI release

On *tagged* release, the source distribution and wheel are published
to PyPI.

For this to work, a valid [PyPI token](https://pypi.org/help/#apitoken)
must be configured: the `PYPI_TOKEN` secret of the `release`
[environment](https://docs.github.com/en/actions/reference/environments)
will be used. Additionally, the optional `PYPI_URL` secret can be set to
use another PyPI compatible index (e.g. Test PyPI).

### GitHub release

On *tagged* release, a new release draft is created on GitHub.

On *continuous* release, the `continuous` release and corresponding tag
are created / updated, but only if the existing release version is not
newer, in order to:
* prevent an old workflow re-run from overwriting the latest continuous release
* reduce the likelihood that a flurry of merges to the continuous branch will
  result in the continuous release not pointing to the most recent valid commit
  (because multiple workflows were created in parallel).

All the artifacts will be included as assets.

The release notes are automatically generated from the last release section in
`NEWS.md` (*tagged* release) or the existing `news.d` entries (*continuous*
release), and the template in `.github/RELEASE_DRAFT_TEMPLATE.md`.


## Limitations

- The artifact upload action [always wraps artifacts in a
  zip](https://github.com/actions/upload-artifact/issues/39),
  even if they are a single file such as an exe or a dmg.
- Artifacts can only be downloaded when logged-in.
- Artifacts are only accessible once all the jobs of a workflow have completed.
