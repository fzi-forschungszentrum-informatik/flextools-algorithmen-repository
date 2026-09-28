import os
from copy import deepcopy
from typing import List
import log_config.log

import pandas as pd
import paramiko
from io import StringIO
from pathlib import Path
import config.config_file as config

from amr_data.amr_status_figure_time_step import create_amr_status_figure
from evaluation_tables.evaluation_table_visualization_live_data import show_data_with_dashboard
from heatmap_figures.functional_analysis.functional_analysis_heatmap_amrs_algo import \
    create_functional_heatmap_amrs_algo_abs
from heatmap_figures.functional_analysis.functional_analysis_heatmap_amrs_tfs import \
    create_functional_heatmap_amrs_tfs_abs
from heatmap_figures.functional_analysis.functional_analysis_heatmap_graph_algo import \
    create_functional_heatmap_graph_algo_abs
from heatmap_figures.functional_analysis.functional_analysis_heatmap_layout_graph import \
    create_functional_heatmap_graph_layout_abs
from scatter_plot_graph_properties.scatter_plot_graph_properties import create_feature_scatter_plot_trends_graph_properties
from graph_figures.detour_figure import create_detour_figure_graph, create_detour_figure_layout, \
    create_detour_figure_algorithm
from graph_figures.sum_of_costs_figure import create_sum_of_costs_figure_graph, create_sum_of_costs_figure_layout, \
    create_sum_of_costs_figure_algorithm
from graph_figures.sum_of_costs_figure_pro_amr import create_sum_of_costs_pro_amr_figure_graph, \
    create_sum_of_costs_pro_amr_figure_layout, create_driving_time_pro_amr_figure_algorithm
from heatmap_figures.heatmap_graph_algorithm import create_correlation_heatmap_graph_algorithm
from heatmap_figures.heatmap_graph_algorithm_abs import create_correlation_heatmap_graph_algorithm_abs
from heatmap_figures.heatmap_layout_algorithm import create_correlation_heatmap_layout_algorithm
from heatmap_figures.heatmap_layout_algorithm_abs import create_correlation_heatmap_layout_algorithm_abs
from heatmap_figures.heatmap_layout_graph import create_correlation_heatmap_graph_layout
from heatmap_figures.heatmap_layout_graph_abs import create_correlation_heatmap_graph_layout_abs
from layout_data.correlation_graph_properties_algorithm_amr_grouped import \
    create_feature_importance_figure_amr_grouped_graph_properties
from layout_data.correlation_graph_properties_algorithm import create_feature_importance_figure_graph_properties

from layout_data.mapd_interaction_effects import create_feature_mapd_interaction_effects_shap, \
    create_feature_mapd_interaction_effects_shap_pro_layout, \
    create_feature_mapd_interaction_effects_shap_pro_layout_advanced

from layout_graph_figures.figure_graph_amr_distribution_auto import create_graph_density_figure
from layout_graph_figures.figure_graph_amr_order_distribution_auto import create_graph_density_order_figure

logger = log_config.log.set_logger(config.LOGGER_NAME)


