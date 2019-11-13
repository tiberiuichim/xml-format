.PHONY: test
test:
	bin/pytest --cov-report term-missing --cov=format tests.py
