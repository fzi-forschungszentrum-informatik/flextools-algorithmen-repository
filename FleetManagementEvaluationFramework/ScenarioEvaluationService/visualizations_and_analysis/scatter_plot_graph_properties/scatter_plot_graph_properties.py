import logging
from copy import deepcopy
from pathlib import Path
import config.config_file

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import matplotlib
from matplotlib.lines import Line2D

from order_evaluation.order_evaluation_script import compute_detour


matplotlib.use("TkAgg")

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def create_feature_scatter_plot_trends_graph_properties(data_base, layout_names, graph_file_list, graph_list,
                                                        distance_list, algorithm, save_path, save=False,
                                                        show_figure=True):
    metric_list = ['Makespan', 'Rel. service time empty driving', 'Rel. service time loaded driving',
                   'Detour time']
    graph_property_list = ['Number of nodes', 'Number of edges', 'Edge length', 'Avg. clustering coefficient',
                           'Mean node degree', 'Avg. betweenness centrality']

    graph_props_list = []

    for file in graph_file_list:
        df_graph_props = pd.read_csv(file, sep=';', decimal=',')
        graph_props_list.append(df_graph_props)

    df_graph_props_all = pd.concat(graph_props_list, ignore_index=True)

    # Renaming columns
    df_graph_props_all.rename(columns={'Edge distance': 'Edge length'}, inplace=True)
    df_graph_props_all.rename(columns={'Density': 'Density graph'}, inplace=True)
    df_graph_props_all.rename(columns={'Mean degree': 'Mean node degree'}, inplace=True)
    df_graph_props_all.rename(columns={'diameter': 'Diameter graph'}, inplace=True)
    df_graph_props_all.rename(columns={'degree_centrality': 'Avg. degree centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'bet_centrality': 'Avg. betweenness centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'close_centrality': 'Avg. closeness centrality'}, inplace=True)
    df_graph_props_all.rename(columns={'clustering': 'Avg. clustering coefficient'}, inplace=True)

    df = pd.concat(data_base, ignore_index=True)

    df['Layout'] = df['Layout'].replace({
        'Matrix_22x22': 'matrix_22x22',
        'Warehouse_35x21': 'warehouse_35x21',
        "Grid_35x21_not_well_formed": 'space_35x21'
    })

    data_layout = []
    data_graph = []
    data_makespan = []
    data_computational_time = []
    data_loaded_service_time = []
    data_unloaded_service_time = []
    data_detour = []
    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                df = deepcopy(data)
                filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                filtered_data = filtered_data[filtered_data['Path Planning Algorithm'] == algorithm]
                data_layout += [layout_names[d]] * len(filtered_data)
                data_graph += [f'{graph}_{dist}'] * len(filtered_data)
                data_makespan += filtered_data['Makespan [s]'].tolist()
                data_computational_time += filtered_data['Path Planning time'].tolist()
                data_loaded_service_time += (
                            filtered_data['Loaded Driving Time'] / filtered_data['Driving Time']).tolist()
                data_unloaded_service_time += (
                            filtered_data['Empty Driving Time'] / filtered_data['Driving Time']).tolist()
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
        'Rel. driving time loaded driving': data_loaded_service_time,
        'Rel. driving time empty driving': data_unloaded_service_time,  # z. B. aus CSV
        'Detour time': data_detour
    })

    for graph_prop in graph_property_list:
        for metric in metric_list:
            df_grouped = df_heatmap.groupby(['Layout', 'Graph']).agg(
                Metric_mean=(metric, 'mean'),
                Metric_std=(metric, 'std'),
                PP_time_mean=('Computational time', 'mean')
            ).reset_index()

            df_grouped['merge_name'] = df_grouped['Layout'] + '_' + df_grouped['Graph']
            df_graph_props_all.rename(columns={'Graph': 'merge_name'}, inplace=True)

            df = df_grouped.merge(df_graph_props_all, on="merge_name", how="left")

            fig, ax = plt.subplots(figsize=(12, 7))

            layout_colors = {
                "Warehouse 35x21": "tab:blue",
                "Space 35x21": "tab:green",
                "Matrix 22x22": "tab:red",
                "Matrix 33x33": "tab:orange"
            }

            graph_markers = {
                "Grid 1": "o",
                "Triangle 1": "s",
                "Grid 0.5": "H",
                "Triangle 0.5": "D",
                "Hexagonal 0.5": "P"
            }

            df['Graph'] = df['Graph'].str.replace('_', ' ').str.capitalize()
            df['Layout'] = df['Layout'].str.replace('_', ' ').str.capitalize()

            for _, row in df.iterrows():
                graph_type = row["Graph"]
                ax.scatter(
                    row[graph_prop],
                    row['Metric_mean'],
                    color=layout_colors[row["Layout"]],
                    marker=graph_markers.get(graph_type, "o"),
                    s=40 + row["PP_time_mean"] * 0.5,  # Size = computation time
                    alpha=0.8,
                    edgecolor="k",
                    linewidth=0.4
                )
                # --- Legend: Layout (colors) ---

            layout_handles = [
                mpatches.Patch(color=col, label=lay)
                for lay, col in layout_colors.items()
                if lay in df["Layout"].unique()
            ]
            leg1 = ax.legend(handles=layout_handles, title="Layout", loc="upper right",
                             bbox_to_anchor=(1.3, 1), borderaxespad=0)
            leg1.get_title().set_fontweight('bold')
            ax.add_artist(leg1)

            # --- Legend: Graph shapes ---
            marker_handles = [
                plt.Line2D([0], [0],
                           marker=mk, color='gray', linestyle="",
                           markersize=10, label=gtype)
                for gtype, mk in graph_markers.items()
            ]
            leg2 = ax.legend(handles=marker_handles, title="Graph type", loc="lower right",
                             bbox_to_anchor=(1.3, 0.57), borderaxespad=0)
            leg2.get_title().set_fontweight('bold')
            ax.add_artist(leg2)
            leg3 = ax.legend(
                handles=[Line2D([0], [0], color='none', label='Marker Size ∝ Computational Time')],
                title="Computational Time",
                loc="center right",
                bbox_to_anchor=(1.31, 0.52)
            )

            leg3.get_title().set_fontweight("bold")
            #ax.add_artist(leg3)
            # --- Labels ---
            ax.set_xlabel(graph_prop, fontsize=16)
            if metric == 'Makespan' or metric == 'Detour time':
                metric_name =f'{metric} [ZE]'
            else:
                metric_name = metric
            ax.set_ylabel(metric_name, fontsize=16)
            ax.tick_params(axis='y', labelcolor='black', labelsize=16)
            ax.tick_params(axis='x', labelcolor='black', labelsize=16)
            ax.set_title(
                f"{metric} vs. Graph Property ({graph_prop})",
                fontsize=18, fontweight='bold'
            )

            ax.grid(True, linestyle="--", alpha=0.3)

            plt.tight_layout()
            if save:
                save_file = save_path + f'_{metric}_{graph_prop}.png'
                Path(save_file).parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(save_file, dpi=300)
            if show_figure:
                plt.show()