def visualization_pipeline(create_figures: bool = False):
    # 1. Load data from VM #################################################
    folder = ['Warehouse_35x21', 'Grid_35x21_not_well_formed', 'Matrix_33x33', 'Matrix_22x22',
              'Cross_Docking_Layout_45_45', 'Warehouse_35x21_with_bottlenecks']

    data_base = connect(folder)
    layout_names_comp = ['warehouse_35x21', 'space_35x21', 'matrix_33x33', 'matrix_22x22', 'cross_docking_45x45',
                         'warehouse_35x21_with_bottlenecks']

    # 2. Set data ##########################################################
    graph_list = ['grid', 'triangle', 'hexagonal']
    distance_list = [[1, 0.5], [1, 0.5], [0.5]]
    algo_list = ['cbs_1.0', 'ecbs_1.3', 'cbs_djs_test_1.0', 'ecbs_djs_test_1.3']
    metric_list = ['Makespan [s]', 'Empty Driving Time', 'Loaded Driving Time', 'Path Planning time',
                   'Evaluation Duration', 'Generated nodes cbs', 'Expanded nodes astar']  # Easy expandable
    number_of_amrs = [10, 20, 30, 40, 50]
    tfs = [1, 2, 5, 10]
    number_of_orders = 200
    image_paths = [r'./layout_graph_figures/images/Warehouse_35x21.PNG',
                   r'./layout_graph_figures/images/FreeSpace.PNG',
                   r'./layout_graph_figures/images/Matrix_Layout_33x33.PNG',
                   r'./layout_graph_figures/images/Matrix_22x22.PNG',
                   r'./layout_graph_figures/images/CrossDockingLayout.PNG',
                   r'./layout_graph_figures/images/Warehouse_35x21_with_bottlenecks_well_formed.PNG']

    layout_size_list = [[35, 21], [35, 21],  [33, 33], [22, 22], [45, 45], [35, 21]]

    graph_file_list = [r'./layout_data/graph_properties/warehouse_35x21_graph_properties.csv',
                       r'./layout_data/graph_properties/space_35x21_graph_properties.csv',
                       r'./layout_data/graph_properties/matrix_33x33_graph_properties.csv',
                       r'./layout_data/graph_properties/matrix_22x22_graph_properties.csv',
                       r'./layout_data/graph_properties/cross_docking_graph_properties.csv',
                       r'./layout_data/graph_properties/warehouse_35x21_own1_graph_properties.csv']

    # 3. Dashboard view live data #########################################m
    if create_figures is False:
        show_data_with_dashboard(data_base, layout_names_comp, graph_list, distance_list, algo_list, metric_list,
                                 number_of_amrs, tfs)

    # 4. Create and save figures ##########################################
    if create_figures:
        plot_amr_status_figures(folder, layout_names_comp, graph_list, distance_list, number_of_amrs, tfs,
                                number_of_orders, algo_list, save=True, show_figures=False)
        plot_detour_pro_amr_figures(data_base, folder, layout_names_comp, graph_list, distance_list, algo_list,
                                    save=True, show_figures=True)
        plot_driving_time_figures(data_base, folder, layout_names_comp, graph_list, distance_list, algo_list,
                                  save=True, show_figures=False)
        plot_driving_time_pro_amr_figures(data_base, folder, layout_names_comp, graph_list, distance_list, algo_list,
                                          save=True, show_figures=True)
        plot_heatmap_scalability_and_robustness_analysis(data_base, save=True, show_figures=True)
        plot_heatmap_layout_graph_correlations(data_base, layout_names_comp, graph_list, distance_list,
                                               save=True, show_figures=True)
        plot_heatmap_layout_algo_correlations(data_base, layout_names_comp, graph_list, distance_list, algo_list,
                                              save=True, show_figures=True)
        plot_heatmap_graph_algo_correlations(data_base, layout_names_comp, graph_list, distance_list, algo_list,
                                             save=True, show_figures=True)
        plot_feature_importance_figure_graph_properties(data_base, graph_file_list, layout_names_comp,
                                                        graph_list, distance_list, save=True, show_figures=True)
        plot_feature_importance_figure_graph_properties_shap(data_base, algo_list, layout_names_comp,
                                                             graph_list, graph_file_list, distance_list, save=True,
                                                             show_figures=True)
        plot_graph_density_map_order(folder, layout_names_comp, graph_list, distance_list, number_of_amrs, tfs,
                                     number_of_orders, algo_list, image_paths, layout_size_list, save=True,
                                     show_figures=False)
        plot_feature_scatter_plot_graph_properties(data_base, graph_file_list, layout_names_comp,
                                                   graph_list, distance_list, algo_list, save=True, show_figures=True)
    logger.info('All figures finished created!')
    return


