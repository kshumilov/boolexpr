from __future__ import annotations

from typing import TYPE_CHECKING, Self

from attrs import define, field, validators

from boolexpr import exprnode
from boolexpr.expression.simple import SimpleExpression

from .index import VariableIndex

if TYPE_CHECKING:
    from collections.abc import Hashable

__all__ = [
    "Variable",
]


@define(frozen=True, order=False, hash=True)
class Variable:
    label: Hashable = field(hash=True, eq=True)
    idx: VariableIndex = field(hash=False, eq=False)

    literals: tuple[exprnode.ExprNode, exprnode.ExprNode] = field(
        validator=validators.and_(
            validators.deep_iterable(validators.instance_of(exprnode.ExprNode)),
            validators.min_len(2),
            validators.max_len(2),
        ),
        repr=False,
        hash=False,
        eq=False,
    )

    def to_node(self, *, polarity: bool = True) -> exprnode.ExprNode:
        return self.literals[polarity]

    def to_lit(self, *, polarity: bool = True) -> SimpleExpression:
        return SimpleExpression(self.literals[polarity])

    def __pos__(self) -> exprnode.ExprNode:
        return self.literals[1]

    def __neg__(self) -> exprnode.ExprNode:
        return self.literals[0]

    def __exprnode__(self) -> exprnode.ExprNode:
        return self.literals[1]

    @property
    def pos_lit(self) -> exprnode.ExprNode:
        return self.literals[1]

    @property
    def neg_lit(self) -> exprnode.ExprNode:
        return self.literals[0]

    @classmethod
    def create(cls, label: Hashable, idx: int) -> Self:
        assert idx > 0
        return cls(
            label=label,
            idx=VariableIndex(idx),
            literals=(
                exprnode.lit(-idx),
                exprnode.lit(idx),
            ),
        )

    def _assert_valid(self) -> None:
        assert self.idx > 0
        assert self.pos_lit.kind() == exprnode.VAR
        assert self.neg_lit.kind() == exprnode.COMP
        assert self.pos_lit.data() == self.idx
        assert self.neg_lit.data() == -self.idx
