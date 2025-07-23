# Install the package
install:
	uv sync

# Run the demo with defined entry command
run:
	uv run textual-pyfiglet

# Runs ruff, exits with 0 if no issues are found
lint:
	uv run ruff check src || (echo "Ruff found issues. Please address them." && exit 1)

# Runs mypy, exits with 0 if no issues are found
typecheck:
	uv run mypy src || (echo "Mypy found issues. Please address them." && exit 1)

# Runs black
format:
	uv run black src

# Runs ruff, mypy, and black
all-checks: lint typecheck format
	echo "All pre-commit checks passed. You're good to publish."

# Remove the build and dist directories
clean:
	rm -rf build dist
	find . -name "*.pyc" -delete

# Remove tool caches
clean-caches:
	rm -rf .mypy_cache
	rm -rf .ruff_cache	

# Remove the virtual environment and lock file
del-env:
	rm -rf .venv
	rm -rf uv.lock

# Removes all environment and build stuff
reset: clean clean-caches del-env install
	echo "Environment reset."

# Runs all-checks and cleaning stages before building
build: all-checks clean
	uv build
	
# Runs build stage before publishing
publish: build
	uv publish	