def plot_amr_status_figures(folder_list, layout_names, graph_list, distance_list, number_of_amrs,
                            tf_list, number_of_orders, algo_list, save: bool, show_figures: bool):
    for f, folder in enumerate(folder_list):  # Iteration over layouts
        for g, graph in enumerate(graph_list):
            for distance in distance_list[g]:
                for n_amr in number_of_amrs:
                    for tf in tf_list:
                        for algo in algo_list:
                            file = (rf'{config.REMOTE_MAPD_SCENARIO_FOLDER_PATH}{folder}/output/amr_data/{folder}'
                                    rf'_{graph}_{distance}_AMR_{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_amr_data.csv')
                            save_file = (rf'./amr_data/figures/{folder}/Workload_{folder}_{graph}_{distance}_AMR_'
                                         rf'{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_figure_time_step.png')
                            if os.path.exists(save_file):
                                continue
                            Path(save_file).parent.mkdir(parents=True, exist_ok=True)
                            try:
                                algo_name = algo.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()
                                df = get_amr_data_from_server(file)
                                title_name = (f'Workload {n_amr} AMRs ' + layout_names[f].replace('_', ' ').capitalize() +
                                              ' Meter \n ' + graph.capitalize() + ' ' + str(distance) +
                                              f' Meter Task Frequency {tf} {algo_name}')
                                create_amr_status_figure(df, title_name, save_file, save, show_figures)
                            except Exception as e:
                                logger.info(f'Plot figure AMR workload failed for {file}; Exception {e}')
    logger.info('AMR workload status figures finish created for all selected data!')
    return


def plot_detour_pro_amr_figures(data_base, folder_list, layout_names, graph_list, distance_list, algo_list,
                                save: bool, show_figures: bool):
    iteration_list = []
    for g, graph in enumerate(graph_list):
        for dist in distance_list[g]:
            iteration_list.append(f'{graph}_{dist}')
    for algo in algo_list:
        for l, layout in enumerate(layout_names):
            save_path = rf'./graph_figures/figures/{algo}/relative_additional_detour_{algo}_{layout}_graphs.png'
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(save_path):
                continue
            # Only graph variation
            df = deepcopy(data_base[l])
            df = df[df['Path Planning Algorithm'] == algo]
            create_detour_figure_graph(df, algo, layout, iteration_list, save_path, save, show_figures)

    for algo in algo_list:
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{algo}/relative_additional_detour_{algo}_{graph}_{dist}_layouts.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = pd.DataFrame()
                iteration_list = []
                for f, folder in enumerate(folder_list):
                    iteration_list.append(folder_list[f])
                    df_add = deepcopy(data_base[f])
                    df_add = df_add[df_add['Path Planning Algorithm'] == algo]
                    df_add = df_add[df_add['Graph'] == f'{graph}_{dist}']
                    df = pd.concat([df, deepcopy(df_add)], ignore_index=True)
                create_detour_figure_layout(df, algo, f'{graph}_{dist}', iteration_list, save_path,
                                            layout_names, save, show_figures)

    iteration_list = []
    for algo in algo_list:
        iteration_list.append(algo)

    for f, folder in enumerate(folder_list):
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{graph}/relative_additional_detour_{graph}_{dist}_{layout_names[f]}_algorithm.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = deepcopy(data_base[f])
                df = df[df['Graph'] == f'{graph}_{dist}']
                create_detour_figure_algorithm(df, f'{graph}_{dist}', layout_names[f], iteration_list,
                                               save_path, save, show_figures)

    logger.info('AMR detour figures finish created for all selected data!')
    return


def plot_driving_time_figures(data_base, folder_list, layout_names, graph_list, distance_list, algo_list,
                              save: bool, show_figures: bool):
    iteration_list = []
    for g, graph in enumerate(graph_list):
        for dist in distance_list[g]:
            iteration_list.append(f'{graph}_{dist}')
    for algo in algo_list:
        for l, layout in enumerate(layout_names):
            save_path = rf'./graph_figures/figures/{algo}/driving_time_{algo}_{layout}_graphs.png'
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(save_path):
                continue
            # Only graph variation
            df = deepcopy(data_base[l])
            df = df[df['Path Planning Algorithm'] == algo]
            create_sum_of_costs_figure_graph(df, algo, layout, iteration_list, save_path, save, show_figures)

    for algo in algo_list:
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{algo}/driving_time_{algo}_{graph}_{dist}_layouts.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = pd.DataFrame()
                iteration_list = []
                for f, folder in enumerate(folder_list):
                    iteration_list.append(folder_list[f])
                    df_add = deepcopy(data_base[f])
                    df_add = df_add[df_add['Path Planning Algorithm'] == algo]
                    df_add = df_add[df_add['Graph'] == f'{graph}_{dist}']
                    df = pd.concat([df, deepcopy(df_add)], ignore_index=True)
                create_sum_of_costs_figure_layout(df, algo, f'{graph}_{dist}', iteration_list,
                                                  save_path, save, show_figures)

    iteration_list = []
    for algo in algo_list:
        iteration_list.append(algo)

    for f, folder in enumerate(folder_list):
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{graph}/driving_time_{graph}_{dist}_{layout_names[f]}_algorithm.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = deepcopy(data_base[f])
                df = df[df['Graph'] == f'{graph}_{dist}']
                create_sum_of_costs_figure_algorithm(df, f'{graph}_{dist}', layout_names[f], iteration_list,
                                                     save_path, save, show_figures)
    logger.info('Driving time figures finish created for all selected data!')
    return


def plot_driving_time_pro_amr_figures(data_base, folder_list, layout_names, graph_list, distance_list, algo_list,
                                      save: bool, show_figures: bool):
    iteration_list = []
    for g, graph in enumerate(graph_list):
        for dist in distance_list[g]:
            iteration_list.append(f'{graph}_{dist}')
    for algo in algo_list:
        for l, layout in enumerate(layout_names):
            save_path = rf'./graph_figures/figures/{algo}/driving_time_pro_amr_{algo}_{layout}_graphs.png'
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(save_path):
                continue
            # Only graph variation
            df = deepcopy(data_base[l])
            df = df[df['Path Planning Algorithm'] == algo]
            create_sum_of_costs_pro_amr_figure_graph(df, algo, layout, iteration_list, save_path, save, show_figures)

    for algo in algo_list:
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{algo}/driving_time_pro_amr_{algo}_{graph}_{dist}_layouts.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = pd.DataFrame()
                iteration_list = []
                for f, folder in enumerate(folder_list):
                    iteration_list.append(folder_list[f])
                    df_add = deepcopy(data_base[f])
                    df_add = df_add[df_add['Path Planning Algorithm'] == algo]
                    df_add = df_add[df_add['Graph'] == f'{graph}_{dist}']
                    df = pd.concat([df, deepcopy(df_add)], ignore_index=True)
                create_sum_of_costs_pro_amr_figure_layout(df, algo, f'{graph}_{dist}', iteration_list,
                                                          save_path, save, show_figures)

    iteration_list = []
    for algo in algo_list:
        iteration_list.append(algo)

    for f, folder in enumerate(folder_list):
        for g, graph in enumerate(graph_list):
            for dist in distance_list[g]:
                save_path = rf'./graph_figures/figures/{graph}/driving_time_pro_amr_{graph}_{dist}_{layout_names[f]}_algorithm.png'
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                if os.path.exists(save_path):
                    continue
                df = deepcopy(data_base[f])
                df = df[df['Graph'] == f'{graph}_{dist}']
                create_driving_time_pro_amr_figure_algorithm(df, f'{graph}_{dist}', layout_names[f],
                                                             iteration_list, save_path, save, show_figures)
    logger.info('Driving time pro AMR figures finish created for all selected data!')
    return


def plot_heatmap_scalability_and_robustness_analysis(data_base, save: bool, show_figures: bool):
    save_path = rf'./heatmap_figures/figures/heatmap_functional_analysis_graph_layout'
    create_functional_heatmap_graph_layout_abs(data_base, save_path, save, show_figures)
    save_path = rf'./heatmap_figures/figures/heatmap_functional_analysis_amrs_tfs'
    create_functional_heatmap_amrs_tfs_abs(data_base, save_path, save, show_figures)
    save_path = rf'./heatmap_figures/figures/heatmap_functional_analysis_amrs_algo'
    create_functional_heatmap_amrs_algo_abs(data_base, save_path, save, show_figures)
    save_path = rf'./heatmap_figures/figures/heatmap_functional_analysis_graph_algo'
    create_functional_heatmap_graph_algo_abs(data_base, save_path, save, show_figures)
    logger.info('All heatmap figures for functional analysis to show performance overview finish created!')
    return


def plot_heatmap_layout_graph_correlations(data_base, layout_names, graph_list, distance_list,
                                           save: bool, show_figures: bool):
    save_path = rf'./heatmap_figures/figures/heatmap_graph_layout'
    create_correlation_heatmap_graph_layout(data_base, layout_names, graph_list, distance_list,
                                            save_path, save, show_figures)
    create_correlation_heatmap_graph_layout_abs(data_base, layout_names, graph_list, distance_list,
                                                save_path, save, show_figures)
    logger.info('Correlation layout graph algorithm figures finish created for all selected data!')
    return


