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
    from collections.abc import Callable, Hashable, Iterator

    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable


def get_operands(node: ExprNode) -> tuple[ExprNode, ...]:
    if node.kind() in OP_TO_BUILDER:
        operands = node.data()
        assert isinstance(operands, tuple)
        assert all(isinstance(op, ExprNode) for op in operands)
        return operands
    return ()


def get_support(node: ExprNode) -> dict[int, ExprNode]:
    input_lits: dict[int, ExprNode] = {}
    for child in node:
        if child.kind() in (VAR, COMP):
            idx = child.data()
            assert isinstance(idx, int)
            input_lits[idx] = child
    return input_lits


def are_trivially_equivalent(lhs: ExprNode, rhs: ExprNode) -> bool:
    if lhs.kind() != rhs.kind():
        return False

    if lhs.kind() in (ZERO, ONE):
        return True

    if lhs.kind() in (VAR, COMP):
        return lhs.data() == rhs.data()

    return lhs.id() == rhs.id()


def restrict_by_point[L: Hashable](node: ExprNode, point: Point[L]) -> ExprNode:
    return node.restrict({var.pos_lit: (One if polarity else Zero) for var, polarity in point.items()})


def point_to_term[L: Hashable](point: Point[L]) -> ExprNode:
    return and_(*iter_point_lits(point))


def point_to_clause[L: Hashable](point: Point[L]) -> ExprNode:
    return or_(*iter_point_lits(point))


def iter_cofactors[L: Hashable](node: ExprNode, *variables: Variable[L]) -> Iterator[ExprNode]:
    for point in iter_points(variables):
        yield restrict_by_point(node, point)


def universal[L: Hashable](node: ExprNode, *variables: Variable[L]) -> ExprNode:
    return and_(*iter_cofactors(node, *variables))


def existential[L: Hashable](node: ExprNode, *variables: Variable[L]) -> ExprNode:
    return or_(*iter_cofactors(node, *variables))


def derivative[L: Hashable](node: ExprNode, *variables: Variable[L]) -> ExprNode:
    return xor(*iter_cofactors(node, *variables))


def shannon[L: Hashable](node: ExprNode, *variables: Variable[L]) -> ExprNode:
    return or_(*(and_(point_to_term(p), restrict_by_point(node, p)) for p in iter_points(variables)))


def iter_point_lits[L: Hashable](point: Point[L]) -> Iterator[ExprNode]:
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


def tseitin_constraints(
    node: ExprNode, get_new_var: Callable[[], ExprNode]
) -> tuple[ExprNode, list[tuple[ExprNode, ExprNode]]]:
    if node.kind() in (ZERO, ONE, VAR, COMP):
        return node, []

    constraints = []
    lit_for: dict[int, ExprNode] = {}
    stack: list[tuple[ExprNode, bool]] = [(node, False)]

    while stack:
        curr, visited = stack.pop()
        if curr.id() in lit_for:
            continue

        if curr.kind() in (ZERO, ONE, VAR, COMP):
            lit_for[curr.id()] = curr
            continue

        if not visited:
            stack.append((curr, True))
            for child in reversed(cast("tuple[ExprNode,...]", curr.data())):
                stack.append((child, False))
        else:
            new_var = get_new_var()
            builder = cast("Callable[..., ExprNode]", OP_TO_BUILDER[curr.kind()])
            constraint = builder(*(lit_for[c.id()] for c in cast("tuple[ExprNode, ...]", curr.data())))
            constraints.append((new_var, constraint))
            lit_for[curr.id()] = new_var

    return lit_for[node.id()], constraints


OP_TO_KIND = {
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

OP_TO_BUILDER = {
    OP_NOT: not_,
    OP_AND: and_,
    OP_OR: or_,
    OP_XOR: xor,
    OP_EQ: eq,
    OP_IMPL: impl,
    OP_ITE: ite,
}

OP_TO_NAME = {
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
