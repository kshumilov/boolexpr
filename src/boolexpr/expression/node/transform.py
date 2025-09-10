from __future__ import annotations

from typing import TYPE_CHECKING, cast

from boolexpr.exprnode import ExprNode, One, Zero, and_, or_, xor
from boolexpr.point import iter_points

from .point import point_to_term
from .utils import NODE_ATOMS, NODE_OP_TO_BUILDER, NODE_OPS

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable


__all__ = [
    "condition",
    "iter_cofactors",
    "universal",
    "existential",
    "derivative",
    "shannon",
    "tseitin",
]


def condition(node: ExprNode, point: Point[Variable]) -> ExprNode:
    return node.restrict({var.pos_lit: (One if polarity else Zero) for var, polarity in point.items()})


def iter_cofactors(node: ExprNode, *variables: Variable) -> Iterator[ExprNode]:
    for point in iter_points(variables):
        yield condition(node, point)


def universal(node: ExprNode, *variables: Variable) -> ExprNode:
    return and_(*iter_cofactors(node, *variables))


def existential(node: ExprNode, *variables: Variable) -> ExprNode:
    return or_(*iter_cofactors(node, *variables))


def derivative(node: ExprNode, *variables: Variable) -> ExprNode:
    return xor(*iter_cofactors(node, *variables))


def shannon(node: ExprNode, *variables: Variable) -> ExprNode:
    return or_(*(and_(point_to_term(p), condition(node, p)) for p in iter_points(variables)))


def tseitin(node: ExprNode, get_new_var: Callable[[], ExprNode]) -> tuple[ExprNode, list[tuple[ExprNode, ExprNode]]]:
    if node.kind() in NODE_ATOMS:
        return node, []

    constraints = []
    lit_for: dict[int, ExprNode] = {}
    stack: list[tuple[ExprNode, bool]] = [(node, False)]

    while stack:
        curr, visited = stack.pop()

        operands = cast("tuple[ExprNode,...]", curr.data())

        if not visited:
            stack.append((curr, True))
            stack.extend(
                (operand, False) for operand in operands if operand.kind() in NODE_OPS and operand.id() not in lit_for
            )
        elif curr.id() not in lit_for:
            builder = cast("Callable[..., ExprNode]", NODE_OP_TO_BUILDER[curr.kind()])
            constraint = builder(*(lit_for.get(c.id(), c) for c in operands))

            new_var = get_new_var()
            constraints.append((new_var, constraint))
            lit_for[curr.id()] = new_var

    return lit_for[node.id()], constraints
