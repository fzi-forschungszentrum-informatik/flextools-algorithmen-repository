import logging
from copy import deepcopy
from pathlib import Path
import config.config_file
import numpy as np
import pandas as pd
import shap
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from sklearn.ensemble import RandomForestRegressor

from order_evaluation.order_evaluation_script import compute_detour

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def create_feature_mapd_interaction_effects_shap(data_base, layout_names, graph_list, distance_list,
                                                 algorithm_list, tf_list, number_of_amr_list, save_file,
                                                 save=False, show_figure=True):
    data_layout = []
    data_graph = []
    data_makespan = []
    data_computational_time = []
    data_loaded_driving_time = []
    data_unloaded_driving_time = []
    data_detour = []
    data_num_amrs = []
    data_generated_nodes = []
    data_task_frequency = []
    data_algorithm = []

    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                for algo in algorithm_list:
                    for tf in tf_list:
                        for n_amr in number_of_amr_list:
                            df = deepcopy(data)
                            filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                            filtered_data = filtered_data[
                                                (filtered_data['Path Planning Algorithm'] == algo) &
                                                (filtered_data['Task Frequency'] == tf) &
                                                (filtered_data['Number AMR'] == n_amr)]
                            n = len(filtered_data)
                            if n == 0:
                                continue

                            data_layout += [layout_names[d].replace('_', ' ').upper()] * n
                            data_graph += [f'{graph} {dist} m'] * n
                            data_algorithm += [algo] * n
                            data_makespan += filtered_data['Makespan [s]'].tolist()
                            data_computational_time += filtered_data['Path Planning time'].tolist()
                            data_loaded_driving_time += (
                                        filtered_data['Loaded Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_unloaded_driving_time += (
                                        filtered_data['Empty Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_num_amrs += filtered_data['Number AMR'].tolist()
                            data_generated_nodes += filtered_data['Generated nodes cbs'].tolist()
                            data_task_frequency += filtered_data['Task Frequency'].tolist()
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
        'Task Frequency': data_task_frequency,
        'Algorithm': data_algorithm,
        'Makespan': data_makespan,
        'Computational time': data_computational_time,
        'Rel. Loaded Driving Time': data_loaded_driving_time,
        'Rel. Empty Driving Time': data_unloaded_driving_time,
        'Detour time': data_detour,
        'Generated nodes': data_generated_nodes
    })

    targets = ['Makespan', 'Computational time', 'Detour time']

    target_map = {
        "Makespan": "Makespan",
        "Computational time": "Computational time",
        "Detour time": "Detour time"
    }
    for target in targets:
        if target not in target_map:
            raise ValueError(f"Unknown target: {target}")

        y = df_heatmap[target_map[target]]

        x = pd.get_dummies(
            df_heatmap[['Graph', 'Algorithm']],
            columns=['Graph', 'Algorithm'],
            drop_first=True
        )
        x['Number of AMRs'] = df_heatmap['Number of AMRs'].values
        x['Task Frequency'] = df_heatmap['Task Frequency'].values

        model = RandomForestRegressor(n_estimators=300, random_state=42)
        model.fit(x, y)

        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(x)
        interaction_values = explainer.shap_interaction_values(x)

        shap_values = np.array(shap_values)
        interaction_values = np.array(interaction_values)

        feature_names = x.columns

        group_map = {
            "Graph": [i for i, col in enumerate(feature_names) if col.startswith("Graph_")],
            "Algorithm": [i for i, col in enumerate(feature_names) if col.startswith("Algorithm_")],
            "Number of AMRs": [i for i, col in enumerate(feature_names) if col == "Number of AMRs"],
            "Task Frequency": [i for i, col in enumerate(feature_names) if col == "Task Frequency"]
        }

        main_effects = {}
        for name, idxs in group_map.items():
            if len(idxs) == 0:
                main_effects[name] = np.zeros(shap_values.shape[0])
            else:
                main_effects[name] = np.sum(np.abs(shap_values[:, idxs]), axis=1)

        interaction_effects = {}

        group_names = list(group_map.keys())

        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                g1 = group_names[i]
                g2 = group_names[j]

                idxs_1 = group_map[g1]
                idxs_2 = group_map[g2]

                interaction_effects[f"{g1} × {g2}"] = np.sum(
                    np.abs(interaction_values[:, idxs_1][:, :, idxs_2]),
                    axis=(1, 2)
                )

        combined_df = pd.DataFrame({**main_effects, **interaction_effects})

        mean_abs = combined_df.abs().mean(axis=0)
        percent_importance = 100 * mean_abs / mean_abs.sum()

        percent_df = pd.DataFrame({"Feature": percent_importance.index, "Importance [%]": percent_importance.values})
        percent_df = percent_df.sort_values("Importance [%]", ascending=False).reset_index(drop=True)

        plt.figure(figsize=(14, 8))
        plt.barh(percent_df['Feature'][::-1], percent_df['Importance [%]'][::-1])
        plt.xlabel('Importance [%]', fontsize=16,  fontweight="bold")
        plt.ylabel('MAPD Feature', fontsize=16,  fontweight="bold")
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.title(f'Grouped SHAP Importance ({target})', fontsize=16, fontweight="bold")
        plt.tight_layout()
        if save:
            Path(rf'{save_file}{target}.png').parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(rf'{save_file}{target}.png', dpi=300)
        if show_figure:
            plt.show()
        plt.close()


def create_feature_mapd_interaction_effects_shap_pro_layout(data_base, layout_names, graph_list, distance_list,
                                                            algorithm_list, tf_list, number_of_amr_list, save_file,
                                                            save=False, show_figure=True):
    data_layout = []
    data_graph = []
    data_makespan = []
    data_computational_time = []
    data_loaded_driving_time = []
    data_unloaded_driving_time = []
    data_detour = []
    data_num_amrs = []
    data_generated_nodes = []
    data_task_frequency = []
    data_algorithm = []

    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                for algo in algorithm_list:
                    for tf in tf_list:
                        for n_amr in number_of_amr_list:
                            df = deepcopy(data)
                            filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                            filtered_data = filtered_data[
                                                (filtered_data['Path Planning Algorithm'] == algo) &
                                                (filtered_data['Task Frequency'] == tf) &
                                                (filtered_data['Number AMR'] == n_amr)]
                            n = len(filtered_data)
                            if n == 0:
                                continue

                            data_layout += [layout_names[d].replace('_', ' ').upper()] * n
                            data_graph += [f'{graph} {dist} m'] * n
                            data_algorithm += [algo] * n
                            data_makespan += filtered_data['Makespan [s]'].tolist()
                            data_computational_time += filtered_data['Path Planning time'].tolist()
                            data_loaded_driving_time += (
                                        filtered_data['Loaded Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_unloaded_driving_time += (
                                        filtered_data['Empty Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_num_amrs += filtered_data['Number AMR'].tolist()
                            data_generated_nodes += filtered_data['Generated nodes cbs'].tolist()
                            data_task_frequency += filtered_data['Task Frequency'].tolist()
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
        'Task Frequency': data_task_frequency,
        'Algorithm': data_algorithm,
        'Makespan': data_makespan,
        'Computational time': data_computational_time,
        'Rel. Loaded Driving Time': data_loaded_driving_time,
        'Rel. Empty Driving Time': data_unloaded_driving_time,
        'Detour time': data_detour,
        'Generated nodes': data_generated_nodes
    })

    targets = ['Makespan', 'Computational time', 'Detour time']

    target_map = {
        "Makespan": "Makespan",
        "Computational time": "Computational time",
        "Detour time": "Detour time"
    }
    for target in targets:
        if target not in target_map:
            raise ValueError(f"Unknown target: {target}")
        layout_results = []
        for layout in df_heatmap['Layout'].unique():
            df_layout = df_heatmap[df_heatmap['Layout'] == layout]
            y = df_layout[target_map[target]]
            x = pd.get_dummies(
                df_layout[['Graph', 'Algorithm']],
                columns=['Graph', 'Algorithm'],
                drop_first=True
            )
            x['Number of AMRs'] = df_layout['Number of AMRs'].values
            x['Task Frequency'] = df_layout['Task Frequency'].values

            model = RandomForestRegressor(n_estimators=300, random_state=42)
            model.fit(x, y)

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(x)
            interaction_values = explainer.shap_interaction_values(x)

            shap_values = np.array(shap_values)
            interaction_values = np.array(interaction_values)

            feature_names = x.columns

            group_map = {
                "Graph": [i for i, col in enumerate(feature_names) if col.startswith("Graph_")],
                "Algorithm": [i for i, col in enumerate(feature_names) if col.startswith("Algorithm_")],
                "Number of AMRs": [i for i, col in enumerate(feature_names) if col == "Number of AMRs"],
                "Task Frequency": [i for i, col in enumerate(feature_names) if col == "Task Frequency"]
            }

            main_effects = {}
            for name, idxs in group_map.items():
                if len(idxs) == 0:
                    main_effects[name] = np.zeros(shap_values.shape[0])
                else:
                    main_effects[name] = np.sum(np.abs(shap_values[:, idxs]), axis=1)

            interaction_effects = {}

            group_names = list(group_map.keys())

            for i in range(len(group_names)):
                for j in range(i + 1, len(group_names)):
                    g1 = group_names[i]
                    g2 = group_names[j]

                    idxs_1 = group_map[g1]
                    idxs_2 = group_map[g2]

                    interaction_effects[f"{g1} × {g2}"] = np.sum(
                        np.abs(interaction_values[:, idxs_1][:, :, idxs_2]),
                        axis=(1, 2)
                    )

            combined_df = pd.DataFrame({**main_effects, **interaction_effects})

            mean_abs = combined_df.abs().mean(axis=0)
            percent_importance = 100 * mean_abs / mean_abs.sum()


            percent_df = pd.DataFrame({"Feature": percent_importance.index, "Importance [%]": percent_importance.values})
            percent_df = percent_df.sort_values("Importance [%]", ascending=False).reset_index(drop=True)
            percent_df['Layout'] = layout
            layout_results.append(percent_df)

            plt.figure(figsize=(14, 8))
            plt.barh(percent_df['Feature'][::-1], percent_df['Importance [%]'][::-1])
            plt.xlabel('Importance [%]', fontsize=16, fontweight="bold")
            plt.ylabel('MAPD Feature', fontsize=16, fontweight="bold")
            plt.xticks(fontsize=14)
            plt.yticks(fontsize=14)
            plt.title(f'Grouped SHAP Importance {target} {layout.lower().capitalize()}',
                      fontsize=16, fontweight="bold")
            plt.tight_layout()
            if save:
                Path(rf'{save_file}{target}_{layout}.png').parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(rf'{save_file}{target}_{layout}.png', dpi=300)
            if show_figure:
                plt.show()
            plt.close()

        all_layouts_df = pd.concat(layout_results)

        pivot_df = all_layouts_df.pivot(index='Feature', columns='Layout', values='Importance [%]').fillna(0)
        pivot_df['mean'] = pivot_df.mean(axis=1)
        pivot_df = pivot_df.sort_values('mean', ascending=True)
        pivot_df = pivot_df.drop(columns='mean')

        feature_sorted = pivot_df.mean(axis=1).sort_values().index
        pivot_df = pivot_df.loc[feature_sorted]

        cmap = cm.get_cmap("tab20")
        colors = [cmap(i) for i in range(pivot_df.shape[1])]

        fig, ax = plt.subplots(figsize=(14, 8))
        legend_handles = [
            Patch(facecolor=colors[i], edgecolor='black', label=f'{layout.lower().capitalize()}')
            for i, layout in enumerate(pivot_df.columns)
        ]

        ax.legend(handles=legend_handles, title="Layouts", fontsize=14, title_fontsize=14, loc="lower right")
        bar_height = 0.8
        for idx, feature in enumerate(feature_sorted):
            val_df = pivot_df.loc[feature]
            val_sorted_df = val_df.sort_values()
            last_val = 0
            for layout, val in val_sorted_df.items():
                color = colors[pivot_df.columns.get_loc(layout)]
                ax.barh(idx, val - last_val, height=bar_height, left=last_val, color=color, edgecolor='black',
                        align='center')
                last_val += val - last_val

        plt.xlabel('Importance [%]', fontsize=16, fontweight="bold")
        plt.ylabel("MAPD Feature", fontsize=16, fontweight="bold")
        plt.xticks(fontsize=14)
        ax.set_yticks(range(len(feature_sorted)))
        ax.set_yticklabels(feature_sorted)
        plt.yticks(fontsize=14)
        plt.title(
            f"SHAP MAPD Feature Layouts {target}",
            fontsize=16,
            fontweight="bold"
        )
        plt.tight_layout()
        if save:
            Path(rf'{save_file}{target}_layout_overview.png').parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(rf'{save_file}{target}_layout_overview.png', dpi=300)
        if show_figure:
            plt.show()
        plt.close()


def create_feature_mapd_interaction_effects_shap_pro_layout_advanced(data_base, layout_names, graph_list, distance_list,
                                                                     algorithm_list, tf_list, number_of_amr_list, save_file,
                                                                     save=False, show_figure=True):
    data_layout = []
    data_graph = []
    data_makespan = []
    data_computational_time = []
    data_loaded_driving_time = []
    data_unloaded_driving_time = []
    data_detour = []
    data_num_amrs = []
    data_generated_nodes = []
    data_task_frequency = []
    data_algorithm = []

    for d, data in enumerate(data_base):
        for i, graph in enumerate(graph_list):
            for dist in distance_list[i]:
                for algo in algorithm_list:
                    for tf in tf_list:
                        for n_amr in number_of_amr_list:
                            df = deepcopy(data)
                            filtered_data = df[df['Graph'] == f'{graph}_{dist}']
                            filtered_data = filtered_data[
                                                (filtered_data['Path Planning Algorithm'] == algo) &
                                                (filtered_data['Task Frequency'] == tf) &
                                                (filtered_data['Number AMR'] == n_amr)]
                            n = len(filtered_data)
                            if n == 0:
                                continue

                            data_layout += [layout_names[d].replace('_', ' ').upper()] * n
                            data_graph += [f'{graph} {dist} m'] * n
                            data_algorithm += [algo] * n
                            data_makespan += filtered_data['Makespan [s]'].tolist()
                            data_computational_time += filtered_data['Path Planning time'].tolist()
                            data_loaded_driving_time += (
                                        filtered_data['Loaded Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_unloaded_driving_time += (
                                        filtered_data['Empty Driving Time'] /
                                        filtered_data['Driving Time']).tolist()
                            data_num_amrs += filtered_data['Number AMR'].tolist()
                            data_generated_nodes += filtered_data['Generated nodes cbs'].tolist()
                            data_task_frequency += filtered_data['Task Frequency'].tolist()
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
        'Task Frequency': data_task_frequency,
        'Algorithm': data_algorithm,
        'Makespan': data_makespan,
        'Computational time': data_computational_time,
        'Rel. Loaded Driving Time': data_loaded_driving_time,
        'Rel. Empty Driving Time': data_unloaded_driving_time,
        'Detour time': data_detour,
        'Generated nodes': data_generated_nodes
    })

    targets = ['Makespan', 'Computational time', 'Detour time']

    target_map = {
        "Makespan": "Makespan",
        "Computational time": "Computational time",
        "Detour time": "Detour time"
    }
    for target in targets:
        if target not in target_map:
            raise ValueError(f"Unknown target: {target}")
        layout_results = []
        combined_all = []
        for layout in df_heatmap['Layout'].unique():
            df_layout = df_heatmap[df_heatmap['Layout'] == layout]
            y = df_layout[target_map[target]]
            x = pd.get_dummies(
                df_layout[['Graph', 'Algorithm']],
                columns=['Graph', 'Algorithm'],
                drop_first=True
            )
            x['Number of AMRs'] = df_layout['Number of AMRs'].values
            x['Task Frequency'] = df_layout['Task Frequency'].values

            model = RandomForestRegressor(n_estimators=300, random_state=42)
            model.fit(x, y)

            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(x)
            interaction_values = explainer.shap_interaction_values(x)

            shap_values = np.array(shap_values)
            interaction_values = np.array(interaction_values)

            feature_names = x.columns

            group_map = {
                "Graph": [i for i, col in enumerate(feature_names) if col.startswith("Graph_")],
                "Algorithm": [i for i, col in enumerate(feature_names) if col.startswith("Algorithm_")],
                "Number of AMRs": [i for i, col in enumerate(feature_names) if col == "Number of AMRs"],
                "Task Frequency": [i for i, col in enumerate(feature_names) if col == "Task Frequency"]
            }

            main_effects = {}
            for name, idxs in group_map.items():
                if len(idxs) == 0:
                    main_effects[name] = np.zeros(shap_values.shape[0])
                else:
                    main_effects[name] = np.sum(np.abs(shap_values[:, idxs]), axis=1)

            interaction_effects = {}

            group_names = list(group_map.keys())

            for i in range(len(group_names)):
                for j in range(i + 1, len(group_names)):
                    g1 = group_names[i]
                    g2 = group_names[j]

                    idxs_1 = group_map[g1]
                    idxs_2 = group_map[g2]

                    interaction_effects[f"{g1} × {g2}"] = np.sum(
                        np.abs(interaction_values[:, idxs_1][:, :, idxs_2]),
                        axis=(1, 2)
                    )

            combined_df = pd.DataFrame({**main_effects, **interaction_effects})
            combined_df["Layout"] = layout
            combined_all.append(combined_df)

            mean_abs = combined_df.drop(columns=["Layout"]).abs().mean(axis=0)
            percent_importance = 100 * mean_abs / mean_abs.sum()


            percent_df = pd.DataFrame({"Feature": percent_importance.index, "Importance [%]": percent_importance.values})
            percent_df = percent_df.sort_values("Importance [%]", ascending=False).reset_index(drop=True)
            percent_df['Layout'] = layout
            layout_results.append(percent_df)

            plt.figure(figsize=(14, 8))
            plt.barh(percent_df['Feature'][::-1], percent_df['Importance [%]'][::-1])
            plt.xlabel('Importance [%]', fontsize=16, fontweight="bold")
            plt.ylabel('MAPD Feature', fontsize=16, fontweight="bold")
            plt.xticks(fontsize=14)
            plt.yticks(fontsize=14)
            plt.title(f'Grouped SHAP Importance {target} {layout.lower().capitalize()}',
                      fontsize=16, fontweight="bold")
            plt.tight_layout()
            if save:
                Path(rf'{save_file}{target}_{layout}.png').parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(rf'{save_file}{target}_{layout}.png', dpi=300)
            if show_figure:
                plt.show()
            plt.close()

        combined_all_df = pd.concat(combined_all, ignore_index=True)

        all_layouts_df = pd.concat(layout_results)

        pivot_df = all_layouts_df.pivot(index='Feature', columns='Layout', values='Importance [%]').fillna(0)
        pivot_df['mean'] = pivot_df.mean(axis=1)
        pivot_df = pivot_df.sort_values('mean', ascending=True)
        pivot_df = pivot_df.drop(columns='mean')

        feature_sorted = pivot_df.mean(axis=1).sort_values().index
        pivot_df = pivot_df.loc[feature_sorted]
        #############################################Old##############################################################

        fig, ax = plt.subplots(figsize=(12, 6))
        features = pivot_df.index
        layouts = pivot_df.columns

        x = np.arange(len(features))
        width = 0.8 / len(layouts)

        cmap = cm.get_cmap("tab20")
        colors = [cmap(i) for i in range(len(layouts))]

        for i, layout in enumerate(layouts[::-1]):
            ax.barh(
                x + i * width,
                pivot_df[layout],
                height=width,
                label=layout,
                color=colors[i]
            )

        ax.set_xlim(0, max(pivot_df.max()) * 1.1)
        for val in np.arange(0, ax.get_xlim()[1], 5):
            ax.axvline(val, color='gray', linestyle='-', linewidth=0.8, alpha=0.3, zorder=0)

        ax.set_yticks(x + width * (len(layouts) / 2))
        ax.tick_params(axis='y', labelsize=12)
        ax.set_yticklabels(features)
        # ax.invert_yaxis()
        plt.xticks(fontsize=14)
        plt.xlabel("Importance [%]", fontsize=16, fontweight="bold")
        plt.ylabel("MAPD Feature", fontsize=16, fontweight="bold")
        plt.title(
                f"SHAP-based Feature Importance for {target} in MAPD",
                fontsize=16,
                fontweight="bold"
            )
        # handles, labels = ax.get_legend_handles_labels()
        legend_handles = [
            Patch(
                facecolor=colors[i],
                edgecolor='black',
                label=f'{layout.lower().capitalize()}'
            )
            for i, layout in enumerate(layouts)
        ]
        ax.legend(handles=legend_handles[::-1], title="Layouts", fontsize=14, title_fontsize=14, loc="lower right")

        plt.tight_layout()
        if save:
            Path(rf'{save_file}{target}_layout_overview.png').parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(rf'{save_file}{target}_layout_overview_bar.png', dpi=300)
        if show_figure:
            plt.show()
        plt.close()

        ##########################Dumbbell###################################################################
        fig, ax = plt.subplots(figsize=(12, 6))

        y_pos = np.arange(len(pivot_df.index))
        cmap = cm.get_cmap("tab20")
        colors = {layout: cmap(i) for i, layout in enumerate(pivot_df.columns)}
        markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '<', '>', '*']
        marker_map = {
            layout: markers[i % len(markers)]
            for i, layout in enumerate(pivot_df.columns)
        }

        offset_scale = 0.08

        for i, feature in enumerate(pivot_df.index):
            values = pivot_df.loc[feature]
            padding = (values.max() - values.min()) * 0.05
            ax.hlines(i, values.min() - padding, values.max() + padding, alpha=0.3)

            for j, (layout, val) in enumerate(values.items()):
                offset = (j - len(values) / 2) * offset_scale
                ax.scatter(val, i + offset, color=colors[layout], marker=marker_map[layout], s=60)

        legend_handles = [
            Line2D(
                [0], [0],
                marker=marker_map[layout],
                color='w',
                label=f'{layout.lower().capitalize()}',
                markerfacecolor=colors[layout],
                markersize=10
            )
            for layout in pivot_df.columns
        ]

        ax.legend(handles=legend_handles, title="Layout", fontsize=14, title_fontsize=14, loc="lower right")

        ax.set_xlim(0, max(pivot_df.max()) * 1.1)
        for val in np.arange(0, ax.get_xlim()[1], 5):
            ax.axvline(val, color='gray', linestyle='-', linewidth=0.8, alpha=0.3, zorder=0)

        ax.set_yticks(y_pos, pivot_df.index)

        ax.set_xlabel("Importance [%]", fontsize=16, fontweight="bold")
        ax.set_title(f"{target} - Layout Comparison (Dumbbell)", fontsize=16, fontweight="bold")

        plt.tight_layout()
        if save:
            plt.savefig(rf"{save_file}{target}_layout_dumbbell.png", dpi=300)
        if show_figure:
            plt.show()
        plt.close()
        #####################################Beeswarm Dumbell#####################################################
        plt.figure(figsize=(14, 8))

        features = [col for col in combined_all_df.columns if col != "Layout"]

        layouts = combined_all_df["Layout"].unique()

        cmap = cm.get_cmap("Set2", len(layouts))
        color_map = {layout: cmap(i) for i, layout in enumerate(layouts)}

        for i, feature in enumerate(features):
            for layout in layouts:
                values = combined_all_df[combined_all_df["Layout"] == layout][feature]

                y = np.random.normal(i, 0.08, size=len(values))

                plt.scatter(values, y,
                            color=color_map[layout],
                            alpha=0.4,
                            s=10)

            # global mean
            plt.scatter(combined_all_df[feature].mean(), i,
                        color="black", s=80, zorder=3)

        plt.yticks(range(len(features)), features)

        # Legende
        for layout, color in color_map.items():
            plt.scatter([], [], color=color, label=layout)

        plt.legend(title="Layout")

        plt.xlabel("SHAP Contribution", fontsize=16, fontweight="bold")
        plt.title(f"{target} - Beeswarm (all instances, colored by layout)",
                  fontsize=16, fontweight="bold")

        plt.tight_layout()

        if save:
            plt.savefig(rf"{save_file}{target}_layout_beeswarm_full.png", dpi=300)
        if show_figure:
            plt.show()
        plt.close()



