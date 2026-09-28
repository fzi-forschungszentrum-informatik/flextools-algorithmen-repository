# api
All content regarding the restful api is placed here.

## api_config:
* host: defines the host-address under which the dispatching service is available
* port: defines port under which the dispatching service  is available
* allowed_origins: defines the host-addresses, that are allowed to communicate with the dispatching service.
* set_service_urls: defines urls from other microservices for the api communication
* initialize app: defines the FastAPI configuration

## client_api:
* defines the outgoing client api calls

## client_api_models:
* defines the data models for the outgoing client api calls

## server_api:
* defines the incoming api calls required to handle the request of other microservices.

## server_api_models:
* defines the request and response data models for incoming api calls from other microservice.

## serialization:
* Defines how to serialize a class model to a dictionary for transforming to json for the outgoing api calls.