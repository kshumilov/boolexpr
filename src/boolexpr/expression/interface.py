from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from boolexpr.point import iter_points

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Self

    from boolexpr.expression.kind import Kind
    from boolexpr.point import Point
    from boolexpr.variable.index import VariableIndex
    from boolexpr.variable.variable import Variable


__all__ = [
    "Expression",
    "VarMap",
    "HasOperands",
    "HasCompose",
    "Invertable",
    "Conjoinable",
    "Disjoinable",
    "ConvertableToCNF",
    "ConvertableToDNF",
    "ConvertableToNNF",
    "ConvertableToAtom",
]

type VarMap[Value] = Mapping[Variable, Value]


class Expression(Protocol):
    @property
    def kind(self) -> Kind: ...

    @property
    def is_tautology(self) -> bool:
        return self.kind == Kind.Tautology

    @property
    def is_contradiction(self) -> bool:
        return self.kind == Kind.Contradiction

    @property
    def is_constant(self) -> bool:
        return self.is_tautology or self.is_contradiction

    @property
    def is_variable(self) -> bool: ...

    @property
    def is_complement(self) -> bool: ...

    @property
    def is_literal(self) -> bool:
        return self.is_variable or self.is_complement

    @property
    def is_atom(self) -> bool:
        return self.is_constant or self.is_literal

    @property
    def depth(self) -> int: ...

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

    def condition(self, point: Point[Variable]) -> Self: ...

    def iter_cofactors(self, *variables: Variable) -> Iterator[Self]:
        for point in iter_points(variables):
            yield self.condition(point)


class HasOperands[Operand: Expression](Protocol):
    @property
    def operands(self) -> tuple[Operand, ...]: ...


class HasCompose[Input: Expression](Protocol):
    def compose(self, mapping: VarMap[Input]) -> Self: ...


class ConvertableToAtom[Output: Expression](Protocol):
    def to_atom(self) -> Output: ...


class Invertable[Output: Expression](Protocol):
    def __invert__(self) -> Output: ...


class Conjoinable[With: Expression, Result: Expression](Protocol):
    def __and__(self, lhs: With) -> Result: ...

    # def __rand__(self, rhs: With) -> Output: ...


class Disjoinable[With: Expression, Result: Expression](Protocol):
    def __or__(self, other: With) -> Result: ...

    # def __ror__(self, rhs: With) -> Output: ...


class ConvertableToCNF[Result: Expression](Protocol):
    def to_cnf(self) -> Result: ...


class ConvertableToDNF[Result: Expression](Protocol):
    def to_dnf(self) -> Result: ...


class ConvertableToNNF[Result: Expression](Protocol):
    def to_nnf(self) -> Result: ...
