# logic

All content regarding calculation of logical processes is placed here.

## api_services:

### general_task_assignment_functions:
* Implementation of corresponding functions for task assignment are placed here.

### general_functions:
* Implementation of general help functions for task assignment are placed here.

### services:
* Defines all methods with directly associated with the expected service of the endpoint.

## core:

### task_assignment_init:
* Initialize the different dispatching strategies.

### class_selection:
* Implementation to get the dispatching strategy interface only for the selected strategy.

## task_assignment:

### greedy:
* Implementation of the Greedy dispatching strategy from the TaskAssignmentInterface.

### greedy_earliest_completion_time:
* Implementation of the Greedy dispatching strategy from the TaskAssignmentInterface with earliest completion time.

### pushback:
* Implementation of the PushBack dispatching strategy from the TaskAssignmentInterface.

### token passing:
* Implementation of the token passing dispatching strategy from the TaskAssignmentInterface, where amrs request self orders.

### central:
* Implementation of the Central dispatching strategy from the TaskAssignmentInterface, where each time step orders and
endpoints assigned to free AMRs.
