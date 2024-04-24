build:
    python -m build

publish:
    twine

update-deps:
    pip-compile dev-requirements.in

develop:
    python -m pip install -e .
    python -m pip install -r dev-requirements.txt

test:
    python -m pytest

clean:
    rm -rf dist