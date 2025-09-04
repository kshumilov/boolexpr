from __future__ import annotations

from collections.abc import Hashable
from functools import reduce
from operator import and_, or_, xor
from typing import TYPE_CHECKING

from boolexpr.point import Point, iter_points

from .interface import Expression
from .kind import Kind
from .simple import SimpleExpression

if TYPE_CHECKING:
    from boolexpr.variable.variable import Variable

type Expr[Label: Hashable] = Expression[Label, SimpleExpression[Label]]


def universal_quantify[L: Hashable](expr: Expr[L], *vs: Variable[L]) -> Expr[L]:
    r"""Return the consensus of a function over a sequence of N variables.

    The *vs* argument is a sequence of :math:`N` Boolean variables.

    The *consensus* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
    respect to variable :math:`x_i` is:
    :math:`C_{x_i}(f) = f_{x_i} \cdot f_{x_i'}`

    This is the same as the universal quantification operator:
    :math:`\forall \{x_1, x_2, \dots\} \: f`
    """
    return reduce(and_, expr.iter_cofactors(*vs))


def existential_quantify[L: Hashable](expr: Expr[L], *vs: Variable[L]) -> Expr[L]:
    r"""Return the smoothing of a function over a sequence of N variables.

    The *vs* argument is a sequence of :math:`N` Boolean variables.

    The *smoothing* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
    respect to variable :math:`x_i` is:
    :math:`S_{x_i}(f) = f_{x_i} + f_{x_i'}`

    This is the same as the existential quantification operator:
    :math:`\exists \{x_1, x_2, \dots\} \: f`
    """
    return reduce(or_, expr.iter_cofactors(*vs))


def derivative[L: Hashable](expr: Expr[L], *vs: Variable[L]) -> Expr[L]:
    r"""Return the derivative of a function over a sequence of N variables.

    The *vs* argument is a sequence of :math:`N` Boolean variables.

    The *derivative* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
    respect to variable :math:`x_i` is:
    :math:`\frac{\partial}{\partial x_i} f = f_{x_i} \oplus f_{x_i'}`

    This is also known as the Boolean *difference*.
    """
    return reduce(xor, expr.iter_cofactors(*vs))


def point_to_term[L: Hashable](point: Point[L]) -> Expr[L]:
    return SimpleExpression.make_nary(Kind.Conjunction, *(+v if p else -v for v, p in point.items()))


def point_to_clause[L: Hashable](point: Point[L]) -> Expr[L]:
    return SimpleExpression.make_nary(Kind.Disjunction, *(+v if p else -v for v, p in point.items()))


def shannon_decompose[L: Hashable](expr: Expr[L], *vs: Variable[L]) -> Expr[L]:
    return reduce(or_, (point_to_term(p) & expr.restrict(p) for p in iter_points(vs)))
