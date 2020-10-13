"""Test fixtures for backends"""

from enum import Enum


class NamedClassA:
    """An example named class"""

    name = "A"


class NamedClassB:
    """A second example named class"""

    name = "B"


class NamedClassEnum(Enum):
    """A named test classes Enum"""

    A = "tests.fixtures.backends.NamedClassA"
    B = "tests.fixtures.backends.NamedClassB"
