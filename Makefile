build:
	python setup.py sdist bdist_wheel

test:
	python -m unittest

clean:
	rm -Rf build dist apyproxy.egg-info
