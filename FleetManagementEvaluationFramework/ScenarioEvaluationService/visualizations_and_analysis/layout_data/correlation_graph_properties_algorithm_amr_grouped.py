import logging
from copy import deepcopy
from pathlib import Path
import config.config_file

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import cm
from matplotlib.patches import Patch

from order_evaluation.order_evaluation_script import compute_detour

matplotlib.use("TkAgg")

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def create_feature_importance_figure_amr_grouped_graph_properties(data_base, graph_file_list, layout_names, graph_list,
                                                                  distance_list, algorithm, save_path, save=False,
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
    data_num_amrs = []
    data_generated_nodes = []
    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                df = deepcopy(data)
                filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                # filtered_data = filtered_data[filtered_data['Path Planning Algorithm'] == algorithm]
                data_layout += [layout_names[d].replace('_', ' ').upper()] * len(filtered_data)
                data_graph += [f'{graph} {dist} m'] * len(filtered_data)
                data_makespan += filtered_data['Makespan [s]'].tolist()
                data_computational_time += filtered_data['Path Planning time'].tolist()
                data_loaded_driving_time += (filtered_data['Loaded Driving Time'] / filtered_data['Driving Time']).tolist()
                data_unloaded_driving_time += (filtered_data['Empty Driving Time']/ filtered_data['Driving Time']).tolist()
                data_num_amrs += filtered_data['Number AMR'].tolist()
                data_generated_nodes += filtered_data['Generated nodes cbs'].tolist()
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
        'Number of AMRs': data_num_amrs,
        'Makespan': data_makespan,
        'Computational time': data_computational_time,
        'Rel. driving time loaded driving': data_loaded_driving_time,
        'Rel. driving time unloaded driving': data_unloaded_driving_time,
        'Detour time': data_detour,
        'Generated nodes': data_generated_nodes
    })

    df_heatmap['Makespan'] = df_heatmap['Makespan'] * (-1)
    df_heatmap['Computational time'] = df_heatmap['Computational time'] * (-1)
    df_heatmap['Rel. driving time loaded driving'] = df_heatmap['Rel. driving time loaded driving']
    df_heatmap['Rel. driving time unloaded driving'] = df_heatmap['Rel. driving time unloaded driving'] * (-1)
    df_heatmap['Detour time'] = df_heatmap['Detour time'] * (-1)
    df_heatmap['Generated nodes'] = df_heatmap['Generated nodes'] * (-1)

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

    metrics = ['Makespan', 'Computational time', 'Rel. driving time loaded driving', 'Rel. driving time unloaded driving',
               'Detour time', 'Generated nodes']
    amr_values = [10, 20, 30, 40, 50]

    for metric in metrics:
        corr_dict = {}
        for amr in amr_values:
            df_amr = df_corr[df_corr['Number of AMRs'] == amr]
            corr_dict[amr] = df_amr[graph_features + [metric]].corr()[metric].drop(metric)

        df_corr_features = pd.DataFrame(corr_dict)
        # sort features depending on average correlation
        features_sorted = df_corr_features.mean(axis=1).sort_values().index
        df_corr_features = df_corr_features.loc[features_sorted]

        cmap = cm.get_cmap("tab20")
        colors = [cmap(i) for i in range(df_corr_features.shape[1])]

        fig, ax = plt.subplots(figsize=(14, 8))
        legend_handles = [
            Patch(facecolor=colors[i], edgecolor='black', label=f'{amr} AMRs')
            for i, amr in enumerate(df_corr_features.columns)
        ]

        ax.legend(handles=legend_handles, title="Number of AMRs", fontsize=14, title_fontsize=14, loc="lower right")
        bar_height = 0.8

        for idx, feature in enumerate(features_sorted):
            corrs = df_corr_features.loc[feature]
            neg_amrs = corrs[corrs < 0].sort_values()
            pos_amrs = corrs[corrs >= 0].sort_values()

            left_neg = 0
            for amr, val in neg_amrs.items():
                color = colors[df_corr_features.columns.get_loc(amr)]
                ax.barh(idx, val-left_neg, height=bar_height, left=left_neg, color=color, edgecolor='black',
                        align='center')
                left_neg += val-left_neg

            left_pos = 0
            for amr, val in pos_amrs.items():
                color = colors[df_corr_features.columns.get_loc(amr)]
                ax.barh(idx, val-left_pos, height=bar_height, left=left_pos, color=color, edgecolor='black',
                        align='center')
                left_pos += val-left_pos

        plt.xlabel(f'Correlation (<0: {metric} increasing , >0 = {metric} decreasing)', fontsize=12,
                   fontweight='bold')
        plt.ylabel('Graph Properties', fontsize=14, fontweight='bold')
        plt.xticks(fontsize=14)
        ax.set_yticks(range(len(features_sorted)))
        ax.set_yticklabels(features_sorted)
        plt.yticks(fontsize=14)
        ax.set_ylabel('Graph Properties', fontsize=14, fontweight='bold')
        ax.axvline(0, color='black', linewidth=1)
        plt.title(f'Feature Importance for {metric}', fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save:
            Path(f'{save_path}_{metric}.png').parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(f'{save_path}_{metric}.png', dpi=300)
        if show_figure:
            plt.show()

