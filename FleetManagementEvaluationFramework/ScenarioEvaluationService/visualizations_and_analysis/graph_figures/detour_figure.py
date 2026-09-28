import logging
from copy import deepcopy
import config.config_file

import matplotlib
import seaborn as sns

import matplotlib.pyplot as plt

from order_evaluation.order_evaluation_script import compute_detour

matplotlib.use("TkAgg")

logger = logging.getLogger(config.config_file.LOGGER_NAME)

def create_detour_figure_graph(data, algorithm_name, layout_name, iteration_list, save_path, save=False,
                               show_figure=True):
    df = deepcopy(data)

    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    for item in iteration_list:
        df_new = df[df['Graph'] == item]
        try:
            driving_time_without_collision = compute_detour(layout_name, item.split('_')[0], float(item.split('_')[1]),
                                                            None)
        except Exception as e:
            logger.info(f'Error: {e}')
            continue
        df_new['Detour'] = ((df_new["Loaded Driving Time"] - driving_time_without_collision) /
                            driving_time_without_collision) * 100
        df_new = df_new.groupby("Number AMR", as_index=False)["Detour"].mean()
        label_df = layout_name.replace('_', ' ') + ' Layout ' + item.split('_')[0] + ' ' + str(
            item.split('_')[1]) + 'meter with ' + algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Detour", data=df_new, ax=ax1, color=palette[color_index],
                         label=label_df.capitalize())
            color_index += 1

    ax1.set_ylabel(f"Relative additional detour to avoid collisions [%]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black')

    ax1.legend(title='Legend', loc='upper right', bbox_to_anchor=(1.6, 1), borderaxespad=0)
    plt.title(f"{layout_name.replace('_', ' ').capitalize() + ' Layout '} relative additional detour "
              f"{algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()}", fontsize=16, fontweight='bold')
    plt.xlabel("Number of AMRs", fontsize=16)
    plt.xticks([10, 20, 30, 40, 50], fontsize=14)
    plt.yticks(fontsize=14)
    plt.subplots_adjust(right=0.7)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return


def create_detour_figure_layout(data, algorithm_name, graph_name, iteration_list, save_path, layout_comp_list,
                                save=False, show_figure=True):
    df = deepcopy(data)

    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    for l, item in enumerate(iteration_list):
        df_new = df[df['Layout'] == item]
        try:
            driving_time_without_collision = compute_detour(layout_comp_list[l], graph_name.split('_')[0],
                                                            float(graph_name.split('_')[1]), None)
        except Exception as e:
            logger.info(f'Error: {e}')
            continue
        df_new['Detour'] = ((df_new["Loaded Driving Time"] - driving_time_without_collision) /
                            driving_time_without_collision) * 100
        df_new = df_new.groupby("Number AMR", as_index=False)["Detour"].mean()
        label_df = (graph_name.split('_')[0] + ' ' + str(graph_name.split('_')[1]) + ' meter graph ' +
                    layout_comp_list[l].replace('_', ' ').capitalize() + ' Layout with ' +
                    algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper())

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Detour", data=df_new, ax=ax1, color=palette[color_index],
                         label=label_df.capitalize())
            color_index += 1

    ax1.set_ylabel(f"Relative additional detour to avoid collisions [%]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black')

    ax1.legend(title='Legend', loc='upper right', bbox_to_anchor=(1.63, 1), borderaxespad=0)
    plt.title(f"{graph_name.split('_')[0].capitalize()} {str(graph_name.split('_')[1])} meter"
              f" graph relative additional detour "
              f"{algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()}", fontsize=16, fontweight='bold')
    plt.xlabel("Number of AMRs", fontsize=16)
    plt.xticks([10, 20, 30, 40, 50], fontsize=14)
    plt.yticks(fontsize=14)
    plt.subplots_adjust(right=0.7)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return


def create_detour_figure_algorithm(data, graph_name, layout_name, iteration_list, save_path, save=False,
                                   show_figure=True):
    df = deepcopy(data)
    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(12, 6))

    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    for item in iteration_list:
        df_new = df[df['Path Planning Algorithm'] == item]
        try:
            driving_time_without_collision = compute_detour(layout_name, graph_name.split('_')[0],
                                                            float(graph_name.split('_')[1]), None)
        except Exception as e:
            logger.info(f'Error: {e}')
            continue
        df_new['Detour'] = ((df_new["Loaded Driving Time"] - driving_time_without_collision) /
                            driving_time_without_collision) * 100
        df_new = df_new.groupby("Number AMR", as_index=False)["Detour"].mean()

        label_df = layout_name.replace('_', ' ').capitalize() + ' Layout ' + graph_name.split('_')[0] + ' ' + str(
            graph_name.split('_')[1]) + ' meter Graph ' + item.replace('cbs_1.0', 'CBS').replace('_', ' ').upper()

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Detour", data=df_new, ax=ax1, color=palette[color_index],
                         label=label_df.capitalize())
            color_index += 1

    ax1.set_ylabel(f"Relative additional detour to avoid collisions [%]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black')

    ax1.legend(title='Legend', loc='upper right', bbox_to_anchor=(1.6, 1), borderaxespad=0)
    plt.title(f'Relative additional detour ' + layout_name.replace('_', ' ').capitalize() +
              ' Layout ' + ' with ' + str(graph_name.split('_')[0]) + ' ' + str(graph_name.split('_')[1]) +
              ' meter Graph', fontsize=16, fontweight='bold')
    plt.xlabel("Number of AMRs", fontsize=16)
    plt.xticks([10, 20, 30, 40, 50], fontsize=14)
    plt.yticks(fontsize=14)
    plt.subplots_adjust(right=0.7)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return

