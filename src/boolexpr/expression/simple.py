from __future__ import annotations

from collections.abc import Hashable
from functools import cached_property
from typing import TYPE_CHECKING, Self, cast

import attrs

from boolexpr import exprnode
from boolexpr.variable.index import VariableIndex

from .interface import Expression
from .kind import Kind

if TYPE_CHECKING:
    from rich.repr import RichReprResult

    from boolexpr.point import Point

    from .interface import ExprMap


EXPRNODE_KIND_TO_KIND = {
    exprnode.ZERO: Kind.Contradiction,
    exprnode.ONE: Kind.Tautology,
    exprnode.VAR: Kind.Literal,
    exprnode.COMP: Kind.Literal,
    exprnode.OP_NOT: Kind.Negation,
    exprnode.OP_AND: Kind.Conjunction,
    exprnode.OP_OR: Kind.Disjunction,
    exprnode.OP_XOR: Kind.Parity,
    exprnode.OP_EQ: Kind.Equivalence,
    exprnode.OP_IMPL: Kind.Implication,
    exprnode.OP_ITE: Kind.Decision,
}

NARY_KIND_TO_BUILD = {
    Kind.Conjunction: exprnode.and_,
    Kind.Disjunction: exprnode.or_,
    Kind.Parity: exprnode.xor,
    Kind.Equivalence: exprnode.eq,
}


OP_EXPRNODE_KIND_TO_REPR = {
    exprnode.OP_NOT: "Not",
    exprnode.OP_AND: "And",
    exprnode.OP_OR: "Or",
    exprnode.OP_XOR: "XOR",
    exprnode.OP_EQ: "Equiv",
    exprnode.OP_IMPL: "Implies",
    exprnode.OP_ITE: "ITE",
}


@attrs.define(repr=False)
class SimpleExpression[Label: Hashable](Expression[Label, "SimpleExpression[Label]"]):
    node: exprnode.ExprNode = attrs.field()

    def __rich_repr__(self) -> RichReprResult:
        yield "node", self.node.to_ast()

    def __invert__(self) -> SimpleExpression[Label]:
        return self.__class__(exprnode.not_(self.node).simplify())

    def __and__(self, other: Self | exprnode.ExprNode) -> SimpleExpression[Label]:
        if isinstance(other, type(self)):
            return self.__class__(exprnode.and_(self.node, other.node).simplify())
        if isinstance(other, exprnode.ExprNode):
            return self.__class__(exprnode.and_(self.node, other).simplify())
        raise TypeError(f"Invalid input: {other}")

    def __or__(self, other: Self | exprnode.ExprNode) -> SimpleExpression[Label]:
        if isinstance(other, self.__class__):
            return self.__class__(exprnode.or_(self.node, other.node).simplify())
        if isinstance(other, exprnode.ExprNode):
            return self.__class__(exprnode.or_(self.node, other).simplify())
        raise TypeError(f"Invalid input: {other}")

    def __xor__(self, other: Self | exprnode.ExprNode) -> SimpleExpression[Label]:
        if isinstance(other, self.__class__):
            return self.__class__(exprnode.xor(self.node, other.node).simplify())
        if isinstance(other, exprnode.ExprNode):
            return self.__class__(exprnode.xor(self.node, other).simplify())
        raise TypeError(f"Invalid input: {other}")

    @property
    def kind(self) -> Kind:
        return EXPRNODE_KIND_TO_KIND[self.node.kind()]

    @cached_property
    def operands(self) -> tuple[Self, ...]:
        match self.node.kind():
            case (
                exprnode.OP_NOT
                | exprnode.OP_AND
                | exprnode.OP_OR
                | exprnode.OP_XOR
                | exprnode.OP_EQ
                | exprnode.OP_IMPL
                | exprnode.OP_ITE
            ):
                operands = cast("tuple[exprnode.ExprNode]", self.node.data())
                return tuple(self.__class__(n) for n in operands)
        return ()

    @cached_property
    def support(self) -> frozenset[VariableIndex]:
        input_vars: set[VariableIndex] = set()
        for child in self.node:
            match child.kind():
                case exprnode.VAR:
                    idx = child.data()
                    assert isinstance(idx, int)
                    input_vars.add(VariableIndex(idx))
                case exprnode.COMP:
                    idx = child.data()
                    assert isinstance(idx, int)
                    input_vars.add(VariableIndex(abs(idx)))
        return frozenset(input_vars)

    @cached_property
    def depth(self) -> int:
        return self.node.depth()

    @cached_property
    def size(self) -> int:
        return self.node.size()

    def simplify(self) -> Self:
        return self.__class__(self.node.simplify())

    def pushdown_not(self) -> Self:
        return self.__class__(self.node.pushdown_not())

    def restrict(self, point: Point[Label]) -> Self:
        return self.__class__(
            self.node.restrict(
                {var.pos_lit: (exprnode.One if polarity else exprnode.Zero) for var, polarity in point.items()}
            )
        )

    def compose(self, expr_map: ExprMap[Label, SimpleExpression[Label]]) -> Self:
        return self.__class__(self.node.compose({var.pos_lit: expr.node for var, expr in expr_map.items()}))

    def to_cnf(self) -> Self:
        return self.__class__(self.node.to_cnf())

    def to_dnf(self) -> Self:
        return self.__class__(self.node.to_dnf())

    def to_nnf(self) -> Self:
        return self.__class__(self.node.to_nnf())

    @classmethod
    def tautology(cls) -> Self:
        return cls(exprnode.One)

    @classmethod
    def contradiction(cls) -> Self:
        return cls(exprnode.Zero)

    @classmethod
    def from_exprnode(cls, node: exprnode.ExprNode, /, *, simplify: bool = True) -> Self:
        if simplify:
            return cls(node.simplify())

        return cls(node)

    @classmethod
    def make_nary(cls, kind: Kind, *nodes: exprnode.ExprNode, simplify: bool = True) -> Self:
        builder = NARY_KIND_TO_BUILD[kind]
        return cls.from_exprnode(builder(*nodes), simplify=simplify)

    @classmethod
    def make_negated_nary(cls, kind: Kind, *nodes: exprnode.ExprNode, simplify: bool = True) -> Self:
        builder = NARY_KIND_TO_BUILD[kind]
        return cls.from_exprnode(exprnode.not_(builder(*nodes)), simplify=simplify)

    @classmethod
    def make_implication(cls, p: exprnode.ExprNode, q: exprnode.ExprNode, /, *, simplify: bool = True) -> Self:
        return cls.from_exprnode(exprnode.impl(p, q), simplify=simplify)

    @classmethod
    def make_decision(
        cls, s: exprnode.ExprNode, d1: exprnode.ExprNode, d0: exprnode.ExprNode, /, *, simplify: bool = True
    ) -> Self:
        return cls.from_exprnode(exprnode.ite(s, d1, d0), simplify=simplify)

    # def shannon_decompose(self, *variables: VariableData[Label], conj: bool = True) -> Self:
    #     match variables:
    #         case (variable,):
    #             success = self.node.restrict({variable.pos: exprnode.One})
    #             failure = self.node.restrict({variable.pos: exprnode.Zero})
    #             return self.__class__(exprnode.ite(variable.pos, success, failure))
    #         case (*variables,):
    #             raise NotImplementedError
