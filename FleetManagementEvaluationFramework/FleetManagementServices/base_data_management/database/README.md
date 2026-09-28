# database
All content regarding the database for storing long living data is placed here.

## dao:
* All python files, with data access object functions, for adding or request data from the database is placed here. 

## models:
* All models for the structure of the tables from the database is placed here.

## transformations:
* All python scripts for transform database objects to api objects are placed here.

## db:
* Python file for creating the base and the engine of the sql-database.

## db_init:
* Start-up event for setting up the database by starting the microservice is placed here.

## reset_database:
* Method for resetting the database is placed here. 
* Deletes the entries of the database tables.

## setup_initial_db:
* Method for set up the database with initial values from the selected json-file.
* Creates the Session object for committing data to the database.
