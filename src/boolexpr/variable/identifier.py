from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from attrs import define, field, validators

if TYPE_CHECKING:
    from typing import Any, Self, SupportsInt

__all__ = [
    "VariableIdentifier",
    "Names",
    "Indices",
]

type Names = tuple[str, ...]
type Indices = tuple[int, ...]


def standardize_name[T: Any](raw_name: T | Sequence[T]) -> Names:
    match raw_name:
        case (*names,):
            return tuple(map(str, names))
        case _:
            return (str(raw_name),)


def standardize_indices[T: SupportsInt](indices: T | Sequence[T]) -> tuple[int, ...]:
    if isinstance(indices, Sequence) and not isinstance(indices, str | bytes | bytearray):
        return tuple(int(i) for i in indices)
    return (int(indices),)


@define(frozen=True, order=False, hash=True)
class VariableIdentifier:
    names: tuple[str, ...] = field(
        converter=standardize_name,
        validator=validators.and_(
            validators.deep_iterable(validators.instance_of(str)),
            validators.min_len(1),
        ),
    )

    indices: tuple[int, ...] = field(
        factory=tuple,
        converter=standardize_indices,
        validator=validators.deep_iterable(
            validators.and_(
                validators.instance_of(int),
                validators.ge(0),
            ),
        ),
    )

    def __str__(self) -> str:
        if self.indices:
            suffix = ",".join(str(idx) for idx in self.indices)
            return f"{self.qual_name}[{suffix}]"
        return self.qual_name

    def __lt__(self, other: Self) -> bool:
        if self.names == other.names:
            return self.indices < other.indices
        return self.names < other.names

    @property
    def inner_name(self) -> str:
        """Return the innermost variable name."""
        return self.names[0]

    @property
    def qual_name(self) -> str:
        """Return the fully qualified name."""
        return ".".join(reversed(self.names))
