# Base Data Management
The base data management microservice contains a database to storing all physical data of all amr operating in the
fleet management system according the fact sheet of vda5050. 
The microservice responding to request regarding base data management.

## 1. Deployment

### a.) Deployment microservice for the fleet management system using python
To deploy the basedatamanagement service locally, run 
```
pip install -r requirements.txt
```
to install all dependencies. Then, run ``main.py``.

To test the endpoints open your browser at: http://localhost:3005/docs

### b.)  Deployment microservice for the fleet management system using docker
1. Open a new wsl terminal
2. To deploy the base data management service via docker, build the docker image using the Dockerfile by executing
```
docker build -t basedatamanagement .
```
3. Then, run a container from created image with the IMAGE_ID by executing
```
docker run -p 3005:3005 -t IMAGE_ID 
```
To test the endpoints open your browser at: http://localhost:3005/docs


## 2. Project Structure:
- api: All content regarding the restful api is placed here.
- config: All content regarding config parameter of the microservice is placed here.
- data: All content regarding the data models is placed here.
- database: All content regarding the database to storing all content regarding the amr is placed here.
- log_config: All content regarding the logging is placed here.
- logic: All content regarding calculation of logical processes is placed here.
- tests: ALl content regarding testing is placed here.
- main.py: File to start the microservice. 

## 3. Configuration Parameter:
In the ./config/config_file.py file you can set some configuration parameter:
- PORT: 3006 (default)
- HOST: '0.0.0.0' (default)


- LOAD_LAST_STATUS: Boolean, only possible if order management service is not used with an in-memory database
- DATABASE_FILE: Specify the kind of database. the default configuration specify an in-memory database, this means the
  database is empty after restart the service. The other database configuration defines a sqlite-database and all
  orders are stored, also after a restart of this service.


- Logging Level Parameter and paths
- A lot of other ports and network addresses of the other microservices, which communicate with the base data management
service. 

## 4. API-Documentation
- OpenAPI Specification: [`docs/openapi.json`](docs/openapi.json)
