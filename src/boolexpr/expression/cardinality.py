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
from .node.utils import NodeMap, get_support, to_node, varmap_to_nodemap
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
    nodes: tuple[exprnode.ExprNode, ...] = attrs.field(
        validator=attrs.validators.deep_iterable(
            attrs.validators.instance_of(exprnode.ExprNode),
        ),
    )

    @property
    def kind(self) -> Kind:
        return Kind.Cardinality

    @property
    def is_tautology(self) -> bool:
        return self.k <= 0 or (self.k <= sum(node.kind() == exprnode.One for node in self.nodes))

    @property
    def is_contradiction(self) -> bool:
        return self.k > len(self.nodes) or (self.k <= sum(node.kind() == exprnode.Zero for node in self.nodes))

    @property
    def is_variable(self) -> bool:
        return False

    @property
    def is_complement(self) -> bool:
        return False

    def to_atom(self) -> Expression:
        if self.is_tautology:
            return SimpleExpression(exprnode.One)
        if self.is_contradiction:
            return SimpleExpression(exprnode.Zero)
        raise ValueError("Cannot convert non-constant expression to atom.")

    @cached_property
    def depth(self) -> int:
        return 1 + max(op.depth() for op in self.nodes)

    @cached_property
    def size(self) -> int:
        return min(
            at_least_size(len(self.nodes), self.k, as_cnf=True),
            at_least_size(len(self.nodes), self.k, as_cnf=False),
        )

    @cached_property
    def support(self) -> frozenset[VariableIndex]:
        return frozenset(VariableIndex(abs(idx)) for idx in get_support(*self.nodes))

    @cached_property
    def operands(self) -> tuple[SimpleExpression, ...]:
        return tuple(SimpleExpression(node) for node in self.nodes)

    def pushdown_not(self, /, *, simplify: bool = True) -> Self:
        if simplify:
            operands = (node.pushdown_not().simplify() for node in self.nodes)
        else:
            operands = (node.pushdown_not() for node in self.nodes)
        return self.__class__(self.k, tuple(operands))

    def compose(self, mapping: VarMap[SimpleOrNode], /, *, simplify: bool = True) -> Self:
        node_map = varmap_to_nodemap(mapping)
        return self.node_compose(node_map, simplify=simplify)

    def node_compose(self, node_map: NodeMap, /, *, simplify: bool = True) -> Self:
        if simplify:
            operands = (node.compose(node_map).simplify() for node in self.nodes)
        else:
            operands = (node.compose(node_map) for node in self.nodes)
        return self.__class__(self.k, tuple(operands))

    def condition(self, point: Point[Variable], /, *, simplify: bool = True) -> Self:
        if simplify:
            operands = (condition(node, point).simplify() for node in self.nodes)
        else:
            operands = (condition(node, point) for node in self.nodes)
        return self.__class__(self.k, tuple(operands))

    def simplify(self) -> Self:
        delta_k, new_xs = remove_constants(node.simplify() for node in self.nodes)
        return self.__class__(self.k + delta_k, tuple(new_xs))

    def to_cnf(self, /, *, simplify: bool = True) -> SimpleExpression:
        node = expand(self.k, at_least, *self.nodes, as_cnf=True)
        return SimpleExpression.from_node(node, simplify=simplify)

    def to_dnf(self, /, *, simplify: bool = True) -> SimpleExpression:
        node = expand(self.k, at_least, *self.nodes, as_cnf=False)
        return SimpleExpression.from_node(node, simplify=simplify)

    @classmethod
    def from_expressions(cls, k: int, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        gate = cls(k, tuple(map(to_node, operands)))
        return gate.simplify() if simplify else gate
