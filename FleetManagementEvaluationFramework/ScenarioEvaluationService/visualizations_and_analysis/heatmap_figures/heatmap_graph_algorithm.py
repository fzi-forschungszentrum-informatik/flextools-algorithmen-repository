import os
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import seaborn as sns

import matplotlib.pyplot as plt

from order_evaluation.order_evaluation_script import compute_detour

matplotlib.use("TkAgg")


def create_correlation_heatmap_graph_algorithm(data_base, layout_names, graph_list, distance_list, algorithm_list,
                                                save_path, save=False, show_figures=True):
    metric_list = ['Makespan [s]',  'Rel. Empty Driving Time', 'Rel. Loaded Driving Time',
                   'Path Planning time', 'Detour']
    for m, metric in enumerate(metric_list):
        metric_name = metric.replace('[s]', '').replace(' ', '')
        algo_name_list = []
        graph_label_list = []
        cost_list = []
        for d, data in enumerate(data_base):
            for j, graph in enumerate(graph_list):
                for k, dist in enumerate(distance_list[j]):
                    for j, algo in enumerate(algorithm_list):
                        df = deepcopy(data)
                        df_new = df[df['Graph'] == f'{graph}_{dist}']
                        df_new = df_new[df_new['Path Planning Algorithm'] == algo]
                        if df_new.empty:
                            continue
                        graph_label_list += [f'{graph.capitalize()} {dist}m'] * len(df_new)
                        algo_name_list += [algo.replace('cbs_1.0', 'CBS').replace('_', ' ').capitalize()] * len(df_new)
                        if metric == 'Detour':
                            try:
                                driving_time_without_collision = compute_detour(layout_names[d], graph, dist, None)
                            except:
                                continue
                            df_new['Detour'] = (df_new["Loaded Driving Time"] - driving_time_without_collision)
                        elif metric == 'Rel. Empty Driving Time':
                            df_new['Rel. Empty Driving Time'] = (df_new["Empty Driving Time"] /
                                                                         df_new['Driving Time'])
                        elif metric == 'Rel. Loaded Driving Time':
                            df_new['Rel. Loaded Driving Time'] = (df_new["Loaded Driving Time"] /
                                                                          df_new['Driving Time'])
                        cost_list += df_new[metric].tolist()

        df_heatmap = pd.DataFrame({
            'Graph': graph_label_list,
            'Algo': algo_name_list,
            'Costs': cost_list
        })

        heatmap_data = df_heatmap.pivot_table(
            index='Graph', columns='Algo', values='Costs', aggfunc='mean'
        )
        data_values = heatmap_data.values
        min_val = np.nanmin(data_values)
        max_val = np.nanmax(data_values)

        normalized = (data_values - min_val) / (max_val - min_val)
        if metric != 'Rel. Loaded Driving Time':
            heatmap_normalized = 1 - pd.DataFrame(normalized, index=heatmap_data.index, columns=heatmap_data.columns)
        else:
            heatmap_normalized = pd.DataFrame(normalized, index=heatmap_data.index, columns=heatmap_data.columns)

        plt.figure(figsize=(8, 6))
        sns.heatmap(
            heatmap_normalized, annot=True, fmt=".2f",
            cmap="plasma", cbar=True, linecolor='gray', linewidths=0.5, mask=heatmap_normalized.isna()
        )
        plt.title(f"Normalized {metric}", fontsize=16, fontweight='bold')
        plt.xlabel("Algorithm", fontsize=16)
        plt.xticks(fontsize=12)
        plt.ylabel("Graph", fontsize=16)
        plt.yticks(fontsize=11)
        plt.tight_layout()
        if save:
            file_name_figure = rf'{save_path}_{metric_name}.png'
            Path(file_name_figure).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(file_name_figure):
                continue
            plt.savefig(file_name_figure, dpi=300)
        if show_figures:
            plt.show()
        plt.close()
    return


