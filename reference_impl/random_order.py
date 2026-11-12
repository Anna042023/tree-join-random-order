"""Small-instance reference for signed tree joins and random-order output.

Answers are explicitly materialized. This module does not implement the
completion-weighted heavy/light index analyzed in the accompanying paper.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from bisect import bisect_right
import random
import secrets
from typing import Any, Iterator


@dataclass(frozen=True)
class Atom:
    relation: str
    left: str
    right: str


class SignedTreeQuery:
    """Set-valued binary positive atoms forming a tree, and one ordered NOT edge."""

    def __init__(self, atoms: list[Atom], negative: tuple[str, str],
                 relations: dict[str, list[list[Any]]], blocked: list[list[Any]]):
        if not atoms:
            raise ValueError('positive atom tree must not be empty')
        self.atoms = tuple(atoms)
        self.negative = tuple(negative)
        self.relations = {k: set(tuple(pair) for pair in v) for k, v in relations.items()}
        self.blocked = set(tuple(pair) for pair in blocked)
        graph: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for i, a in enumerate(atoms):
            if a.left == a.right:
                raise ValueError('positive self-edge is not a tree edge')
            if a.relation not in self.relations:
                raise ValueError(f'missing relation: {a.relation}')
            graph[a.left].append((a.right, i))
            graph[a.right].append((a.left, i))
        self.variables = tuple(sorted(graph))
        if len(atoms) != len(self.variables) - 1:
            raise ValueError('positive atom occurrence graph is not a tree')
        u, v = self.negative
        if u == v or u not in graph or v not in graph:
            raise ValueError('negative endpoints must be distinct, safe tree variables')
        prev: dict[str, tuple[str | None, int | None]] = {u: (None, None)}
        bfs = deque([u])
        while bfs:
            node = bfs.popleft()
            for other, ix in graph[node]:
                if other not in prev:
                    prev[other] = (node, ix)
                    bfs.append(other)
        if len(prev) != len(self.variables):
            raise ValueError('positive occurrence graph is disconnected')
        path = [v]
        while path[-1] != u:
            path.append(prev[path[-1]][0])
        self.core_path = tuple(reversed(path))
        if not 1 <= len(self.core_path) - 1 <= 3:
            raise ValueError('negative span must be in [1,3]')
        self.graph = graph
        # This BFS ordering fixes a deterministic, reproducible rank interface.
        self.order = tuple(prev.keys())
        self.parent = prev
        self._indices: dict[tuple[int, str], dict[Any, tuple[Any, ...]]] = {}
        for i, a in enumerate(atoms):
            xy, yx = defaultdict(set), defaultdict(set)
            for x, y in self.relations[a.relation]:
                xy[x].add(y)
                yx[y].add(x)
            self._indices[i, a.left] = {x: tuple(sorted(v, key=repr)) for x, v in xy.items()}
            self._indices[i, a.right] = {y: tuple(sorted(v, key=repr)) for y, v in yx.items()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SignedTreeQuery':
        return cls([Atom(*x) for x in data['atoms']], tuple(data['negative']),
                   data['relations'], data.get('blocked', []))

    def answers(self, max_answers: int = 100000) -> list[tuple[Any, ...]]:
        """Materialize exact answers up to an explicit safety cap."""
        if max_answers < 0:
            raise ValueError('max_answers must be nonnegative')
        bindings: dict[str, Any] = {}
        found: list[tuple[Any, ...]] = []
        order = self.order
        def recurse(t: int) -> None:
            if t == len(order):
                u, v = self.negative
                if (bindings[u], bindings[v]) not in self.blocked:
                    if len(found) >= max_answers:
                        raise OverflowError('reference materialization cap exceeded')
                    found.append(tuple(bindings[k] for k in self.variables))
                return
            node = order[t]
            parent, ix = self.parent[node]
            if parent is None:
                values: set[Any] = set()
                for other, i in self.graph[node]:
                    values.update(self._indices[i, node])
                choices = sorted(values, key=repr)
            else:
                choices = self._indices[ix, parent].get(bindings[parent], ())
            for value in choices:
                bindings[node] = value
                recurse(t + 1)
            bindings.pop(node, None)
        recurse(0)
        return sorted(set(found), key=lambda row: tuple(map(repr, row)))


class ExactAnswerGroups:
    """Disjoint core groups with exact weights; full answers stored in memory."""
    def __init__(self, query: SignedTreeQuery, max_answers: int = 100000):
        answers = query.answers(max_answers)
        idx = {v: i for i, v in enumerate(query.variables)}
        grouped: dict[tuple[Any, ...], list[tuple[Any, ...]]] = defaultdict(list)
        for row in answers:
            grouped[tuple(row[idx[v]] for v in query.core_path)].append(row)
        self.keys = sorted(grouped, key=lambda g: tuple(map(repr, g)))
        self.groups = tuple(tuple(grouped[g]) for g in self.keys)
        self.prefix = []
        acc = 0
        for group in self.groups:
            acc += len(group)
            self.prefix.append(acc)
        self.total = acc

    def access(self, rank: int) -> tuple[Any, ...]:
        if not 0 <= rank < self.total:
            raise IndexError('rank outside [0,total)')
        g = bisect_right(self.prefix, rank)
        return self.groups[g][rank - (self.prefix[g-1] if g else 0)]


class SparsePermutation:
    """Sparse Fisher--Yates on implicit integer interval [0,n)."""
    def __init__(self, size: int, seed: int | None = None):
        if size < 0:
            raise ValueError('negative size')
        self.remaining = size
        self._swap: dict[int, int] = {}
        self._random = secrets.SystemRandom() if seed is None else random.Random(seed)

    def next_rank(self) -> int:
        if not self.remaining:
            raise StopIteration
        j = self._random.randrange(self.remaining)
        rank = self._swap.get(j, j)
        last = self.remaining - 1
        replacement = self._swap.get(last, last)
        if j != last:
            self._swap[j] = replacement
        else:
            self._swap.pop(j, None)
        self._swap.pop(last, None)
        self.remaining -= 1
        return rank

    def __iter__(self) -> Iterator[int]:
        while self.remaining:
            yield self.next_rank()


def random_answers(groups: ExactAnswerGroups, seed: int | None = None) -> Iterator[tuple[Any, ...]]:
    for rank in SparsePermutation(groups.total, seed):
        yield groups.access(rank)
