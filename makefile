.PHONY: all build publish clean test cli

# Dev: `make test` — unittest suite; `make cli` / `make cli ARGS="--watch"` — local CLI (optional ARGS forwarded)

all: publish clean

build:
	@echo "building package..."
	uv build
	@echo "done"

publish:
	@echo "building package..."
	uv build
	@echo "publishing package..."
	uv publish
	@echo "done"

test:
	uv run python -m unittest discover -s tests -v

cli:
	uv run python -m pydaffodil $(ARGS)

clean:
	@echo "cleaning up..."
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	@echo "done"