def plot_heatmap_layout_algo_correlations(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                          save: bool, show_figures: bool):
    save_path = rf'./heatmap_figures/figures/heatmap_layout_algorithm'
    create_correlation_heatmap_layout_algorithm(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                                save_path, save, show_figures)
    create_correlation_heatmap_layout_algorithm_abs(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                                    save_path, save, show_figures)
    logger.info('Correlation heatmap layout algorithm figures finish created for all selected data!')
    return


def plot_heatmap_graph_algo_correlations(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                         save: bool, show_figures: bool):
    save_path = rf'./heatmap_figures/figures/heatmap_graph_algorithm'
    create_correlation_heatmap_graph_algorithm(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                               save_path, save, show_figures)
    create_correlation_heatmap_graph_algorithm_abs(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                                   save_path, save, show_figures)
    logger.info('Correlation heatmap graph algorithm figures finish created for all selected data!')
    return


def plot_feature_importance_figure_graph_properties(data_base, graph_file_list, layout_names, graph_list,
                                                    distance_list, save: bool, show_figures: bool):

    save_path = rf'./layout_data/figures/graphs/feature_importance_graph'
    create_feature_importance_figure_graph_properties(data_base, graph_file_list, layout_names, graph_list,
                                                      distance_list,  save_path, save, show_figures)
    logger.info('Feature importance graph properties correlation figures finish created for all selected data!')
    return


def plot_feature_importance_figure_graph_properties_shap(data_base, algo_list, layout_names, graph_list, graph_file_list,
                                                         distance_list, save: bool, show_figures: bool):
    tf_list = [1, 2, 5, 10]
    amr_list = [10, 20, 30, 40, 50]
    save_file = rf'./layout_data/figures/mapd_feature_importance/shap_total_'
    create_feature_mapd_interaction_effects_shap(data_base, layout_names, graph_list, distance_list, algo_list, tf_list,
                                                 amr_list, save_file, save, show_figures)
    create_feature_mapd_interaction_effects_shap_pro_layout_advanced(data_base, layout_names, graph_list, distance_list,
                                                            algo_list, tf_list, amr_list, save_file, save, show_figures)

    for algo in algo_list:
        save_path = rf'./layout_data/figures/graphs/feature_importance_graph_grouped_amr'
        create_feature_importance_figure_amr_grouped_graph_properties(data_base, graph_file_list, layout_names,
                                                                      graph_list, distance_list, algo, save_path,
                                                                      save, show_figures)
    logger.info('Feature importance graph properties correlation figures finish created for all selected data!')
    return


def plot_feature_scatter_plot_graph_properties(data_base, graph_file_list, layout_names, graph_list,
                                               distance_list, algo_list, save: bool, show_figures: bool):
    for algo in algo_list:
        save_path = rf'./layout_data/figures/graphs/scatter_plot_graph_property_{algo}'
        create_feature_scatter_plot_trends_graph_properties(data_base, layout_names, graph_file_list, graph_list,
                                                            distance_list, algo, save_path, save, show_figures)
    logger.info('Scatter plot graph properties correlation figures finish created for all selected data!')
    return


def plot_graph_density_map(folder_list, layout_names, graph_list, distance_list, number_of_amrs, tf_list,
                           number_of_orders, algo_list, layout_image_path_list, layout_size_list, save: bool,
                           show_figures: bool):
    for f, folder in enumerate(folder_list):  # Iteration over layouts
        for g, graph in enumerate(graph_list):
            for distance in distance_list[g]:
                for n_amr in number_of_amrs:
                    for tf in tf_list:
                        for algo in algo_list:
                            file = (rf'{config.REMOTE_MAPD_SCENARIO_FOLDER_PATH}{folder}/output/graph_data/{folder}'
                                    rf'_{graph}_{distance}_AMR_{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_graph_data.csv')
                            save_file = (rf'./layout_graph_figures/figures/{folder}/Density_graph_map_{folder}_{graph}_{distance}_AMR_'
                                         rf'{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_figure.png')
                            Path(save_file).parent.mkdir(parents=True, exist_ok=True)
                            if os.path.exists(save_file):
                                continue
                            try:
                                df = get_graph_data_from_server(file)
                                algo_name = algo.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()
                                title_name = (layout_names[f].replace('_', ' ').capitalize() + ' ' +
                                              graph.capitalize() + ' ' + str(distance) +
                                              f' meter graph traffic density map with {n_amr} AMRs {algo_name}')
                                lif_file = rf'./order_evaluation/lif_files/LIF_{layout_names[f]}_dist_{distance}_{graph}.json'
                                create_graph_density_figure(df, title_name, save_file, layout_image_path_list[f],
                                                            layout_size_list[f], lif_file, save, show_figures)
                            except Exception as e:
                                logger.info(f'Plot figure graph density map failed for {file}', e)


