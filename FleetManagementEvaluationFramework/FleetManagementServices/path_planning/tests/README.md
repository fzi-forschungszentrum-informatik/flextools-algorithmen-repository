# Tests
This folder contains all tests of the traveltime microservice that are to be executed during the ci-build process. 
For testing locally, make sure all required microservice-endpoints to test against are up and running. 

As test framework, we apply [pytest](https://docs.pytest.org/en/8.2.x/#). Hence, by executing the command
```
python -m pytest
```

all files of the form test_*.py or *_test.py in the current directory and its subdirectories are executed.


## random_lif_generator:
* This folder contains a random lif generator to test path planning algorithms of random networks.

##  test_data:
* This folder contains data for testing. 

## conftest:
* The file conftest.py contains all fixtures needed for testing.

## Other test files (cbs_test, test_collision_detection, test_general_mapf):
* Contains all tests of this microservice.
