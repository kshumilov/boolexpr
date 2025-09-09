from __future__ import annotations

from itertools import combinations
from typing import TYPE_CHECKING, cast

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
    One,
    Zero,
    and_,
    eq,
    impl,
    ite,
    not_,
    or_,
    xor,
)
from boolexpr.point import iter_points

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable

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

NODE_OP_TO_BUILDER = {
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

__all__ = [
    "get_operands",
    "get_support",
    "are_trivially_equivalent",
    "condition",
    "point_to_term",
    "point_to_clause",
    "iter_cofactors",
    "universal",
    "existential",
    "derivative",
    "shannon",
    "iter_point_lits",
    "at_least",
    "less_than",
    "exactly",
    "tseitin_encoding",
    "NODE_KIND_TO_KIND",
    "NARY_TO_BUILDER",
    "NODE_OP_TO_BUILDER",
    "NODE_LITERALS",
    "NODE_CONSTANTS",
]


def get_operands(node: ExprNode) -> tuple[ExprNode, ...]:
    if node.kind() in NODE_OPS:
        return cast("tuple[ExprNode, ...]", node.data())
    return ()


def get_support(node: ExprNode) -> dict[int, ExprNode]:
    input_lits: dict[int, ExprNode] = {}
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


def condition(node: ExprNode, point: Point[Variable]) -> ExprNode:
    return node.restrict({var.pos_lit: (One if polarity else Zero) for var, polarity in point.items()})


def point_to_term(point: Point[Variable]) -> ExprNode:
    return and_(*iter_point_lits(point))


def point_to_clause(point: Point[Variable]) -> ExprNode:
    return or_(*iter_point_lits(point))


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


def iter_point_lits(point: Point[Variable]) -> Iterator[ExprNode]:
    yield from (+v if p else -v for v, p in point.items())


def at_least(k: int, *nodes: ExprNode, as_cnf: bool = True) -> ExprNode:
    num_nodes = len(nodes)

    if k <= 0:
        return One
    if k == 1:
        return or_(*nodes)
    if k == num_nodes:
        return and_(*nodes)
    if k > num_nodes:
        return Zero

    if as_cnf:
        return and_(*(or_(*ops) for ops in combinations(nodes, num_nodes - k + 1)))

    return or_(*(and_(*ops) for ops in combinations(nodes, k)))


def less_than(k: int, *nodes: ExprNode, as_cnf: bool = True) -> ExprNode:
    num_nodes = len(nodes)
    negated_nodes = map(not_, nodes)

    if k <= 0:
        return Zero
    if k == 1:
        return and_(*negated_nodes)
    if k == num_nodes:
        return or_(*negated_nodes)
    if k > num_nodes:
        return One

    if as_cnf:
        return and_(*(or_(*ops) for ops in combinations(negated_nodes, k)))

    return or_(*(and_(*ops) for ops in combinations(negated_nodes, num_nodes - k + 1)))


def exactly(k: int, *nodes: ExprNode, as_cnf: bool = True) -> ExprNode:
    return and_(at_least(k, *nodes, as_cnf=as_cnf), less_than(k + 1, *nodes, as_cnf=as_cnf))


def tseitin_encoding(
    node: ExprNode, get_new_var: Callable[[], ExprNode]
) -> tuple[ExprNode, list[tuple[ExprNode, ExprNode]]]:
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
