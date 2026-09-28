# tests
This folder contains all tests of the basedatamanagement microservice that are to be executed during the ci-build process. 
For testing locally, make sure all required microservice-endpoints to test against are up and running. 

As test framework, we apply [pytest](https://docs.pytest.org/en/8.2.x/#). Hence, by executing the command
```
python -m pytest
```

all files of the form test_*.py or *_test.py in the current directory and its subdirectories are executed.


## test_logic:
* The file test_logic.py contains all tests regrading the logic of the microservice and mock used object from other
microservices.

## conftest:
* The file conftest.py contains all fixtures needed for testing.