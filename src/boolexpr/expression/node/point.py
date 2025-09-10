from __future__ import annotations

from typing import TYPE_CHECKING

from boolexpr.exprnode import ExprNode, and_, or_

if TYPE_CHECKING:
    from collections.abc import Iterator

    from boolexpr.point import Point
    from boolexpr.variable.variable import Variable

__all__ = [
    "point_to_term",
    "point_to_clause",
    "iter_point_lits",
]


def point_to_term(point: Point[Variable]) -> ExprNode:
    return and_(*iter_point_lits(point))


def point_to_clause(point: Point[Variable]) -> ExprNode:
    return or_(*iter_point_lits(point))


def iter_point_lits(point: Point[Variable]) -> Iterator[ExprNode]:
    yield from (+v if p else -v for v, p in point.items())
