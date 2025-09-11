from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

import attrs

from boolexpr import exprnode
from boolexpr.variable.index import VariableIndex

from .interface import (
    Conjoinable,
    ConvertableToAtom,
    ConvertableToCNF,
    ConvertableToDNF,
    ConvertableToNNF,
    Disjoinable,
    Expression,
    HasCompose,
    HasOperands,
    Invertable,
)
from .node.point import point_to_clause, point_to_term
from .node.transform import condition, derivative, existential, shannon, universal
from .node.utils import (
    NARY_TO_BUILDER,
    NODE_ATOMS,
    NODE_KIND_TO_KIND,
    NODE_LITERALS,
    NodeMap,
    get_operands,
    get_support,
    to_node,
    varmap_to_nodemap,
)

if TYPE_CHECKING:
    from typing import Self

    from rich.repr import RichReprResult

    from boolexpr.exprnode import ExprNode
    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable

    from .interface import (
        VarMap,
    )
    from .kind import Kind

__all__ = [
    "SimpleExpression",
    "SimpleOrNode",
]

type SimpleOrNode = exprnode.ExprNode | SimpleExpression


@attrs.define(repr=False, order=False, eq=False)
class SimpleExpression(
    HasOperands["SimpleExpression"],
    HasCompose["SimpleExpression"],
    Invertable["SimpleExpression"],
    Conjoinable["SimpleExpression", "SimpleExpression"],
    Disjoinable["SimpleExpression", "SimpleExpression"],
    ConvertableToCNF["SimpleExpression"],
    ConvertableToDNF["SimpleExpression"],
    ConvertableToNNF["SimpleExpression"],
    ConvertableToAtom["SimpleExpression"],
    Expression,
):
    node: exprnode.ExprNode = attrs.field(
        validator=attrs.validators.instance_of(exprnode.ExprNode),
    )

    def __invert__(self) -> Self:
        return self.__class__(exprnode.not_(self.node).simplify())

    def __and__(self, rhs: SimpleOrNode) -> Self:
        node = exprnode.and_(self.node, to_node(rhs)).simplify()
        return self._new_if_different(node)

    def __or__(self, rhs: SimpleOrNode) -> Self:
        node = exprnode.or_(self.node, to_node(rhs)).simplify()
        return self._new_if_different(node)

    def __xor__(self, rhs: SimpleOrNode) -> Self:
        node = exprnode.xor(self.node, to_node(rhs)).simplify()
        return self._new_if_different(node)

    @property
    def kind(self) -> Kind:
        return NODE_KIND_TO_KIND[self.node.kind()]

    @property
    def is_variable(self) -> bool:
        return self.node.kind() == exprnode.VAR

    @property
    def is_complement(self) -> bool:
        return self.node.kind() == exprnode.COMP

    def to_atom(self) -> Self:
        if self.node.kind() in NODE_LITERALS:
            return self
        if self.node.kind() == exprnode.ONE:
            return self.__class__(exprnode.One)
        if self.node.kind() == exprnode.Zero:
            return self.__class__(exprnode.Zero)
        raise ValueError("Cannot convert non-constant expression to atom.")

    @cached_property
    def depth(self) -> int:
        return self.node.depth()

    @cached_property
    def size(self) -> int:
        return self.node.size()

    @cached_property
    def operands(self) -> tuple[Self, ...]:
        if self.node.kind() in NODE_ATOMS:
            return ()
        return tuple(self.__class__(op) for op in get_operands(self.node))

    @cached_property
    def support(self) -> frozenset[VariableIndex]:
        return frozenset(VariableIndex(abs(idx)) for idx in get_support(self.node))

    def simplify(self) -> Self:
        return self._new_if_different(self.node.simplify())

    def pushdown_not(self, /, *, simplify: bool = True) -> Self:
        node = self.node.pushdown_not()
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def condition(self, point: Point[Variable], /, *, simplify: bool = True) -> Self:
        node = condition(self.node, point)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def compose(self, mapping: VarMap[SimpleOrNode], /, *, simplify: bool = True) -> Self:
        node_map = varmap_to_nodemap(mapping)
        return self.node_compose(node_map, simplify=simplify)

    def node_compose(self, node_map: NodeMap, /, *, simplify: bool = True) -> Self:
        node = self.node.compose(node_map)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def consensus(self, *vs: Variable, simplify: bool = True) -> Self:
        node = universal(self.node, *vs)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def forget(self, *vs: Variable, simplify: bool = True) -> Self:
        node = existential(self.node, *vs)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def differentiate(self, *vs: Variable, simplify: bool = True) -> Self:
        node = derivative(self.node, *vs)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

    def determine(self, *vs: Variable, simplify: bool = True) -> Self:
        node = shannon(self.node, *vs)
        if simplify:
            node = node.simplify()
        return self._new_if_different(node)

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

    def __exprnode__(self) -> ExprNode:
        return self.node

    def _new_if_different(self, new_node: exprnode.ExprNode) -> Self:
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
    def negation(cls, operand: SimpleOrNode, /, *, simplify: bool = True) -> Self:
        return cls.from_node(exprnode.not_(to_node(operand)), simplify=simplify)

    @classmethod
    def conjunction(cls, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        nodes = map(to_node, operands)
        return cls.from_node(exprnode.and_(*nodes), simplify=simplify)

    @classmethod
    def disjunction(cls, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        nodes = map(to_node, operands)
        return cls.from_node(exprnode.or_(*nodes), simplify=simplify)

    @classmethod
    def parity(cls, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        nodes = map(to_node, operands)
        return cls.from_node(exprnode.xor(*nodes), simplify=simplify)

    @classmethod
    def equivalence(cls, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        nodes = map(to_node, operands)
        return cls.from_node(exprnode.eq(*nodes), simplify=simplify)

    @classmethod
    def implication(cls, p: SimpleOrNode, q: SimpleOrNode, /, *, simplify: bool = True) -> Self:
        return cls.from_node(exprnode.impl(to_node(p), to_node(q)), simplify=simplify)

    @classmethod
    def decision(
        cls, on: SimpleOrNode, success: SimpleOrNode, failure: SimpleOrNode, /, *, simplify: bool = True
    ) -> Self:
        return cls.from_node(
            exprnode.ite(to_node(on), to_node(success), to_node(failure)),
            simplify=simplify,
        )

    @classmethod
    def nary(cls, kind: Kind, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        builder = NARY_TO_BUILDER[kind]
        nodes = map(to_node, operands)
        return cls.from_node(builder(*nodes), simplify=simplify)

    @classmethod
    def negated_nary(cls, kind: Kind, *operands: SimpleOrNode, simplify: bool = True) -> Self:
        builder = NARY_TO_BUILDER[kind]
        nodes = map(to_node, operands)
        return cls.from_node(exprnode.not_(builder(*nodes)), simplify=simplify)

    @classmethod
    def term(cls, point: Point[Variable], /) -> Self:
        return cls(point_to_term(point))

    @classmethod
    def clause(cls, point: Point[Variable]) -> Self:
        return cls(point_to_clause(point))
