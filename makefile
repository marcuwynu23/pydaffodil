

all: publish clean


publish:
	@echo "building package..."
	python -m build
	@echo "publishing package..."
	twine upload dist/*
	@echo "done"

clean:
	@echo "cleaning up..."
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	@echo "done"

