# Storage Location and Fleet Management System Deployment with Docker Compose

This directory contains various Docker Compose setups for running the algorithms repository of FlexTools.

## 1. Scope

The example setup is focused on the fleet management system in combination with the storage location management system:

- `docker-compose-storage-management.yml`
- `./env_files/storage_location_tracking.env`

## 2. Start the System

From `./DockerComposeFiles`:

```bash
docker compose --env-file ./env_files/storage_location_tracking -f docker-compose-storage-management.yml up -d
```

Stop the system:

```bash
docker compose --env-file ./env_files/storage_location_tracking -f docker-compose-storage-management.yml down
```

View logs:

```bash
docker compose -f docker-compose-storage-management.yml logs -f
```




## 3. Configuration

Edit `./.env` before startup, especially:

- `INPUT_DATA_PATH`: Path to generated evaluation instances
- `OUTPUT_DATA_PATH`: Path where evaluation results are written

## 4. Docker-Compose and Env-Files:
This repository includes four different docker compose files with corresponding env-files.

1. docker-compose-evaluation.yml and evaluation.env: Starts the fleet management system for the evaluation connected
to event-discrete simulation with synchron VDA5050 communication.
2. docker-compose-to-robot.yml and robot.env: Starts the fleet management system without simulation to communicate
to a real AMR asynchron via Mqtt according to VDA5050.
3. docker-compose-storage-management.yml and storage-location-tracking.env: Starts the fleet management system together 
with the storage location tracking systems.
4. docker-compose-storage-management-with-robots.yml and storage-location-tracking-with-robots.env: 
Starts the fleet management system without simulation together with the storage location tracking systems.


## 5. Service Endpoints

Swagger/OpenAPI endpoints:

- Task Assignment: [http://localhost:3000/docs](http://localhost:3000/docs)
- System State Management: [http://localhost:3001/docs](http://localhost:3001/docs)
- Order Management: [http://localhost:3002/docs](http://localhost:3002/docs)
- AMR Communication: [http://localhost:3003/docs](http://localhost:3003/docs)
- Base Data Management: [http://localhost:3005/docs](http://localhost:3005/docs)
- Path Planning: [http://localhost:3006/docs](http://localhost:3006/docs)
- User Interface: [http://localhost:3010/docs](http://localhost:3010/docs)
- AMR Simulation: [http://localhost:3011/docs](http://localhost:3011/docs)


## 6. Related Documentation

- Framework-level Pipeline: `../FleetManagementEvaluationFramework/README.md`
- Scenario Evaluation Service: `../ScenarioEvaluationServices/scenario_evaluation/README.md`

