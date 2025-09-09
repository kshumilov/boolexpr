from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import attrs

from boolexpr import exprnode
from boolexpr.variable.index import VariableIndex

from .interface import Conjoinable, Disjoinable, Expression, Invertable
from .node import (
    NARY_TO_BUILDER,
    NODE_KIND_TO_KIND,
    derivative,
    existential,
    get_operands,
    get_support,
    point_to_clause,
    point_to_term,
    restrict_by_point,
    shannon,
    universal,
)

if TYPE_CHECKING:
    from typing import Self

    from rich.repr import RichReprResult

    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable

    from .interface import VarMap
    from .kind import Kind

__all__ = [
    "SimpleExpression",
    "X",
]

type X = exprnode.ExprNode | SimpleExpression


@attrs.define(repr=False, order=False, eq=False)
class SimpleExpression(
    Invertable["SimpleExpression"],
    Conjoinable["SimpleExpression", "SimpleExpression"],
    Disjoinable["SimpleExpression", "SimpleExpression"],
    Expression,
):
    node: exprnode.ExprNode = attrs.field()

    def __invert__(self) -> Self:
        return self.__class__(exprnode.not_(self.node).simplify())

    def __and__(self, rhs: X) -> Self:
        node = exprnode.and_(self.node, self.extract_node(rhs)).simplify()
        return self._new_if_different(node)

    def __or__(self, rhs: X) -> Self:
        node = exprnode.or_(self.node, self.extract_node(rhs)).simplify()
        return self._new_if_different(node)

    def __xor__(self, rhs: X) -> Self:
        node = exprnode.xor(self.node, self.extract_node(rhs)).simplify()
        return self._new_if_different(node)

    @property
    def kind(self) -> Kind:
        return NODE_KIND_TO_KIND[self.node.kind()]

    @cached_property
    def operands(self) -> tuple[Self, ...]:
        return tuple(self.__class__(op) for op in get_operands(self.node))

    @cached_property
    def support(self) -> frozenset[VariableIndex]:
        return frozenset(VariableIndex(abs(idx)) for idx in get_support(self.node))

    @cached_property
    def depth(self) -> int:
        return self.node.depth()

    @cached_property
    def size(self) -> int:
        return self.node.size()

    def simplify(self) -> Self:
        return self._new_if_different(self.node.simplify())

    def pushdown_not(self, /, *, simplify: bool = True) -> Self:
        node = self.node.pushdown_not()
        return self._new_if_different(node, simplify=simplify)

    def restrict(self, point: Point[Variable], /, *, simplify: bool = True) -> Self:
        node = restrict_by_point(self.node, point)
        return self._new_if_different(node, simplify=simplify)

    def compose(self, var_to_exr: VarMap[X], /, *, simplify: bool = True) -> Self:
        node = self.node.compose({var.pos_lit: self.extract_node(expr) for var, expr in var_to_exr.items()})
        return self._new_if_different(node, simplify=simplify)

    def consensus(self, *vs: Variable, simplify: bool = True) -> Self:
        node = universal(self.node, *vs)
        return self._new_if_different(node, simplify=simplify)

    def forget(self, *vs: Variable, simplify: bool = True) -> Self:
        node = existential(self.node, *vs)
        return self._new_if_different(node, simplify=simplify)

    def differentiate(self, *vs: Variable, simplify: bool = True) -> Self:
        node = derivative(self.node, *vs)
        return self._new_if_different(node, simplify=simplify)

    def determine(self, *vs: Variable, simplify: bool = True) -> Self:
        node = shannon(self.node, *vs)
        return self._new_if_different(node, simplify=simplify)

    def prime_implicants(self) -> Self:
        node = self.node.complete_sum()
        return self._new_if_different(node)

    def to_cnf(self) -> Self:
        return self._new_if_different(self.node.to_cnf())

    def to_dnf(self) -> Self:
        return self._new_if_different(self.node.to_dnf())

    def to_nnf(self) -> Self:
        return self._new_if_different(self.node.to_nnf())

    def __rich_repr__(self) -> RichReprResult:
        yield "node", self.node.to_ast()

    @classmethod
    def extract_node(cls, other: X) -> exprnode.ExprNode:
        if isinstance(other, SimpleExpression):
            return other.node
        return other

    def _new_if_different(self, new_node: exprnode.ExprNode, /, *, simplify: bool = False) -> Self:
        if simplify:
            new_node = new_node.simplify()

        if new_node.id() != self.node.id():
            return self.__class__(new_node)
        return self

    @classmethod
    def from_node(cls, node: exprnode.ExprNode, /, *, simplify: bool = True) -> Self:
        if simplify:
            return cls(node.simplify())
        return cls(node)

    @classmethod
    def tautology(cls) -> Self:
        return cls(exprnode.One)

    @classmethod
    def contradiction(cls) -> Self:
        return cls(exprnode.Zero)

    @classmethod
    def negation(cls, operand: X, /, *, simplify: bool = True) -> Self:
        node = cls.extract_node(operand)
        return cls.from_node(exprnode.not_(node), simplify=simplify)

    @classmethod
    def conjunction(cls, *operands: X, simplify: bool = True) -> Self:
        nodes = map(cls.extract_node, operands)
        return cls.from_node(exprnode.and_(*nodes), simplify=simplify)

    @classmethod
    def disjunction(cls, *operands: X, simplify: bool = True) -> Self:
        nodes = map(cls.extract_node, operands)
        return cls.from_node(exprnode.or_(*nodes), simplify=simplify)

    @classmethod
    def parity(cls, *operands: X, simplify: bool = True) -> Self:
        nodes = map(cls.extract_node, operands)
        return cls.from_node(exprnode.xor(*nodes), simplify=simplify)

    @classmethod
    def equivalence(cls, *operands: X, simplify: bool = True) -> Self:
        nodes = map(cls.extract_node, operands)
        return cls.from_node(exprnode.eq(*nodes), simplify=simplify)

    @classmethod
    def implication(cls, p: X, q: X, /, *, simplify: bool = True) -> Self:
        return cls.from_node(exprnode.impl(cls.extract_node(p), cls.extract_node(q)), simplify=simplify)

    @classmethod
    def decision(cls, s: X, d1: X, d0: X, /, *, simplify: bool = True) -> Self:
        return cls.from_node(
            exprnode.ite(cls.extract_node(s), cls.extract_node(d1), cls.extract_node(d0)),
            simplify=simplify,
        )

    @classmethod
    def nary(cls, kind: Kind, *operands: X, simplify: bool = True) -> Self:
        builder = NARY_TO_BUILDER[kind]
        nodes = map(cls.extract_node, operands)
        return cls.from_node(builder(*nodes), simplify=simplify)

    @classmethod
    def negated_nary(cls, kind: Kind, *operands: X, simplify: bool = True) -> Self:
        builder = NARY_TO_BUILDER[kind]
        nodes = map(cls.extract_node, operands)
        return cls.from_node(exprnode.not_(builder(*nodes)), simplify=simplify)

    @classmethod
    def term(cls, point: Point[Variable], /) -> Self:
        return cls(point_to_term(point))

    @classmethod
    def clause(cls, point: Point[Variable]) -> Self:
        return cls(point_to_clause(point))
