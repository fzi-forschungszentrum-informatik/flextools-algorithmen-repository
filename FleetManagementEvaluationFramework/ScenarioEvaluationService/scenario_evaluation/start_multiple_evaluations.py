import importlib.util
import os
import time

import pandas as pd
import log_config.log
import data.enums

from api.api_config import set_service_urls
from api.client_api import get_make_span_api, reset_order_management, \
    set_task_assignment_strategy_api, set_path_planning_strategy_api, set_collision_detection_api, reset_time_measurement, \
    reset_task_assignment, reset_base_data_management, reset_amr_simulation, reset_system_state_management, \
    set_waiting_time_in_simulation, set_heuristic_for_a_star, \
    set_cbs_improvement_cost_function, set_dispatching_strategy_in_system_state_management, \
    set_dispatching_strategy_in_amr_simulation, get_statistic_time_parameter_from_path_planning, \
    set_parking_nodes_for_layout, get_statistic_information_from_system_state_management, \
    get_statistic_information_from_amr_simulation, set_duration_edge_in_path_planning, set_focal_heuristic, \
    set_name_of_statistic_files, visualize_full_mapd_scenario

from api.client_api_models import MakeSpanRequest, \
    TaskAssignmentStrategy, CollisionDetection, PathPlanningStrategy, WaitingTimeRequest, \
    HeuristicRequest, CBSImprovementRequest, SetParkingNodesRequest, DurationEdgeRequest, FocalHeuristicRequest, \
    StatisticFileNames
from config.config_file import LOGGER_NAME

from microservice_initialization.init_scenario_orders import init_scenario_with_orders
from microservice_initialization.init_system_and_base_state_management import \
    create_system_state_and_base_state_object_from_file, send_system_state_objects
from microservice_initialization.init_path_planning import set_lif_object_from_file_in_travel_time_service
from simulation.run_simulation import run_simulation


logger = log_config.log.set_logger(LOGGER_NAME)

