from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from rich.tree import Tree

from boolexpr.exprnode import COMP, ONE, OP_AND, OP_EQ, OP_IMPL, OP_ITE, OP_NOT, OP_OR, OP_XOR, VAR, ZERO
from boolexpr.variable.index import VariableIndex

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from boolexpr import exprnode

__all__ = [
    "build_expression_tree",
    "build_expression_forest",
]


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


def new_tree(label: str, parent: Tree | None = None) -> Tree:
    if parent is None:
        return Tree(label)
    return parent.add(label)


def add_children(
    label: str, children: Iterable[exprnode.ExprNode], /, *, parent: Tree | None = None, **kwargs: Any
) -> Tree:
    subtree = new_tree(label, parent=parent)
    for child in children:
        build_expression_tree(child, parent=subtree, **kwargs)
    return subtree


def get_literal_label(
    node: exprnode.ExprNode, /, *, idx_to_label: Callable[[VariableIndex], str], negation_char: str = "¬"
) -> str:
    assert node.kind() in (VAR, COMP)
    var_idx = cast("int", node.data())
    variable_label = str(idx_to_label(VariableIndex(abs(var_idx))))
    return variable_label if var_idx > 0 else f"{negation_char}{variable_label}"


def get_constant_label(node: exprnode.ExprNode) -> str:
    assert node.kind() in (ZERO, ONE)
    return NODE_KIND_TO_NAME[node.kind()]


def build_expression_tree(
    node: exprnode.ExprNode,
    *,
    parent: Tree | None = None,
    inline_literals: bool = True,
    idx_to_label: Callable[[VariableIndex], str] | None = None,
    not_char: str = "¬",
) -> Tree:
    if idx_to_label is None:
        idx_to_label = str

    if node.kind() in (ZERO, ONE):
        label = get_constant_label(node)
        return new_tree(label, parent=parent)

    if node.kind() in (VAR, COMP):
        label = get_literal_label(node, idx_to_label=idx_to_label, negation_char=not_char)
        return new_tree(label, parent=parent)

    if node.kind() == OP_NOT:
        tree = new_tree(NODE_KIND_TO_NAME[node.kind()], parent=parent)
        (operand,) = cast("tuple[exprnode.ExprNode]", node.data())
        build_expression_tree(
            operand,
            parent=tree,
            inline_literals=inline_literals,
            idx_to_label=idx_to_label,
            not_char=not_char,
        )
        return tree

    label = f"{NODE_KIND_TO_NAME[node.kind()]}"

    if inline_literals:
        inlined: list[str] = []
        gates: list[exprnode.ExprNode] = []
        operands = cast("Iterable[exprnode.ExprNode]", node.data())
        for operand in operands:
            if operand.kind() in (ZERO, ONE):
                inlined.append(get_constant_label(operand))
            elif operand.kind() in (VAR, COMP):
                inlined.append(get_literal_label(operand, idx_to_label=idx_to_label, negation_char=not_char))
            else:
                gates.append(operand)

        if inlined:
            literal_set = ", ".join(inlined)
            label = f"{label}{{{literal_set}, ...}}" if gates else f"{label}{{{literal_set}}}"
    else:
        gates = list(cast("Iterable[exprnode.ExprNode]", node.data()))

    return add_children(
        label,
        gates,
        parent=parent,
        inline_literals=inline_literals,
        idx_to_label=idx_to_label,
        not_char=not_char,
    )


def build_expression_forest(
    expressions: Iterable[tuple[exprnode.ExprNode, exprnode.ExprNode]],
    *,
    title: str = "Expressions",
    inline_literals: bool = True,
    idx_to_label: Callable[[VariableIndex], str] | None = None,
    not_char: str = "¬",
) -> Tree:
    forest = Tree(title)

    if idx_to_label is None:
        idx_to_label = str

    for variable, expression in expressions:
        subtree = build_expression_tree(
            expression,
            parent=forest,
            inline_literals=inline_literals,
            idx_to_label=idx_to_label,
            not_char=not_char,
        )

        label = get_literal_label(variable, idx_to_label=idx_to_label, negation_char=not_char)
        subtree.label = f"{label} := {subtree.label}"

    return forest
