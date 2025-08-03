# ezpubsub Changelog

## [0.3.0] 2025-08-03

### Changed

- [dev] Changed `ci-checks.yml` to run Nox instead of individual commands for MyPy, Ruff, Pytest, etc.

### Added

- [dev] Added `/tests` directory with a handful of unit test and a [pytest] section in `pyproject.toml`.
- [dev] Added Nox testing and `noxfile.py` to automate testing with MyPy, Ruff, Pytest, and BasedPyright.
- [dev] Added pytest and pytest-asyncio to dev dependencies.

### Removed

- [dev] Deleted `ci-requirements.txt` as it is no longer needed with the new Nox setup.

## [0.2.0] 2025-07-28

### Code and project changes

- Renamed Changelog.md to CHANGELOG.md
- Added 2 workflow to .github/workflows:
  - ci-checks.yml - runs Ruff, MyPy, BasedPyright (will add Pytest later)
  - release.yml - Workflow to publish to PyPI and github releases
- Added 2 scripts to .github/scripts:
  - adds .github/scripts/validate_main.sh
  - adds .github/scripts/tag_release.py
- Added 1 new file to root: `ci-requirements.txt` - this is used by the ci-checks.yml workflow to install the dev dependencies.
- Added basedpyright as a dev dependency to help with type checking. Made the `just typecheck` command run it after MyPy and set it to 'strict' mode in the config (added [tool.basedpyright] section to pyproject.toml).
- Workflow `update-docs.yml` now runs only if the `release.yml` workflow is successful, so it will only update the docs if a new release is made (Still possible to manually run it if needed, should add a 'docs' tag in the future for this purpose).
- Changed the `.python-version` file to use `3.9` instead of `3.12`.

## [0.1.2] 2025-07-25

- Added py.typed file

## [0.1.0] 2025-07-22

- Initial release
