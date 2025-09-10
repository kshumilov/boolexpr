from __future__ import annotations

from collections import Counter
from itertools import combinations
from math import comb
from typing import TYPE_CHECKING, Protocol

from boolexpr.exprnode import ONE, ZERO, ExprNode, One, Zero, and_, lit, not_, or_
from boolexpr.point import iter_points

from .utils import NODE_LITERALS, get_identifier

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


__all__ = [
    "remove_constants",
    "at_least",
    "at_least_size",
    "less_than",
    "exactly",
    "expand",
]


def remove_constants(nodes: Iterable[ExprNode]) -> tuple[int, list[ExprNode]]:
    delta_k: int = 0
    left: list[ExprNode] = []
    for node in nodes:
        if node.kind() == ZERO:
            continue
        if node.kind() == ONE:
            delta_k -= 1
        else:
            left.append(node)
    return delta_k, left


def iter_duplicate_input_variables(nodes: Iterable[ExprNode]) -> Iterator[ExprNode]:
    seen_operands = Counter[int]()

    for node in nodes:
        if node.kind() in NODE_LITERALS:
            seen_operands[get_identifier(node)] += 1

    yield from (lit(idx) for idx, count in seen_operands.items() if count > 1)


def at_least_size(n: int, k: int, /, *, as_cnf: bool = True) -> int:
    if k <= 0:
        return 1
    if k == 1:
        return n + 1  # n vars + top node
    if k == n:
        return n + 1  # n vars + top node
    if k > n:
        return 1

    if as_cnf:
        or_ops = n - k + 1
        return (or_ops + 1) * comb(n, or_ops) + 1

    return (k + 1) * comb(n, k) + 1


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


class CardinalityBuilder(Protocol):
    def __call__(self, k: int, *nodes: ExprNode, as_cnf: bool) -> ExprNode: ...


def expand(k: int, builder: CardinalityBuilder, *nodes: ExprNode, as_cnf: bool = True) -> ExprNode:
    decidable = list(iter_duplicate_input_variables(nodes))

    terms = []
    for point in iter_points(decidable):
        mapping = {v: (One if p else Zero) for v, p in point.items()}
        delta_k, cofactor_nodes = remove_constants(op.restrict(mapping) for op in nodes)
        cofactor = builder(k + delta_k, *cofactor_nodes, as_cnf=as_cnf)
        terms.append(and_(*point.keys(), cofactor))

    if as_cnf:
        return or_(*terms).simplify().to_cnf()

    return or_(*terms).simplify().to_cnf()
