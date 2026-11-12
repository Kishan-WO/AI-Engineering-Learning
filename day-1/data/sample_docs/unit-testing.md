# Unit Testing in Python

A unit test checks one small piece of code in isolation. pytest is the most popular testing framework in Python.

Tests are plain functions whose names start with `test_`, and they use `assert`. Fixtures provide shared setup, and `pytest.mark.parametrize` runs one test with many inputs.

Mock external services, such as HTTP APIs, so tests are fast and do not depend on the network.
