from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import define, field, validators

from .variable import Variable

if TYPE_CHECKING:
    from collections.abc import Hashable, Iterator

    from .index import VariableIndex

__all__ = [
    "Universe",
]


@define(hash=False, order=False)
class Universe[Label: Hashable]:
    label_to_idx: dict[Label, int] = field(factory=dict)
    idx_to_data: list[Variable[Label]] = field(factory=list)

    idx_offset: int = field(
        default=1,
        validator=validators.and_(
            validators.instance_of(int),
            validators.ge(1),
        ),
    )

    def get_or_make(self, label: Label) -> Variable[Label]:
        idx = self.label_to_idx.get(label)
        if idx is None:
            idx = len(self.idx_to_data)
            self.idx_to_data.append(Variable.create(label, self.idx_offset + idx))
            self.label_to_idx[label] = idx
        return self.idx_to_data[idx]

    def iter_vars(self, *idxs: VariableIndex) -> Iterator[Variable[Label]]:
        yield from (self.idx_to_data[idx] for idx in idxs)

    def __getitem__(self, idx: VariableIndex) -> Variable[Label]:
        return self.idx_to_data[int(idx)]

    def __len__(self) -> int:
        return len(self.label_to_idx)

    def _assert_valid(self) -> None:
        assert self.idx_offset > 0
        assert len(self.idx_to_data) == len(self.label_to_idx)
        for label, idx in self.label_to_idx.items():
            assert idx < len(self.idx_to_data)
            var = self.idx_to_data[idx]
            assert var.idx == idx
            assert var.literals == label
            var._assert_valid()
