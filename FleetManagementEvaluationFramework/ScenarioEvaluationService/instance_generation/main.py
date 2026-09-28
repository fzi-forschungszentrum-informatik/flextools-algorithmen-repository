import copy
import random

import generator_scripts.image_to_graph_triangle
import generator_scripts.image_to_graph_quadratic
import generator_scripts.image_to_graph_hexagonal
import generator_scripts.image_to_graph_prm
from generator_scripts.generate_system_state_file import generate_system_state_file_new
from generator_scripts.image_to_tasks import image_to_tasks_coordinates
from generator_scripts.mapf_scenario_generation import generate_mapf_scenario
from generator_scripts.network_x_to_lif import create_lif_from_network_x_graph
from generator_scripts.order_scenario_generation import generate_order_scenario
from generator_scripts.prm_graph_to_odrm_graph import create_graph
from generator_scripts.odrm_graph_to_udrm_graph import create_graph

###### Select Config file to import ###################################################################################
from configs_scenario_generation.warehouse_35x21_config import (IMAGE_FILE, LAYOUT_NAME, FORMS, DISTANCES,
                                                                 DISTANCES_TO_SIDE, LENGTH, WIDTH, MAX_REACH,
                                                                 NUMBER_OF_AMRS, LAYOUT_ID, PICKUP_TIME, DELIVERY_TIME,
                                                                 SEED, TIMESTEP, TASK_FREQUENCY_LIST,
                                                                 NUMBER_OF_ORDERS_LIST, SPLIT_Y, SPLIT_X, AMR_RADIUS,
                                                                 ENDPOINT_DISTANCE_THRESHOLD, NUMBER_OF_NODES,
                                                                 DISTANCE_BETWEEN_START_POSITION, DISTANCE_BETWEEN_START_AND_GOAL,
                                                                 MAX_TIME_START_POSITION)
from graph_computation_scripts.compute_graph_properties import compute_graph_properties
from log_config.config import LOGGER_NAME
import log_config.log
from mapf.image_to_mapf_instance import image_to_mapf_coordinates

logger = log_config.log.set_logger(LOGGER_NAME)

#######################################################################################################################

