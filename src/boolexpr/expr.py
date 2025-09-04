"""
Copyright (c) 2012, Chris Drake
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The :mod:`pyeda.boolalg.expr` module implements
Boolean functions represented as expressions.

Data Types:

abstract syntax tree
   A nested tuple of entries that represents an expression.
   It is defined recursively::

      ast := ('const', bool)
           | ('lit', uniqid)
           | (nary, ast, ...)
           | ('not', ast)
           | ('impl', ast, ast)
           | ('ite', ast, ast, ast)

      bool := 0 | 1

      uniqid := nonzero int

      nary := 'or'
            | 'and'
            | 'xor'
            | 'eq'

Interface Functions:

* :func:`exprvar` --- Return a unique Expression variable
* :func:`expr` --- Convert an arbitrary object into an Expression
* :func:`ast2expr` --- Convert an abstract syntax tree to an Expression
* :func:`expr2dimacscnf` --- Convert an expression into an equivalent DIMACS CNF
* :func:`upoint2exprpoint` --- Convert an untyped point into an Expression point

* :func:`Not` --- Expression negation operator
* :func:`Or` --- Expression disjunction (sum, OR) operator
* :func:`And` --- Expression conjunction (product, AND) operator

* :func:`Xor` --- Expression exclusive or (XOR) operator
* :func:`Equal` --- Expression equality operator
* :func:`Implies` --- Expression implication operator
* :func:`ITE` --- Expression If-Then-Else (ITE) operator

* :func:`Nor` --- Expression NOR (not OR) operator
* :func:`Nand` --- Expression NAND (not AND) operator
* :func:`Xnor` --- Expression XNOR (not XOR) operator
* :func:`Unequal` --- Expression inequality (not EQUAL) operator

* :func:`OneHot0`
* :func:`OneHot`
* :func:`NHot`
* :func:`Majority`
* :func:`AchillesHeel`
* :func:`Mux`

Interface Classes:

* :class:`Expression`

  * :class:`Atom`

    * :class:`Constant`

      * Zero
      * One

    * :class:`Literal`

      * :class:`Complement`
      * :class:`Variable`

  * :class:`Operator`

    * :class:`NaryOp`

      * :class:`OrOp`
      * :class:`AndOp`
      * :class:`XorOp`
      * :class:`EqualOp`

    * :class:`NotOp`
    * :class:`ImpliesOp`
    * :class:`IfThenElseOp`

* :class:`NormalForm`

  * :class:`DisjNormalForm`
  * :class:`ConjNormalForm`

    * :class:`DimacsCNF`
"""


# Disable 'no-member' error, b/c pylint can't look into C extensions
# foo bar pylint: disable=E1101

from collections.abc import Callable, Set
from functools import cached_property
from typing import Any, Self

from boolexpr import exprnode
from boolexpr.boolfunc import utils
from boolexpr.boolfunc.function import Function
from boolexpr.boolfunc.utils import Point
from boolexpr.variable import Indices, Names
from boolexpr.variable import Variable as _Variable

from .math import bit_on
from .parsing.boolexpr import parse

# existing Literal references
_LITS = {}

# satisfy_one literal assumptions
_ASSUMPTIONS = set()


def _assume2point() -> Point:
    """Convert global assumptions to a point."""
    point: Point = {}
    for lit in _ASSUMPTIONS:
        if isinstance(lit, Complement):
            point[~lit] = 0
        elif isinstance(lit, Variable):
            point[lit] = 1
    return point


def exprvar(name: Names, index: Indices | None = None) -> "Variable":
    r"""Return a unique Expression variable.

    A Boolean *variable* is an abstract numerical quantity that may assume any
    value in the set :math:`B = \{0, 1\}`.
    The ``exprvar`` function returns a unique Boolean variable instance
    represented by a logic expression.
    Variable instances may be used to symbolically construct larger expressions.

    A variable is defined by one or more *names*,
    and zero or more *indices*.
    Multiple names establish hierarchical namespaces,
    and multiple indices group several related variables.
    If the ``name`` parameter is a single ``str``,
    it will be converted to ``(name, )``.
    The ``index`` parameter is optional;
    when empty, it will be converted to an empty tuple ``()``.
    If the ``index`` parameter is a single ``int``,
    it will be converted to ``(index, )``.

    Given identical names and indices, the ``exprvar`` function will always
    return the same variable:

    >>> exprvar('a', 0) is exprvar('a', 0)
    True

    To create several single-letter variables:

    >>> a, b, c, d = map(exprvar, 'abcd')

    To create variables with multiple names (inner-most first):

    >>> fifo_push = exprvar(('push', 'fifo'))
    >>> fifo_pop = exprvar(('pop', 'fifo'))

    .. seealso::
       For creating arrays of variables with incremental indices,
       use the :func:`pyeda.boolalg.bfarray.exprvars` function.
    """
    bvar = _Variable.create(name, index)
    try:
        var = _LITS[bvar.uniqid]
    except KeyError:
        var = _LITS[bvar.uniqid] = Variable(bvar)
    return var


