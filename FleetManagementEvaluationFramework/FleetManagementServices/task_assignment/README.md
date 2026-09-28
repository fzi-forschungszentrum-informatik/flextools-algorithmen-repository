# Task Assignment

Microservice to assign orders to AMRs and compute task assignment.

## 1. Deployment:

### a.) Deployment microservice for the fleet management system using python
To deploy the task assignment service locally, run
```
pip install -r requirements.txt
```
to install all dependencies. then, run ``main.py``

To test the endpoints open your browser at: http://localhost:3000/docs

### b.) Deployment microservice for the fleet management system using docker
1. Open a new wsl terminal
2. To deploy the task assignment service via docker, build the docker image using the Dockerfile by executing
```
docker build -t taskassignment .
```
3. Then, run a container from created image with the IMAGE_ID by executing
```
docker run -p 3003:3003 -t IMAGE_ID 
```
To test the endpoints open your browser at: http://localhost:3000/docs

## 2. Project structure

- api: All content regarding the restful api is placed here.
- config: All content regarding config parameter of the microservice is placed here.
- data: All content regarding the data models is placed here.
- interfaces: All content regarding the task assignment interface is placed here.
- log_config: All content regarding the logging is placed here.
- logic: All content regarding task assignment is placed here.
  - api_services: All content regarding service methods to process the incoming api calls.
  - core: All content regarding the initialization of the task assignment service is placed here.
  - task assignment: All methods of task assignment is placed here.
- tests: All content regarding testing is placed here.
- main.py: File to start the microservice. 

## 3. Configuration Parameter Task Assignment:
In the ./config/config_file.py file you can set some configuration parameter:
- PORT: 3000 (default)
- HOST: '0.0.0.0' (default)


- TASK_ASSIGNMENT_STRATEGY: TaskAssignmentStrategy enum to select the used task assignment strategy (see next point (4)).
- USE_IMPROVEMENT: Only relevant for greedy task assignment strategy to find improvement with the 2-opt approach.
- MAX_IMPROVEMENT_TIME: Only relevant for greedy task assignment strategy. Maximal time to find improvement.
- BUFFER_TIME_PRO_ORDER: time delta between new planned orders, only considered in greedy and push-back task assignment.
- Logging Level Parameter and paths.
- A lot of other ports and network addresses of the other microservices, which communicate with the travel time service. 

## 4. Task Assignments Algorithms Overview:

### Push-Back:
Assign order to an amr with the lowest cost to process order at the end after all already scheduled orders.
### Greedy:
Assign order to an amr with the lowest insertion costs to the desired position of the already assigned orders.
With exception for the first position, because the first order has already been sent to the AMR and is
possibly currently being executed. The order sequence can also be improved after the new order has been inserted,
if the 2-opt approach [2] is activated. [1]
### Greedy completion time: 
Same procedure like the previous greedy method with the difference that the order is inserted to the position, where 
the estimated end time of this order plus the postponed duration of all subsequent orders of the AMR is the shortest. [1]
### Token passing:
This approach is close to state of the art. 
It is a decentralized approach in which AMR request orders, when they are available. For the case that no order can be assigned,
the AMR checks whether he is blocking another order from being executed; if this is the case the AMR reposition
itself if necessary. Otherwise, the position is okay and he still stays there. [3]
### Central:
This method [3] is one of the state-of-the-art algorithms for the considered "Multi-Agent Pickup- and Delivery Problem 
(MAPD)". It is an improvement of the previous token passing approach. 
The advantage of this approach is that the order is only fix assigned to an agent until he collects the item from the pick-up location.
After each timestep, all agents are assigned endpoints and the following "Multi-Agent Path-Finding Problem" is solved
with Conflict Based Search (CBS) [4]. At first, all agents that are at an endpoint of a non-executed task are taken into account.
Then, all free agents is assigned an endpoint, whether a pickup location of a non-executed task or another
predefined parking location. The endpoint assignment is done using the hungarian method. 
When selecting the possible endpoints, it is important to consider the solvability of the corresponding MAPD instance.  


### Sources:
- [1]: Toth, Paolo, and Daniele Vigo, eds. "The vehicle routing problem". Society for Industrial and Applied Mathematics,
(2002)
- [2]: Croes, Georges A. "A method for solving traveling-salesman problems." Operations research 6.6 (1958): 791-812
- [3]: Ma, Hang, et al. "Lifelong multi-agent path finding for online pickup and delivery tasks." AAMAS 71: 
Proceedings of the 16th Conference on Autonomous Agents andMultiAgent Systems (2017): 837-845
- [4]: Sharon, Guni, et al. "Conflict-vbased search for optimal multi-agent pathfinding."
Artificial intelligence 219 (2015): 40-66


## 4. API-Documentation
- OpenAPI Specification: [`docs/openapi.json`](docs/openapi.json)