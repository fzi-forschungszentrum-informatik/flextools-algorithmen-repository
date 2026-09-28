import os
from copy import deepcopy
from pathlib import Path

import pandas as pd
import matplotlib
import seaborn as sns

import matplotlib.pyplot as plt

from order_evaluation.order_evaluation_script import compute_detour

matplotlib.use("TkAgg")


def create_correlation_heatmap_graph_layout_abs(data_base, layout_names, graph_list, distance_list,
                                                save_path, save=False, show_figures=True):
    metric_list = ['Makespan [s]', 'Rel. Empty Driving Time', 'Rel. Loaded Driving Time',
                   'Path Planning time', 'Detour']  # create figure for each metric
    c_map = ['plasma_r', 'plasma_r', 'plasma', 'plasma_r', 'plasma_r']
    for m, metric in enumerate(metric_list):
        metric_name = metric.replace('[s]', '').replace(' ', '')
        layout_list = []
        graph_label_list = []
        cost_list = []
        for d, data in enumerate(data_base):
            for j, graph in enumerate(graph_list):
                for k, dist in enumerate(distance_list[j]):
                    df = deepcopy(data)
                    df_new = df[df['Graph'] == f'{graph}_{dist}']
                    if df_new.empty:
                        continue
                    layout_list += [layout_names[d].replace('_', ' ').capitalize()] * len(df_new)
                    graph_label_list += [f'{graph.capitalize()} {dist}m'] * len(df_new)
                    if metric == 'Detour':
                        try:
                            driving_time_without_collision = compute_detour(layout_names[d], graph, dist, None)
                        except:
                            continue
                        df_new['Detour'] = (df_new["Loaded Driving Time"] - driving_time_without_collision)
                    elif metric == 'Rel. Empty Driving Time':
                        df_new['Rel. Empty Driving Time'] = df_new["Empty Driving Time"] / df_new[
                            'Driving Time']
                    elif metric == 'Rel. Loaded Driving Time':
                        df_new['Rel. Loaded Driving Time'] = df_new["Loaded Driving Time"] / df_new[
                            'Driving Time']
                    cost_list += df_new[metric].tolist()

        df_heatmap = pd.DataFrame({
            'Layout': layout_list,
            'Graph': graph_label_list,
            'Costs': cost_list
        })

        heatmap_data = df_heatmap.pivot_table(
            index='Layout', columns='Graph', values='Costs', aggfunc='mean'
        )

        plt.figure(figsize=(12, 6))
        sns.heatmap(
            heatmap_data, annot=True, fmt=".2f",
            cmap=c_map[m], cbar=True, linecolor='gray', linewidths=0.5, mask=heatmap_data.isna()
        )
        plt.title(f"Absolute {metric}", fontsize=16, fontweight='bold')
        plt.xlabel("Graph", fontsize=16)
        plt.xticks(fontsize=12)
        plt.ylabel("Layout", fontsize=16)
        plt.yticks(fontsize=12, rotation=0)
        plt.tight_layout()
        if save:
            file_name_figure = rf'{save_path}_{metric_name}_abs.png'
            Path(file_name_figure).parent.mkdir(parents=True, exist_ok=True)
            if os.path.exists(file_name_figure):
                continue
            plt.savefig(file_name_figure, dpi=300)
        if show_figures:
            plt.show()
        plt.close()
    return