def _exprcomp(node: exprnode.ExprNode) -> "Expression":
    """Return a unique Expression complement."""
    try:
        comp = _LITS[node.data()]
    except KeyError:
        comp = _LITS[node.data()] = Complement(node)
    return comp


_KIND2EXPR: dict[int, Callable[[exprnode.ExprNode], "Expression"]] = {
    exprnode.ZERO: lambda _: Zero,
    exprnode.ONE: lambda _: One,
    exprnode.COMP: lambda node: _exprcomp(node),
    exprnode.VAR: lambda node: _LITS[node.data()],
    exprnode.OP_OR: lambda node: OrOp(node),
    exprnode.OP_AND: lambda node: AndOp(node),
    exprnode.OP_XOR: lambda node: XorOp(node),
    exprnode.OP_EQ: lambda node: EqualOp(node),
    exprnode.OP_NOT: lambda node: NotOp(node),
    exprnode.OP_IMPL: lambda node: ImpliesOp(node),
    exprnode.OP_ITE: lambda node: IfThenElseOp(node),
}


def _expr(node: exprnode.ExprNode) -> "Expression":
    """Expression constructor that returns unique atomic nodes."""
    return _KIND2EXPR[node.kind()](node)


def expr(obj: Any, *, simplify: bool = True) -> "Expression":
    """Convert an arbitrary object into an Expression."""
    if isinstance(obj, Expression):
        return obj
    # False, True, 0, 1
    if isinstance(obj, int) and obj in {0, 1}:
        return _CONSTS[obj]
    if isinstance(obj, str):
        ast = parse(obj)
        ex = ast2expr(ast)
        if simplify:
            ex = ex.simplify()
        return ex
    return One if bool(obj) else Zero


def ast2expr(ast):
    """Convert an abstract syntax tree to an Expression."""
    if ast[0] == "const":
        return _CONSTS[ast[1]]
    if ast[0] == "var":
        return exprvar(ast[1], ast[2])
    xs = [ast2expr(x) for x in ast[1:]]
    return ASTOPS[ast[0]](*xs, simplify=False)


def expr2dimacscnf(ex):
    """Convert an expression into an equivalent DIMACS CNF."""
    litmap, nvars, clauses = ex.encode_cnf()
    return litmap, DimacsCNF(nvars, clauses)


def expr2dimacssat(ex):
    """Convert an expression into an equivalent DIMACS SAT string."""
    if not ex.simple:
        raise ValueError("expected ex to be simplified")

    litmap, nvars = ex.encode_inputs()

    formula = _expr2sat(ex, litmap)
    if "xor" in formula:
        if "=" in formula:
            fmt = "satex"
        else:
            fmt = "satx"
    elif "=" in formula:
        fmt = "sate"
    else:
        fmt = "sat"

    return f"p {fmt} {nvars}\n{formula}"


def _expr2sat(ex, litmap):  # pragma: no cover
    """Convert an expression to a DIMACS SAT string."""
    if isinstance(ex, Literal):
        return str(litmap[ex])
    if isinstance(ex, NotOp):
        return "-(" + _expr2sat(ex.x, litmap) + ")"
    if isinstance(ex, OrOp):
        return "+(" + " ".join(_expr2sat(x, litmap) for x in ex.xs) + ")"
    if isinstance(ex, AndOp):
        return "*(" + " ".join(_expr2sat(x, litmap) for x in ex.xs) + ")"
    if isinstance(ex, XorOp):
        return "xor(" + " ".join(_expr2sat(x, litmap) for x in ex.xs) + ")"
    if isinstance(ex, EqualOp):
        return "=(" + " ".join(_expr2sat(x, litmap) for x in ex.xs) + ")"
    fstr = "expected ex to be a Literal or Not/Or/And/Xor/Equal op, got {0.__name__}"
    raise ValueError(fstr.format(type(ex)))


