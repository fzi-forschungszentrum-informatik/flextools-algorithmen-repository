# FlexTools Fleet Management Framework and Planning Algorithms
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/fzi-forschungszentrum-informatik/flextools-algorithmen-repository)](https://github.com/fzi-forschungszentrum-informatik/flextools-algorithmen-repository/releases)


![plot](./images_readme/flextools.png)
## 🟢 What is it?
This repository provides a modular framework for planning and controlling Autonomous Mobile Robots (AMRs) in
intralogistic processes, including storage location tracking.
The system is designed to facilitate the deployment of AMRs in brownfield environments by enabling flexible integration,
adaptability to existing infrastructure and data-driven optimization of robot operations.
The framework provides functionality for AMR fleet management, path planning, task assignment, routing graph generation,
and storage location tracking in intralogistic environments.
For evaluation and experimentation, it includes an event-driven simulation, benchmark generation for different layouts,
visualization of evaluation results, and automated processing of experimental evaluations.
The framework is based on industrial standards such as VDA5050 [1] and the Layout Interchange Format (LIF) [2].

Figure 1 illustrates the overall system architecture and the interaction between its components.

![plot](./images_readme/MAPD_Framework_with_Storage_Location_Management.svg)

[Figure 1: Components FlexTools Fleet Management Framework and Planning Algorithms]

[1]: Vda5050 - version 2.1.0 (2024), https://github.com/VDA5050/VDA5050/tree/main

[2]: Lif - layout interchange format (2024), https://vdma.eu/documents/34570/3317035/FuI_Guideline_LIF_GB.pdf


## 📦 Main Components

| Component | Type | Purpose | Start mode | Location                         |
|---|---|---|---|----------------------------------|
| Storage Location Tracking | Service | Tracks storage item locations | Docker | `.../storage_location_tracking/` |
| Path Planning | Service / Algorithms | Collision-free route planning for AMRs | Docker / local | `.../path_planning_service/`     |
| Task Assignment | Service / Algorithms | Assigns transport tasks to AMRs | Docker / local | `.../task_assignment/`           |
| System state management | Service  | Store the current system state and processes state updates | Docker / local | `.../system_state_management/`   |
| Order Management | Service | Stores information about all transport orders | Docker / local | `.../order_management/`          |
| AMR Communication | Service | Interface to AMRs via messaging standard VDA5050 | Docker / local | `.../amr_communication/`         |
| User Interface | Service | Web Interface to manage fleet management system | Docker / local | `.../user_interface/`            |
| Base Data Management | Service | Conatins base data of the AMR fleet | Docker / local | `.../base_data_management/`      |
| AMR Simulation | Evaluation Service | Event-driven discrete time step simulation of AMR fleet | Docker / local | `.../amr_simulation/`            |
| Scenario Evaluation | Evaluation Service | Runs evaluation scenarios | Local | `.../scenario_evaluation/`       |
| Rouitng Graph Generation | Algorithms | Generates routing graphs and benchmark instances | Local | `.../instance_generation/`       |
| Visualization and Analysis | Evaluation Service | Analyzes and visualizes results | Local | `.../visualizations_analysis`    |

## 📁 Repository Structure
The repository is structured as follows:

```text
.
├── FleetManagementEvaluationFramework/
│   ├── FleetManagementServices/
│   │   ├── amr_communication/
│   │   ├── storage_location_tracking/
│   │   ├── base_data_management/
│   │   ├── order_management/
│   │   ├── path_planning/
│   │   ├── system_state_management/
│   │   ├── task_assignment/
│   │   └── user_interface/
│   ├── ScenarioEvaluationServices/
│   │   ├── amr_simulation/
│   │   ├── routing_graph_generation/
│   │   ├── scenario_evaluation/
│   │   └── visualizations_analysis/
│   └── README.md
└── DockerComposeFiles/
└── images_readme/
└── LICENSE
└── README.md
```

## 🧠 Core Algorithms

### **Multi-Agent Path Planning / MAPF**
- FleetManagementEvaluationFramework/FleetManagementServices/path_planning/mapf_algorithms/path_planning/

### **Routing Graph Generation / Instance Generation** 
- FleetManagementEvaluationFramework/ScenarioEvaluationServices/instance_generation/generator_scripts/

### **Multi-Agent Task Assignment / MAPD**
- FleetManagementEvaluationFramework/FleetManagementServices/task_assignment/logic/task_assignment/


These modules are currently embedded in service-oriented code because they are closely coupled to the data models and execution flow of the surrounding system.

## 🛠️ Deployment and Quick Start
This repository supports both containerized and local execution.  

### Option A - Start selected components with Docker Compose
1. Go to the `./DockerComposeFiles/` directory.
2. Select the specific docker compose file:
   - `docker-compose-storage-management.yml`
3. Configure and select the environment variables:
   - `./env_files/storage_location_tracking.env`
4. Start:
```
docker compose --env-file ./env_files/storage_location_tracking.env -f docker-compose-storage-management.yml up -d
```

### Option B - Start a service locally
1. Go to the desired service directory
2. Install all dependencies of the regarding service:
```
pip install -r requirements.txt
```
3. Set the configuration parameters in `./config/config_file.py`
4. Start the service:
```
python3 main.py
```

## 🔁 Common Workflows

### Run a fleet management service locally
Use the REDAME inside the corresponding service directory.

### Reproduce scenario-based evaluation experiments:
See:
'`./FleetManagementEvaluationFramework/README.md`

### Working on algorithmic components:
Start with:
- path planning
- task assignment
- routing graph generation


## 📚 Documentation (Where to find further details):
- Docker compose file selection: `./DockerComposeFiles/README.md`
- Framework specific evaluation: '`./FleetManagementEvaluationFramework/README.md`
- Service specific parameters and scripts: `./Folder/(SubFolder)/service_name/README.md`

## 📖 Research Context and Citation
This repository is part of the FlexTools project and is associated with research on modular fleet management and
planning for AMRs in intralogistics. If you use this repository in academic work,
cite the related publication and archived release if available.


## 📄 License:
This repository is licensed under the MIT License. See [LICENSE](LICENSE).

Third-party license attributions and component-specific license files are documented in the corresponding 
THIRD_PARTY_NOTICES.md files of each service, where required, e.g. for the path planning service
[./FleetManagementEvaluationFramework/FleetManagementServices/path_planning_service/THIRD_PARTY_NOTICES.md](./FleetManagementEvaluationFramework/FleetManagementServices/path_planning_service/THIRD_PARTY_NOTICES.md).


## 👥 Authors:

### Storage Location Tracking: 
Max Disselnmeyer  <max.disselnmeyer@kit.edu>, Janik Bischoff <janik.bischoff@kit.edu>

### Fleet Management System and Evaluation Services: 
Justus Knierim <knierim@fzi.de>, Jonas Ringel


## Acknowledgements:
<img src="images_readme/BMWE2025_NextGenEU.jpg" width="300">

The research project "FlexTools - The Modular Toolbox for Flexible Robotics for Small and Medium-Sized
Automotive Suppliers" is funded by the Federal Ministry for Economic Affairs and Energy of the Federal Republic
of Germany and by the European Union under the NextGenerationEU programme, grant number 13IK032. 
