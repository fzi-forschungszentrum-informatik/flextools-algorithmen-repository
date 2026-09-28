import typing as _t

from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_context import Relation
from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_context import Context as _Context
from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_context import get_context as _get_context

from mapf_algorithms.collision_detection.bentley_ottmann.payload_data.payload_data import Segment as _Segment

from mapf_algorithms.collision_detection.bentley_ottmann.core.base import sweep as _sweep


class BoDetector:

    def graph_get_collision(self, segments: _t.Sequence[_Segment],
                       *,
                       context: _t.Optional[_Context] = None) -> tuple[int, int] | None :
        for event in _sweep(segments, context=context or _get_context()):
            relations = event.get_relations()
            if not relations:
                continue
            if Relation.TOUCH in relations or Relation.CROSS in relations:
                if len(event.end.payload) >= 2:
                    l = list(event.end.payload)
                    if event.end.__eq__(event.original_end):
                        return l[0], l[1]
                    else:
                        return l[0], l[1]
                else:
                    return None

            else:
                if len(event.start.payload) >= 2:
                    l = list(event.start.payload)
                    return l[0], l[1]
                else:
                    if len(event.end.payload) >= 2:
                        l = list(event.end.payload)
                        return l[0], l[1]
                    else:
                        #print("->", event.start, event.end) TODO check those cases
                        return None

        return None

    def graph_get_collisions(self, segments: _t.Sequence[_Segment], *,
                             context: _t.Optional[_Context] = None) -> _t.Iterator[tuple[int, int]]:
        for event in _sweep(segments, context=context or _get_context()):
            relations = event.get_relations()
            if not relations:
                continue
            if len(event.end.payload) >= 2:
                yield event.end.payload
            elif len(event.start.payload) >= 2:
                yield event.end.payload
            elif len(event.original_start.payload.union(event.original_end.payload)) >= 2:
                yield event.original_start.payload.union(event.original_end.payload)
            else:
                # Could log or handle this case if needed
                continue