import logging

import plotly.graph_objects as go

from api.client_api import get_order_info
from data.models import Station, OrderInfoRequest, AMRPORequest, AMRPathRequest
from logic.get_dataframe_functions import get_amr_df
from logic.get_info_functions import create_networkx_graph, get_interaction_nodes, get_station_types
import api.client_api

import config.config_file

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def create_map_figure_hovering(prev=False, curr=False, amr_id="0", future_orders=False):
    """
    :param prev: bool
    :param curr: bool
    :param amr_id: str
    :param future_orders: bool
    :return: Method to create an overview over the production layout and the position of the amr with planed orders
             1. ...
             2. ...
    """
    # Graph is graph
    node_color = {"0": 'green', "1": 'aqua', "2": 'lime', "3": 'greenyellow', "4": 'red', "5": 'yellow', "6": 'springgreen',
                  "7": 'darkred', "8": 'deepskyblue', "9": 'navy', "10": 'orange', "11": 'orangered', '12': 'blue'}
    station_type_color = {}
    legend = {}
    map_id = api.client_api.get_current_map_id().json()
    if map_id['mapId'] is not None:
        config.config_file.MAP_ID_DEFAULT = map_id['mapId']
    graph = create_networkx_graph()

    if len(graph.nodes) == 0:           # if not able to create sufficient graph, return
        return

    if amr_id == '0':
        amr_id_selected = '*'
    else:
        amr_id_selected = amr_id

    df_amrs = get_amr_df(amr_id_selected)
    interaction_nodes = get_interaction_nodes()
    stations_types = get_station_types()  # {Node: StationId} Node is element in interaction node from station
    response_prev, response_curr = None, None

    if prev:  # gets previous paths of all amr
        response_prev = api.client_api.get_amr_path_info(AMRPathRequest(amrId=amr_id_selected, prev=True)).json()
    if curr:  # gets current paths of all amr
        response_curr = api.client_api.get_amr_path_info(AMRPathRequest(amrId=amr_id_selected, prev=False)).json()
    future_orders_list = []
    if future_orders:
        response_future_orders = get_order_info(OrderInfoRequest(orderIds=['*'])).json()
        for future_order in response_future_orders:
            if future_order["orderStatus"] == "PLANNED":
                future_orders_list.append(future_order)
    planned_orders = {}
    if amr_id_selected != "*":
        planned_orders = api.client_api.get_amr_planned_orders(AMRPORequest(amrId=amr_id_selected)).json()

    node_x = []
    node_y = []
    node_text = []
    node_shape = []
    color_map = []

    edge_x = []
    edge_y = []
    edge_color_map = []
    edge_text_map = []

    for node in graph:  # iterates through node ID's in graph as String
        if node in interaction_nodes and not isinstance(graph.nodes[node]["data"], Station):
            # if the current node is an interaction node of the station draw the wanted colour
            type = stations_types[graph.nodes[node]["data"].nodeId]
            if type in node_color.keys():
                legend[type] = node_color[type]
                graph.nodes[node]["colour"] = node_color[type]
                graph.nodes[node]["text"] = stations_types[graph.nodes[node]["data"].nodeId]
            else:
                legend['Node'] = 'sandybrown'  # if no other case draw standard node colour
                graph.nodes[node]["colour"] = "sandybrown"
        elif isinstance(graph.nodes[node]["data"], Station):
            # if the current node is a station-node draw the wanted colour
            station_id = graph.nodes[node]["data"].stationName
            if station_id in node_color.keys():
                legend[station_id] = node_color[station_id]
                graph.nodes[node]["colour"] = node_color[station_id]
                graph.nodes[node]["text"] = station_id
            else:
                station_type_color[station_id] = node_color[
                    str(len(node_color.keys()) - len(station_type_color.keys()) - 1)]
                legend[station_id] = station_type_color[station_id]
                graph.nodes[node]["colour"] = station_type_color[station_id]
                graph.nodes[node]["text"] = stations_types[graph.nodes[node]["data"].nodeId]
        else:
            legend['Node'] = 'sandybrown'  # if no other case draw standard node colour
            graph.nodes[node]["colour"] = "sandybrown"
        if graph.nodes[node]["text"] is None:
            graph.nodes[node]["text"] = node
        else:
            graph.nodes[node]["text"] += str(" | " + node)

    if amr_id_selected == "*":
        for future_order in future_orders_list:
                graph.nodes[future_order["sourceNodeId"]]["shape"] = "square-open-dot"
                graph.nodes[future_order["sourceNodeId"]]["text"] += " | Pickup Order " + future_order["orderId"]
                graph.nodes[future_order["sinkNodeId"]]["shape"] = "triangle-up-open-dot"
                graph.nodes[future_order["sinkNodeId"]]["text"] += " | Dropoff Order " + future_order["orderId"]
    else:
        for future_order in future_orders_list:
            if future_order["amrId"] == amr_id_selected: # and
                graph.nodes[future_order["sourceNodeId"]]["shape"] = "square-open-dot"
                graph.nodes[future_order["sourceNodeId"]]["text"] += " | Pickup Order " + future_order["orderId"]
                graph.nodes[future_order["sinkNodeId"]]["shape"] = "triangle-up-open-dot"
                graph.nodes[future_order["sinkNodeId"]]["text"] += " | Dropoff Order " + future_order["orderId"]

    if df_amrs is not None:
        for index, row in df_amrs.iterrows():  # search through all AMR's, index not used, row are objects of type AMR
            node = graph.nodes[row['Last Position']]  # get the position node
            id = str((index+1) % 13)

            legend[str('AMR ' + row['AMR ID'])] = node_color[id]
            node["colour"] = node_color[id]
            node["shape"] = "hexagon"
            node["text"] += str(' | AMR ' + row["AMR ID"])

    if future_orders_list != [] or planned_orders != {}:
        legend["Pickup-Node Order"] = "black"
        legend["Dropoff-Node Order"] = "black"

    if df_amrs is not None:
        if response_prev is not None:
            for index, row in df_amrs.iterrows():
                try:
                    for future_order in response_prev[row["AMR ID"]]['order']["edges"]:
                        graph[future_order["startNodeId"]][future_order["endNodeId"]]["colour"] = legend[str('AMR ' + row['AMR ID'])]
                        graph[future_order["startNodeId"]][future_order["endNodeId"]]["text"] += "Order " + \
                                                                           response_prev[row["AMR ID"]]['order']["orderId"]
                except Exception as e:
                    logger.info('Error in creating in map figure for AMR: {}: {}'.format(row["AMR ID"], e))
                    break
        if response_curr is not None:
            for index, row in df_amrs.iterrows():
                try:
                    for edge in response_curr[row["AMR ID"]]['order']["edges"]:
                        graph[edge["startNodeId"]][edge["endNodeId"]]["colour"] = legend[str('AMR ' + row['AMR ID'])]
                        graph[edge["startNodeId"]][edge["endNodeId"]]["text"] += "Order " + \
                                                                           response_curr[row["AMR ID"]]['order'][
                                                                               "orderId"]
                    for node in response_curr[row["AMR ID"]]["order"]["nodes"]:
                        for action in node["actions"]:
                            if action["actionType"] == "DropOff":
                                if graph.nodes[node["nodeId"]]["shape"] != "hexagon":
                                    graph.nodes[node["nodeId"]]["shape"] = "triangle-up-open-dot"
                                if amr_id_selected == "*" and not future_orders:
                                    graph.nodes[node["nodeId"]]["text"] += " | Dropoff Order " + \
                                                                           response_curr[row["AMR ID"]]['order'][
                                                                               "orderId"]
                                continue
                            elif action["actionType"] == "PickUp":
                                if graph.nodes[node["nodeId"]]["shape"] != "hexagon":
                                    graph.nodes[node["nodeId"]]["shape"] = "square-open-dot"
                                if amr_id_selected == "*" and not future_orders:
                                    graph.nodes[node["nodeId"]]["text"] += " | Pickup Order " + \
                                                                           response_curr[row["AMR ID"]]['order'][
                                                                               "orderId"]
                                continue
                except Exception as e:
                    logger.info('Error in creating in map figure for AMR: {}: {}'.format(row["AMR ID"], e))
                    break

    for node in graph:  # instantiate all graph nodes
        x, y = graph.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
        color_map.append(graph.nodes[node]["colour"])
        node_text.append(graph.nodes[node]["text"])
        node_shape.append(graph.nodes[node]["shape"])

    for edge in graph.edges:
        x0, y0 = graph.nodes[edge[0]]['pos']
        x1, y1 = graph.nodes[edge[1]]['pos']
        edge_x += [x0, x1]
        edge_y += [y0, y1]
        edge_color_map.append(graph[edge[0]][edge[1]]["colour"])
        edge_text_map.append(graph[edge[0]][edge[1]]["text"])

    # load data into node an edge objects
    edge_traces = []
    edge_token_trace = []
    for i in range(0, len(edge_x), 2):  # edge have two x and y coordinates, increment accordingly
        if edge_color_map[i // 2] == 'black':
            big = 1
        else:
            big = 8  # multiplication for edge width
        edge_trace = go.Scatter(
            x=edge_x[i:i + 2],
            y=edge_y[i:i + 2],
            line=dict(
                width=0.5 * big,
                color=edge_color_map[i // 2],
            ),
            hoverinfo='text',
            # text=edge_text_map[i // 2],
            mode='lines',
            showlegend=False,
        )
        diff_x = (edge_x[i + 1] - edge_x[i]) // 2
        diff_y = (edge_y[i + 1] - edge_y[i]) // 2
        edge_token = go.Scatter(
            x=[edge_x[i] + diff_x, edge_x[i + 1] - diff_x],
            y=[edge_y[i] + diff_y, edge_y[i + 1] - diff_y],
            mode='markers',
            text=edge_text_map[i // 2],
            hoverinfo='text',
            marker=dict(
                showscale=False,  # no scala next to graph
                size=1,
                color="black",
                opacity=0),
            showlegend=False
        )

        edge_traces.append(edge_trace)
        edge_token_trace.append(edge_token)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers',
        text=node_text,
        hoverinfo='text',
        marker=dict(
            showscale=False,    # scala next to graph
            colorscale='YlGnBu',
            size=10,
            color=[],
            symbol=[],
            line_width=2),
        showlegend=False
    )
    node_trace.marker.color = color_map
    node_trace.marker.symbol = node_shape

    legend_traces = []
    for type_name, color in legend.items():
        if type_name == "Dropoff-Node Order":
            sym = "triangle-up-open-dot"
        elif type_name == "Pickup-Node Order":
            sym = "square-open-dot"
        else:
            sym = "circle"
        legend_trace = go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=15, color=color, symbol=sym),
            name=type_name,
            showlegend=True,
            legendgroup=type_name
        )

        legend_traces.append(legend_trace)

    fig = go.Figure(data=edge_traces + [node_trace] + legend_traces + edge_token_trace,
                    layout=go.Layout(
                        title='Production Layout',
                        showlegend=True,
                        legend=dict(
                            title='Legend',
                            x=1,
                            y=1,
                            traceorder='normal',
                            itemsizing='constant'
                        ),
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    ))
    return fig



