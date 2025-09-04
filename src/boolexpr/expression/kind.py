from __future__ import annotations

from enum import Enum, auto

__all__ = [
    "Kind",
]


class Kind(Enum):
    Tautology = auto()  # True
    Contradiction = auto()  # False
    Literal = auto()  # Variable or its Negation
    Negation = auto()  # Not
    Conjunction = auto()  # And
    Disjunction = auto()  # Or
    Parity = auto()  # Xor
    Equivalence = auto()  # Equals
    Implication = auto()  # Implies
    Decision = auto()  # If-then-else
    Cardinality = auto()  # AtLeast[k], AtMost[k], Exactly[k]
