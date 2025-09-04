from collections.abc import Hashable
from typing import Protocol

__all__ = [
    "VariableLike",
    "ExpressionLike",
    "Point",
    "Term",
    "UntypedPoint",
]


class ExpressionLike(Protocol):
    def __invert__(self) -> "ExpressionLike": ...


class VariableLike(ExpressionLike, Hashable, Protocol):
    @property
    def uniqid(self) -> int: ...

    def __invert__(self) -> ExpressionLike: ...


type Point[T: VariableLike] = dict[T, int]
type Term[T: (ExpressionLike, VariableLike)] = tuple[T, ...]
type UntypedPoint = tuple[frozenset[int], frozenset[int]]
