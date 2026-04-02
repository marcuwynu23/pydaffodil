
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

clean:
	@echo "cleaning up..."
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	@echo "done"
