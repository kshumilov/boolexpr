from __future__ import annotations

from typing import TYPE_CHECKING

from boolexpr.math import bit_on

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator, Mapping, Sequence

    from boolexpr.variable.variable import Variable

__all__ = [
    "num2point",
    "iter_points",
    "Point",
]

type Point[Label: Hashable] = Mapping[Variable[Label], bool]


def num2point[L: Hashable](num: int, vs: Sequence[Variable[L]]) -> Point[L]:
    """Convert *num* into a point in an N-dimensional Boolean space.

    Parameters
    ----------
    num : int
        The *num* argument is an int in range :math:`[0, 2^N)`.
    vs : Sequence[Variable]
        The `vs` argument is a sequence of :math:`N` Boolean variables.
        There are :math:`2^N` points in the corresponding Boolean space.
        The dimension number of each variable is its index in the sequence.

    For example, consider the 3-dimensional space formed by variables
    :math:`a`, :math:`b`, :math:`c`.
    Each vertex corresponds to a 3-dimensional point as summarized by the
    table::

                6-----------7  ===== ======= =================
               /|          /|   num   a b c        point
              / |         / |  ===== ======= =================
             /  |        /  |    0    0 0 0   {a:0, b:0, c:0}
            4-----------5   |    1    1 0 0   {a:1, b:0, c:0}
            |   |       |   |    2    0 1 0   {a:0, b:1, c:0}
            |   |       |   |    3    1 1 0   {a:1, b:1, c:0}
            |   2-------|---3    4    0 0 1   {a:0, b:0, c:1}
            |  /        |  /     5    1 0 1   {a:1, b:0, c:1}
       c b  | /         | /      6    0 1 1   {a:0, b:1, c:1}
       |/   |/          |/       7    1 1 1   {a:1, b:1, c:1}
       +-a  0-----------1      ===== ======= =================

    .. note::
       The ``a b c`` column is the binary representation of *num*
       written in little-endian order.
    """
    num %= 2 ** len(vs)
    return {v: bit_on(num, i) for i, v in enumerate(vs)}


def iter_points[L: Hashable](vs: Sequence[Variable[L]]) -> Iterator[Point[L]]:
    """Iterate through all points in an N-dimensional Boolean space.

    The *vs* argument is a sequence of :math:`N` Boolean variables.
    """
    for num in range(1 << len(vs)):
        yield num2point(num, vs)
