from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from rich.tree import Tree

from boolexpr.expression.cardinality import AtLeastOp
from boolexpr.expression.node.utils import (
    NODE_CONSTANTS,
    NODE_LITERALS,
    NODE_OPS,
    ExprOrNode,
    get_identifier,
    get_operands,
    to_node,
)
from boolexpr.exprnode import COMP, ONE, OP_AND, OP_EQ, OP_IMPL, OP_ITE, OP_NOT, OP_OR, OP_XOR, VAR, ZERO

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from boolexpr import exprnode
    from boolexpr.variable.index import VariableIndex

__all__ = [
    "build_node_tree",
    "build_expression_tree",
    "build_assignment_tree",
    "Displayable",
]

type Displayable = AtLeastOp | ExprOrNode

NODE_KIND_TO_NAME: dict[int, str] = {
    ZERO: "Zero",
    ONE: "One",
    VAR: "Var",
    COMP: "Comp",
    OP_NOT: "Not",
    OP_AND: "And",
    OP_OR: "Or",
    OP_XOR: "XOR",
    OP_EQ: "Equiv",
    OP_IMPL: "Implies",
    OP_ITE: "ITE",
}


class SupportsStr(Protocol):
    def __str__(self) -> str: ...


def new_tree(label: str, parent: Tree | None, /) -> Tree:
    if parent is None:
        return Tree(label)
    return parent.add(label)


def add_children(
    label: str,
    children: Iterable[exprnode.ExprNode],
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    not_char: str = "¬",
) -> Tree:
    subtree = new_tree(label, parent)
    for child in children:
        build_node_tree(child, subtree, idx_to_label, inline_size=inline_size, not_char=not_char)
    return subtree


def get_literal_node_label(
    node: exprnode.ExprNode, /, idx_to_label: Callable[[VariableIndex], str], *, not_char: str = "¬"
) -> str:
    assert node.kind() in NODE_LITERALS
    var_idx = get_identifier(node)
    variable_label = idx_to_label(var_idx)
    return variable_label if var_idx > 0 else f"{not_char}{variable_label}"


def get_constant_node_label(node: exprnode.ExprNode, /) -> str:
    assert node.kind() in NODE_CONSTANTS
    return NODE_KIND_TO_NAME[node.kind()]


def get_op_node_label(node: exprnode.ExprNode, /) -> str:
    assert node.kind() in NODE_OPS
    return f"{NODE_KIND_TO_NAME[node.kind()]}"


def get_infix_op_node_label(
    node: exprnode.ExprNode,
    /,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    not_char: str = "¬",
) -> str:
    assert node.kind() in NODE_OPS

    inlined: list[str] = []
    for operand in node.data():
        if operand.kind() in NODE_CONSTANTS:
            inlined.append(get_constant_node_label(operand))
        elif operand.kind() in NODE_LITERALS:
            inlined.append(get_literal_node_label(operand, idx_to_label, not_char=not_char))
        else:
            op_str = get_infix_op_node_label(operand, idx_to_label, not_char=not_char)
            inlined.append(f"({op_str})")

    if node.kind() == OP_ITE:
        return f"{inlined[0]} ? {inlined[1]} : {inlined[2]}"

    op_symbol = {
        OP_NOT: "~",
        OP_AND: "&",
        OP_OR: "|",
        OP_XOR: "<+>",
        OP_EQ: "<->",
        OP_IMPL: "->",
    }[node.kind()]

    return f"{f' {op_symbol} '.join(inlined)}"


def inline_associative_op_node_operands(
    label: str,
    operands: Iterable[exprnode.ExprNode],
    /,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    not_char: str = "¬",
    # inline_size: int = 5,
) -> tuple[str, list[exprnode.ExprNode]]:
    inlined: list[str] = []
    gates: list[exprnode.ExprNode] = []

    for operand in operands:
        if operand.kind() in NODE_CONSTANTS:
            inlined.append(get_constant_node_label(operand))
        elif operand.kind() in NODE_LITERALS:
            inlined.append(get_literal_node_label(operand, idx_to_label, not_char=not_char))
        else:
            gates.append(operand)
        # elif operand.size() > inline_size:
        #     gates.append(operand)
        # else:
        #     inlined.append(get_infix_op_node_label(operand, idx_to_label, not_char=not_char))

    if inlined:
        literal_set = ", ".join(inlined)
        label = f"{label}{{{literal_set}, ...}}" if gates else f"{label}{{{literal_set}}}"

    return label, gates


