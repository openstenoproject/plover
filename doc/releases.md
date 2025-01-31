# Release Process

Version numbers:

- official release: `{major}.{minor}.{patch}` (e.g. `2.2.1`, `3.1.0`, `4.0.0`...)
- pre-release: `{major}.{minor}.{patch}.{dev|rc}{devel}` (e.g. `4.0.0.dev7`, `4.0.0rc1`, ...)


Steps to cut a new release (from a clean checkout of `main`):

1. Run `tox -e release_prepare {NEW_VERSION_NUMBER}`.
2. Review the staged changes, check all news fragments in `news.d` were
   properly handled (merged into `NEWS.md` and removed by towncrier).
3. Run `tox -e release_finalize`
4. Follow the last command instructions, and push to GitHub.
