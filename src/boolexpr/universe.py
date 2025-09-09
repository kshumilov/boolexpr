from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field, validators

from boolexpr.expression.simple import SimpleExpression
from boolexpr.io.parser import get_expr_parser
from boolexpr.io.visualization.expression import build_expression_forest, build_expression_tree
from boolexpr.variable.identifier import VariableIdentifier
from boolexpr.variable.variable import Variable

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterable, Iterator
    from typing import Any

    from rich import tree

    from boolexpr import exprnode
    from boolexpr.expression.simple import X
    from boolexpr.io.parser import SimpleExpressionParser
    from boolexpr.variable.index import VariableIndex


__all__ = [
    "Universe",
]


@define(hash=False, order=False)
class Universe:
    label_to_idx: dict[Hashable, int] = field(factory=dict)
    idx_to_data: list[Variable] = field(factory=list)

    idx_offset: int = field(
        default=1,
        validator=validators.and_(
            validators.instance_of(int),
            validators.ge(1),
        ),
    )

    def get_or_make(self, label: Hashable) -> Variable:
        idx = self.label_to_idx.get(label)
        if idx is None:
            idx = len(self.idx_to_data)
            self.idx_to_data.append(Variable.create(label, self.idx_offset + idx))
            self.label_to_idx[label] = idx
        return self.idx_to_data[idx]

    def iter_vars(self, *idxs: VariableIndex) -> Iterator[Variable]:
        yield from (self.idx_to_data[idx] for idx in idxs)

    def __getitem__(self, idx: VariableIndex) -> Variable:
        return self.idx_to_data[idx - self.idx_offset]

    def __len__(self) -> int:
        return len(self.label_to_idx)

    def get_parser(self, **kwargs: Any) -> SimpleExpressionParser:
        return get_expr_parser(self, **kwargs)

    def var(self, prefix: str, *indices: int) -> Variable:
        return self.get_or_make(VariableIdentifier(prefix, indices))

    def get_next_var(self, prefix: str = "v") -> Variable:
        return self.var(prefix, len(self))

    def node(self, prefix: str, *indices: int, polarity: bool = True) -> exprnode.ExprNode:
        return self.var(prefix, *indices).to_node(polarity=polarity)

    def get_next_node(self, prefix: str = "v", *, polarity: bool = True) -> exprnode.ExprNode:
        return self.get_next_var(prefix).to_node(polarity=polarity)

    def lit(self, prefix: str = "v", *indices: int, polarity: bool = True) -> SimpleExpression:
        return self.var(prefix, *indices).to_lit(polarity=polarity)

    def get_next_lit(self, prefix: str = "v", *, polarity: bool = True) -> SimpleExpression:
        return self.get_next_var(prefix).to_lit(polarity=polarity)

    def show(self, expression: X, **kwargs: Any) -> tree.Tree:
        return build_expression_tree(
            SimpleExpression.extract_node(expression), idx_to_label=lambda idx: str(self[idx].label), **kwargs
        )

    def show_forest(self, expressions: Iterable[tuple[X, X]], **kwargs: Any) -> tree.Tree:
        expression_nodes = (
            (SimpleExpression.extract_node(v), SimpleExpression.extract_node(e)) for v, e in expressions
        )

        return build_expression_forest(expression_nodes, idx_to_label=lambda idx: str(self[idx].label), **kwargs)

    def _assert_valid(self) -> None:
        assert self.idx_offset > 0
        assert len(self.idx_to_data) == len(self.label_to_idx)
        for label, idx in self.label_to_idx.items():
            assert idx < len(self.idx_to_data)
            var = self.idx_to_data[idx]
            assert var.idx == idx
            assert var.literals == label
            var._assert_valid()
