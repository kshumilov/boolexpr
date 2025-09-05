from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from boolexpr.point import iter_points

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator, Mapping
    from typing import Self

    from boolexpr.expression.kind import Kind
    from boolexpr.point import Point
    from boolexpr.variable.index import VariableIndex
    from boolexpr.variable.variable import Variable


__all__ = [
    "Expression",
    "VarMap",
    "Invertable",
    "Conjoinable",
    "Disjoinable",
]

type VarMap[Label: Hashable, Value] = Mapping[Variable[Label], Value]


class Expression(Protocol):
    @property
    def kind(self) -> Kind: ...

    @property
    def depth(self) -> int: ...

    @property
    def operands(self) -> tuple[Self, ...]: ...

    @property
    def support(self) -> frozenset[VariableIndex]: ...

    @property
    def size(self) -> int: ...

    @property
    def degree(self) -> int:
        return len(self.support)

    @property
    def cardinality(self) -> int:
        return 1 << self.degree

    def simplify(self) -> Self: ...

    def pushdown_not(self) -> Self: ...

    def restrict[L: Hashable](self, point: Point[L]) -> Self: ...

    def compose[L: Hashable](self, expressions: VarMap[L, Self]) -> Self: ...

    def to_cnf(self) -> Self: ...

    def to_dnf(self) -> Self: ...

    def to_nnf(self) -> Self: ...

    def iter_cofactors[L: Hashable](self, *variables: Variable[L]) -> Iterator[Self]:
        for point in iter_points(variables):
            yield self.restrict(point)


class Invertable[Output: Expression](Protocol):
    def __invert__(self) -> Output: ...


class Conjoinable[LHS: Expression, Output: Expression](Protocol):
    def __and__(self, other: LHS) -> Output: ...


class Disjoinable[LHS: Expression, Output: Expression](Protocol):
    def __or__(self, other: Self) -> Self: ...
