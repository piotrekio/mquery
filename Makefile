all : black test
.PHONY: all

black:
	black *.py

test:
	py.test
