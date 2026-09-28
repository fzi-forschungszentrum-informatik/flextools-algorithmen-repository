This algorithm, mainly a product of lycantropos:
https://github.com/lycantropos/bentley_ottmann.

I added payload-logic to the context and algorithm to reflect our use case



Types of relation used by the algorithm: 
DISJOINT = 0
#: intersection is a strict subset of each of the geometries,
#: has dimension less than at least of one of the geometries
#: and if we traverse boundary of each of the geometries in any direction
#: then boundary of the other geometry won't be on one of sides
#: at each point of boundaries intersection
TOUCH = 1
#: intersection is a strict subset of each of the geometries,
#: has dimension less than at least of one of the geometries
#: and if we traverse boundary of each of the geometries in any direction
#: then boundary of the other geometry will be on both sides
#: at some point of boundaries intersection
CROSS = 2
#: intersection is a strict subset of each of the geometries
#: and has the same dimension as geometries
OVERLAP = 3
#: interior of the geometry is a superset of the other
COVER = 4
#: boundary of the geometry contains
#: at least one boundary point of the other, but not all,
#: interior of the geometry contains other points of the other
ENCLOSES = 5
#: geometry is a strict superset of the other
#: and interior/boundary of the geometry is a superset
#: of interior/boundary of the other
COMPOSITE = 6
#: geometries are equal
EQUAL = 7
#: geometry is a strict subset of the other
#: and interior/boundary of the geometry is a subset
#: of interior/boundary of the other
COMPONENT = 8
#: at least one boundary point of the geometry
#: lies on the boundary of the other, but not all,
#: other points of the geometry lie in the interior of the other
ENCLOSED = 9
#: geometry is a subset of the interior of the other
WITHIN = 10