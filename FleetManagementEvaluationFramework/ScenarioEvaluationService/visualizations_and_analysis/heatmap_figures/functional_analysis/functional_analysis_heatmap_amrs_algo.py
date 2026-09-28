import itertools
import json

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
import seaborn as sns

import matplotlib.pyplot as plt

matplotlib.use("TkAgg")


def create_functional_heatmap_amrs_algo_abs(data_base, save_path, save=False, show_figures=True):
    alpha = 1
    beta = 0
    MAX_PP_TIME = 7200

    df = pd.concat(data_base, ignore_index=True)

    # 1. create instance room
    instance_file = r'./heatmap_figures/functional_analysis/instance_dict.json'
    with open(instance_file, "r") as f:
        layout_dict = json.load(f)

    rows = []
    for layout, info in layout_dict.items():
        graphs = info["Graphs"]
        algorithms = info["Path Planning Algorithm"]
        tfs = info["Task Frequency"]
        amrs = info["Number AMR"]
        for graph, tf, amr, algo in itertools.product(
                graphs, tfs, amrs, algorithms):
            rows.append({"Layout": layout,
                         "Graph": graph,
                         "Task Frequency": tf,
                         "Number AMR": amr,
                         "Path Planning Algorithm": algo})
    full_instance_space = pd.DataFrame(rows)

    df_full = full_instance_space.merge(
        df,
        how="left",
        on=["Layout", "Graph", "Task Frequency", "Number AMR", "Path Planning Algorithm"]
    )
    df_full['Solved'] = df_full['Makespan [s]'].notna().astype(int)
    df_full["PP_success_rate_instance"] = (
            1 - df_full["Failed path planing computations"] /
            df_full["Number executed CBS computations"]
    )
    df_full["Difficulty_instance"] = (
            #np.log(1 + df_full["Generated nodes cbs"] * df_full["Expanded nodes astar"])
            alpha * np.log(1 + df_full["Generated nodes cbs"]) +
            beta * np.log(1 + df_full["Expanded nodes astar"])
    )
    df_full["Evaluation Duration penalized"] = df_full["Evaluation Duration"].copy()
    df_full.loc[df_full["Solved"] == 0, "Evaluation Duration penalized"] = MAX_PP_TIME
    df_full["Evaluation Duration penalized"] = df_full["Evaluation Duration penalized"] / 60  # compute in minutes


    df_summary = (
        df_full
        .groupby(["Number AMR", "Path Planning Algorithm"])
        .agg(
            Makespan_mean=("Makespan [s]", "mean"),
            Solved_rate=("Solved", "mean"),
            Path_planning_rate=("PP_success_rate_instance", "mean"),
            difficulty_score=("Difficulty_instance", "mean"),
            path_planning_time=("Evaluation Duration penalized", "mean")
        )
        .reset_index()
    )
    algorithm_map = {
        "cbs_1.0": "CBS",
        "cbs_djs_test_1.0": "CBS-DJS",
        "ecbs_1.3": "ECBS w=1.3",
        "ecbs_djs_test_1.3": "ECBS-DJS w=1.3"
    }
    df_summary["Path Planning Algorithm"] = df_summary["Path Planning Algorithm"].map(algorithm_map)

    algorithm_order = ['ECBS w=1.3', 'ECBS-DJS w=1.3', 'CBS', 'CBS-DJS']

    heatmap_data_makespan = df_summary.pivot_table(
        index='Path Planning Algorithm', columns='Number AMR', values='Makespan_mean', aggfunc='mean'
    )
    heatmap_data_makespan = heatmap_data_makespan.reindex(algorithm_order)

    heatmap_data_solved_mapd = df_summary.pivot_table(
        index='Path Planning Algorithm', columns='Number AMR', values='Solved_rate', aggfunc='mean'
    )
    heatmap_data_solved_mapd = heatmap_data_solved_mapd.reindex(algorithm_order)

    heatmap_data_solved_mapf = df_summary.pivot_table(
        index='Path Planning Algorithm', columns='Number AMR', values='Path_planning_rate', aggfunc='mean'
    )
    heatmap_data_solved_mapf = heatmap_data_solved_mapf.reindex(algorithm_order)

    heatmap_data_path_planning_time = df_summary.pivot_table(
        index='Path Planning Algorithm', columns='Number AMR', values='path_planning_time', aggfunc='mean'
    )

    heatmap_data_path_planning_time = heatmap_data_path_planning_time.reindex(algorithm_order)

    annot = heatmap_data_path_planning_time.copy().astype(str)

    for i in range(annot.shape[0]):
        for j in range(annot.shape[1]):
            if pd.isna(heatmap_data_path_planning_time.iloc[i, j]) or heatmap_data_solved_mapd.iloc[i, j] == 0:
                annot.iloc[i, j] = (
                    f"Sol. MAPD: 0.0%\n"
                    f"Sol. MAPF: -"
                )
            else:
                annot.iloc[i, j] = (
                    f"Sol. MAPD: {heatmap_data_solved_mapd.iloc[i, j] * 100:.1f}%\n"
                    f"Sol. MAPF: {heatmap_data_solved_mapf.iloc[i, j] * 100:.1f}%"
                )

    max_val = heatmap_data_path_planning_time.max().max()
    heatmap_data_path_planning_time = heatmap_data_path_planning_time.fillna(max_val)
    plt.figure(figsize=(10, 4))

    sns.heatmap(
        heatmap_data_path_planning_time,
        annot=annot.values,
        fmt="",
        cmap="RdYlGn_r",
        linewidths=0.5,
        linecolor="gray",
        #annot_kws={"color": "black"},
        cbar_kws={'label': 'Solved MAPD Instances'},
    )
    ax = plt.gca()
    ax.set_yticklabels([
        label.get_text().replace(" w", "\nw")
        for label in ax.get_yticklabels()
    ])
    cbar = ax.collections[0].colorbar
    cbar.set_label('Avg. Evaluation Time [min]', fontsize=14)

    plt.title("Lay2Graph-MAPD Framework Performance Overview", fontsize=16, fontweight='bold')
    plt.xlabel("Number of AMRs", fontsize=14)
    plt.ylabel("Algorithm", fontsize=14)
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(rotation=0, fontsize=12)

    plt.tight_layout()
    if save:
        file_name_figure = rf'{save_path}_performance_overview.png'
        Path(file_name_figure).parent.mkdir(parents=True, exist_ok=True)
        #if not os.path.exists(file_name_figure):
        plt.savefig(file_name_figure, dpi=300)
    if show_figures:
        plt.show()
    plt.close()
    return