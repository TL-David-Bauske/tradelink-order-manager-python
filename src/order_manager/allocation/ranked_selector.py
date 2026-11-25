from collections.abc import Callable, Iterable
from typing import Protocol, Self


class SupportsLessThan(Protocol):
    def __lt__(self, other: Self, /) -> bool: ...


class RankedSelector[T, K: SupportsLessThan]:
    def __init__(self, rank: Callable[[T], K], qualifies: Callable[[T], bool]) -> None:
        self.rank = rank
        self.qualifies = qualifies

    def select(self, candidates: Iterable[T]) -> T | None:
        for candidate in sorted(candidates, key=self.rank):
            if self.qualifies(candidate):
                return candidate
        return None