def plot_graph_density_map_order(folder_list, layout_names, graph_list, distance_list, number_of_amrs, tf_list,
                                 number_of_orders, algo_list, layout_image_path_list, layout_size_list, save: bool,
                                 show_figures: bool):
    for f, folder in enumerate(folder_list):  # Iteration over layouts
        for g, graph in enumerate(graph_list):
            for distance in distance_list[g]:
                for n_amr in number_of_amrs:
                    for tf in tf_list:
                        for algo in algo_list:
                            file = (
                                rf'{config.REMOTE_MAPD_SCENARIO_FOLDER_PATH}{folder}/output/graph_data/{folder}'
                                rf'_{graph}_{distance}_AMR_{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_graph_data.csv')
                            save_file = (
                                rf'./layout_graph_figures/figures/{folder}/Density_graph_order_map_{folder}_{graph}_{distance}_AMR_'
                                rf'{n_amr}_TF_{tf}_Orders_{number_of_orders}_{algo}_figure.png')
                            Path(save_file).parent.mkdir(parents=True, exist_ok=True)
                            if os.path.exists(save_file):
                                continue
                            try:
                                df = get_graph_data_from_server(file)
                                algo_name = algo.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()
                                title_name = (layout_names[f].replace('_',' ').capitalize() + ' ' + graph.capitalize()
                                              + ' ' + str(distance) +
                                              f' meter graph density map with {n_amr} AMRs {algo_name} {tf} TF')
                                lif_file = rf'./order_evaluation/lif_files/LIF_{layout_names[f]}_dist_{distance}_{graph}.json'
                                order_file = f'./order_evaluation/order_files/orders_scenario_{layout_names[f]}_{graph}_{distance}_200_fq_1.json'
                                create_graph_density_order_figure(df, title_name, save_file, layout_image_path_list[f],
                                                                  layout_size_list[f], lif_file, order_file, save,
                                                                  show_figures)
                            except Exception as e:
                                logger.info(f'Plot figure graph density map failed for {file}', e)
    logger.info('AMR graph density map figures finish created for all selected data!')
    return


def get_graph_data_from_server(file: str):
    host = config.HOST
    port = config.PORT
    username = config.USER_NAME
    password = config.PASSWORD

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)
    sftp = ssh.open_sftp()
    with sftp.file(file, "r") as f:
        csv_content = f.read().decode()
        df = pd.read_csv(StringIO(csv_content), sep=';', decimal=',')
        sftp.close()
        ssh.close()
    return df


def get_amr_data_from_server(file: str):
    host = config.HOST
    port = config.PORT
    username = config.USER_NAME
    password = config.PASSWORD

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=username, password=password)
    sftp = ssh.open_sftp()
    with sftp.file(file, "r") as f:
        csv_content = f.read().decode()
        df = pd.read_csv(StringIO(csv_content), sep=';', decimal=',')
        sftp.close()
        ssh.close()
    return df


def connect(folder_list: List[str]):
    data = []
    host = config.HOST
    port = config.PORT
    username = config.USER_NAME
    password = config.PASSWORD
    remote_path = config.REMOTE_MAPD_SCENARIO_FOLDER_PATH
    additional_path = config.FILE_NAME_END_RESULTS
    for f, folder in enumerate(folder_list):
        path = remote_path + folder + "/output/" + folder + additional_path
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=username, password=password)
        sftp = ssh.open_sftp()
        with sftp.file(path, "r") as f:
            csv_content = f.read().decode()
        df = pd.read_csv(StringIO(csv_content), sep=';', decimal=',')  # CSV in DataFrame laden
        data.append(df)
        sftp.close()
        ssh.close()
    return data


if __name__ == '__main__':
    visualization_pipeline(create_figures=True)
