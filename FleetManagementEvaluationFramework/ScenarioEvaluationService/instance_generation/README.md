# Instance Generation Benchmarks Multi-Agent Pickup and Delivery Problems
This project provides an instance generation script for Multi-Agent Pickup- and Delivery Problems (MAPD).
The goal of this service is, to get for an arbitrary layout a suitable routing graph in the
Layout-Interchange-Format (LIF) and order and system state files for the evaluation.

## 1. Instance Generator Overview and components (Project structure):
* configs_scenario_generation: This folder provides all config files for the different layouts.
* data: All content regarding the data models is placed here.
* endpoints: All endpoints/ parking nodes are saved here for each layout.
* generator_scripts: All logic scripts to generate routing graphs of the different layouts are placed here.
* graph_computation_scripts: Script to compute the graph properties of the created routing graphs.
* graph_properties: Csv-files with the graph properties for all graphs of a layout.
* images: Folder for the Layout images.
* lif_files: Folder of the lif files of all generated routing graphs.
* methods: Help methods, e.g. serialization
* order_files: Folder of the order files of all MAPF instances.
* system_state_files: Folder of the system state files of all MAPF instances.

## 2. Generate new MAPD instance/benchmark: 
1. To generate a routing graph or a MAPD instance for a layout, you can save an image of the layout in the ./images
folder. E.g. you can create such an image in excel with different cell colors and then doing a screenshot. 
Important is that the black space are hints, where the robots can't drive.
The robots can drive in the white and gray fields. The pickup and delivery locations of the orders and initial
position of the robots are sampled in the gray range. Figure 1 shows an example warehouse layout:

2. Each layout needs a config file. In the config file you must determine the real size of the layout and the paths
to the data. Furthermore, you can select the graph form, determine the distance between the nodes and the distance to
the top left corner to place the first node. 
Next, you can select the number of robots and the reach of the robots, e.g. if you consider charging. 
Last you can determine the number of orders, the task frequency of publishing the orders, the pickup- and delivery time
and the distance minimum distance between pickup and delivery location of an order. There are further properties,
e.g. the list split_x means for order generation the layout is splitted by the given x-coordinate and
an order have the pickup location at one side and the delivery location at the other side. For example, 
it is particularly relevant for cross-docking layouts. 

3. Last, to generate the benchmarks, you must import this config file in the main.py file.
Then you can run the main.py file for the benchmark creation:
```
python3 main.py
```
For example, figure 2 shows an possible routing graph for the above warehouse layout with a quadratic grid and a node
distance of one meter: