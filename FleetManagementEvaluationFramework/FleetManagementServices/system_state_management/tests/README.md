# tests
This folder contains all tests of the system state management microservice that are to be executed during the ci-build process. For 
testing locally, make sure all required microservice-endpoints to test against are up and running. 

As test framework, we apply [pytest](https://docs.pytest.org/en/8.2.x/#). Hence, by executing the command
```
python -m pytest
```

all files of the form test_*.py or *_test.py in the current directory and its subdirectories are executed.


## system_state_file_test:
* Contains system state files for the test pipeline. 

## test_logic:
* The file test_logic.py contains all tests regrading the logic of the microservice and mock used object from other
microservices.

## conftest: