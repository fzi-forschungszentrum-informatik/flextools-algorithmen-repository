# path_planning
* All content regarding path planning algorithms is placed here.

## multi_agent_path_planning:
* All content regarding multi-agent path planning algorithms is placed here.

### High-Level:
* All content regarding high-level search algorithms for the conflict tree is placed here.
  - CBS: Conflict Based Search algorithm
  - CBS with disjoint splitting: Conflict Based Search algorithm with disjoint splitting, this means also agent specific positive constraints.
  - ECBS: Suboptimal Enhanced Conflict Based Search
  - ECBS with disjoint splitting: Suboptimal Enhanced Conflict Based Search with disjoint splitting.

### Low-Level: 
* All content regarding the low-level search algorithms for plan agent paths is placed here.
  - A Star: Classical A Star algorithm with space-time constraints.
  - A Star with agent specific constraints: A Star algorithm with space-time constraints dependent of the agent for the CBS disjoint splitting variant.
  - Focal Search: Focal search algorithm for ECBS. 
  - Focal Search with agent specific constraints: Focal search algorithm for ECBS with space-time constraints dependent of the agent for the CBS disjoint splitting variant. 
  - Interval A Star: A Star with other collision data type for geometrically collisions.
  - Interval Focal Search: Focal search with other collision data type for geometrically collisions.
  - 
## prioritized_planning:
* Multi-agent prioritized path planning algorithm cooperative a star.

## single_agent_path_planning: 
+ Single agent path planning algorithm dijkstra.