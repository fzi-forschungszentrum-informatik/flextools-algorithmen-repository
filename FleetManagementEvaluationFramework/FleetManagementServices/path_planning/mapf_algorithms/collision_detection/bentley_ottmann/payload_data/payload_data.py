### Reference: https://github.com/lycantropos/ground/blob/master/ground/_core/geometries.py #
from ground import hints
from reprit.base import generate_repr
from typing import Set

class Point:
    __slots__ = '_x', '_y', '_payload'

    def __init__(self, x: hints.Scalar, y: hints.Scalar, payload: Set = None ) -> None:
        self._x, self._y = x, y
        self._payload = payload

    @property
    def x(self) -> hints.Scalar:
        return self._x

    @property
    def y(self) -> hints.Scalar:
        return self._y

    @property
    def payload(self):
        return self._payload

    def __eq__(self, other: 'Point') -> bool:
        return (self.x == other.x and self.y == other.y
                if isinstance(other, Point)
                else NotImplemented)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __le__(self, other: 'Point') -> bool:
        return (self.x < other.x or self.x == other.x and self.y <= other.y
                if isinstance(other, Point)
                else NotImplemented)

    def __lt__(self, other: 'Point') -> bool:
        return (self.x < other.x or self.x == other.x and self.y < other.y
                if isinstance(other, Point)
                else NotImplemented)



    __repr__ = generate_repr(__init__)

    @payload.setter
    def payload(self, value):
        self._payload = value


class Segment:
    __slots__ = '_start', '_end', '_payload'

    def __init__(self, start: Point, end: Point, payload: Set = None ) -> None:
        self._start, self._end = start, end
        self._payload = payload
        if payload is not None:
            self._start.payload = self.payload
            self._end.payload = self.payload

    @property
    def start(self) -> Point:
        return self._start

    @property
    def end(self) -> Point:
        return self._end

    @property
    def payload(self):
        return self._payload

    def __eq__(self, other: 'Segment') -> bool:
        return (self.start == other.start and self.end == other.end
                or self.start == other.end and self.end == other.start
                if isinstance(other, Segment)
                else NotImplemented)


    __repr__ = generate_repr(__init__)

    @payload.setter
    def payload(self, value):
        self._payload = value