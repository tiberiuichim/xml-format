.PHONY: test
test:
	bin/pytest -v --cov-report term-missing --cov=format tests.py
