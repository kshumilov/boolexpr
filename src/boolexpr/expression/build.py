from collections.abc import Hashable
from typing import Any

from boolexpr import exprnode
from boolexpr.expression.kind import Kind
from boolexpr.expression.simple import SimpleExpression

type X[Label: Hashable] = exprnode.ExprNode | SimpleExpression[Label]

__all__ = [
    "Not",
    "And",
    "Nand",
    "Or",
    "Nor",
    "Xor",
    "Xnor",
    "Equal",
    "NotEqual",
    "Imply",
]


def to_node(x: X[Any]) -> exprnode.ExprNode:  # noqa: N802
    if isinstance(x, exprnode.ExprNode):
        return x
    if isinstance(x, SimpleExpression):
        return x.node
    raise TypeError(f"Invalid expression type: {x}")


def Not[Label: Hashable](x: X[Label], *, simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    if isinstance(x, SimpleExpression):
        new_node = exprnode.not_(x.node)
    elif isinstance(x, exprnode.ExprNode):
        new_node = exprnode.not_(x)
    else:
        raise ValueError(f"Invalid input: {x}")

    return SimpleExpression.from_exprnode(new_node, simplify=simplify)


def Or[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_nary(Kind.Disjunction, *map(to_node, xs), simplify=simplify)


def And[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_nary(Kind.Conjunction, *map(to_node, xs), simplify=simplify)


def Xor[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_nary(Kind.Parity, *map(to_node, xs), simplify=simplify)


def Equal[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_nary(Kind.Equivalence, *map(to_node, xs), simplify=simplify)


def Imply[Label: Hashable](p: X[Label], q: X[Label], /, *, simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_implication(to_node(p), to_node(q), simplify=simplify)


def ITE[Label: Hashable](  # noqa: N802
    s: X[Label], d1: X[Label], d0: X[Label], /, *, simplify: bool = True
) -> SimpleExpression[Label]:
    return SimpleExpression.make_decision(to_node(s), to_node(d1), to_node(d0), simplify=simplify)


# high order functions
def Nor[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_negated_nary(Kind.Disjunction, *map(to_node, xs), simplify=simplify)


def Nand[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_negated_nary(Kind.Conjunction, *map(to_node, xs), simplify=simplify)


def Xnor[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_negated_nary(Kind.Parity, *map(to_node, xs), simplify=simplify)


def NotEqual[Label: Hashable](*xs: X[Label], simplify: bool = True) -> SimpleExpression[Label]:  # noqa: N802
    return SimpleExpression.make_negated_nary(Kind.Equivalence, *map(to_node, xs), simplify=simplify)


# def AtMostOne(*xs, simplify=True, conj=True):
#     """
#     Return an expression that means
#     "at most one input function is true".
#
#     If *simplify* is ``True``, return a simplified expression.
#
#     If *conj* is ``True``, return a CNF.
#     Otherwise, return a DNF.
#     """
#     nodes = map(to_node, xs)
#
#     if conj:
#         terms = exprnode.and_(*(
#             exprnode.or_(exprnode.not_(x0), exprnode.not_(x1))
#             for x0, x1 in combinations(nodes, 2)
#         ))
#     # else:
#     #     terms: list[exprnode.ExprNode] = []
#     #     for xs_ in itertools.combinations(xs, len(xs) - 1):
#     #         terms.append(exprnode.and_(*[exprnode.not_(x) for x in xs_]))
#     #     y = exprnode.or_(*terms)
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#
#
# def OneHot(*xs, simplify=True, conj=True):
#     """
#     Return an expression that means
#     "exactly one input function is true".
#
#     If *simplify* is ``True``, return a simplified expression.
#
#     If *conj* is ``True``, return a CNF.
#     Otherwise, return a DNF.
#     """
#     xs = [Expression.box(x).node for x in xs]
#     terms = []
#     if conj:
#         for x0, x1 in itertools.combinations(xs, 2):
#             terms.append(exprnode.or_(exprnode.not_(x0), exprnode.not_(x1)))
#         terms.append(exprnode.or_(*xs))
#         y = exprnode.and_(*terms)
#     else:
#         for i, xi in enumerate(xs):
#             zeros = [exprnode.not_(x) for x in xs[:i] + xs[i + 1 :]]
#             terms.append(exprnode.and_(xi, *zeros))
#         y = exprnode.or_(*terms)
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#
#
# def NHot(n, *xs, simplify=True):
#     """
#     Return an expression that means
#     "exactly N input functions are true".
#
#     If *simplify* is ``True``, return a simplified expression.
#     """
#     if not isinstance(n, int):
#         raise TypeError("expected n to be an int")
#     if not 0 <= n <= len(xs):
#         fstr = "expected 0 <= n <= {}, got {}"
#         raise ValueError(fstr.format(len(xs), n))
#
#     xs = [Expression.box(x).node for x in xs]
#     num = len(xs)
#     terms = []
#     for hot_idxs in itertools.combinations(range(num), n):
#         hot_idxs = set(hot_idxs)
#         xs_ = [xs[i] if i in hot_idxs else exprnode.not_(xs[i]) for i in range(num)]
#         terms.append(exprnode.and_(*xs_))
#     y = exprnode.or_(*terms)
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#
#
# def Majority(*xs, simplify=True, conj=False):
#     """
#     Return an expression that means
#     "the majority of input functions are true".
#
#     If *simplify* is ``True``, return a simplified expression.
#
#     If *conj* is ``True``, return a CNF.
#     Otherwise, return a DNF.
#     """
#     xs = [Expression.box(x).node for x in xs]
#     if conj:
#         terms = []
#         for xs_ in itertools.combinations(xs, (len(xs) + 1) // 2):
#             terms.append(exprnode.or_(*xs_))
#         y = exprnode.and_(*terms)
#     else:
#         terms = []
#         for xs_ in itertools.combinations(xs, len(xs) // 2 + 1):
#             terms.append(exprnode.and_(*xs_))
#         y = exprnode.or_(*terms)
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#
#
# def AchillesHeel(*xs, simplify=True):
#     r"""
#     Return the Achille's Heel function, defined as:
#     :math:`\prod_{i=0}^{n/2-1}{X_{2i} + X_{2i+1}}`.
#
#     If *simplify* is ``True``, return a simplified expression.
#     """
#     nargs = len(xs)
#     if nargs & 1:
#         fstr = "expected an even number of arguments, got {}"
#         raise ValueError(fstr.format(nargs))
#     xs = [Expression.box(x).node for x in xs]
#     y = exprnode.and_(*[exprnode.or_(xs[2 * i], xs[2 * i + 1]) for i in range(nargs // 2)])
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#
#
# def Mux(fs, sel, simplify=True):
#     """
#     Return an expression that multiplexes a sequence of input functions over a
#     sequence of select functions.
#     """
#     # convert Mux([a, b], x) to Mux([a, b], [x])
#     if isinstance(sel, Expression):
#         sel = [sel]
#
#     if len(sel) < clog2(len(fs)):
#         fstr = "expected at least {} select bits, got {}"
#         raise ValueError(fstr.format(clog2(len(fs)), len(sel)))
#
#     it = utils.iter_terms(sel)
#     y = exprnode.or_(*[exprnode.and_(f.node, *[lit.node for lit in next(it)]) for f in fs])
#     if simplify:
#         y = y.simplify()
#     return _expr(y)
#


# def ForAll(vs, ex):  # noqa: N802
#     """
#     Return an expression that means
#     "for all variables in *vs*, *ex* is true".
#     """
#     return And(*ex.cofactors(vs))
#
#
# def Exists(vs, ex):  # noqa: N802
#     """
#     Return an expression that means
#     "there exists a variable in *vs* such that *ex* is true".
#     """
#     return Or(*ex.cofactors(vs))