def upoint2exprpoint(upoint):
    """Convert an untyped point into an Expression point.

    .. seealso::
       For definitions of points and untyped points,
       see the :mod:`pyeda.boolalg.boolfunc` module.
    """
    point = {}
    for uniqid in upoint[0]:
        point[_LITS[uniqid]] = 0
    for uniqid in upoint[1]:
        point[_LITS[uniqid]] = 1
    return point


# primitive functions


class _Clause:
    """Helper interface for operators in *clause* form."""

    def _lits(self):
        """Return the clause as a frozenset of literals."""
        raise NotImplementedError

    def _encode_clause(self, litmap):
        """Encode a clause as a frozenset of ints."""
        raise NotImplementedError


class _DNF:
    """Helper interface for operators in disjunctive normal form."""

    def _encode_dnf(self):
        """Encode DNF as a set of frozenset of ints."""
        raise NotImplementedError

    @cached_property
    def _cover(self):
        """Return the DNF as a set of frozenset of literals."""
        raise NotImplementedError


class _CNF:
    """Helper interface for operators in conjunctive normal form."""

    def _encode_cnf(self):
        """Encode CNF as a set of frozenset of ints."""
        raise NotImplementedError


class Expression(Function):
    """Boolean function represented by a logical expression

    .. seealso::
       This is a subclass of :class:`pyeda.boolalg.boolfunc.Function`

    The ``Expression`` class is useful for type checking,
    e.g. ``isinstance(f, Expression)``.

    Do **NOT** create an Expression using the ``Expression`` constructor.
    """

    ASTOP = NotImplemented
    node: exprnode.ExprNode

    def __init__(self, node: exprnode.ExprNode) -> None:
        self.node = node

    def __repr__(self) -> str:
        return str(self)

    # Context manager
    def __enter__(self) -> None:
        raise ValueError("expected assumption to be a literal")

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        raise ValueError("expected assumption to be a literal")

    # Operators
    def __invert__(self):
        return _expr(exprnode.not_(self.node))

    def __or__(self, other):
        other_node = self.box(other).node
        return _expr(exprnode.or_(self.node, other_node))

    def __and__(self, other):
        other_node = self.box(other).node
        return _expr(exprnode.and_(self.node, other_node))

    def __xor__(self, other):
        other_node = self.box(other).node
        return _expr(exprnode.xor(self.node, other_node))

    def eq(self, other):
        """Boolean equal operator."""
        other_node = self.box(other).node
        return _expr(exprnode.eq(self.node, other_node))

    def __rshift__(self, other):
        other_node = self.box(other).node
        return _expr(exprnode.impl(self.node, other_node))

    def __rrshift__(self, other):
        other_node = self.box(other).node
        return _expr(exprnode.impl(other_node, self.node))

    # From Function
    @cached_property
    def support(self) -> Set["Variable"]:
        s = set()
        for ex in self.iter_dfs():
            if isinstance(ex, Complement):
                s.add(~ex)
            elif isinstance(ex, Variable):
                s.add(ex)

        return frozenset(s)

    @cached_property
    def inputs(self) -> tuple["Variable", ...]:
        return tuple(sorted(self.support, key=lambda ex: ex.node.data()))

    def restrict(self, point: Point) -> Self:
        d = {}
        for key, val in point.items():
            if not isinstance(key, Variable):
                raise TypeError("expected point keys to be variables")
            val = _expr(self.box(val).node)
            if not isinstance(val, Constant):
                raise TypeError("expected point values to be constants")
            d[key.node] = val.node
        return _expr(self.node.restrict(d))

    def compose(self, mapping):
        d = {}
        for key, val in mapping.items():
            if not isinstance(key, Variable):
                raise TypeError("expected mapping keys to be variables")
            d[key.node] = self.box(val).node
        return _expr(self.node.compose(d))

    def is_zero(self):
        return False

    def is_one(self):
        return False

    @staticmethod
    def box(obj):
        if isinstance(obj, Expression):
            return obj
        # False, True, 0, 1
        if isinstance(obj, int) and obj in {0, 1}:
            return _CONSTS[obj]
        if isinstance(obj, str):
            ast = parse(obj)
            return ast2expr(ast)
        return One if bool(obj) else Zero

    # Specific to Expression

    ### Start C API ###
    def to_ast(self):
        """Convert this node to an abstract syntax tree."""
        return self.node.to_ast()

    def iter_dfs(self):
        """Iterate through all expression nodes in DFS order."""
        for node in self.node:
            yield _expr(node)

    @cached_property
    def depth(self) -> int:
        """Return the depth of the expression.

        Expression depth is defined recursively:

        1. An atom node (constant or literal) has zero depth.
        2. A branch node (operator) has depth equal to the maximum depth of
           its children (arguments) plus one.
        """
        return self.node.depth()

    @cached_property
    def size(self) -> int:
        """Return the size of the expression.

        1. An atom node (constant or literal) has size one.
        2. A branch node (operator) has size equal to the sum of its children's
           sizes plus one.
        """
        return self.node.size()

    def is_dnf(self) -> bool:
        """Return True if the expression is in disjunctive normal form."""
        return self.node.is_dnf()

    def is_cnf(self) -> bool:
        """Return True if the expression is in conjunctive normal form."""
        return self.node.is_cnf()

    def pushdown_not(self) -> Self:
        """Return an expression with NOT operators pushed down thru dual ops.

        Specifically, perform the following transformations:
            ~(a | b | c ...) <=> ~a & ~b & ~c ...
            ~(a & b & c ...) <=> ~a | ~b | ~c ...
            ~(s ? d1 : d0) <=> s ? ~d1 : ~d0
        """
        node = self.node.pushdown_not()
        if node is self.node:
            return self
        return _expr(node)

    def simplify(self) -> Self:
        """Return a simplified expression."""
        node = self.node.simplify()
        if node is self.node:
            return self
        return _expr(node)

    @property
    def simple(self) -> bool:
        """Return True if the expression has been simplified."""
        return self.node.simple()

    def to_binary(self) -> Self:
        """Convert N-ary operators to binary operators."""
        node = self.node.to_binary()
        if node is self.node:
            return self
        return _expr(node)

    def to_nnf(self) -> Self:
        """Return an equivalent expression is negation normal form."""
        node = self.node.to_nnf()
        if node is self.node:
            return self
        return _expr(node)

    def to_dnf(self) -> Self:
        """Return an equivalent expression in disjunctive normal form."""
        node = self.node.to_dnf()
        if node is self.node:
            return self
        return _expr(node)

    def to_cnf(self) -> Self:
        """Return an equivalent expression in conjunctive normal form."""
        node = self.node.to_cnf()
        if node is self.node:
            return self
        return _expr(node)

    def complete_sum(self) -> Self:
        """
        Return an equivalent DNF expression that includes all prime
        implicants.
        """
        node = self.node.complete_sum()
        if node is self.node:
            return self
        return _expr(node)

    ### End C API ###

    def expand(self, *variables: "Variable", conj: bool = False):
        """Return the Shannon expansion with respect to a list of variables."""
        outer, inner = (And, Or) if conj else (Or, And)
        terms = [inner(self.restrict(p), *utils.point2term(p, conj=conj)) for p in utils.iter_points(variables)]
        if conj:
            terms = [term for term in terms if term is not One]
        else:
            terms = [term for term in terms if term is not Zero]
        return outer(*terms, simplify=False)

    @property
    def cover(self):
        """Return the DNF expression as a cover of cubes."""
        if self.is_dnf():
            return self._cover
        raise ValueError("expected a DNF expression")

    def encode_inputs(self):
        """Return a compact encoding for input variables."""
        litmap = {}
        nvars = 0
        for i, v in enumerate(self.inputs, start=1):
            litmap[v] = i
            litmap[~v] = -i
            litmap[i] = v
            litmap[-i] = ~v
            nvars += 1
        return litmap, nvars

    def encode_dnf(self):
        """Encode as a compact DNF."""
        if self.is_dnf():
            return self._encode_dnf()
        raise ValueError("expected a DNF expression")

    def encode_cnf(self):
        """Encode as a compact CNF."""
        if self.is_cnf():
            return self._encode_cnf()
        raise ValueError("expected a CNF expression")

    def tseitin(self, auxvarname="aux"):
        """Convert the expression to Tseitin's encoding."""
        if self.is_cnf():
            return self

        _, constraints = _tseitin(self.to_nnf(), auxvarname)
        fst = constraints[-1][1]
        rst = [Equal(v, ex).to_cnf() for v, ex in constraints[:-1]]
        return And(fst, *rst)


