from copy import deepcopy

import matplotlib
import seaborn as sns

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

matplotlib.use("TkAgg")


def create_sum_of_costs_pro_amr_figure_graph(data, algorithm_name, layout_name, iteration_list, save_path, save=False,
                                             show_figure=True):
    df = deepcopy(data)

    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(16, 6))
    ax2 = ax1.twinx()

    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    data_name = []

    for item in iteration_list:
        df_new = df[df['Graph'] == item]
        df_new = df_new.groupby("Number AMR", as_index=False)[
            ["Makespan [s]", "Loaded Driving Time", "Empty Driving Time"]].mean()
        df_new["Loaded Driving Time pro amr"] = df_new["Loaded Driving Time"] / df_new["Number AMR"]
        df_new["Empty Driving Time pro amr"] = df_new["Empty Driving Time"] / df_new["Number AMR"]

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Loaded Driving Time pro amr", data=df_new, ax=ax1, linestyle='dashed',
                         color=palette[color_index], label='Loaded driving')
            sns.lineplot(x="Number AMR", y="Empty Driving Time pro amr", data=df_new, ax=ax1, linestyle='dotted',
                         color=palette[color_index], label='Empty driving')

            sns.lineplot(x="Number AMR", y="Makespan [s]", data=df_new, color=palette[color_index], linestyle='-',
                         label='Makespan')
            color_index += 1
            data_name.append(layout_name.replace('_', ' ') + ' Layout ' + item.split('_')[0] + ' ' +
                             str(item.split('_')[1]) + ' meter with ' +
                             algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper())

    ax1.set_ylabel("Driving Times [s]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=16)
    ax2.set_ylabel('Makespan [s]', color='blue', fontsize=16)
    ax2.tick_params(axis='y', labelcolor='blue', labelsize=16)
    ax1.legend().remove()
    ax2.legend().remove()
    custom_legend = [
                        Line2D([0], [0], linestyle='dashed', color=palette[i], lw=2,
                               label=f'Loaded driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='dotted', color=palette[i], lw=2,
                               label=f'Empty driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='-', color=palette[i], lw=2, label=f'Makespan: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                    ]
    plt.legend(handles=custom_legend, title='Legende', loc='upper right', bbox_to_anchor=(1.74, 1), borderaxespad=0)

    plt.title("Driving Time pro AMR and Makespan based on the Number of AMRs",fontsize=16, fontweight='bold')
    ax1.set_xlabel("Number of AMRs", fontsize=16)
    ax1.set_xticks([10, 20, 30, 40, 50])
    ax1.tick_params(axis='x', labelsize=16)
    plt.subplots_adjust(right=0.68)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return


def create_sum_of_costs_pro_amr_figure_layout(data, algorithm_name, graph_name, iteration_list, save_path, save=False,
                                              show_figure=True):
    df = deepcopy(data)

    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(16, 6))
    ax2 = ax1.twinx()

    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    data_name = []

    for item in iteration_list:
        df_new = df[df['Layout'] == item]
        df_new = df_new.groupby("Number AMR", as_index=False)[
            ["Makespan [s]", "Loaded Driving Time", "Empty Driving Time"]].mean()
        df_new["Loaded Driving Time pro amr"] = df_new["Loaded Driving Time"] / df_new["Number AMR"]
        df_new["Empty Driving Time pro amr"] = df_new["Empty Driving Time"] / df_new["Number AMR"]

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Loaded Driving Time pro amr", data=df_new, ax=ax1, linestyle='dashed',
                         color=palette[color_index], label='Loaded driving')
            sns.lineplot(x="Number AMR", y="Empty Driving Time pro amr", data=df_new, ax=ax1, linestyle='dotted',
                         color=palette[color_index], label='Empty driving')
            sns.lineplot(x="Number AMR", y="Makespan [s]", data=df_new, color=palette[color_index], linestyle='-',
                         label='Makespan')
            color_index += 1
            data_name.append(item.replace('_', ' ').capitalize() + ' Layout ' + graph_name.split('_')[0] + ' ' +
                             str(graph_name.split('_')[1]) + ' meter with ' +
                             algorithm_name.replace('cbs_1.0', 'CBS').replace('_', ' ').upper())

    ax1.set_ylabel("Driving Times [s]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=16)
    ax2.set_ylabel('Makespan [s]', color='blue', fontsize=16)
    ax2.tick_params(axis='y', labelcolor='blue', labelsize=16)
    ax1.legend().remove()
    ax2.legend().remove()
    custom_legend = [
                        Line2D([0], [0], linestyle='dashed', color=palette[i], lw=2,
                               label=f'Loaded driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='dotted', color=palette[i], lw=2,
                               label=f'Empty driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='-', color=palette[i], lw=2, label=f'Makespan: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                    ]
    plt.legend(handles=custom_legend, title='Legende', loc='upper right', bbox_to_anchor=(1.75, 1), borderaxespad=0)

    plt.title("Driving Time pro AMR and Makespan based on the Number of AMRs", fontsize=16, fontweight='bold')
    ax1.set_xlabel("Number of AMRs", fontsize=16)
    ax1.set_xticks([10, 20, 30, 40, 50])
    ax1.tick_params(axis='x', labelsize=16)
    plt.subplots_adjust(right=0.68)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return


def create_driving_time_pro_amr_figure_algorithm(data, graph_name, layout_name, iteration_list, save_path, save=False,
                                                 show_figure=True):
    df = deepcopy(data)

    sns.set_theme(style="darkgrid")
    fig, ax1 = plt.subplots(figsize=(16, 6))
    ax2 = ax1.twinx()

    num_lines = len(iteration_list)
    palette = sns.color_palette("tab20", num_lines)
    color_index = 0

    data_name = []

    for item in iteration_list:
        df_new = df[df['Path Planning Algorithm'] == item]
        df_new = df_new.groupby("Number AMR", as_index=False)[
            ["Makespan [s]", "Loaded Driving Time", "Empty Driving Time"]].mean()
        df_new["Loaded Driving Time pro amr"] = df_new["Loaded Driving Time"] / df_new["Number AMR"]
        df_new["Empty Driving Time pro amr"] = df_new["Empty Driving Time"] / df_new["Number AMR"]

        if not df_new.empty:
            sns.lineplot(x="Number AMR", y="Loaded Driving Time pro amr", data=df_new, ax=ax1, linestyle='dashed',
                         color=palette[color_index], label='Loaded driving')
            sns.lineplot(x="Number AMR", y="Empty Driving Time pro amr", data=df_new, ax=ax1, linestyle='dotted',
                         color=palette[color_index], label='Empty driving')

            sns.lineplot(x="Number AMR", y="Makespan [s]", data=df_new, color=palette[color_index], linestyle='-',
                         label='Makespan')
            color_index += 1
            data_name.append(layout_name.replace('_', ' ').capitalize() + ' Layout ' + graph_name.split('_')[0] + ' ' +
                             str(graph_name.split('_')[1]) + ' meter with ' +
                             item.replace('cbs_1.0', 'CBS').replace('_',' ').upper())

    ax1.set_ylabel("Driving Times [s]", fontsize=16)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=16)
    ax2.set_ylabel('Makespan [s]', color='black', fontsize=16)
    ax2.tick_params(axis='y', labelcolor='blue', labelsize=16)
    ax1.legend().remove()
    ax2.legend().remove()
    custom_legend = [
                        Line2D([0], [0], linestyle='dashed', color=palette[i], lw=2,
                               label=f'Loaded driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='dotted', color=palette[i], lw=2,
                               label=f'Empty driving: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                        Line2D([0], [0], linestyle='-', color=palette[i], lw=2, label=f'Makespan: {d.capitalize()}')
                        for i, d in enumerate(data_name)] + [
                    ]
    plt.legend(handles=custom_legend, title='Legende', loc='upper right', bbox_to_anchor=(1.72, 1), borderaxespad=0)

    plt.title("Driving Time pro AMR and Makespan based on the number of AMRs", fontsize=16, fontweight='bold')
    ax1.set_xlabel("Number of AMRs", fontsize=16)
    ax1.set_xticks([10, 20, 30, 40, 50])
    ax1.tick_params(axis='x', labelsize=16)
    plt.subplots_adjust(right=0.68)
    plt.tight_layout()
    if save:
        fig.savefig(save_path, dpi=300)
    if show_figure:
        plt.show()
    plt.close(fig)
    return

