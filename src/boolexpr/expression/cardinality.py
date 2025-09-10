from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Self

import attrs

from boolexpr import exprnode
from boolexpr.variable.index import VariableIndex

from .interface import ConvertableToCNF, ConvertableToDNF, Expression, HasCompose, HasOperands, VarMap
from .kind import Kind
from .node.cardinality import at_least, at_least_size, expand, remove_constants
from .node.transform import condition
from .node.utils import get_support, to_node
from .simple import SimpleExpression, SimpleOrNode

__all__ = [
    "AtLeastOp",
]


if TYPE_CHECKING:
    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable


@attrs.define(frozen=True, hash=True, repr=False)
class AtLeastOp(
    HasOperands[SimpleExpression],
    HasCompose[SimpleExpression],
    ConvertableToCNF[SimpleExpression],
    ConvertableToDNF[SimpleExpression],
    Expression,
):
    k: int = attrs.field(converter=int)
    xs: tuple[exprnode.ExprNode, ...] = attrs.field(
        validator=attrs.validators.deep_iterable(
            attrs.validators.instance_of(exprnode.ExprNode),
        ),
    )

    @property
    def kind(self) -> Kind:
        return Kind.Cardinality

    @cached_property
    def depth(self) -> int:
        return 1 + max(op.depth() for op in self.xs)

    @cached_property
    def size(self) -> int:
        return min(
            at_least_size(len(self.xs), self.k, as_cnf=True),
            at_least_size(len(self.xs), self.k, as_cnf=False),
        )

    @cached_property
    def support(self) -> frozenset[VariableIndex]:
        return frozenset(VariableIndex(abs(idx)) for idx in get_support(*self.xs))

    @cached_property
    def operands(self) -> tuple[SimpleExpression, ...]:
        return tuple(SimpleExpression(op) for op in self.xs)

    def pushdown_not(self, /, *, simplify: bool = True) -> Self:
        if simplify:
            operands = (op.pushdown_not().simplify() for op in self.xs)
        else:
            operands = (op.pushdown_not() for op in self.xs)
        return self.__class__(self.k, tuple(operands))

    def compose(self, expressions: VarMap[SimpleOrNode], /, *, simplify: bool = True) -> Self:
        mapping = {v.pos_lit: to_node(e) for v, e in expressions.items()}
        if simplify:
            operands = (op.compose(mapping).simplify() for op in self.xs)
        else:
            operands = (op.compose(mapping) for op in self.xs)
        return self.__class__(self.k, tuple(operands))

    def condition(self, point: Point[Variable], /, *, simplify: bool = True) -> Self:
        if simplify:
            operands = (condition(op, point).simplify() for op in self.xs)
        else:
            operands = (condition(op, point) for op in self.xs)
        return self.__class__(self.k, tuple(operands))

    def simplify(self) -> Self:
        delta_k, new_xs = remove_constants(op.simplify() for op in self.xs)
        return self.__class__(self.k + delta_k, tuple(new_xs))

    def to_cnf(self, /, *, simplify: bool = True) -> SimpleExpression:
        node = expand(self.k, at_least, *self.xs, as_cnf=True)
        return SimpleExpression.from_node(node, simplify=simplify)

    def to_dnf(self, /, *, simplify: bool = True) -> SimpleExpression:
        node = expand(self.k, at_least, *self.xs, as_cnf=False)
        return SimpleExpression.from_node(node, simplify=simplify)