def main():
    base_path = 'evaluation_mapd'

    evaluation_folders = ['Warehouse_35x21', 'Free_Space_35x21', 'Matrix_33x33', 'Matrix_22x22',
                          'Cross_Docking_Layout_45_45', 'Warehouse_35x21_with_bottlenecks']

    graph_list = ['grid', 'triangle', 'hexagonal']

    distance_list = [[1, 0.5], [1, 0.5], [0.5]]

    path_planning_algorithm_list = [data.enums.PathPlanningStrategy.cbs, data.enums.PathPlanningStrategy.ecbs,
                                    data.enums.PathPlanningStrategy.cbs_djs_test,
                                    data.enums.PathPlanningStrategy.ecbs_djs_test]

    focal_heuristics = [[None], [data.enums.ECBSHeuristic.h1_fast], [None], [data.enums.ECBSHeuristic.h1_fast]]
    optimality_bound_list = [[1.0], [1.3], [1.0], [1.3]]
    number_of_orders = [200]
    task_frequencies = [1, 2, 5, 10]
    number_amr = [10, 20, 30, 40, 50]
    configs = {}
    start_time_main_evaluation = time.monotonic()
    for i, evaluation_folder in enumerate(evaluation_folders):
        for j, algorithm in enumerate(path_planning_algorithm_list):
            for focal_heuristic in focal_heuristics[j]:
                for w in optimality_bound_list[j]:
                    file_name_evaluation_results = fr'evaluation_mapd/{evaluation_folder}/output/{evaluation_folder}_results_finally.csv'
                    logger.info(f'Start evaluation from folder {evaluation_folder}')
                    module_name = f'config_{i}'
                    file = os.path.join(base_path, evaluation_folder, 'evaluation_config.py')

                    spec = importlib.util.spec_from_file_location(module_name, file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    configs[evaluation_folder] = module

                    # for evaluation_folder in evaluation_folders: ?
                    for k, graph in enumerate(graph_list):
                        for d in distance_list[k]:
                            for number_orders in number_of_orders:
                                for task_frequency in task_frequencies:
                                    for n_amr in number_amr:
                                        # Check if data with these computation in the file already computed
                                        if os.path.exists(file_name_evaluation_results):
                                            results_df = pd.read_csv(file_name_evaluation_results, sep=';', decimal=',')
                                        else:
                                            results_df = pd.DataFrame()
                                        already_done = False
                                        if not results_df.empty:
                                            already_done = (
                                                    (results_df['Layout'] == evaluation_folder)
                                                    & (results_df['Graph'] == f"{graph}_{d}")
                                                    & (results_df['Number AMR'] == n_amr)
                                                    & (results_df['Orders'] == number_orders)
                                                    & (results_df['Task Frequency'] == task_frequency)
                                                    & (results_df['Path Planning Algorithm'] == f"{algorithm}_{w}")
                                            ).any()
                                        if already_done:
                                            logger.info(f'Combination already in this file computed, go to next computation')
                                            continue
                                        logger.info(f'Start Scenario Evaluation for {evaluation_folder} with {algorithm}'
                                                    f' algorithm for {graph} {d} graph with {n_amr} and {task_frequency} TF')

                                        configs[evaluation_folder].PATH_PLANNING_ALGORITHM = algorithm
                                        configs[evaluation_folder].PATH_PLANNING_ALGORITHM_BOUND = w
                                        configs[evaluation_folder].FOCAL_HEURISTIC = focal_heuristic
                                        configs[evaluation_folder].GRAPH = graph
                                        configs[evaluation_folder].DISTANCE = d
                                        configs[evaluation_folder].NUMBER_AMR = n_amr
                                        configs[evaluation_folder].TASK_FREQUENCY = task_frequency
                                        configs[evaluation_folder].NUMBER_OF_ORDERS = number_orders
                                        try:
                                            start_single_evaluation(configs[evaluation_folder], file_name_evaluation_results,
                                                                    evaluation_folder)
                                        except Exception as e:
                                            logger.info(f'Error: Evaluation failed in folder {evaluation_folder} with'
                                                        f' {number_orders} orders,'
                                                        f' {task_frequency} task frequency and {n_amr} amr!!!')
                                            logger.exception(f'Error: {e}')
    duration_main_evaluation = time.monotonic() - start_time_main_evaluation
    m, s = divmod(duration_main_evaluation, 60)
    h, m = divmod(m, 60)
    logger.info(f'Evaluation successfully finished after {h} hours, {m} minutes and {s} seconds:)')


def start_single_evaluation(configs, file_name_results, evaluation_folder):
    # Stop time
    start_time = time.monotonic()
    set_service_urls()
    # 1. Reset all service for evaluation
    reset_order_management()
    reset_time_measurement()
    reset_task_assignment()
    reset_base_data_management()
    reset_amr_simulation()
    reset_system_state_management()
    ################
    file_name_statistics = (f'{evaluation_folder}_{configs.GRAPH}_{configs.DISTANCE}_AMR_{configs.NUMBER_AMR}_'
                            f'TF_{configs.TASK_FREQUENCY}_Orders_{configs.NUMBER_OF_ORDERS}_{configs.PATH_PLANNING_ALGORITHM}_'
                            f'{configs.PATH_PLANNING_ALGORITHM_BOUND}')
    set_name_of_statistic_files(StatisticFileNames(AMRStatisticDataFileName=f'./statistic_data/{evaluation_folder}/output/amr_data/{file_name_statistics}_amr_data.csv',
                                                   GraphStatisticDataFileName=f'./statistic_data/{evaluation_folder}/output/graph_data/{file_name_statistics}_graph_data.csv'))
    # 2. Set Layout
    layout = set_lif_object_from_file_in_travel_time_service(configs)
    # 3. Set System state and base state
    system_state_objects, base_state_objects = create_system_state_and_base_state_object_from_file(configs)
    send_system_state_objects(system_state_objects, base_state_objects)

    # 4. Select algorithms
    if configs.TASK_ASSIGNMENT_ALGORITHM != data.enums.TaskAssignmentStrategy.greedy:
        use_improvement = None
    else:
        use_improvement = configs.USE_IMPROVEMENT
    set_task_assignment_strategy_api(TaskAssignmentStrategy(dispatchingStrategy=configs.TASK_ASSIGNMENT_ALGORITHM,
                                                            useImprovement=use_improvement))
    set_dispatching_strategy_in_system_state_management(TaskAssignmentStrategy(dispatchingStrategy=configs.TASK_ASSIGNMENT_ALGORITHM))
    set_dispatching_strategy_in_amr_simulation(TaskAssignmentStrategy(dispatchingStrategy=configs.TASK_ASSIGNMENT_ALGORITHM))

    set_collision_detection_api(CollisionDetection(collisionDetection=configs.COLLISION_DETECTION))

    set_path_planning_strategy_api(PathPlanningStrategy(pathPlanningStrategy=configs.PATH_PLANNING_ALGORITHM,
                                                        boundary=configs.PATH_PLANNING_ALGORITHM_BOUND))
    set_focal_heuristic(FocalHeuristicRequest(heuristic=configs.FOCAL_HEURISTIC))
    set_heuristic_for_a_star(HeuristicRequest(heuristic=configs.PATH_PLANNING_HEURISTIC))
    set_cbs_improvement_cost_function(CBSImprovementRequest(useAdvancedCostFunction=configs.CBS_COST_FUNCTION_IMPROVEMENT))
    set_waiting_time_in_simulation(WaitingTimeRequest(waitingTime=configs.WAIT_DURATION))
    set_duration_edge_in_path_planning(DurationEdgeRequest(duration=configs.DISTANCE))

    # 5. Set order scenario
    last_order_id = init_scenario_with_orders(configs)

    # 6. Optional: Set parking nodes for layout if available
    set_parking_nodes_for_layout(SetParkingNodesRequest(layoutId=configs.MAP_ID,
                                                        parkingNodes=configs.get_parking_nodes(configs.GRAPH,
                                                                                               configs.DISTANCE)))

    # 7. Run simulation
    error = run_simulation()
    duration_2 = time.monotonic() - start_time
    if error is False:
        if configs.VISUALIZE_SCENARIO is True:
            visualize_full_mapd_scenario(layout)
        logger.info(f'Evaluation finished successfully after {duration_2} seconds!')
        # 8. Makespan request, also to export statistics data
        makespan_request = MakeSpanRequest(earliestOrderId=str(1),
                                           latestOrderId=str(int(last_order_id)-1))
        makespan_response = get_make_span_api(makespan_request).json()
        m, s = divmod(makespan_response['time'], 60)
        h, m = divmod(m, 60)

        sim_info = get_statistic_information_from_amr_simulation().json()
        driving_time_with_loads = sim_info['drivingTimeLoaded']
        driving_time_empty_driving = sim_info['drivingTimeUnloaded']
        driving_time = driving_time_empty_driving + driving_time_with_loads
        throughput = round(configs.NUMBER_OF_ORDERS / makespan_response['time'], 2)
        duration = time.monotonic() - start_time


        logger.info(f'Evaluation finished successfully after {duration} seconds with makespan!')
        logger.info(str('Makespan = ' + str(h) + ' Hours ' + str(m) + ' Minutes ' + str(s) + ' Seconds'))
        statistic_parameter = get_statistic_time_parameter_from_path_planning().json()
        path_planning_success_information = get_statistic_information_from_system_state_management().json()
        logger.info('Number of failed path planning computations: {}'.format(statistic_parameter['number_of_failed_path_computations']))
        logger.info('Number of exceeded routing time threshold: {}'.format(statistic_parameter['number_of_exceed_routing_time_threshold']))
        logger.info('Number of executed CBS computations: {}'.format(statistic_parameter['number_of_path_planning_requests']))
        logger.info('Total number of generated nodes in conflict tree: {}'.format(statistic_parameter['number_of_generated_nodes_cbs']))
        logger.info('Average number of generated nodes in conflict tree pro CBS computation: {}'.format(
              round(statistic_parameter['number_of_generated_nodes_cbs'] /
                    statistic_parameter['number_of_path_planning_requests'], 2)))
        logger.info('Recovery times to find path planning solution again: {}'.format(
            path_planning_success_information['number_to_find_path_again']))
        result_df = pd.DataFrame({'Layout': [evaluation_folder], 'Number AMR': [configs.NUMBER_AMR],
                                  'Orders': [configs.NUMBER_OF_ORDERS], 'Task Frequency': [configs.TASK_FREQUENCY],
                                  'Makespan [s]': [makespan_response['time']], 'Driving Time': [driving_time],
                                  'Empty Driving Time': [driving_time_empty_driving],
                                  'Loaded Driving Time': [driving_time_with_loads], 'Throughput': [throughput],
                                  'Evaluation Duration': [duration], 'Path Planning time': [statistic_parameter['path_planning_time']],
                                  'Failed path planing computations': [statistic_parameter['number_of_failed_path_computations']],
                                  'Number exceeded routing time threshold': [statistic_parameter['number_of_exceed_routing_time_threshold']],
                                  'Number executed CBS computations': [statistic_parameter['number_of_path_planning_requests']],
                                  'Generated nodes cbs': [statistic_parameter['number_of_generated_nodes_cbs']],
                                  'Expanded nodes astar': [statistic_parameter['number_of_expanded_nodes_a_star']],
                                  'Graph': [f'{configs.GRAPH}_{configs.DISTANCE}'], 'Path Planning Algorithm':
                                      [f'{configs.PATH_PLANNING_ALGORITHM}_{configs.PATH_PLANNING_ALGORITHM_BOUND}'],
                                  'Number time steps find path again': [path_planning_success_information['number_to_find_path_again']]})
        file_exists = os.path.exists(file_name_results)
        result_df.to_csv(
            file_name_results,
            mode='a' if file_exists else 'w',
            header=not file_exists,
            index=False,
            sep=';',
            decimal=','
        )
    else:
        statistic_parameter = get_statistic_time_parameter_from_path_planning().json()
        logger.info(f'Error: Evaluation finished unsuccessfully after {duration_2} seconds!')
        logger.info(f'Error: Evaluation finished unsuccessfully after {duration_2} seconds!')
        logger.info('Number of failed path planning computations: {}'.format(
              statistic_parameter['number_of_failed_path_computations']))
        logger.info('Number of exceeded routing time threshold: {}'.format(
              statistic_parameter['number_of_exceed_routing_time_threshold']))
        logger.info('Number of executed CBS computations: {}'.format(statistic_parameter['number_of_path_planning_requests']))
        logger.info('Total number of generated nodes in conflict tree: {}'.format(
              statistic_parameter['number_of_generated_nodes_cbs']))
    return


if __name__ == "__main__":
    main()
