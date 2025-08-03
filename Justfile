# Install the package
install:
	uv sync

# Run the demo with defined entry command
run:
	uv run textual-pyfiglet

# Runs ruff, exits with 0 if no issues are found
lint:
  @uv run ruff check src || (echo "Ruff found issues. Please address them." && exit 1)

# Runs mypy, exits with 0 if no issues are found
typecheck:
  @uv run mypy src || (echo "Mypy found issues. Please address them." && exit 1)
  @uv run basedpyright src || (echo "BasedPyright found issues. Please address them." && exit 1)

typecheck-tests:
  @uv run mypy tests || (echo "Mypy found issues in tests. Please address them." && exit 1)
  @uv run basedpyright tests || (echo "BasedPyright found issues in tests. Please address them." && exit 1)

# Runs black
format:
  @uv run black src

test:
  @uv run pytest tests -vvv

# Run the Nox testing suite for comprehensive testing
nox:
  nox

# Remove build/dist directories and pyc files
clean:
  rm -rf build dist
  find . -name "*.pyc" -delete

# Remove tool caches
clean-caches:
  rm -rf .mypy_cache
  rm -rf .ruff_cache
  rm -rf .nox

# Remove the virtual environment and lock file
del-env:
  rm -rf .venv
  rm -rf uv.lock

nuke: clean clean-caches del-env
  @echo "All build artifacts and caches have been removed."

# Removes all environment and build stuff
reset: nuke install
  @echo "Environment reset."

# Release the kraken
release:
  bash .github/scripts/validate_main.sh && \
  uv run .github/scripts/tag_release.py && \
  git push --tags

sync-tags:
  git fetch --prune origin "+refs/tags/*:refs/tags/*"