class Atom(Expression):
    """Atom Expression"""


class Constant(Atom):
    """Constant Expression"""

    VALUE = NotImplemented


class _Zero(Constant, _DNF):
    """Constant Zero"""

    VALUE = False

    def __bool__(self):
        return self.VALUE

    def __int__(self):
        return int(self.VALUE)

    def __str__(self):
        return str(self.__int__())

    def is_zero(self):
        return True

    # _DNF
    def _encode_dnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = set()
        return litmap, nvars, clauses

    @cached_property
    def _cover(self):
        return set()


class _One(Constant, _CNF):
    """Constant One"""

    VALUE = True

    def __bool__(self):
        return self.VALUE

    def __int__(self):
        return int(self.VALUE)

    def __str__(self):
        return str(self.__int__())

    def is_one(self):
        return True

    # _CNF
    def _encode_cnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = set()
        return litmap, nvars, clauses


# Constants are singletons
Zero = _Zero(exprnode.Zero)
One = _One(exprnode.One)

_CONSTS = [Zero, One]


class Literal(Atom, _Clause, _DNF, _CNF):
    """Literal Expression"""

    ASTOP = "lit"

    def __enter__(self):
        _ASSUMPTIONS.add(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        _ASSUMPTIONS.discard(self)

    # _Clause
    @cached_property
    def _lits(self):
        return frozenset([self])

    def _encode_clause(self, litmap):
        return frozenset([litmap[self]])

    # _DNF
    def _encode_dnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {self._encode_clause(litmap)}
        return litmap, nvars, clauses

    @cached_property
    def _cover(self):
        return {self._lits}

    # _CNF
    def _encode_cnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {self._encode_clause(litmap)}
        return litmap, nvars, clauses


class Complement(Literal):
    """Complement Expression"""

    def __str__(self):
        return f"~{self.__invert__()}"

    @cached_property
    def uniqid(self):
        """Return a unique integer for this complement.

        The value is the negation of the complement's variable.
        For example, if the uniqid of x1 = 1, then the uniqid of ~x1 = -1.
        """
        return self.node.data()


class Variable(_Variable, Literal):
    """Variable Expression"""

    def __init__(self, bvar):
        _Variable.__init__(self, bvar.names, bvar.indices)
        Literal.__init__(self, exprnode.lit(bvar.uniqid))


class Operator(Expression):
    """Operator Expression"""

    NAME = NotImplemented

    def __str__(self):
        args = ", ".join(str(x) for x in self.xs)
        return f"{self.NAME}({args})"

    @cached_property
    def xs(self):
        """Return a tuple of this operator's arguments."""
        return tuple(_expr(node) for node in self.node.data())


class NaryOp(Operator):
    """Operator with N arguments"""


class OrAndOp(NaryOp, _Clause, _DNF, _CNF):
    """Either an OR or AND operator (a lattice op)"""

    # _Clause
    @cached_property
    def _lits(self):
        return frozenset(self.xs)

    def _encode_clause(self, litmap):
        return frozenset(litmap[x] for x in self.xs)


class OrOp(OrAndOp):
    """OR Operator"""

    ASTOP = "or"
    NAME = "Or"

    # _DNF
    def _encode_dnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {x._encode_clause(litmap) for x in self.xs}
        return litmap, nvars, clauses

    @cached_property
    def _cover(self):
        return {x._lits for x in self.xs}

    # _CNF
    def _encode_cnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {self._encode_clause(litmap)}
        return litmap, nvars, clauses


class AndOp(OrAndOp):
    """AND Operator"""

    ASTOP = "and"
    NAME = "And"

    def __enter__(self):
        for x in self.xs:
            if isinstance(x, Literal):
                _ASSUMPTIONS.add(x)
            else:
                raise ValueError("expected assumption to be a literal")

    def __exit__(self, exc_type, exc_val, traceback):
        for x in self.xs:
            if isinstance(x, Literal):
                _ASSUMPTIONS.discard(x)
            else:
                raise ValueError("expected assumption to be a literal")

    # _DNF
    def _encode_dnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {self._encode_clause(litmap)}
        return litmap, nvars, clauses

    @cached_property
    def _cover(self):
        return {self._lits}

    # _CNF
    def _encode_cnf(self):
        litmap, nvars = self.encode_inputs()
        clauses = {x._encode_clause(litmap) for x in self.xs}
        return litmap, nvars, clauses


class XorOp(NaryOp):
    """XOR Operator"""

    ASTOP = "xor"
    NAME = "Xor"


class EqualOp(NaryOp):
    """Equal Operator"""

    ASTOP = "eq"
    NAME = "Equal"


class NotOp(Operator):
    """NOT Operator"""

    ASTOP = "not"
    NAME = "Not"

    @cached_property
    def x(self):
        """For Not(x), return x."""
        return self.xs[0]


class ImpliesOp(Operator):
    """Implies Operator"""

    ASTOP = "impl"
    NAME = "Implies"

    @cached_property
    def p(self):
        """For Implies(p, q), return p."""
        return self.xs[0]

    @cached_property
    def q(self):
        """For Implies(p, q), return q."""
        return self.xs[1]


class IfThenElseOp(Operator):
    """If-Then-Else (ITE) Operator"""

    ASTOP = "ite"
    NAME = "ITE"

    @cached_property
    def s(self):
        """For ITE(s, d1, d0), return s."""
        return self.xs[0]

    @cached_property
    def d1(self):
        """For ITE(s, d1, d0), return d1."""
        return self.xs[1]

    @cached_property
    def d0(self):
        """For ITE(s, d1, d0), return d0."""
        return self.xs[2]


class NormalForm:
    """Normal form expression"""

    def __init__(self, nvars, clauses):
        self.nvars = nvars
        self.clauses = clauses

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "\n".join(" ".join(str(idx) for idx in clause) + " 0" for clause in self.clauses)

    @cached_property
    def nclauses(self):
        """Return the count of clauses in the CNF."""
        return len(self.clauses)

    def invert(self):
        """Return the inverse normal form expression."""
        raise NotImplementedError

    def reduce(self):
        """Reduce to a canonical form."""
        support = frozenset(range(1, self.nvars + 1))
        new_clauses = set()
        for clause in self.clauses:
            vs = list(support - {abs(uniqid) for uniqid in clause})
            if vs:
                for num in range(1 << len(vs)):
                    new_part = {v if bit_on(num, i) else ~v for i, v in enumerate(vs)}
                    new_clauses.add(clause | new_part)
            else:
                new_clauses.add(clause)
        return self.__class__(self.nvars, new_clauses)


class DisjNormalForm(NormalForm):
    """Disjunctive normal form expression"""

    def decode(self, litmap):
        """Convert the DNF to an expression."""
        return Or(*[And(*[litmap[idx] for idx in clause]) for clause in self.clauses])

    def invert(self):
        clauses = {frozenset(-idx for idx in clause) for clause in self.clauses}
        return ConjNormalForm(self.nvars, clauses)


class ConjNormalForm(NormalForm):
    """Conjunctive normal form expression"""

    def decode(self, litmap):
        """Convert the CNF to an expression."""
        return And(*[Or(*[litmap[idx] for idx in clause]) for clause in self.clauses])

    def invert(self):
        clauses = {frozenset(-idx for idx in clause) for clause in self.clauses}
        return DisjNormalForm(self.nvars, clauses)

    @staticmethod
    def soln2point(soln, litmap):
        """Convert a solution vector to a point."""
        return {litmap[i]: int(val > 0) for i, val in enumerate(soln, start=1)}


class DimacsCNF(ConjNormalForm):
    """Wrapper class for a DIMACS CNF representation"""

    def __str__(self):
        formula = super().__str__()
        return f"p cnf {self.nvars} {self.nclauses}\n{formula}"


def _tseitin(ex, auxvarname, auxvars=None):
    """Convert a factored expression to a literal, and a list of constraints."""
    if isinstance(ex, Literal):
        return ex, []
    if auxvars is None:
        auxvars = []

    lits = []
    constraints = []
    for x in ex.xs:
        lit, subcons = _tseitin(x, auxvarname, auxvars)
        lits.append(lit)
        constraints.extend(subcons)

    auxvarindex = len(auxvars)
    auxvar = exprvar(auxvarname, auxvarindex)
    auxvars.append(auxvar)

    f = ASTOPS[ex.ASTOP](*lits)
    constraints.append((auxvar, f))
    return auxvar, constraints


ASTOPS = {
    "not": Not,
    "or": Or,
    "and": And,
    "xor": Xor,
    "equal": Equal,
    "implies": Implies,
    "ite": ITE,
    "nor": Nor,
    "nand": Nand,
    "xnor": Xnor,
    "unequal": Unequal,
    "onehot0": OneHot0,
    "onehot": OneHot,
    "majority": Majority,
    "achillesheel": AchillesHeel,
}
