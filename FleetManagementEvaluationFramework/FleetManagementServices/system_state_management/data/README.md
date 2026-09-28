# data
All content regarding the database for storing long living data is placed here.

## models:
* Contains all data models to hold and store data in a structured way.

## enums:
* Contains all data enums to specify data in a structured way.

## db_init:
* initialize the global database dictionary.
* defines a startup event by starting the microservice to read the input data file and creates the system_state_management database model.

## system_state_management_db:
* defines the system_state_management data model with the initialization function for this microservice.