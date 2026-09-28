from copy import deepcopy

import numpy as np
from dash import Dash, dash_table, dcc, html, Input, Output
import pandas as pd


def show_data_with_dashboard(data_base, layout_names_comp, graph_list, distance_list, algo_list, metric_list,
                             number_of_amrs, tfs):
    app = Dash(__name__, suppress_callback_exceptions=True)
    data_table = []
    data_table.append({"name": ["", "", "TF"], "id": "tf"})
    data_table.append({"name": ["", "", "Number of AMRs"], "id": "amrs"})

    columns = [
        {"name": ["", "", "TF"], "id": "tf"},
        {"name": ["", "", "Number of AMRs"], "id": "amrs"},
    ]

    data = []
    style_cell_conditional = []

    for tf in tfs:
        for amr in number_of_amrs:
            row = {"tf": tf, "amrs": amr}
            for i, data_df in enumerate(data_base):
                df = deepcopy(data_base[i])
                for j, graph in enumerate(graph_list):
                    for k, dist in enumerate(distance_list[j]):
                        for algo in algo_list:
                            for metric_idx, metric in enumerate(metric_list):
                                df_filtered = df[
                                    (df['Graph'] == f'{graph}_{dist}') &
                                    (df['Path Planning Algorithm'] == algo) &
                                    (df['Task Frequency'] == tf) &
                                    (df['Number AMR'] == amr)
                                    ]

                                if not df_filtered.empty:
                                    value = round(df_filtered[metric].values[0], 2)
                                    if pd.isna(value):
                                        value = None
                                    else:
                                        value = float(value)
                                    metric_clean = metric.replace(" ", "_").replace("[", "").replace("]", "")
                                    col_id = f"{layout_names_comp[i]}_{graph.lower()}{dist}_{algo}_{metric_clean}".lower()
                                    col_name = [
                                        layout_names_comp[i].replace('_', ' ').capitalize() + f' {graph.capitalize()} {dist} m',
                                        algo.replace('_', ' ').replace('0', '').upper(),
                                        metric
                                    ]
                                    if col_id not in [c['id'] for c in columns]:
                                        columns.append({"name": col_name, "id": col_id})

                                    row[col_id] = value

                                    if metric_idx == len(metric_list) - 1:
                                        style_cell_conditional.append({
                                            'if': {'column_id': col_id},
                                            'borderRight': '3px solid black'
                                        })
            data.append(row)

    layout_options = ["Warehouse 35x21", "Space 35x21"]
    layout_options = [l.replace('_', ' ').capitalize() for l in layout_names_comp]
    graph_options = [g.capitalize() for g in graph_list]
    dist_options = [1, 0.5]
    algo_options = [a.replace('_', ' ').upper() for a in algo_list]
    metric_options = [m.replace(" ", "_").replace("[", "").replace("]", "") for m in metric_list]

    app.layout = html.Div([
        html.Div([
            dcc.Dropdown(id="layout-selector",
                         options=[{"label": l, "value": l} for l in layout_options],
                         value="Warehouse 35x21",
                         multi=True,
                         clearable=False,
                         placeholder="Select Layout",
                         style={'width': '250px'}),
            dcc.Dropdown(id="graph-selector",
                         options=[{"label": g, "value": g} for g in graph_options],
                         value="Grid",
                         multi=True,
                         clearable=False,
                         placeholder="Select Graph",
                         style={'width': '250px'}),
            dcc.Dropdown(id="dist-selector",
                         options=[{"label": str(d) + " m", "value": d} for d in dist_options],
                         value=1,
                         multi=True,
                         clearable=False,
                         placeholder="Select Distance",
                         style={'width': '250px'}),
            dcc.Dropdown(id="algorithm-selector",
                         options=[{"label": a, "value": a} for a in algo_options],
                         value=["CBS 1.0"],
                         multi=True,
                         clearable=False,
                         placeholder="Select Algorithm",
                         style={'width': '250px'}),
            dcc.Dropdown(id="metric-selector",
                         options=[{"label": m, "value": m} for m in metric_options],
                         value=['Makespan_s', 'Empty Driving Time', 'Loaded Driving Time', 'Path_Planning_time'],
                         multi=True,
                         clearable=False,
                         placeholder="Select Metrics",
                         style={'width': '250px'}),
            ], style={'display': 'flex', 'gap': '10px', 'margin-bottom': '20px'}),
        html.Div([
            dcc.Checklist(
            id="relative-toggle",
            options=[{"label": "Show relative changes to reference", "value": "on"}],
            value=[],
            style={"marginTop": "10px"}
            ),
            dcc.Dropdown(id="reference-layout", options=[{"label": l, "value": l} for l in layout_options], value=None, multi=False, style={'width': '200px'}),
            dcc.Dropdown(id="reference-graph", options=[{"label": g, "value": g} for g in graph_options], value=None, multi=False, style={'width': '150px'}),
            dcc.Dropdown(id="reference-dist", options=[{"label": str(d) + " m", "value": d} for d in dist_options], value=None, multi=False, style={'width': '120px'}),
            dcc.Dropdown(id="reference-algo", options=[{"label": a, "value": a} for a in algo_options], value=None, multi=False, style={'width': '150px'}),
        ], style={'display': 'flex', 'gap': '10px', 'margin-bottom': '20px'}),
        dash_table.DataTable(
            id="table",
            columns=columns,
            data=data,
            tooltip_data=[{} for _ in data],  # Platzhalter initial
            tooltip_duration=None,  # Tooltip bleibt solange der Mauszeiger da ist
            merge_duplicate_headers=True,
            style_header={
                'fontWeight': 'bold',
                'textAlign': 'center',
                'backgroundColor': '#f2f2f2',
                'border': '2px solid black'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '5px',
            },
            style_cell_conditional=[
                                       {'if': {'column_id': 'amrs'}, 'borderRight': '3px solid black'},
                                       {'if': {'column_id': 'tf'}, 'borderRight': '3px solid black'}
                                   ] + style_cell_conditional,
            style_data_conditional=[
                {
                    'if': {'filter_query': '{amrs} = 50'},
                    'borderBottom': '3px solid black'
                },
            ],
            style_table={'overflowX': 'auto'},
        )])

    @app.callback(
        Output("table", "hidden_columns"),
        Input("layout-selector", "value"),
        Input("graph-selector", "value"),
        Input("dist-selector", "value"),
        Input("algorithm-selector", "value"),
        Input("metric-selector", "value"),
    )
    def filter_columns(layouts, graphs, dists, algos, metrics):
        if not isinstance(layouts, list):
            layouts = [layouts]
        if not isinstance(graphs, list):
            graphs = [graphs]
        if not isinstance(dists, list):
            dists = [dists]
        if not isinstance(algos, list):
            algos = [algos]
        if not isinstance(metrics, list):
            metrics = [metrics]

        all_columns = [c["id"] for c in columns]
        always_visible = ["tf", "amrs"]

        prefixes = []
        for layout in layouts:
            for graph in graphs:
                for dist in dists:
                    for algo in algos:
                        for metric in metrics:
                            dist_str = str(dist)  # exact like in col_id
                            algo_part = algo.lower().strip().replace(" ", "_")
                            prefix = f"{layout.lower().replace(' ', '_')}_{graph.lower()}{dist_str}_{algo_part}_{metric.lower()}"
                            prefixes.append(prefix)
        # Hide columns that do not match with the prefix
        hidden = [c for c in all_columns if c not in always_visible and not any(c.startswith(p) for p in prefixes)]
        return hidden

    @app.callback(
        Output("table", "data"),
        Output("table", "style_data_conditional"),
        Output("table", "tooltip_data"),
        Input("relative-toggle", "value"),
        Input("reference-layout", "value"),
        Input("reference-graph", "value"),
        Input("reference-dist", "value"),
        Input("reference-algo", "value"),
        Input("metric-selector", "value"),
    )
    def update_relative_table(toggle, ref_layout, ref_graph, ref_dist, ref_algo, metrics):
        table_data = deepcopy(data)
        style_rules = [
            {'if': {'column_id': 'amrs'}, 'borderRight': '3px solid black'},
            {'if': {'column_id': 'tf'}, 'borderRight': '3px solid black'},
            {'if': {'filter_query': '{amrs} = 50'}, 'borderBottom': '3px solid black'}
        ]
        tooltip_data = [{} for _ in table_data]

        # if checkbox not activated
        if "on" not in toggle or not all([ref_layout, ref_graph, ref_dist, ref_algo, metrics]):
            average_row = {'tf': 'Average', 'amrs': ''}
            for col in table_data[0].keys():
                if col not in ['tf', 'amrs']:
                    # Average of all values of this column
                    values = [row[col] for row in table_data if row.get(col) is not None]
                    if values:
                        average_row[col] = round(sum(values) / len(values), 2)
                    else:
                        average_row[col] = None
            table_data.append(average_row)
            style_rules.append({
                "if": {"filter_query": "{tf} = 'Average'"},
                "fontWeight": "bold",
                "backgroundColor": "#f0f0f0"
            })
            tooltip_data.append({})
            return table_data, style_rules, tooltip_data

        if not isinstance(metrics, list):
            metrics = [metrics]

        ref_algo_norm = ref_algo.lower().strip().replace(" ", "_")
        ref_dist_str = str(ref_dist)

        for row_idx, row in enumerate(table_data):
            row_tooltip = {}

            for metric in metrics:
                metric_clean = metric.replace(" ", "_").replace("[", "").replace("]", "").lower()
                # Reference value
                ref_col = next(
                    (c for c in row.keys()
                     if c.startswith(f"{ref_layout.lower().replace(' ', '_')}_{ref_graph.lower()}{ref_dist_str}_"
                                     f"{ref_algo_norm}_{metric_clean}")),
                    None
                )
                if ref_col is None or row.get(ref_col) is None:
                    continue

                ref_value = row[ref_col]

                # Compare with other combinations
                for layout in layout_options:
                    for graph in graph_options:
                        for dist in dist_options:
                            for algo in algo_options:
                                if layout == ref_layout and graph == ref_graph and dist == ref_dist and algo == ref_algo:
                                    continue

                                dist_str = str(dist)
                                algo_norm = algo.lower().strip().replace(" ", "_")

                                # All suitable columns
                                compare_cols = [c for c in row.keys()
                                                if c.startswith(f"{layout.lower().replace(' ', '_')}_"
                                                                f"{graph.lower()}{dist_str}_{algo_norm}_{metric_clean}")
                                                ]

                                for compare_col in compare_cols:
                                    value = row.get(compare_col)
                                    if value is None:
                                        continue

                                    change = ((value - ref_value) / ref_value * 100) if ref_value != 0 else 0
                                    row[compare_col] = round(change, 1)
                                    row_tooltip[compare_col] = f"{change:+.1f}%"

                                    # red/green color
                                    style_rules.extend([
                                        {
                                            "if": {
                                                "filter_query": f"{{{compare_col}}} < 0",
                                                "column_id": compare_col
                                            },
                                            "color": "green",
                                            "fontWeight": "bold"
                                        },
                                        {
                                            "if": {
                                                "filter_query": f"{{{compare_col}}} > 0",
                                                "column_id": compare_col
                                            },
                                            "color": "red",
                                            "fontWeight": "bold"
                                        },
                                    ])

            tooltip_data[row_idx] = row_tooltip

        avg_row = {"tf": "Average", "amrs": ""}
        for col in table_data[0].keys():
            if col in ["tf", "amrs"]:
                continue
            values = [row[col] for row in table_data if row.get(col) is not None and isinstance(row[col], (int, float))]
            avg_row[col] = round(np.mean(values), 2) if values else None

        table_data.append(avg_row)

        # Style for summary row
        style_rules.append({
            "if": {"filter_query": "{tf} = 'Average'"},
            "fontWeight": "bold",
            "backgroundColor": "#f0f0f0"
        })

        tooltip_data.append({})

        return table_data, style_rules, tooltip_data

    app.run(debug=True)