def inline_not_associative_op_node_operands(
    label: str,
    operands: Iterable[exprnode.ExprNode],
    /,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    not_char: str = "¬",
    # inline_size: int = 5,
) -> tuple[str, list[exprnode.ExprNode]]:
    inlined: list[str] = []
    gates: list[exprnode.ExprNode] = []

    for operand in operands:
        if operand.kind() in NODE_CONSTANTS:
            inlined.append(get_constant_node_label(operand))
        elif operand.kind() in NODE_LITERALS:
            inlined.append(get_literal_node_label(operand, idx_to_label, not_char=not_char))
        else:
            inlined.append("...")
            gates.append(operand)
        # elif operand.size() > inline_size:
        #     inlined.append("...")
        #     gates.append(operand)
        # else:
        #     inlined.append(get_infix_op_node_label(operand, idx_to_label, not_char=not_char))

    if inlined:
        literal_set = ", ".join(inlined)
        label = f"{label}({literal_set})"

    return label, gates


def build_op_node_tree(
    node: exprnode.ExprNode,
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    not_char: str = "¬",
) -> Tree:
    label = get_op_node_label(node)
    operands: Iterable[exprnode.ExprNode] = get_operands(node)

    if node.size() < inline_size:
        label = get_infix_op_node_label(node, idx_to_label, not_char=not_char)
        return new_tree(label, parent)

    if node.kind() in (OP_ITE, OP_IMPL):
        label, operands = inline_not_associative_op_node_operands(
            label,
            operands,
            idx_to_label,
            not_char=not_char,
            # inline_size=inline_size,
        )
    else:
        label, operands = inline_associative_op_node_operands(
            label,
            operands,
            idx_to_label,
            not_char=not_char,
            # inline_size=inline_size,
        )

    return add_children(
        label,
        operands,
        parent,
        idx_to_label,
        inline_size=inline_size,
        not_char=not_char,
    )


def build_node_tree(
    node: exprnode.ExprNode,
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    not_char: str = "¬",
) -> Tree:
    if node.kind() in NODE_CONSTANTS:
        label = get_constant_node_label(node)
        return new_tree(label, parent)

    if node.kind() in NODE_LITERALS:
        label = get_literal_node_label(node, idx_to_label, not_char=not_char)
        return new_tree(label, parent)

    return build_op_node_tree(node, parent, idx_to_label, inline_size=inline_size, not_char=not_char)


def build_at_least_tree(
    k: int,
    operands: Iterable[exprnode.ExprNode],
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    not_char: str = "¬",
) -> Tree:
    label = f"AtLeast[{k}]"

    if inline_size:
        label, operands = inline_associative_op_node_operands(label, operands, idx_to_label, not_char=not_char)

    return add_children(
        label,
        operands,
        parent,
        idx_to_label,
        inline_size=inline_size,
        not_char=not_char,
    )


def build_expression_tree(
    expression: Displayable,
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    not_char: str = "¬",
) -> Tree:
    match expression:
        case AtLeastOp(k=k, xs=nodes):
            return build_at_least_tree(
                k,
                nodes,
                parent,
                idx_to_label,
                inline_size=inline_size,
                not_char=not_char,
            )

    return build_node_tree(
        to_node(expression),
        parent,
        idx_to_label,
        inline_size=inline_size,
        not_char=not_char,
    )


def build_assignment_tree(
    variable: exprnode.ExprNode,
    expression: Displayable,
    /,
    parent: Tree | None,
    idx_to_label: Callable[[VariableIndex], str],
    *,
    inline_size: int = 5,
    assign_char: str = " := ",
    not_char: str = "¬",
) -> Tree:
    assert variable.kind() == VAR
    tree = build_expression_tree(
        expression,
        parent,
        inline_size=inline_size,
        idx_to_label=idx_to_label,
        not_char=not_char,
    )

    label = get_literal_node_label(variable, idx_to_label=idx_to_label, not_char=not_char)
    tree.label = f"{label}{assign_char}{tree.label}"
    return tree
