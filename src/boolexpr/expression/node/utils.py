from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from boolexpr.expression.kind import Kind
from boolexpr.exprnode import (
    COMP,
    ONE,
    OP_AND,
    OP_EQ,
    OP_IMPL,
    OP_ITE,
    OP_NOT,
    OP_OR,
    OP_XOR,
    VAR,
    ZERO,
    ExprNode,
    and_,
    eq,
    impl,
    ite,
    not_,
    or_,
    xor,
)
from boolexpr.variable.index import VariableIndex

if TYPE_CHECKING:
    from boolexpr.expression.interface import VarMap

__all__ = [
    "NODE_KIND_TO_KIND",
    "NARY_TO_BUILDER",
    "NODE_OP_TO_BUILDER",
    "NODE_LITERALS",
    "NODE_CONSTANTS",
    "NODE_ATOMS",
    "NODE_OPS",
    "get_operands",
    "get_support",
    "get_identifier",
    "are_trivially_equivalent",
    "ConvertibleToExprNode",
    "to_node",
    "varmap_to_nodemap",
    "NodeMap",
    "ExprOrNode",
]


type NodeMap = dict[ExprNode, ExprNode]


class ExprNodeBuilder(Protocol):
    def __call__(self, *nodes: ExprNode) -> ExprNode: ...


NODE_KIND_TO_KIND = {
    ZERO: Kind.Contradiction,
    ONE: Kind.Tautology,
    VAR: Kind.Literal,
    COMP: Kind.Literal,
    OP_NOT: Kind.Negation,
    OP_AND: Kind.Conjunction,
    OP_OR: Kind.Disjunction,
    OP_XOR: Kind.Parity,
    OP_EQ: Kind.Equivalence,
    OP_IMPL: Kind.Implication,
    OP_ITE: Kind.Decision,
}
NARY_TO_BUILDER = {
    Kind.Conjunction: and_,
    Kind.Disjunction: or_,
    Kind.Parity: xor,
    Kind.Equivalence: eq,
}
NODE_OP_TO_BUILDER: dict[int, ExprNodeBuilder] = {
    OP_NOT: not_,
    OP_AND: and_,
    OP_OR: or_,
    OP_XOR: xor,
    OP_EQ: eq,
    OP_IMPL: impl,
    OP_ITE: ite,
}
NODE_LITERALS = frozenset({VAR, COMP})
NODE_CONSTANTS = frozenset({ZERO, ONE})
NODE_ATOMS = NODE_LITERALS | NODE_CONSTANTS
NODE_OPS = frozenset({OP_NOT, OP_AND, OP_OR, OP_XOR, OP_EQ, OP_IMPL, OP_ITE})


def get_identifier(node: ExprNode) -> VariableIndex:
    assert node.kind() in NODE_LITERALS
    idx = abs(cast("int", node.data()))
    return VariableIndex(idx)


def get_operands(node: ExprNode) -> tuple[ExprNode, ...]:
    assert node.kind() in NODE_OPS
    return cast("tuple[ExprNode, ...]", node.data())


def get_support(*nodes: ExprNode) -> dict[int, ExprNode]:
    input_lits: dict[int, ExprNode] = {}
    for node in nodes:
        for child in node:
            if child.kind() in NODE_LITERALS:
                idx = child.data()
                assert isinstance(idx, int)
                input_lits[idx] = child
    return input_lits


def are_trivially_equivalent(lhs: ExprNode, rhs: ExprNode) -> bool:
    if lhs.kind() != rhs.kind():
        return False

    if lhs.kind() in NODE_CONSTANTS:
        return True

    if lhs.kind() in NODE_LITERALS:
        return lhs.data() == rhs.data()

    return lhs.id() == rhs.id()


class ConvertibleToExprNode(Protocol):
    def __exprnode__(self) -> ExprNode: ...


type ExprOrNode = ConvertibleToExprNode | ExprNode


def to_node(expression: ExprOrNode) -> ExprNode:
    if isinstance(expression, ExprNode):
        return expression
    return expression.__exprnode__()


def varmap_to_nodemap(mapping: VarMap[ExprOrNode]) -> NodeMap:
    return {v.pos_lit: to_node(e) for v, e in mapping.items()}
