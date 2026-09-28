# Order Management Service

The order management microservice contains a database to storing all relevant data of orders for the fleet management 
system. The microservice responding to request regarding order management.

## 1. Deployment:

### a.) Deployment microservice for the fleet management system using python
To deploy the order management service locally, run
```
pip install -r requirements.txt
```
to install all dependencies. then, run ``main.py``

To test the endpoints open your browser at: http://localhost:3002/docs

### b.) Deployment microservice for the fleet management system using docker
1. Open a new wsl terminal
2. To deploy the order management service via docker, build the docker image using the Dockerfile by executing
```
docker build -t ordermanagement .
```
3. Then, run a container from created image with the IMAGE_ID by executing
```
docker run -p 3002:3002 -t IMAGE_ID 
```
To test the endpoints open your browser at: http://localhost:3002/docs

## 2. Project structure:
- api: All content regarding the restful api is placed here.
- config: All content regarding config parameter of the microservice is placed here.
- data: All content regarding the data models is placed here.
- database: All content regarding the database to storing all content regarding the order is placed here.
- log_config: All content regarding the logging is placed here.
- logic: All content regarding calculation of logical processes is placed here.
- tests: ALl content regarding testing is placed here.
- main.py: File to start the microservice. 


## 3. Configuration Parameter:

In the ./config/config_file.py file you can set some configuration parameter:
- PORT: 3002 (default)
- HOST: '0.0.0.0' (default)


- LOAD_LAST_STATUS: Boolean, only possible if order management service is not used with an in-memory database


- STORAGE_LOCATION_ALGORITHM: Algorithm selection for storage location tracking is activated.
- STORAGE_LOCATION_TRACKING: If storage location tracking service are connected and running.

- Logging Level Parameter and paths
- A lot of other ports and network addresses of the other microservices, which communicate with the order management
service. 


- DATABASE_FILE: Specify the kind of database. the default configuration specify an in-memory database, this means the
  database is empty after restart the service. The other database configuration defines a sqlite-database and all
  orders are stored, also after a restart of this service.

## 4. API-Documentation
- OpenAPI Specification: [`docs/openapi.json`](docs/openapi.json)
