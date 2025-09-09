from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from lark import Lark, Token, Transformer

from boolexpr import exprnode
from boolexpr.expression.simple import SimpleExpression
from boolexpr.variable.identifier import VariableIdentifier

if TYPE_CHECKING:
    from boolexpr.universe import Universe
    from boolexpr.variable.identifier import Indices, Names

__all__ = [
    "get_parser",
    "TreeToExprNode",
    "get_expr_parser",
    "SimpleExpressionParser",
]

GRAMMAR_FILENAME = "grammar.lark"


def get_parser(*, parser: str = "lalr", debug: bool = False, strict: bool = False, **kwargs: Any) -> Lark:
    return Lark.open(
        GRAMMAR_FILENAME,
        rel_to=__file__,
        parser=parser,
        debug=debug,
        strict=strict,
        **kwargs,
    )


class TreeToExprNode(Transformer[exprnode.ExprNode, exprnode.ExprNode]):
    universe: Universe

    def __init__(self, universe: Universe, *args: Any, **kwargs: Any) -> None:
        self.universe = universe
        super().__init__(*args, **kwargs)

    @staticmethod
    def complement(tokens: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        assert len(tokens) == 1
        return exprnode.not_(tokens[0])

    @staticmethod
    def disjunction(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.or_(*operands)

    @staticmethod
    def conjunction(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.and_(*operands)

    @staticmethod
    def parity(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.xor(*operands)

    @staticmethod
    def equivalence(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.eq(*operands)

    @staticmethod
    def implication(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.impl(*operands)

    @staticmethod
    def decision(operands: list[exprnode.ExprNode]) -> exprnode.ExprNode:
        return exprnode.ite(*operands)

    @staticmethod
    def prefix(tokens: list[Token]) -> Names:
        return tuple(t.value for t in reversed(tokens))

    @staticmethod
    def index(tokens: list[Token]) -> Indices:
        return tuple(int(t.value) for t in tokens)

    def identifier(self, inputs: list[Names | Indices]) -> exprnode.ExprNode:
        match inputs:
            case (prefix, indices):
                idx = VariableIdentifier(prefix, cast("Indices", indices))
            case (prefix,):
                idx = VariableIdentifier(prefix)
            case _:
                raise ValueError(f"Unexpected inputs: {inputs}")
        return self.universe.get_or_make(idx).pos_lit


class SimpleExpressionParser(Protocol):
    def __call__(self, text: str, *, simplify: bool = True) -> SimpleExpression: ...


def get_expr_parser(universe: Universe, **kwargs: Any) -> SimpleExpressionParser:
    parser = get_parser(start=["expression"], transformer=TreeToExprNode(universe), **kwargs)

    def _parse(text: str, *, simplify: bool = True) -> SimpleExpression:
        node = parser.parse(text)
        return SimpleExpression.from_node(cast("exprnode.ExprNode", node), simplify=simplify)

    return _parse
