import logging
from copy import deepcopy
from pathlib import Path
import config.config_file

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

from order_evaluation.order_evaluation_script import compute_detour

matplotlib.use("TkAgg")

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def create_feature_importance_figure_graph_properties(data_base, graph_file_list, layout_names, graph_list,
                                                      distance_list, save_path, save=False,
                                                      show_figure=True):
    graph_props_list = []
    for file in graph_file_list:
        df_graph_props = pd.read_csv(file, sep=';', decimal=',')
        graph_props_list.append(df_graph_props)

    df_graph_props_all = pd.concat(graph_props_list, ignore_index=True)
    df_graph_props_all['Graph'] = df_graph_props_all['Graph'].str.replace(r'.*_(grid|triangle|hexagonal)_', r'\1_',
                                                                          regex=True).str.replace('_', ' ') + ' m'

    # Renaming columns
    df_graph_props_all.rename(columns={'Edge distance': 'Edge length'}, inplace=True)
    df_graph_props_all.rename(columns={'Density': 'Density graph'}, inplace=True)
    df_graph_props_all.rename(columns={'Mean degree': 'Mean node degree'}, inplace=True)
    df_graph_props_all.rename(columns={'diameter': 'Diameter graph'}, inplace=True)
    df_graph_props_all.rename(columns={'degree_centrality': 'Avg. degree centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'bet_centrality': 'Avg. betweenness centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'close_centrality': 'Avg. closeness centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'clustering': 'Avg. clustering coefficient'}, inplace=True)

    data_layout = []
    data_graph = []
    data_makespan = []
    data_computational_time = []
    data_loaded_driving_time = []
    data_unloaded_driving_time = []
    data_detour = []
    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                df = deepcopy(data)
                filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                data_layout += [layout_names[d].replace('_', ' ').upper()] * len(filtered_data)
                data_graph += [f'{graph} {dist} m'] * len(filtered_data)
                data_makespan += filtered_data['Makespan [s]'].tolist()
                data_computational_time += filtered_data['Path Planning time'].tolist()
                data_loaded_driving_time += (filtered_data['Loaded Driving Time'] / filtered_data['Driving Time']).tolist()
                data_unloaded_driving_time += (filtered_data['Empty Driving Time']/ filtered_data['Driving Time']).tolist()
                try:
                    new_detour_data = compute_detour(layout_names[d], graph, dist,
                                                     filtered_data['Loaded Driving Time'].tolist())
                    data_detour += new_detour_data
                except Exception as e:
                    logger.info(f'Error: {e}')
                    continue

    df_heatmap = pd.DataFrame({
        'Layout': data_layout,
        'Graph': data_graph,
        'Makespan': data_makespan,
        'Computational time': data_computational_time,
        'Rel. driving time loaded driving': data_loaded_driving_time,
        'Rel. driving time unloaded driving': data_unloaded_driving_time,  # z. B. aus CSV
        'Detour time': data_detour
    })

    df_heatmap['Makespan'] = df_heatmap['Makespan'] * (-1)
    df_heatmap['Computational time'] = df_heatmap['Computational time'] * (-1)
    df_heatmap['Rel. driving time loaded driving'] = df_heatmap['Rel. driving time loaded driving']
    df_heatmap['Rel. driving time unloaded driving'] = df_heatmap['Rel. driving time unloaded driving'] * (-1)
    df_heatmap['Detour time'] = df_heatmap['Detour time'] * (-1)

    df_merged_graph = pd.merge(df_heatmap, df_graph_props_all, on='Graph')

    graph_features = [
        'Number of nodes', 'Number of edges', 'Edge length', 'Density graph', 'Mean node degree',
        'Avg. degree centrality', 'Avg. betweenness centrality',
        'Avg. closeness centrality', 'Avg. clustering coefficient', 'Diameter graph', 'Avg. shortest path length'
    ]

    df_corr = df_merged_graph.copy()
    df_corr['Graph_num'] = df_corr['Graph'].replace({
        'grid 1 m': 0, 'grid 0.5 m': 1,
        'triangle 1 m': 2, 'triangle 0.5 m': 3,
        'hexagonal 0.5 m': 4
    })

    metrics = ['Makespan', 'Computational time', 'Rel. driving time loaded driving',
               'Rel. driving time unloaded driving', 'Detour time']

    corr_matrices = {}
    for metric in metrics:
        corr_matrices[metric] = df_merged_graph[graph_features + [metric]].corr()[metric].drop(metric)

    for metric in metrics:
        corr_vals = corr_matrices[metric].sort_values(ascending=False)
        plt.figure(figsize=(14, 6))
        sns.barplot(x=corr_vals.values, y=corr_vals.index, palette='coolwarm', orient='h')
        plt.title(f'Feature Importance for {metric}', fontsize=16, fontweight='bold')
        plt.xlabel(f'Correlation (<0: {metric} increasing , >0 = {metric} decreasing)', fontsize=12, fontweight='bold')
        plt.ylabel('Graph Properties', fontsize=12, fontweight='bold')
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.axvline(0, color='black', linewidth=0.8)
        plt.tight_layout()
        if save:
            Path(rf'{save_path}_{metric}.png').parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(rf'{save_path}_{metric}.png', dpi=300)
        if show_figure:
            plt.show()

    return

