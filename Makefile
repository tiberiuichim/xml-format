.PHONY: test
test:
	bin/pytest --cov=format tests.py
