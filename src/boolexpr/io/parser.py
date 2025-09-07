from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from lark import Lark, Token, Transformer

from boolexpr import exprnode
from boolexpr.expression.simple import SimpleExpression

if TYPE_CHECKING:
    from collections.abc import Hashable

    from boolexpr.universe import Universe

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


class TreeToExprNode[Label: Hashable](Transformer[exprnode.ExprNode, exprnode.ExprNode]):
    universe: Universe[Label]

    def __init__(self, universe: Universe[Label], *args: Any, **kwargs: Any) -> None:
        self.universe = universe
        super().__init__(*args, **kwargs)

    def complement(self, tokens: list[Token | exprnode.ExprNode]) -> exprnode.ExprNode:
        assert len(tokens) == 1
        match tokens[0]:
            case Token(type="CNAME", value=label):
                return self.universe.get_or_make(label).neg_lit
            case exprnode.ExprNode() as node:
                return exprnode.not_(node)
        raise ValueError(f"Unexpected tokens: {tokens}")

    def disjunction(self, raw_operands: list[Token | exprnode.ExprNode]) -> exprnode.ExprNode:
        operands = [self._unwrap_operand(op) for op in raw_operands]
        return exprnode.or_(*operands)

    def conjunction(self, raw_operands: list[exprnode.ExprNode | exprnode.ExprNode]) -> exprnode.ExprNode:
        operands = [self._unwrap_operand(op) for op in raw_operands]
        return exprnode.and_(*operands)

    def parity(self, raw_operands: list[Token | exprnode.ExprNode]) -> exprnode.ExprNode:
        operands = [self._unwrap_operand(op) for op in raw_operands]
        return exprnode.xor(*operands)

    def equivalence(self, raw_operands: list[Token | exprnode.ExprNode]) -> exprnode.ExprNode:
        operands = [self._unwrap_operand(op) for op in raw_operands]
        return exprnode.eq(*operands)

    def _unwrap_operand(self, operand: Token | exprnode.ExprNode) -> exprnode.ExprNode:
        match operand:
            case Token(type="CNAME", value=label):
                return self.universe.get_or_make(label).pos_lit
            case exprnode.ExprNode() as node:
                return node
        raise ValueError(f"Unexpected tokens: {operand}")


class SimpleExpressionParser(Protocol):
    def __call__(self, text: str, *, simplify: bool = True) -> SimpleExpression: ...


def get_expr_parser[Label: Hashable](universe: Universe[Label], **kwargs: Any) -> SimpleExpressionParser:
    parser = get_parser(start=["expression"], transformer=TreeToExprNode(universe), **kwargs)

    def _parse(text: str, *, simplify: bool = True) -> SimpleExpression:
        node = parser.parse(text)
        return SimpleExpression.from_node(cast("exprnode.ExprNode", node), simplify=simplify)

    return _parse
