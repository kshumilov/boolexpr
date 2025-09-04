from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from boolexpr.point import iter_points

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator, Mapping

    from boolexpr.expression.kind import Kind
    from boolexpr.point import Point
    from boolexpr.variable.index import VariableIndex
    from boolexpr.variable.variable import Variable


__all__ = ["Expression", "ExprMap"]

type ExprMap[Label: Hashable, Expr] = Mapping[Variable[Label], Expr]


class Expression[Label: Hashable, Other](Protocol):
    @property
    def kind(self) -> Kind: ...

    @property
    def depth(self) -> int: ...

    @property
    def operands(self) -> tuple[Expression[Label, Other], ...]: ...

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

    def simplify(self) -> Expression[Label, Other]: ...

    def pushdown_not(self) -> Expression[Label, Other]: ...

    def restrict(self, point: Point[Label]) -> Expression[Label, Other]: ...

    def compose(self, expressions: ExprMap[Label, Other]) -> Expression[Label, Other]: ...

    def to_cnf(self) -> Expression[Label, Other]: ...

    def to_dnf(self) -> Expression[Label, Other]: ...

    def to_nnf(self) -> Expression[Label, Other]: ...

    def iter_cofactors(self, *variables: Variable[Label]) -> Iterator[Expression[Label, Other]]:
        for point in iter_points(variables):
            yield self.restrict(point)
