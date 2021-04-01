# Release Process

Version numbers:

- official release: `{major}.{minor}.{patch}` (e.g. `2.2.1`, `3.1.0`, `4.0.0`...)
- pre-release: `{major}.{minor}.{patch}.{dev|rc}{devel}` (e.g. `4.0.0.dev7`, `4.0.0rc1`, ...)


Steps to cut a new release (from a clean checkout of `master`):

1. Update version in `plover/__init__.py`, and stage the change `git add plover/__init__.py`.
2. Install towncrier (`pip install towncrier`) and update `NEWS.md`: `towncrier`.
3. Review the staged changes, check all news fragments in `news.d` were properly handled
   (merged into `NEWS.md` and removed by towncrier).
4. Commit: `git commit -m "release $(./setup.py --version)"`
5. Tag the release: `git tag -m "$(git log -1 --pretty='format:%B')" "v$(./setup.py --version)"`
6. Push to Github: `git push --follow-tags origin`
