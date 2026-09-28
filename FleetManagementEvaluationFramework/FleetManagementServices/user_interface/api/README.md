# api
All content regarding the restful api is placed here.

## api_config:
* host: defines the host-address under which the userinterface service is available
* port: defines port under which the order management service  is available
* allowed_origins: defines the host-addresses, that are allowed to communicate with the order management service.
* set_service_urls: defines urls from other microservices for the api communication
* initialize app: defines the FastAPI configuration

## client_api:
* defines the outgoing client api calls to get data for visualizing.

## serialization:
* Defines how to serialize a class model to a dictionary for transforming to json for the outgoing api calls.