def generate_benchmark_data():
    image_file = IMAGE_FILE
    layout_name = LAYOUT_NAME

    forms = FORMS
    distances = DISTANCES
    distance_to_edges = DISTANCES_TO_SIDE
    length = LENGTH
    width = WIDTH
    amr_radius = AMR_RADIUS
    endpoint_distance_threshold = ENDPOINT_DISTANCE_THRESHOLD
    number_of_nodes = NUMBER_OF_NODES

    min_distance_between_start_and_goal = DISTANCE_BETWEEN_START_AND_GOAL
    min_distance_between_start_positions = DISTANCE_BETWEEN_START_POSITION

    max_reach = MAX_REACH
    number_of_amrs = NUMBER_OF_AMRS

    split_x = SPLIT_X
    split_y = SPLIT_Y

    layout_id = LAYOUT_ID
    pickup_time = PICKUP_TIME
    dropoff_time = DELIVERY_TIME
    random.seed(SEED)
    timestep = TIMESTEP
    task_frequence_list = TASK_FREQUENCY_LIST
    number_orders_list = NUMBER_OF_ORDERS_LIST

    order_coordinates_all, start_position_coordinates, other_positions, gray_placing =\
        image_to_tasks_coordinates(number_orders_list, length, width, image_file, number_of_amrs[-1], SEED, split_x,
                                   split_y, min_distance_between_start_and_goal, min_distance_between_start_positions,
                                   MAX_TIME_START_POSITION)

    mapf_coordinates, gray_placing = image_to_mapf_coordinates(number_paths=[10, 20], length=length, width=width,
                                                               image_file=image_file, seed=SEED,
                                                               number_mapf_instances=2)
    logger.debug(f'Order coordinates all: {order_coordinates_all}')
    logger.debug(f'Start position coordinates: {start_position_coordinates}')
    logger.debug(f'Other positions: {other_positions}')
    logger.debug(f'MAPF coordinates: {mapf_coordinates}, {gray_placing}')

    graph_odrm, endpoints_odrm = None, None
    endpoint_list = []
    for i, form in enumerate(forms):
        for j, distance in enumerate(distances[i]):
            graph = None
            endpoints = None
            lif_file_name = f'./lif_files/LIF_{layout_name}_dist_{distance}_{form}.json'
            endpoints_file_name = f'./endpoints/Endpoints_{layout_name}_dist_{distance}_{form}.txt'
            if form == 'grid':
                graph, endpoints, pos = generator_scripts.image_to_graph_quadratic.create_graph(length, width, distance,
                                                                                                image_file,
                                                                                                distance_to_edges[i][j])
            elif form == 'triangle':
                graph, endpoints, pos = generator_scripts.image_to_graph_triangle.create_graph(length, width, distance,
                                                                                               image_file,
                                                                                               distance_to_edges[i][j])
            elif form == 'hexagonal':
                graph, endpoints, pos = generator_scripts.image_to_graph_hexagonal.create_graph(length, width, distance,
                                                                                                image_file,
                                                                                                distance_to_edges[i][j])

            elif form == 'prm':
                graph, endpoints, pos, _, _, _, _, _ = generator_scripts.image_to_graph_prm.create_graph(length, width, number_of_nodes,
                                                                                                         image_file, amr_radius,
                                                                                                         endpoint_distance_threshold, SEED)
            elif form == 'odrm':
                prm_graph, endpoints, pos, deb_image, gray_mask, obstacle_mask, px_per_meter_x, px_per_meter_y = (
                    generator_scripts.image_to_graph_prm.create_graph(length, width, number_of_nodes,
                                                                      image_file, amr_radius,
                                                                      endpoint_distance_threshold, SEED))

                graph, endpoints = generator_scripts.prm_graph_to_odrm_graph.create_graph(
                    prm_graph,
                    endpoints,
                    length,
                    width,
                    image_file,
                    gray_mask,
                    obstacle_mask,
                    px_per_meter_x,
                    px_per_meter_y)

                graph_odrm, endpoints_odrm = graph, endpoints

            elif form == 'udrm':
                if graph_odrm is not None and endpoints_odrm is not None:
                    graph, nodes = generator_scripts.odrm_graph_to_udrm_graph.create_graph(graph_odrm, endpoints_odrm)
                else:

                    prm_graph, endpoints, pos, deb_image, gray_mask, obstacle_mask, px_per_meter_x, px_per_meter_y = (
                        generator_scripts.image_to_graph_prm.create_graph(length, width, number_of_nodes,
                                                                          image_file, amr_radius,
                                                                          endpoint_distance_threshold, SEED))

                    graph_odrm, endpoints_odrm = generator_scripts.prm_graph_to_odrm_graph.create_graph(
                        prm_graph,
                        endpoints,
                        length,
                        width,
                        image_file,
                        gray_mask,
                        obstacle_mask,
                        px_per_meter_x,
                        px_per_meter_y)
                    graph, nodes = generator_scripts.odrm_graph_to_udrm_graph.create_graph(graph_odrm, endpoints_odrm)

            if graph is not None and endpoints is not None:

                #compute_graph_properties(graph, f'{layout_name}_{form}_{distance}', distance, layout_name, pos)

                generated_endpoints, driving_nodes_list = create_lif_from_network_x_graph(graph, endpoints,
                                                                                          name_file=lif_file_name,
                                                                                          name_file_endpoints=endpoints_file_name)
                endpoint_list.append(generated_endpoints)

                try:
                    for number_amr in number_of_amrs:
                        system_state_file_name = (f'./system_state_files/system_state_file_{layout_name}_{form}_'
                                                  f'{distance}_{number_amr}_amr.json')
                        generate_system_state_file_new(graph, number_amr, copy.deepcopy(start_position_coordinates),
                                                       copy.deepcopy(other_positions), system_state_file_name, max_reach,
                                                       image_file, length, width, gray_placing)
                except Exception as e:
                    logger.exception(f'System state file generation failed, maybe no gray range for placing AMRs: {e}')
                try:
                    for k, number_of_orders in enumerate(number_orders_list):
                        for tf in task_frequence_list:
                            order_file_name = (f'./order_files/orders_scenario_{layout_name}_{form}_{distance}_'
                                               f'{number_of_orders}_seed_{SEED}_fq_{str(tf)}.json')
                            generate_order_scenario(graph, number_of_orders, order_coordinates_all[k], order_file_name,
                                                    layout_id, pickup_time, dropoff_time, tf, timestep, image_file,
                                                    length, width, gray_placing)
                except Exception as e:
                    logger.exception(f'Order generation failed {e}')
                try:
                    mapf_file_name = (f'./mapf_files/mapf_scenario_{layout_name}_{form}_{distance}_'
                                      f'{len(mapf_coordinates)}.json')
                    generate_mapf_scenario(graph, mapf_coordinates, mapf_file_name, image_file, length, width,
                                           gray_placing, False)
                except Exception as e:
                    logger.exception(f'MAPF Generation failed {e}')

    logger.info(f'Benchmark for Layout {layout_name} finish generated!')


if __name__ == "__main__":
    generate_benchmark_data()
