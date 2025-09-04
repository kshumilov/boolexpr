from collections.abc import Iterator, Sequence
from typing import Any

from .typing import ExpressionLike, Point, Term, UntypedPoint, VariableLike

__all__ = [
    "num2point",
    "num2upoint",
    "num2term",
    "point2upoint",
    "iter_points",
    "iter_terms",
    "iter_upoints",
    "Point",
    "UntypedPoint",
    "Term",
]


def validate_is_type(value: Any, expected_type: type) -> None:
    if not isinstance(value, expected_type):
        raise TypeError(f"expected {value} to be an {expected_type.__name__}, got {type(value).__name__}")


def validate_number_in_range[T: (int, float)](value: T, lower_bound: T, upper_bound: T) -> None:
    if not lower_bound <= value < upper_bound:
        raise ValueError(f"expected number to be in range [{lower_bound}, {upper_bound}), got {value}")


def num2upoint(num: int, vs: Sequence[VariableLike]) -> UntypedPoint:
    """Convert *num* into an untyped point in an N-dimensional Boolean space.

    The *vs* argument is a sequence of :math:`N` Boolean variables.
    There are :math:`2^N` points in the corresponding Boolean space.
    The dimension number of each variable is its index in the sequence.

    The *num* argument is an int in range :math:`[0, 2^N)`.

    See :func:`num2point` for a description of how *num* maps onto an
    N-dimensional point.
    This function merely converts the output to an immutable (untyped) form.
    """
    return point2upoint(num2point(num, vs))


def num2term(num: int, fs: Sequence[ExpressionLike], *, conj: bool = False) -> Term[ExpressionLike]:
    """Convert *num* into a min/max term in an N-dimensional Boolean space.

    The *fs* argument is a sequence of :math:`N` Boolean functions.
    There are :math:`2^N` points in the corresponding Boolean space.
    The dimension number of each function is its index in the sequence.

    The *num* argument is an int in range :math:`[0, 2^N)`.

    If *conj* is ``False``, return a minterm.
    Otherwise, return a maxterm.

    For example, consider the 3-dimensional space formed by functions
    :math:`f`, :math:`g`, :math:`h`.
    Each vertex corresponds to a min/max term as summarized by the table::

                6-----------7  ===== ======= ========== ==========
               /|          /|   num   f g h    minterm    maxterm
              / |         / |  ===== ======= ========== ==========
             /  |        /  |    0    0 0 0   f' g' h'   f  g  h
            4-----------5   |    1    1 0 0   f  g' h'   f' g  h
            |   |       |   |    2    0 1 0   f' g  h'   f  g' h
            |   |       |   |    3    1 1 0   f  g  h'   f' g' h
            |   2-------|---3    4    0 0 1   f' g' h    f  g  h'
            |  /        |  /     5    1 0 1   f  g' h    f' g  h'
       h g  | /         | /      6    0 1 1   f' g  h    f  g' h'
       |/   |/          |/       7    1 1 1   f  g  h    f' g' h'
       +-f  0-----------1      ===== ======= ========= ===========

    .. note::
       The ``f g h`` column is the binary representation of *num*
       written in little-endian order.
    """
    validate_is_type(num, int)
    validate_number_in_range(num, 0, 2 ** len(fs))

    if conj:
        return tuple(~f if bit_on(num, i) else f for i, f in enumerate(fs))
    return tuple(f if bit_on(num, i) else ~f for i, f in enumerate(fs))


def point2upoint(point: Point[VariableLike]) -> UntypedPoint:
    """Convert *point* into an untyped point."""
    untyped_point: list[set[int]] = [set(), set()]
    for v, val in point.items():
        untyped_point[val].add(v.uniqid)
    return frozenset(untyped_point[0]), frozenset(untyped_point[1])


def point2term(point: Point[VariableLike], *, conj: bool = False) -> Term[ExpressionLike]:
    """Convert *point* into a min/max term.

    If *conj* is ``False``, return a minterm.
    Otherwise, return a maxterm.
    """
    if conj:
        return tuple(~v if val else v for v, val in point.items())
    return tuple(v if val else ~v for v, val in point.items())


def iter_points(vs: Sequence[VariableLike]) -> Iterator[Point[ExpressionLike]]:
    """Iterate through all points in an N-dimensional Boolean space.

    The *vs* argument is a sequence of :math:`N` Boolean variables.
    """
    for num in range(1 << len(vs)):
        yield num2point(num, vs)


def iter_upoints(vs: Sequence[VariableLike]) -> Iterator[UntypedPoint]:
    """Iterate through all untyped points in an N-dimensional Boolean space.

    The *vs* argument is a sequence of :math:`N` Boolean variables.
    """
    for num in range(1 << len(vs)):
        yield num2upoint(num, vs)


def iter_terms(fs: Sequence[VariableLike], *, conj: bool = False) -> Iterator[Term[ExpressionLike]]:
    """Iterate through all min/max terms in an N-dimensional Boolean space.

    The *fs* argument is a sequence of :math:`N` Boolean functions.

    If *conj* is ``False``, yield minterms.
    Otherwise, yield maxterms.
    """
    for num in range(1 << len(fs)):
        yield num2term(num, fs, conj=conj)
