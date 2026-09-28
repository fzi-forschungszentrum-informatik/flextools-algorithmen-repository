# System State Management
This microservice responding to request regarding system states.
In addition to the standard methods like store and process the state updates from the amr,
update the system time and so on, this service is also requested for orders after each timestep.
Thereby, it is checked, if some orders finished processed and should an amr receive a new order.
For this, the system state management service requested for new orders at the dispatching service, 
or check whether there are already orders in the planned order list of an AMR, which has been assigned to the AMR. 
If there are new orders, which can assigned to the AMR, the method requested exact routes for the orders from the 
travel time service and updated the paths of some currently executed orders if necessary.
Next, the new orders and order updates are send to the amr communication service for publishing this orders via mqtt.

## 1. Deployment:

### a.) Deployment microservice for the fleet management system using python
To deploy the routing service locally, run
```
pip install -r requirements.txt
```
to install all dependencies. then, run ``main.py``

To test the endpoints open your browser at: http://localhost:3001/docs

### b.) Deployment microservice for the fleet management system using docker
1. Open a new wsl terminal
2. To deploy the system state management service via docker, build the docker image using the Dockerfile by executing
```
docker build -t systemstatemanagement 
```
3. Then, run a container from created image with the IMAGE_ID by executing
```
docker run -p 3001:3001 -t IMAGE_ID 
```
To test the endpoints open your browser at: http://localhost:3001/docs

## 2. Project Structure:
- api: All content regarding the restful api is placed here.
- config: All content regarding config parameter of the microservice is placed here.
- data: All content regarding the database for storing long living data is placed here.
- log_config: All content regarding the logging is placed here.
- logic: All content regarding computation of logical processes is placed here.
- test: All content regarding tests the api calls and logical processes is placed here.
- main.py: File to start the microservice. 

## 3. Configuration Parameter:

In the ./config/config_file.py file you can set some configuration parameter:
- PORT: 3006 (default)
- HOST: '0.0.0.0' (default)


- TASK_ASSIGNMENT_STRATEGY: Determine the task assignment strategy for assigning the orders to the amrs.
More information about the task assignment strategies can be read in the task assignment service.
- STORAGE_LOCATION_TRACKING: Specify, if the storage location management services are running and should be initialized.
- PATH_PLANNING_INTEGRATION: Specify the kind of path planning integration in the task assignment method Central.
  * Complete CBS: Plans all paths together.
  * Two-Stage: Plans at first the new tasks to the delivery locations and secondly, the paths to the assigned pickup
  locations with initial constraints.
- INFINITY_CONSTRAINT: Specify, if last node from constraint from amr path is blocked on time step or until infinity.
- SIMULATION_ACTIVE: Determine, if a connected simulation active or real robots.
- MAX_NUMBER_OF_FAILED_PATH_PLANNING: Determine the maximum number of following failed path planning requests, the the evaluation scenario terminates. 


- Logging Level Parameter and paths
- A lot of other ports and network addresses of the other microservices, which communicate with the order management
service. 


## 4. API-Documentation
- OpenAPI Specification: [`docs/openapi.json`](docs/openapi.json)