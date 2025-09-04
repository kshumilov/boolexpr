import functools
import operator
from collections.abc import Iterator, Set
from functools import cached_property
from typing import Self

from .typing import ExpressionLike, Point, VariableLike
from .utils import iter_points

__all__ = [
    "Function",
]


class Function(ExpressionLike):
    """
    Abstract base class that defines an interface for a symbolic Boolean
    function of :math:`N` variables.
    """

    # Operators
    def __invert__(self) -> Self:
        """Boolean negation operator

        +-----------+------------+
        | :math:`f` | :math:`f'` |
        +===========+============+
        |         0 |          1 |
        +-----------+------------+
        |         1 |          0 |
        +-----------+------------+
        """
        raise NotImplementedError

    def __or__(self, g: Self) -> Self:
        """Boolean disjunction (sum, OR) operator

        +-----------+-----------+---------------+
        | :math:`f` | :math:`g` | :math:`f + g` |
        +===========+===========+===============+
        |         0 |         0 |             0 |
        +-----------+-----------+---------------+
        |         0 |         1 |             1 |
        +-----------+-----------+---------------+
        |         1 |         0 |             1 |
        +-----------+-----------+---------------+
        |         1 |         1 |             1 |
        +-----------+-----------+---------------+
        """
        raise NotImplementedError

    def __ror__(self, g: Self) -> Self:
        return self.__or__(g)

    def __and__(self, g: Self) -> Self:
        r"""Boolean conjunction (product, AND) operator

        +-----------+-----------+-------------------+
        | :math:`f` | :math:`g` | :math:`f \cdot g` |
        +===========+===========+===================+
        |         0 |         0 |                 0 |
        +-----------+-----------+-------------------+
        |         0 |         1 |                 0 |
        +-----------+-----------+-------------------+
        |         1 |         0 |                 0 |
        +-----------+-----------+-------------------+
        |         1 |         1 |                 1 |
        +-----------+-----------+-------------------+
        """
        raise NotImplementedError

    def __rand__(self, g: Self) -> Self:
        return self.__and__(g)

    def __xor__(self, g: Self) -> Self:
        r"""Boolean exclusive or (XOR) operator

        +-----------+-----------+--------------------+
        | :math:`f` | :math:`g` | :math:`f \oplus g` |
        +===========+===========+====================+
        |         0 |         0 |                  0 |
        +-----------+-----------+--------------------+
        |         0 |         1 |                  1 |
        +-----------+-----------+--------------------+
        |         1 |         0 |                  1 |
        +-----------+-----------+--------------------+
        |         1 |         1 |                  0 |
        +-----------+-----------+--------------------+
        """
        raise NotImplementedError

    def __rxor__(self, g: Self) -> Self:
        return self.__xor__(g)

    @property
    def support(self) -> Set[VariableLike]:
        r"""Return the support set of a function.

        Let :math:`f(x_1, x_2, \dots, x_n)` be a Boolean function of :math:`N`
        variables.

        The unordered set :math:`\{x_1, x_2, \dots, x_n\}` is called the
        *support* of the function.
        """
        raise NotImplementedError

    @cached_property
    def usupport(self) -> Set[int]:
        """Return the untyped support set of a function."""
        return frozenset(v.uniqid for v in self.support)

    @property
    def inputs(self) -> tuple[VariableLike, ...]:
        """Return the support set in name/index order."""
        raise NotImplementedError

    @property
    def top(self) -> VariableLike | None:
        """Return the first variable in the ordered support set."""
        if self.inputs:
            return self.inputs[0]
        return None

    @property
    def degree(self) -> int:
        r"""Return the degree of a function.

        A function from :math:`B^{N} \Rightarrow B` is called a Boolean
        function of *degree* :math:`N`.
        """
        return len(self.support)

    @property
    def cardinality(self) -> int:
        r"""Return the cardinality of the relation :math:`B^{N} \Rightarrow B`.

        Always equal to :math:`2^{N}`.
        """
        return 1 << self.degree

    def iter_domain(self) -> Iterator[Point[VariableLike]]:
        """Iterate through all points in the domain."""
        yield from iter_points(self.inputs)

    def iter_image(self):
        """Iterate through all elements in the image."""
        for point in iter_points(self.inputs):
            yield self.restrict(point)

    def iter_relation(self):
        """Iterate through all (point, element) pairs in the relation."""
        for point in iter_points(self.inputs):
            yield point, self.restrict(point)

    def restrict(self, point) -> Self:
        r"""
        Restrict a subset of support variables to :math:`\{0, 1\}`.

        Returns a new function: :math:`f(x_i, \ldots)`

        :math:`f \: | \: x_i = b`
        """
        raise NotImplementedError

    def compose(self, mapping):
        r"""
        Substitute a subset of support variables with other Boolean functions.

        Returns a new function: :math:`f(g_i, \ldots)`

        :math:`f_1 \: | \: x_i = f_2`
        """
        raise NotImplementedError

    def satisfy_one(self):
        """
        If this function is satisfiable, return a satisfying input point. A
        tautology *may* return a zero-dimensional point; a contradiction *must*
        return None.
        """
        raise NotImplementedError

    def satisfy_all(self):
        """Iterate through all satisfying input points."""
        raise NotImplementedError

    def satisfy_count(self):
        """Return the cardinality of the set of all satisfying input points."""
        return sum(1 for _ in self.satisfy_all())

    def iter_cofactors(self, *variables: VariableLike):
        r"""Iterate through the cofactors of a function over N variables.

        The *vs* argument is a sequence of :math:`N` Boolean variables.

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i` is:
        :math:`f_{x_i} = f(x_1, x_2, \dots, 1, \dots, x_n)`

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i'` is:
        :math:`f_{x_i'} = f(x_1, x_2, \dots, 0, \dots, x_n)`
        """
        for point in iter_points(variables):
            yield self.restrict(point)

    def cofactors(self, vs=None):
        r"""Return a tuple of the cofactors of a function over N variables.

        The *vs* argument is a sequence of :math:`N` Boolean variables.

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i` is:
        :math:`f_{x_i} = f(x_1, x_2, \dots, 1, \dots, x_n)`

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i'` is:
        :math:`f_{x_i'} = f(x_1, x_2, \dots, 0, \dots, x_n)`
        """
        return tuple(cf for cf in self.iter_cofactors(vs))

    def smoothing(self, vs=None):
        r"""Return the smoothing of a function over a sequence of N variables.

        The *vs* argument is a sequence of :math:`N` Boolean variables.

        The *smoothing* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`S_{x_i}(f) = f_{x_i} + f_{x_i'}`

        This is the same as the existential quantification operator:
        :math:`\exists \{x_1, x_2, \dots\} \: f`
        """
        return functools.reduce(operator.or_, self.iter_cofactors(vs))

    def consensus(self, vs=None):
        r"""Return the consensus of a function over a sequence of N variables.

        The *vs* argument is a sequence of :math:`N` Boolean variables.

        The *consensus* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`C_{x_i}(f) = f_{x_i} \cdot f_{x_i'}`

        This is the same as the universal quantification operator:
        :math:`\forall \{x_1, x_2, \dots\} \: f`
        """
        return functools.reduce(operator.and_, self.iter_cofactors(vs))

    def derivative(self, vs=None):
        r"""Return the derivative of a function over a sequence of N variables.

        The *vs* argument is a sequence of :math:`N` Boolean variables.

        The *derivative* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`\frac{\partial}{\partial x_i} f = f_{x_i} \oplus f_{x_i'}`

        This is also known as the Boolean *difference*.
        """
        return functools.reduce(operator.xor, self.iter_cofactors(vs))

    def is_zero(self):
        """Return whether this function is zero.

        .. note::
           This method will only look for a particular "zero form",
           and will **NOT** do a full search for a contradiction.
        """
        raise NotImplementedError

    def is_one(self):
        """Return whether this function is one.

        .. note::
           This method will only look for a particular "one form",
           and will **NOT** do a full search for a tautology.
        """
        raise NotImplementedError

    @staticmethod
    def box(obj):
        """Convert primitive types to a Function."""
        raise NotImplementedError

    def unbox(self):
        """Return integer 0 or 1 if possible, otherwise return the Function."""
        if self.is_zero():
            return 0
        if self.is_one():
            return 1
        return self
